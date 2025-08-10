#!/usr/bin/env python3
"""
Database configuration and models for AI-CRM authentication system.
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enum import Enum
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_crm.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Enums
class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro" 
    ENTERPRISE = "enterprise"

class UserRole(str, Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"

class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PENDING_VERIFICATION = "pending_verification"

# Database Models
class User(Base):
    """User model for authentication and profile management."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # Account status and verification
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    account_status = Column(SQLEnum(AccountStatus), default=AccountStatus.PENDING_VERIFICATION)
    
    # Role and subscription
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Verification tokens
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking for subscription limits
    monthly_tasks_created = Column(Integer, default=0)
    last_task_reset = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    auth_sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class AuthSession(Base):
    """JWT session tracking for secure token management."""
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token = Column(String(255), unique=True, index=True, nullable=False)
    access_token_jti = Column(String(255), index=True, nullable=False)  # JWT ID for access token
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Session control
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="auth_sessions")


class AuditLog(Base):
    """Audit logging for security and compliance."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # LOGIN, LOGOUT, PASSWORD_CHANGE, etc.
    resource = Column(String(100), nullable=True)  # Resource accessed
    action = Column(String(50), nullable=True)  # Action performed
    result = Column(String(20), nullable=False)  # SUCCESS, FAILURE, ERROR
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True)
    
    # Additional context
    details = Column(Text, nullable=True)  # JSON string with additional context
    risk_score = Column(Integer, default=0)  # Risk assessment score
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class SubscriptionFeature(Base):
    """Feature access control based on subscription tiers."""
    __tablename__ = "subscription_features"

    id = Column(Integer, primary_key=True, index=True)
    feature_name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Tier access
    free_tier = Column(Boolean, default=False)
    pro_tier = Column(Boolean, default=False)
    enterprise_tier = Column(Boolean, default=False)
    
    # Usage limits (null means unlimited)
    free_limit = Column(Integer, nullable=True)
    pro_limit = Column(Integer, nullable=True)
    enterprise_limit = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class RateLimitRule(Base):
    """Rate limiting rules per subscription tier."""
    __tablename__ = "rate_limit_rules"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_pattern = Column(String(200), nullable=False, index=True)  # Regex pattern for endpoints
    subscription_tier = Column(SQLEnum(SubscriptionTier), nullable=False)
    
    # Rate limit configuration
    requests_per_minute = Column(Integer, default=60)
    requests_per_hour = Column(Integer, default=1000)
    requests_per_day = Column(Integer, default=10000)
    
    # Burst allowance
    burst_size = Column(Integer, default=10)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


# Database session dependency for FastAPI
def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables (use with caution!)."""
    Base.metadata.drop_all(bind=engine)


# Initialize default features and rate limits
DEFAULT_FEATURES = [
    {
        "feature_name": "task_creation",
        "description": "Create and manage tasks",
        "free_tier": True,
        "pro_tier": True,
        "enterprise_tier": True,
        "free_limit": 10,
        "pro_limit": None,
        "enterprise_limit": None
    },
    {
        "feature_name": "ai_agent_access",
        "description": "Access to AI agents for task assistance",
        "free_tier": True,
        "pro_tier": True,
        "enterprise_tier": True,
        "free_limit": 9,  # Haiku agents only
        "pro_limit": 46,  # Haiku + Sonnet agents
        "enterprise_limit": None  # All agents
    },
    {
        "feature_name": "analytics_dashboard",
        "description": "Access to analytics and reporting",
        "free_tier": False,
        "pro_tier": True,
        "enterprise_tier": True
    },
    {
        "feature_name": "api_access",
        "description": "REST API access",
        "free_tier": False,
        "pro_tier": True,
        "enterprise_tier": True
    },
    {
        "feature_name": "custom_agents",
        "description": "Create and deploy custom AI agents",
        "free_tier": False,
        "pro_tier": False,
        "enterprise_tier": True
    },
    {
        "feature_name": "priority_support",
        "description": "Priority email support",
        "free_tier": False,
        "pro_tier": True,
        "enterprise_tier": True
    },
    {
        "feature_name": "sso_integration",
        "description": "Single Sign-On integration",
        "free_tier": False,
        "pro_tier": False,
        "enterprise_tier": True
    }
]

DEFAULT_RATE_LIMITS = [
    {
        "endpoint_pattern": "/tasks.*",
        "subscription_tier": SubscriptionTier.FREE,
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 500
    },
    {
        "endpoint_pattern": "/tasks.*",
        "subscription_tier": SubscriptionTier.PRO,
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    {
        "endpoint_pattern": "/tasks.*",
        "subscription_tier": SubscriptionTier.ENTERPRISE,
        "requests_per_minute": 200,
        "requests_per_hour": 5000,
        "requests_per_day": 50000
    },
    {
        "endpoint_pattern": "/auth.*",
        "subscription_tier": SubscriptionTier.FREE,
        "requests_per_minute": 5,
        "requests_per_hour": 20,
        "requests_per_day": 100
    },
    {
        "endpoint_pattern": "/analytics.*",
        "subscription_tier": SubscriptionTier.PRO,
        "requests_per_minute": 30,
        "requests_per_hour": 500,
        "requests_per_day": 2000
    },
    {
        "endpoint_pattern": "/analytics.*",
        "subscription_tier": SubscriptionTier.ENTERPRISE,
        "requests_per_minute": 100,
        "requests_per_hour": 2000,
        "requests_per_day": 20000
    }
]


def seed_default_data(db: SessionLocal):
    """Seed database with default features and rate limits."""
    # Add subscription features
    for feature_data in DEFAULT_FEATURES:
        existing = db.query(SubscriptionFeature).filter_by(feature_name=feature_data["feature_name"]).first()
        if not existing:
            feature = SubscriptionFeature(**feature_data)
            db.add(feature)
    
    # Add rate limit rules
    for rate_limit_data in DEFAULT_RATE_LIMITS:
        existing = db.query(RateLimitRule).filter_by(
            endpoint_pattern=rate_limit_data["endpoint_pattern"],
            subscription_tier=rate_limit_data["subscription_tier"]
        ).first()
        if not existing:
            rate_limit = RateLimitRule(**rate_limit_data)
            db.add(rate_limit)
    
    db.commit()


if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")
    
    # Seed default data
    db = SessionLocal()
    try:
        seed_default_data(db)
        print("Default data seeded successfully!")
    finally:
        db.close()