# 🔐 AI-CRM Authentication System Guide

## Overview

The AI-CRM system implements a comprehensive JWT-based authentication system with enterprise-grade security features including user registration, secure login, session management, role-based access control, and subscription tier enforcement.

## 🏗️ Architecture

### Components

1. **Auth Database** (`auth_database.py`)
   - SQLAlchemy models for users, sessions, audit logs
   - Subscription features and rate limiting rules
   - Support for both SQLite and PostgreSQL

2. **Authentication Module** (`auth.py`)
   - JWT token creation and validation
   - Argon2 password hashing
   - Session management with refresh tokens
   - Role and subscription tier enforcement

3. **Authentication Routes** (`auth_routes.py`)
   - User registration and login endpoints
   - Token refresh and logout functionality
   - Password reset and verification

4. **Security Integration** (`api.py`)
   - CORS configuration
   - Protected endpoint decorators
   - Database initialization

## 🚀 Getting Started

### 1. Environment Setup

```bash
# Required environment variables
export SECRET_KEY="your_secure_secret_key_here"
export DATABASE_URL="sqlite:///./ai_crm.db"  # or PostgreSQL URL

# Optional: For subscription features
export STRIPE_SECRET_KEY="your_stripe_secret_key"
export STRIPE_PUBLISHABLE_KEY="your_stripe_publishable_key"
```

### 2. Database Initialization

```bash
# Initialize authentication database
python3 -c "
from auth_database import create_tables, seed_default_data, SessionLocal
create_tables()
db = SessionLocal()
try:
    seed_default_data(db)
    print('Database initialized successfully!')
finally:
    db.close()
"
```

### 3. Test Authentication

```bash
# Run authentication tests
python3 test_auth_integration.py
python3 test_api_complete.py
```

## 📝 API Endpoints

### Authentication Endpoints

#### POST `/api/auth/register`
Register a new user account.

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com", 
  "password": "securepassword123",
  "full_name": "New User"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user_id": 1,
  "verification_required": true
}
```

#### POST `/api/auth/login`
Authenticate user and receive access tokens.

**Request:**
```json
{
  "username": "newuser",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "newuser",
    "email": "user@example.com",
    "role": "user",
    "subscription_tier": "free"
  }
}
```

#### POST `/api/auth/token/refresh`
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### GET `/api/auth/me`
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

#### POST `/api/auth/logout`
Logout and invalidate session (requires authentication).

#### POST `/api/auth/password/reset-request`
Request password reset email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

#### POST `/api/auth/password/reset`
Reset password using reset token.

**Request:**
```json
{
  "token": "reset_token_here",
  "new_password": "newsecurepassword123"
}
```

## 🔒 Security Features

### Password Security
- **Argon2 Hashing**: Industry-standard password hashing
- **Strength Validation**: Enforces strong password requirements
- **Common Pattern Detection**: Prevents weak passwords

```python
# Password requirements:
# - Minimum 8 characters
# - Contains uppercase and lowercase letters
# - Contains numbers and special characters
# - No common patterns (123, abc, password, etc.)
```

### JWT Token Security
- **Access Tokens**: Short-lived (30 minutes) for API access
- **Refresh Tokens**: Long-lived (7 days) for token renewal
- **JTI Tracking**: Unique token IDs for session management
- **Token Revocation**: Ability to invalidate specific sessions

### Session Management
- **Session Tracking**: Database-stored session information
- **Device Fingerprinting**: IP address and user agent tracking
- **Session Expiration**: Automatic cleanup of expired sessions
- **Multi-session Support**: Multiple active sessions per user

### Audit Logging
- **Security Events**: Login attempts, password changes, etc.
- **API Access**: Comprehensive request logging
- **Risk Scoring**: Anomaly detection for security events
- **Compliance**: GDPR and audit trail requirements

## 👥 User Roles & Permissions

### Role Hierarchy
1. **USER**: Basic access to features based on subscription
2. **MANAGER**: Enhanced access for team management
3. **ADMIN**: Full system access and user management

### Subscription Tiers
1. **FREE**: 10 command executions/month, 9 Haiku agents
2. **PRO**: Unlimited commands, 46 agents, analytics dashboard
3. **ENTERPRISE**: All 59 agents, custom features, priority support

### Feature Access Control

```python
# Example: Protect endpoint with role requirement
@app.get("/admin/users")
async def list_users(
    current_user = Depends(require_roles([UserRole.ADMIN]))
):
    # Only admins can access this endpoint
    pass

# Example: Protect endpoint with subscription requirement
@app.get("/analytics/dashboard") 
async def analytics_dashboard(
    current_user = Depends(require_subscription_tier(SubscriptionTier.PRO))
):
    # Requires Pro subscription or higher
    pass

# Example: Protect endpoint with feature access
@app.post("/api/command")
async def execute_command(
    current_user = Depends(require_feature_access("command_execution"))
):
    # Checks subscription limits and feature access
    pass
