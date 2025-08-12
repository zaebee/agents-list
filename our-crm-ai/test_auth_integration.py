#!/usr/bin/env python3
"""
Test script for the new authentication integration.
"""

import asyncio
import requests
import json
from auth_database import SessionLocal, User
from auth import get_password_hash
from auth_database import UserRole, SubscriptionTier, AccountStatus

def create_test_user():
    """Create a test user for authentication testing."""
    db = SessionLocal()
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            print("Test user already exists")
            return existing_user.id
        
        # Create test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword123"),
            full_name="Test User",
            is_active=True,
            is_verified=True,
            account_status=AccountStatus.ACTIVE,
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"Created test user with ID: {test_user.id}")
        return test_user.id
        
    finally:
        db.close()

def test_login_api():
    """Test the login API endpoint."""
    try:
        # Create test user
        user_id = create_test_user()
        
        # Test login
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        print("Testing login endpoint...")
        print(f"Login data: {login_data}")
        
        # This would normally be a request to the actual API
        # For now, we'll test the auth function directly
        from auth import authenticate_user
        from auth_database import SessionLocal
        
        db = SessionLocal()
        try:
            result = authenticate_user("testuser", "testpassword123", db)
            print(f"Authentication result: {result}")
            
            if result:
                print("✅ Authentication successful!")
                print(f"User details: {json.dumps(result, indent=2, default=str)}")
            else:
                print("❌ Authentication failed!")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run authentication tests."""
    print("🧪 Testing AI-CRM Authentication Integration")
    print("=" * 50)
    
    test_login_api()
    
    print("\n✅ Authentication integration test complete!")

if __name__ == "__main__":
    main()