"""
AI-CRM Authentication Module

Handles user authentication, authorization, security, and access control.
"""

# Import key components for easy access
from .auth import (
    PasswordValidator,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    verify_password,
    verify_token,
    require_roles,
    require_subscription_tier,
    check_feature_access,
    require_feature_access,
)

from .database import (
    AccountStatus,
    AuthSession,
    AuditLog,
    RateLimitRule,
    SubscriptionFeature,
    SubscriptionTier,
    User,
    UserRole,
    get_db,
    create_tables,
    seed_default_data,
)

from .routes import router as auth_router

__all__ = [
    # Core auth functions
    "PasswordValidator",
    "authenticate_user", 
    "create_access_token",
    "create_refresh_token",
    "get_current_user",
    "get_password_hash",
    "verify_password",
    "verify_token",
    "require_roles",
    "require_subscription_tier", 
    "check_feature_access",
    "require_feature_access",
    
    # Database models and enums
    "AccountStatus",
    "AuthSession",
    "AuditLog", 
    "RateLimitRule",
    "SubscriptionFeature",
    "SubscriptionTier",
    "User",
    "UserRole",
    "get_db",
    "create_tables",
    "seed_default_data",
    
    # FastAPI router
    "auth_router",
    
    # Submodules
    "auth",
    "database", 
    "routes",
    "security",
]