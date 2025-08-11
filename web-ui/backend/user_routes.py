#!/usr/bin/env python3
"""
User management API routes for AI-CRM system.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import logging

from database import get_db, User, AuthSession
from database import UserRole, SubscriptionTier, AccountStatus
from auth import (
    get_current_active_user,
    require_roles,
    log_auth_event,
    check_feature_access,
    invalidate_user_sessions,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/users", tags=["user_management"])


# Pydantic models
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    subscription_tier: Optional[SubscriptionTier] = None
    account_status: Optional[AccountStatus] = None
    is_active: Optional[bool] = None


class UserListResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    subscription_tier: SubscriptionTier
    account_status: AccountStatus
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    monthly_tasks_created: int


class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    subscription_breakdown: Dict[str, int]
    role_breakdown: Dict[str, int]
    recent_registrations: int


class SessionInfo(BaseModel):
    id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool
    created_at: datetime
    last_used: datetime
    expires_at: datetime


@router.get("/profile", response_model=UserListResponse)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's detailed profile."""

    return UserListResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        subscription_tier=current_user.subscription_tier,
        account_status=current_user.account_status,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        monthly_tasks_created=current_user.monthly_tasks_created,
    )


@router.put("/profile", response_model=dict)
async def update_user_profile(
    profile_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile."""

    try:
        # Check if email is being changed and if it's already taken
        if profile_data.email and profile_data.email != current_user.email:
            existing_user = (
                db.query(User)
                .filter(User.email == profile_data.email, User.id != current_user.id)
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already registered to another account",
                )

            # If email is changed, require re-verification
            current_user.email = profile_data.email
            current_user.is_verified = False
            current_user.account_status = AccountStatus.PENDING_VERIFICATION
            # TODO: Send new verification email

        # Update other fields
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name

        db.commit()

        # Log profile update
        await log_auth_event(
            db,
            current_user.id,
            "PROFILE_UPDATE",
            "SUCCESS",
            request,
            f"Profile updated for user: {current_user.username}",
            risk_score=1,
        )

        return {
            "message": "Profile updated successfully",
            "requires_verification": profile_data.email
            and profile_data.email != current_user.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed",
        )


@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get current user's active sessions."""

    sessions = (
        db.query(AuthSession)
        .filter(AuthSession.user_id == current_user.id, AuthSession.is_active == True)
        .order_by(AuthSession.last_used.desc())
        .all()
    )

    return [
        SessionInfo(
            id=session.id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            is_active=session.is_active,
            created_at=session.created_at,
            last_used=session.last_used,
            expires_at=session.expires_at,
        )
        for session in sessions
    ]


@router.delete("/sessions/{session_id}", response_model=dict)
async def revoke_session(
    session_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke a specific session."""

    session = (
        db.query(AuthSession)
        .filter(AuthSession.id == session_id, AuthSession.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    try:
        session.is_active = False
        db.commit()

        # Log session revocation
        await log_auth_event(
            db,
            current_user.id,
            "SESSION_REVOKE",
            "SUCCESS",
            request,
            f"Session {session_id} revoked by user: {current_user.username}",
            risk_score=1,
        )

        return {"message": "Session revoked successfully"}

    except Exception as e:
        logger.error(f"Session revocation error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session revocation failed",
        )


@router.get("/subscription/features", response_model=dict)
async def get_user_features(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get current user's available features based on subscription tier."""

    from database import SubscriptionFeature

    features = (
        db.query(SubscriptionFeature)
        .filter(SubscriptionFeature.is_active == True)
        .all()
    )

    available_features = {}
    for feature in features:
        has_access = await check_feature_access(feature.feature_name, current_user, db)

        # Get usage limit for user's tier
        tier_limits = {
            SubscriptionTier.FREE: feature.free_limit,
            SubscriptionTier.PRO: feature.pro_limit,
            SubscriptionTier.ENTERPRISE: feature.enterprise_limit,
        }

        available_features[feature.feature_name] = {
            "has_access": has_access,
            "description": feature.description,
            "usage_limit": tier_limits.get(current_user.subscription_tier),
            "current_usage": 0,  # TODO: Implement usage tracking per feature
        }

    return {
        "subscription_tier": current_user.subscription_tier.value,
        "features": available_features,
    }


@router.get("/usage/monthly", response_model=dict)
async def get_monthly_usage(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get user's monthly usage statistics."""

    # Check if we need to reset monthly counters
    current_date = datetime.now(timezone.utc)
    if (
        current_user.last_task_reset.month != current_date.month
        or current_user.last_task_reset.year != current_date.year
    ):
        current_user.monthly_tasks_created = 0
        current_user.last_task_reset = current_date
        db.commit()

    # Get subscription limits
    from database import SubscriptionFeature

    task_feature = (
        db.query(SubscriptionFeature)
        .filter(
            SubscriptionFeature.feature_name == "task_creation",
            SubscriptionFeature.is_active == True,
        )
        .first()
    )

    tier_limits = {
        SubscriptionTier.FREE: task_feature.free_limit if task_feature else 10,
        SubscriptionTier.PRO: task_feature.pro_limit if task_feature else None,
        SubscriptionTier.ENTERPRISE: task_feature.enterprise_limit
        if task_feature
        else None,
    }

    monthly_limit = tier_limits.get(current_user.subscription_tier)

    return {
        "period": f"{current_date.year}-{current_date.month:02d}",
        "tasks_created": current_user.monthly_tasks_created,
        "tasks_limit": monthly_limit,
        "subscription_tier": current_user.subscription_tier.value,
        "reset_date": current_user.last_task_reset.isoformat(),
    }


# Admin-only endpoints
@router.get("/admin/list", response_model=Dict[str, Any])
async def list_users_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    subscription_tier: Optional[SubscriptionTier] = Query(None),
    account_status: Optional[AccountStatus] = Query(None),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """List all users with filtering and pagination (Admin only)."""

    query = db.query(User)

    # Apply filters
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    if role:
        query = query.filter(User.role == role)

    if subscription_tier:
        query = query.filter(User.subscription_tier == subscription_tier)

    if account_status:
        query = query.filter(User.account_status == account_status)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    users = query.offset(offset).limit(limit).order_by(User.created_at.desc()).all()

    # Convert to response format
    user_list = [
        UserListResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            subscription_tier=user.subscription_tier,
            account_status=user.account_status,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            monthly_tasks_created=user.monthly_tasks_created,
        )
        for user in users
    ]

    return {
        "users": user_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
    }


@router.get("/admin/stats", response_model=UserStatsResponse)
async def get_user_stats_admin(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Get user statistics (Admin only)."""

    # Basic counts
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()

    # Recent registrations (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_registrations = (
        db.query(User).filter(User.created_at >= thirty_days_ago).count()
    )

    # Subscription breakdown
    subscription_stats = (
        db.query(User.subscription_tier, func.count(User.id).label("count"))
        .group_by(User.subscription_tier)
        .all()
    )

    subscription_breakdown = {tier.value: count for tier, count in subscription_stats}

    # Role breakdown
    role_stats = (
        db.query(User.role, func.count(User.id).label("count"))
        .group_by(User.role)
        .all()
    )

    role_breakdown = {role.value: count for role, count in role_stats}

    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        verified_users=verified_users,
        subscription_breakdown=subscription_breakdown,
        role_breakdown=role_breakdown,
        recent_registrations=recent_registrations,
    )


@router.put("/admin/{user_id}", response_model=dict)
async def update_user_admin(
    user_id: int,
    update_data: AdminUserUpdate,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Update user account (Admin only)."""

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        changes = []

        # Check email uniqueness
        if update_data.email and update_data.email != target_user.email:
            existing_user = (
                db.query(User)
                .filter(User.email == update_data.email, User.id != user_id)
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already registered to another account",
                )

            target_user.email = update_data.email
            changes.append(f"email changed to {update_data.email}")

        # Update fields
        if update_data.full_name is not None:
            target_user.full_name = update_data.full_name
            changes.append("full_name updated")

        if update_data.role is not None:
            old_role = target_user.role
            target_user.role = update_data.role
            changes.append(
                f"role changed from {old_role.value} to {update_data.role.value}"
            )

        if update_data.subscription_tier is not None:
            old_tier = target_user.subscription_tier
            target_user.subscription_tier = update_data.subscription_tier
            changes.append(
                f"subscription changed from {old_tier.value} to {update_data.subscription_tier.value}"
            )

        if update_data.account_status is not None:
            old_status = target_user.account_status
            target_user.account_status = update_data.account_status
            changes.append(
                f"account status changed from {old_status.value} to {update_data.account_status.value}"
            )

            # If suspending user, invalidate all sessions
            if update_data.account_status == AccountStatus.SUSPENDED:
                invalidate_user_sessions(db, user_id)
                changes.append("all sessions invalidated")

        if update_data.is_active is not None:
            target_user.is_active = update_data.is_active
            changes.append(f"is_active set to {update_data.is_active}")

            # If deactivating user, invalidate all sessions
            if not update_data.is_active:
                invalidate_user_sessions(db, user_id)
                changes.append("all sessions invalidated")

        db.commit()

        # Log admin action
        await log_auth_event(
            db,
            current_user.id,
            "ADMIN_USER_UPDATE",
            "SUCCESS",
            request,
            f"Admin {current_user.username} updated user {target_user.username}: {', '.join(changes)}",
            risk_score=2,
        )

        return {"message": "User updated successfully", "changes": changes}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin user update error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed",
        )


@router.delete("/admin/{user_id}", response_model=dict)
async def delete_user_admin(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Delete user account (Admin only)."""

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent admin from deleting themselves
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    try:
        # Mark as deleted instead of hard delete (GDPR compliance)
        target_user.account_status = AccountStatus.DELETED
        target_user.is_active = False

        # Invalidate all sessions
        invalidate_user_sessions(db, user_id)

        # Anonymize sensitive data
        target_user.email = f"deleted_user_{user_id}@deleted.local"
        target_user.full_name = None

        db.commit()

        # Log admin action
        await log_auth_event(
            db,
            current_user.id,
            "ADMIN_USER_DELETE",
            "SUCCESS",
            request,
            f"Admin {current_user.username} deleted user: {target_user.username}",
            risk_score=8,
        )

        return {"message": "User account deleted successfully"}

    except Exception as e:
        logger.error(f"Admin user delete error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed",
        )
