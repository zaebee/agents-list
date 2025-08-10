#!/usr/bin/env python3
"""
Database initialization script for AI-CRM authentication system.
"""

import os
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    create_tables, drop_tables, SessionLocal, seed_default_data,
    User, SubscriptionFeature, RateLimitRule, 
    UserRole, SubscriptionTier, AccountStatus
)
from auth import get_password_hash


def create_admin_user(db: Session, username: str, email: str, password: str, full_name: str = None):
    """Create an admin user."""
    
    # Check if admin user already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        print(f"User with username '{username}' or email '{email}' already exists.")
        return existing_user
    
    # Create admin user
    admin_user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=UserRole.ADMIN,
        subscription_tier=SubscriptionTier.ENTERPRISE,
        account_status=AccountStatus.ACTIVE,
        is_active=True,
        is_verified=True,  # Admin is pre-verified
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"Admin user '{username}' created successfully!")
    return admin_user


def create_test_users(db: Session):
    """Create test users for development."""
    
    test_users = [
        {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "role": UserRole.USER,
            "subscription_tier": SubscriptionTier.FREE
        },
        {
            "username": "promgr",
            "email": "manager@example.com",
            "password": "ManagerPass123!",
            "full_name": "Project Manager",
            "role": UserRole.MANAGER,
            "subscription_tier": SubscriptionTier.PRO
        },
        {
            "username": "enterprise",
            "email": "enterprise@example.com",
            "password": "EnterprisePass123!",
            "full_name": "Enterprise User",
            "role": UserRole.USER,
            "subscription_tier": SubscriptionTier.ENTERPRISE
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == user_data["username"]) | 
            (User.email == user_data["email"])
        ).first()
        
        if existing_user:
            print(f"Test user '{user_data['username']}' already exists.")
            created_users.append(existing_user)
            continue
        
        # Create test user
        test_user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            subscription_tier=user_data["subscription_tier"],
            account_status=AccountStatus.ACTIVE,
            is_active=True,
            is_verified=True,  # Test users are pre-verified
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(test_user)
        created_users.append(test_user)
        print(f"Test user '{user_data['username']}' created successfully!")
    
    db.commit()
    return created_users


def initialize_database(reset: bool = False, create_admin: bool = True, create_test: bool = False):
    """Initialize the database with tables and default data."""
    
    print("=== AI-CRM Database Initialization ===")
    
    if reset:
        print("Dropping existing tables...")
        drop_tables()
        print("Tables dropped successfully!")
    
    print("Creating database tables...")
    create_tables()
    print("Tables created successfully!")
    
    # Initialize session
    db = SessionLocal()
    
    try:
        print("Seeding default data...")
        seed_default_data(db)
        print("Default data seeded successfully!")
        
        # Create admin user
        if create_admin:
            print("\n=== Creating Admin User ===")
            admin_username = input("Admin username (default: admin): ").strip() or "admin"
            admin_email = input("Admin email (default: admin@example.com): ").strip() or "admin@example.com"
            admin_password = input("Admin password (default: AdminPass123!): ").strip() or "AdminPass123!"
            admin_full_name = input("Admin full name (default: System Administrator): ").strip() or "System Administrator"
            
            create_admin_user(db, admin_username, admin_email, admin_password, admin_full_name)
        
        # Create test users
        if create_test:
            print("\n=== Creating Test Users ===")
            create_test_users(db)
        
        print("\n=== Database Initialization Complete ===")
        print("Summary:")
        
        # Print statistics
        total_users = db.query(User).count()
        total_features = db.query(SubscriptionFeature).count()
        total_rate_limits = db.query(RateLimitRule).count()
        
        print(f"- Total users: {total_users}")
        print(f"- Subscription features: {total_features}")
        print(f"- Rate limit rules: {total_rate_limits}")
        
        # Print user breakdown
        for role in UserRole:
            count = db.query(User).filter(User.role == role).count()
            print(f"- {role.value.title()} users: {count}")
        
        for tier in SubscriptionTier:
            count = db.query(User).filter(User.subscription_tier == tier).count()
            print(f"- {tier.value.title()} subscribers: {count}")
        
        print("\nDatabase is ready for use!")
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


def main():
    """Main function with command-line interface."""
    
    print("AI-CRM Database Initialization Tool")
    print("=" * 40)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if "--reset" in sys.argv:
            reset = True
        else:
            reset = False
        
        if "--no-admin" in sys.argv:
            create_admin = False
        else:
            create_admin = True
        
        if "--test-users" in sys.argv:
            create_test = True
        else:
            create_test = False
    else:
        # Interactive mode
        reset = input("Reset database? (y/N): ").lower().startswith('y')
        create_admin = input("Create admin user? (Y/n): ").lower() != 'n'
        create_test = input("Create test users? (y/N): ").lower().startswith('y')
    
    # Confirmation for reset
    if reset:
        confirm = input("⚠️  This will DELETE ALL DATA! Are you sure? (type 'yes' to confirm): ")
        if confirm != 'yes':
            print("Aborted.")
            return
    
    # Run initialization
    try:
        initialize_database(reset=reset, create_admin=create_admin, create_test=create_test)
    except KeyboardInterrupt:
        print("\nInitialization cancelled.")
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()