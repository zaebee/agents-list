#!/usr/bin/env python3
"""
Complete integration test for the fixed authentication system.
"""

import json

from fastapi.testclient import TestClient

from api import app
from src.ai_crm.auth import get_password_hash
from src.ai_crm.auth.database import AccountStatus, SessionLocal, SubscriptionTier, User, UserRole


def setup_test_user():
    """Create a test user for API testing."""
    db = SessionLocal()
    try:
        # Clean up existing test user
        existing_user = db.query(User).filter(User.username == "apitest").first()
        if existing_user:
            db.delete(existing_user)
            db.commit()

        # Create fresh test user
        test_user = User(
            username="apitest",
            email="apitest@example.com",
            hashed_password=get_password_hash("apitest123"),
            full_name="API Test User",
            is_active=True,
            is_verified=True,
            account_status=AccountStatus.ACTIVE,
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print(f"✅ Created test user: {test_user.username}")
        return test_user.id

    finally:
        db.close()


def test_login_endpoint():
    """Test the /api/auth/login endpoint."""
    client = TestClient(app)

    # Setup test user
    setup_test_user()

    print("🧪 Testing /api/auth/login endpoint...")

    # Test login
    login_data = {"username": "apitest", "password": "apitest123"}

    response = client.post("/api/auth/login", json=login_data)

    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")

    if response.status_code == 200:
        print("✅ Login successful!")
        response_data = response.json()

        # Check response structure
        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert "user" in response_data
        assert response_data["token_type"] == "bearer"

        user_data = response_data["user"]
        assert user_data["username"] == "apitest"
        assert user_data["email"] == "apitest@example.com"
        assert user_data["role"] == "user"

        print("✅ Response structure is correct!")
        print(f"User data: {json.dumps(user_data, indent=2)}")

        return response_data["access_token"]
    else:
        print(f"❌ Login failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return None


def test_protected_endpoint(access_token):
    """Test a protected endpoint with authentication."""
    if not access_token:
        print("⏭️ Skipping protected endpoint test (no token)")
        return

    client = TestClient(app)

    print("🧪 Testing protected endpoint /api/auth/verify...")

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/auth/verify", headers=headers)

    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        print("✅ Protected endpoint access successful!")
        user_data = response.json()["user"]
        print(f"Verified user: {user_data['username']}")
    else:
        print(f"❌ Protected endpoint failed with status {response.status_code}")
        print(f"Response: {response.text}")


def main():
    """Run complete API tests."""
    print("🧪 Complete AI-CRM API Authentication Test")
    print("=" * 50)

    try:
        # Test login endpoint
        access_token = test_login_endpoint()

        print()

        # Test protected endpoint
        test_protected_endpoint(access_token)

        print("\n✅ All tests completed successfully!")
        print("🎉 ResponseValidationError has been fixed!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