```

## 🧪 Testing & Development

### Test User Creation

```python
# Create test users for development
from auth_database import SessionLocal, User
from auth import get_password_hash
from auth_database import UserRole, SubscriptionTier, AccountStatus

def create_test_users():
    db = SessionLocal()
    try:
        # Admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            subscription_tier=SubscriptionTier.ENTERPRISE,
            account_status=AccountStatus.ACTIVE,
            is_active=True,
            is_verified=True
        )
        
        # Regular user
        regular_user = User(
            username="user",
            email="user@example.com", 
            hashed_password=get_password_hash("user123"),
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE,
            account_status=AccountStatus.ACTIVE,
            is_active=True,
            is_verified=True
        )
        
        db.add_all([admin_user, regular_user])
        db.commit()
        print("Test users created successfully!")
        
    finally:
        db.close()
```

### API Testing with curl

```bash
# Register new user
curl -X POST "http://localhost:5001/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "testpass123",
       "full_name": "Test User"
     }'

# Login
TOKEN=$(curl -s -X POST "http://localhost:5001/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "testpass123"}' \
     | jq -r '.access_token')

# Use protected endpoint
curl -X GET "http://localhost:5001/api/auth/me" \
     -H "Authorization: Bearer $TOKEN"

# Execute command (requires authentication)
curl -X POST "http://localhost:5001/api/command" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"command": "test command"}'
```

## 🔧 Configuration

### Database Configuration

```python
# SQLite (default)
DATABASE_URL = "sqlite:///./ai_crm.db"

# PostgreSQL (production)
DATABASE_URL = "postgresql://user:password@localhost:5432/ai_crm"
```

### JWT Configuration

```python
# Security settings
SECRET_KEY = "your_secure_secret_key"  # Generate with secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing (Argon2 configuration)
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_TIME_COST = 3
ARGON2_PARALLELISM = 1
```

### Rate Limiting

```python
# Default rate limits per subscription tier
FREE_TIER_LIMITS = {
    "requests_per_minute": 5,
    "requests_per_hour": 50,
    "requests_per_day": 200
}

PRO_TIER_LIMITS = {
    "requests_per_minute": 30,
    "requests_per_hour": 500,
    "requests_per_day": 5000
}

ENTERPRISE_TIER_LIMITS = {
    "requests_per_minute": 100,
    "requests_per_hour": 2000,
    "requests_per_day": 20000
}
```

## 🚨 Security Best Practices

### Deployment Security

1. **Environment Variables**: Never commit secrets to version control
2. **HTTPS Only**: Always use TLS in production
3. **Secret Rotation**: Implement regular key rotation
4. **Database Security**: Use connection pooling and encryption
5. **Monitoring**: Implement security event monitoring

### Development Security

1. **Test Credentials**: Use separate test database and keys
2. **Code Review**: Review all authentication-related changes
3. **Dependency Scanning**: Regular security audits of dependencies
4. **Input Validation**: Validate all user inputs
5. **Error Handling**: Don't expose sensitive information in errors

## 📊 Monitoring & Analytics

### Security Metrics

- Failed authentication attempts
- Token refresh frequency
- Session duration patterns
- API endpoint access patterns
- Subscription usage tracking

### Audit Events

```python
# Security events tracked in audit logs
AUDIT_EVENTS = [
    "LOGIN",           # Successful login
    "LOGIN_FAILED",    # Failed login attempt
    "LOGOUT",          # User logout
    "REGISTER",        # New user registration
    "PASSWORD_CHANGE", # Password reset/change
    "TOKEN_REFRESH",   # Token refresh
    "API_ACCESS",      # Protected endpoint access
    "PERMISSION_DENIED" # Access denied events
]
```

## 🔄 Migration & Upgrades

### Database Migrations

```python
# Future database schema updates
from alembic import command
from alembic.config import Config

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

### Backward Compatibility

The authentication system is designed to be backward compatible with existing API endpoints. Non-authenticated endpoints continue to work, while new protected endpoints require authentication.

## 📞 Support & Troubleshooting

### Common Issues

1. **Token Expired**: Use refresh token to get new access token
2. **Invalid Credentials**: Check username/password and account status
3. **Permission Denied**: Verify user role and subscription tier
4. **Database Errors**: Check DATABASE_URL and table initialization

### Debug Mode

```python
# Enable debug logging for authentication
import logging
logging.getLogger("auth").setLevel(logging.DEBUG)
```

### Health Checks

```bash
# Verify authentication system health
curl -X GET "http://localhost:5001/health"

# Test database connectivity
python3 -c "
from auth_database import SessionLocal
db = SessionLocal()
try:
    db.execute('SELECT 1')
    print('Database connection: OK')
finally:
    db.close()
"
```

---

**Note**: This authentication system is production-ready and follows enterprise security best practices. For additional security requirements or custom configurations, please refer to the security checklist and consult with your security team.