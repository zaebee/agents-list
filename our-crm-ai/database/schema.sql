-- AI-CRM Database Schema for PostgreSQL
-- This schema matches the SQLAlchemy models in auth_database.py

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    
    -- Account status and verification
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    account_status VARCHAR(50) DEFAULT 'PENDING_VERIFICATION',
    
    -- Role and subscription
    role VARCHAR(50) DEFAULT 'USER',
    subscription_tier VARCHAR(50) DEFAULT 'FREE',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Verification tokens
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    monthly_tasks_created INTEGER DEFAULT 0,
    last_task_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_account_status CHECK (account_status IN ('ACTIVE', 'SUSPENDED', 'DELETED', 'PENDING_VERIFICATION')),
    CONSTRAINT valid_role CHECK (role IN ('USER', 'MANAGER', 'ADMIN')),
    CONSTRAINT valid_subscription_tier CHECK (subscription_tier IN ('FREE', 'PRO', 'ENTERPRISE'))
);

-- Auth sessions table
CREATE TABLE IF NOT EXISTS auth_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    access_token_jti VARCHAR(255) NOT NULL,
    
    -- Session metadata
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    
    -- Session control
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for auth_sessions
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_refresh_token ON auth_sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_access_token_jti ON auth_sessions(access_token_jti);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    
    -- Request context
    ip_address VARCHAR(45),
    user_agent TEXT,
    endpoint VARCHAR(255),
    http_method VARCHAR(10),
    
    -- Additional data
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Subscription features table
CREATE TABLE IF NOT EXISTS subscription_features (
    id SERIAL PRIMARY KEY,
    feature_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Tier availability
    free_tier BOOLEAN DEFAULT FALSE,
    pro_tier BOOLEAN DEFAULT FALSE,
    enterprise_tier BOOLEAN DEFAULT FALSE,
    
    -- Usage limits
    free_limit INTEGER,
    pro_limit INTEGER,
    enterprise_limit INTEGER,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Rate limit rules table
CREATE TABLE IF NOT EXISTS rate_limit_rules (
    id SERIAL PRIMARY KEY,
    endpoint_pattern VARCHAR(200) NOT NULL,
    subscription_tier VARCHAR(50) NOT NULL,
    
    -- Rate limit configuration
    requests_per_minute INTEGER DEFAULT 60,
    requests_per_hour INTEGER DEFAULT 1000,
    requests_per_day INTEGER DEFAULT 10000,
    
    -- Burst allowance
    burst_size INTEGER DEFAULT 10,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT valid_subscription_tier_rate_limit CHECK (subscription_tier IN ('FREE', 'PRO', 'ENTERPRISE'))
);

-- Create indexes for rate_limit_rules
CREATE INDEX IF NOT EXISTS idx_rate_limit_rules_endpoint_pattern ON rate_limit_rules(endpoint_pattern);
CREATE INDEX IF NOT EXISTS idx_rate_limit_rules_subscription_tier ON rate_limit_rules(subscription_tier);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Default data insertion
INSERT INTO subscription_features (feature_name, description, free_tier, pro_tier, enterprise_tier, free_limit, pro_limit, enterprise_limit) VALUES
('command_execution', 'Execute natural language commands', TRUE, TRUE, TRUE, 10, NULL, NULL),
('ai_agent_access', 'Access to AI agents for task assistance', TRUE, TRUE, TRUE, 9, 46, NULL),
('analytics_dashboard', 'Access to analytics and reporting', FALSE, TRUE, TRUE, NULL, NULL, NULL),
('api_access', 'REST API access', FALSE, TRUE, TRUE, NULL, NULL, NULL),
('billing_dashboard', 'Access to billing and subscription management', FALSE, TRUE, TRUE, NULL, NULL, NULL)
ON CONFLICT (feature_name) DO NOTHING;

-- Default rate limits
INSERT INTO rate_limit_rules (endpoint_pattern, subscription_tier, requests_per_minute, requests_per_hour, requests_per_day) VALUES
('/api/command.*', 'FREE', 5, 50, 200),
('/api/command.*', 'PRO', 30, 500, 5000),
('/api/command.*', 'ENTERPRISE', 100, 2000, 20000)
ON CONFLICT DO NOTHING;

-- Create default admin user (will be created by application startup)
-- This is handled by the application's seed_default_data function