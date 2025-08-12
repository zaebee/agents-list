#!/usr/bin/env python3
"""
Enhanced authentication utilities for AI-CRM system.
Integrates auth_database.py with existing security patterns.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import secrets
import os
import uuid
import re
import logging

from auth_database import (
    get_db,
    User,
    AuthSession,
    AuditLog,
    SubscriptionFeature,
    RateLimitRule,
)
from auth_database import UserRole, SubscriptionTier, AccountStatus

# Configure logging
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context with Argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=1,
)

# HTTP Bearer token security
security = HTTPBearer(auto_error=False)


class PasswordValidator:
    """Password strength validation."""

    @staticmethod
    def validate(password: str) -> Dict[str, Any]:
        """Validate password strength."""
        result = {"is_valid": False, "score": 0, "feedback": []}

        if len(password) < 8:
            result["feedback"].append("Password must be at least 8 characters long")
        else:
            result["score"] += 1

        if len(password) > 12:
            result["score"] += 1

        if re.search(r"[A-Z]", password):
            result["score"] += 1
        else:
            result["feedback"].append("Password should contain uppercase letters")

        if re.search(r"[a-z]", password):
            result["score"] += 1
        else:
            result["feedback"].append("Password should contain lowercase letters")

        if re.search(r"\d", password):
            result["score"] += 1
        else:
            result["feedback"].append("Password should contain numbers")

        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            result["score"] += 1
        else:
            result["feedback"].append("Password should contain special characters")

        # Check for common patterns
        common_patterns = ["123", "abc", "password", "qwerty", "000"]
        if any(pattern in password.lower() for pattern in common_patterns):
            result["feedback"].append("Password contains common patterns")
        else:
            result["score"] += 1

        result["is_valid"] = result["score"] >= 4 and len(result["feedback"]) == 0
        return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),  # JWT ID for token tracking
            "type": "access",
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: int) -> str:
    """Create a refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def authenticate_user(username: str, password: str, db: Session) -> Optional[Dict[str, Any]]:
    """Authenticate user with username/email and password."""
    try:
        # Try to find user by username or email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
            
        if not user.is_active or user.account_status != AccountStatus.ACTIVE:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
        
        # Convert to dict for compatibility with existing code
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if user.role else "user",
            "subscription_tier": user.subscription_tier.value if user.subscription_tier else "free",
            "disabled": not user.is_active
        }
        
        return user_dict
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    # Verify token
    payload = verify_token(credentials.credentials)
    if not payload:
        raise credentials_exception

    # Check token type
    if payload.get("type") != "access":
        raise credentials_exception

    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    try:
        user_id = int(user_id)
    except ValueError:
        raise credentials_exception

    # Check if token is blacklisted (session still active)
    jti = payload.get("jti")
    if jti:
        session = (
            db.query(AuthSession)
            .filter(AuthSession.access_token_jti == jti, AuthSession.is_active == True)
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception

    # Check if user is active
    if not user.is_active or user.account_status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
        )

    # Convert to dict for compatibility
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value if user.role else "user",
        "subscription_tier": user.subscription_tier.value if user.subscription_tier else "free",
        "disabled": not user.is_active
    }

    return user_dict


def require_roles(allowed_roles: List[UserRole]):
    """Decorator to require specific roles."""

    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = UserRole(current_user.get("role", "user"))
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return role_checker


def require_subscription_tier(required_tier: SubscriptionTier):
    """Decorator to require specific subscription tier or higher."""
    tier_hierarchy = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 1,
        SubscriptionTier.ENTERPRISE: 2,
    }

    def tier_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_tier = SubscriptionTier(current_user.get("subscription_tier", "free"))
        user_tier_level = tier_hierarchy.get(user_tier, -1)
        required_tier_level = tier_hierarchy.get(required_tier, 999)

        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_tier.value} subscription or higher",
            )
        return current_user

    return tier_checker


async def check_feature_access(
    feature_name: str,
    current_user: Dict[str, Any],
    db: Session,
    usage_count: Optional[int] = None,
) -> bool:
    """Check if user has access to a specific feature."""
    feature = (
        db.query(SubscriptionFeature)
        .filter(
            SubscriptionFeature.feature_name == feature_name,
            SubscriptionFeature.is_active == True,
        )
        .first()
    )

    if not feature:
        return False

    # Check tier access
    user_tier = SubscriptionTier(current_user.get("subscription_tier", "free"))
    tier_access = {
        SubscriptionTier.FREE: feature.free_tier,
        SubscriptionTier.PRO: feature.pro_tier,
        SubscriptionTier.ENTERPRISE: feature.enterprise_tier,
    }

    if not tier_access.get(user_tier, False):
        return False

    # Check usage limits if provided
    if usage_count is not None:
        tier_limits = {
            SubscriptionTier.FREE: feature.free_limit,
            SubscriptionTier.PRO: feature.pro_limit,
            SubscriptionTier.ENTERPRISE: feature.enterprise_limit,
        }

        limit = tier_limits.get(user_tier)
        if limit is not None and usage_count >= limit:
            return False

    return True


def require_feature_access(feature_name: str):
    """Decorator to require access to a specific feature."""

    def feature_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        if not check_feature_access(feature_name, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_name}' not available for your subscription tier",
            )
        return current_user

    return feature_checker