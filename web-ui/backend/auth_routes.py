#!/usr/bin/env python3
"""
Authentication API routes for AI-CRM system.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
import secrets
import logging

from database import get_db, User, AuthSession, AuditLog
from database import UserRole, SubscriptionTier, AccountStatus
from auth import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    verify_token, get_current_user, get_current_active_user, PasswordValidator,
    log_auth_event, generate_verification_token, send_verification_email,
    send_password_reset_email, create_session, invalidate_user_sessions,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for requests/responses
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)

class UserLogin(BaseModel):
    username_or_email: str
    password: str
    remember_me: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class EmailVerification(BaseModel):
    token: str

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    subscription_tier: SubscriptionTier
    account_status: AccountStatus
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    monthly_tasks_created: int


@router.post("/register", response_model=dict)
async def register_user(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user account."""
    
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        await log_auth_event(
            db, None, "REGISTER_ATTEMPT", "FAILURE", request,
            f"Username already exists: {user_data.username}", risk_score=3
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        await log_auth_event(
            db, None, "REGISTER_ATTEMPT", "FAILURE", request,
            f"Email already exists: {user_data.email}", risk_score=3
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    password_validation = PasswordValidator.validate(user_data.password)
    if not password_validation["is_valid"]:
        await log_auth_event(
            db, None, "REGISTER_ATTEMPT", "FAILURE", request,
            f"Weak password for user: {user_data.username}", risk_score=2
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet security requirements",
                "feedback": password_validation["feedback"]
            }
        )
    
    try:
        # Generate verification token
        verification_token = await generate_verification_token()
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            email_verification_token=verification_token,
            account_status=AccountStatus.PENDING_VERIFICATION
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send verification email
        background_tasks.add_task(
            send_verification_email,
            user_data.email,
            verification_token
        )
        
        # Log successful registration
        await log_auth_event(
            db, user.id, "REGISTER", "SUCCESS", request,
            f"User registered: {user.username}", risk_score=0
        )
        
        return {
            "message": "User registered successfully. Please check your email for verification.",
            "user_id": user.id,
            "requires_verification": True
        }
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.rollback()
        await log_auth_event(
            db, None, "REGISTER_ATTEMPT", "ERROR", request,
            f"Registration error for {user_data.username}: {str(e)}", risk_score=5
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/verify-email", response_model=dict)
async def verify_email(
    verification_data: EmailVerification,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify user email address."""
    
    user = db.query(User).filter(
        User.email_verification_token == verification_data.token
    ).first()
    
    if not user:
        await log_auth_event(
            db, None, "EMAIL_VERIFICATION", "FAILURE", request,
            f"Invalid verification token: {verification_data.token}", risk_score=4
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    try:
        # Update user verification status
        user.is_verified = True
        user.account_status = AccountStatus.ACTIVE
        user.email_verification_token = None
        
        db.commit()
        
        await log_auth_event(
            db, user.id, "EMAIL_VERIFICATION", "SUCCESS", request,
            f"Email verified for user: {user.username}", risk_score=0
        )
        
        return {
            "message": "Email verified successfully. You can now log in.",
            "is_verified": True
        }
    
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access/refresh tokens."""
    
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == login_data.username_or_email) |
        (User.email == login_data.username_or_email)
    ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        await log_auth_event(
            db, user.id if user else None, "LOGIN_ATTEMPT", "FAILURE", request,
            f"Invalid credentials for: {login_data.username_or_email}", risk_score=6
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
    
    # Check account status
    if not user.is_active:
        await log_auth_event(
            db, user.id, "LOGIN_ATTEMPT", "FAILURE", request,
            f"Inactive account login attempt: {user.username}", risk_score=4
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    if user.account_status == AccountStatus.SUSPENDED:
        await log_auth_event(
            db, user.id, "LOGIN_ATTEMPT", "FAILURE", request,
            f"Suspended account login attempt: {user.username}", risk_score=7
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is suspended"
        )
    
    if user.account_status == AccountStatus.PENDING_VERIFICATION:
        await log_auth_event(
            db, user.id, "LOGIN_ATTEMPT", "FAILURE", request,
            f"Unverified account login attempt: {user.username}", risk_score=3
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email address before logging in"
        )
    
    try:
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        if login_data.remember_me:
            access_token_expires = timedelta(hours=24)  # Longer session for "remember me"
        
        access_token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "subscription_tier": user.subscription_tier.value
        }
        
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(user.id)
        
        # Decode token to get JTI
        token_payload = verify_token(access_token)
        access_token_jti = token_payload.get("jti") if token_payload else str(secrets.token_urlsafe(16))
        
        # Create session
        session_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        session = create_session(
            db, user.id, refresh_token, access_token_jti, request, session_expires
        )
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        # Log successful login
        await log_auth_event(
            db, user.id, "LOGIN", "SUCCESS", request,
            f"Successful login: {user.username}", risk_score=0
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "subscription_tier": user.subscription_tier.value,
                "is_verified": user.is_verified
            }
        )
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        db.rollback()
        await log_auth_event(
            db, user.id, "LOGIN_ATTEMPT", "ERROR", request,
            f"Login error for {user.username}: {str(e)}", risk_score=5
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    
    # Verify refresh token
    payload = verify_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        await log_auth_event(
            db, None, "TOKEN_REFRESH", "FAILURE", request,
            "Invalid refresh token", risk_score=5
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if session exists and is active
    session = db.query(AuthSession).filter(
        AuthSession.refresh_token == token_data.refresh_token,
        AuthSession.is_active == True
    ).first()
    
    if not session:
        await log_auth_event(
            db, user_id, "TOKEN_REFRESH", "FAILURE", request,
            "Refresh token not found or inactive", risk_score=6
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    # Check if session has expired
    if session.expires_at < datetime.now(timezone.utc):
        session.is_active = False
        db.commit()
        await log_auth_event(
            db, user_id, "TOKEN_REFRESH", "FAILURE", request,
            "Expired refresh token", risk_score=4
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active or user.account_status != AccountStatus.ACTIVE:
        await log_auth_event(
            db, user_id, "TOKEN_REFRESH", "FAILURE", request,
            "User not found or inactive", risk_score=5
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is no longer active"
        )
    
    try:
        # Create new access token
        access_token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "subscription_tier": user.subscription_tier.value
        }
        
        access_token = create_access_token(data=access_token_data)
        
        # Update session with new access token JTI
        token_payload = verify_token(access_token)
        session.access_token_jti = token_payload.get("jti") if token_payload else str(secrets.token_urlsafe(16))
        session.last_used = datetime.now(timezone.utc)
        db.commit()
        
        # Log successful refresh
        await log_auth_event(
            db, user.id, "TOKEN_REFRESH", "SUCCESS", request,
            f"Token refreshed for user: {user.username}", risk_score=0
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # Keep same refresh token
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "subscription_tier": user.subscription_tier.value,
                "is_verified": user.is_verified
            }
        )
    
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=dict)
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate tokens."""
    
    try:
        # Get authorization header to find current session
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = verify_token(token)
            if payload:
                jti = payload.get("jti")
                if jti:
                    # Find and deactivate current session
                    session = db.query(AuthSession).filter(
                        AuthSession.access_token_jti == jti,
                        AuthSession.user_id == current_user.id
                    ).first()
                    if session:
                        session.is_active = False
        
        db.commit()
        
        # Log logout
        await log_auth_event(
            db, current_user.id, "LOGOUT", "SUCCESS", request,
            f"User logged out: {current_user.username}", risk_score=0
        )
        
        return {"message": "Successfully logged out"}
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/logout-all", response_model=dict)
async def logout_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout from all sessions."""
    
    try:
        # Invalidate all user sessions
        sessions_invalidated = invalidate_user_sessions(db, current_user.id)
        
        # Log logout all
        await log_auth_event(
            db, current_user.id, "LOGOUT_ALL", "SUCCESS", request,
            f"All sessions logged out for user: {current_user.username} ({sessions_invalidated} sessions)",
            risk_score=0
        )
        
        return {
            "message": f"Successfully logged out from all sessions",
            "sessions_invalidated": sessions_invalidated
        }
    
    except Exception as e:
        logger.error(f"Logout all error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout from all sessions failed"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        subscription_tier=current_user.subscription_tier,
        account_status=current_user.account_status,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        monthly_tasks_created=current_user.monthly_tasks_created
    )


@router.post("/request-password-reset", response_model=dict)
async def request_password_reset(
    reset_data: PasswordReset,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset."""
    
    user = db.query(User).filter(User.email == reset_data.email).first()
    if not user:
        # Don't reveal if email exists or not
        await log_auth_event(
            db, None, "PASSWORD_RESET_REQUEST", "FAILURE", request,
            f"Password reset requested for non-existent email: {reset_data.email}",
            risk_score=3
        )
        return {"message": "If the email exists, a password reset link has been sent."}
    
    try:
        # Generate reset token
        reset_token = await generate_verification_token()
        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
        
        user.password_reset_token = reset_token
        user.password_reset_expires = reset_expires
        db.commit()
        
        # Send reset email
        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            reset_token
        )
        
        # Log password reset request
        await log_auth_event(
            db, user.id, "PASSWORD_RESET_REQUEST", "SUCCESS", request,
            f"Password reset requested for: {user.username}", risk_score=2
        )
        
        return {"message": "If the email exists, a password reset link has been sent."}
    
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password", response_model=dict)
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset password with token."""
    
    user = db.query(User).filter(
        User.password_reset_token == reset_data.token
    ).first()
    
    if not user:
        await log_auth_event(
            db, None, "PASSWORD_RESET", "FAILURE", request,
            f"Invalid password reset token: {reset_data.token}", risk_score=6
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset token"
        )
    
    # Check if token has expired
    if not user.password_reset_expires or user.password_reset_expires < datetime.now(timezone.utc):
        await log_auth_event(
            db, user.id, "PASSWORD_RESET", "FAILURE", request,
            f"Expired password reset token for user: {user.username}", risk_score=4
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired"
        )
    
    # Validate new password
    password_validation = PasswordValidator.validate(reset_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet security requirements",
                "feedback": password_validation["feedback"]
            }
        )
    
    try:
        # Update password
        user.hashed_password = get_password_hash(reset_data.new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.commit()
        
        # Invalidate all user sessions
        invalidate_user_sessions(db, user.id)
        
        # Log password reset
        await log_auth_event(
            db, user.id, "PASSWORD_RESET", "SUCCESS", request,
            f"Password reset completed for user: {user.username}", risk_score=1
        )
        
        return {"message": "Password reset successful. Please log in with your new password."}
    
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        await log_auth_event(
            db, current_user.id, "PASSWORD_CHANGE", "FAILURE", request,
            f"Incorrect current password for user: {current_user.username}", risk_score=5
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    password_validation = PasswordValidator.validate(password_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet security requirements",
                "feedback": password_validation["feedback"]
            }
        )
    
    # Check if new password is different from current
    if verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    try:
        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()
        
        # Log password change
        await log_auth_event(
            db, current_user.id, "PASSWORD_CHANGE", "SUCCESS", request,
            f"Password changed for user: {current_user.username}", risk_score=1
        )
        
        return {"message": "Password changed successfully"}
    
    except Exception as e:
        logger.error(f"Password change error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )