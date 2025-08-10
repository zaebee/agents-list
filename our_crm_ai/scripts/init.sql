-- AI-CRM Production Database Initialization Script
-- This script sets up the initial database schema and required tables

-- Create database if not exists (handled by docker-compose)
-- CREATE DATABASE ai_crm_prod;

-- Connect to the database
\c ai_crm_prod;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ai_crm;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set default schema
SET search_path TO ai_crm, public;

-- ========================================
-- CORE TABLES
-- ========================================

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'TODO',
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    complexity VARCHAR(20) DEFAULT 'MODERATE',
    assigned_agent VARCHAR(100),
    creator VARCHAR(100),
    yougile_task_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE', 'CANCELLED')),
    CONSTRAINT valid_priority CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    CONSTRAINT valid_complexity CHECK (complexity IN ('SIMPLE', 'MODERATE', 'COMPLEX'))
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    keywords TEXT[],
    specializations TEXT[],
    tools TEXT[],
    is_available BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    max_concurrent_tasks INTEGER DEFAULT 5,
    current_workload INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    avg_completion_time_hours DECIMAL(8,2) DEFAULT 0.0,
    total_tasks_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Task assignments history
CREATE TABLE IF NOT EXISTS task_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    agent_name VARCHAR(100),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by VARCHAR(100),
    assignment_reason TEXT,
    confidence_score DECIMAL(5,2),
    
    -- Index for performance
    CONSTRAINT task_assignments_task_id_idx UNIQUE (task_id, assigned_at)
);

-- Agent suggestions
CREATE TABLE IF NOT EXISTS agent_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    agent_name VARCHAR(100),
    confidence DECIMAL(5,4) NOT NULL,
    reasoning TEXT,
    matched_keywords TEXT[],
    suggested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    was_selected BOOLEAN DEFAULT false
);

-- PM Analysis results
CREATE TABLE IF NOT EXISTS pm_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    complexity VARCHAR(20),
    priority VARCHAR(20),
    estimated_hours DECIMAL(5,2),
    required_agents TEXT[],
    recommended_agent VARCHAR(100),
    risk_factors TEXT[],
    success_criteria TEXT[],
    subtasks JSONB DEFAULT '[]',
    recommendation TEXT,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzer_version VARCHAR(20) DEFAULT '1.0'
);

-- ========================================
-- ANALYTICS SCHEMA
-- ========================================

-- Task metrics
CREATE TABLE IF NOT EXISTS analytics.task_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES ai_crm.tasks(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    metric_unit VARCHAR(50),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Composite index for time-series queries
    INDEX idx_task_metrics_time_series ON analytics.task_metrics (metric_name, recorded_at DESC)
);

-- Agent performance metrics
CREATE TABLE IF NOT EXISTS analytics.agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    tasks_assigned INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    avg_completion_time_hours DECIMAL(8,2),
    success_rate DECIMAL(5,2),
    workload_percentage DECIMAL(5,2),
    
    -- Unique constraint to prevent duplicate daily records
    UNIQUE(agent_name, date)
);

-- System metrics
CREATE TABLE IF NOT EXISTS analytics.system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12,4),
    metric_tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- MONITORING SCHEMA
-- ========================================

-- Health check logs
CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Index for recent health checks
    INDEX idx_health_checks_recent ON monitoring.health_checks (component, checked_at DESC)
);

-- Error logs
CREATE TABLE IF NOT EXISTS monitoring.error_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT,
    stack_trace TEXT,
    context JSONB DEFAULT '{}',
    user_agent VARCHAR(255),
    ip_address INET,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    severity VARCHAR(20) DEFAULT 'ERROR',
    
    -- Index for error analysis
    INDEX idx_error_logs_analysis ON monitoring.error_logs (error_type, occurred_at DESC)
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Tasks indexes
CREATE INDEX IF NOT EXISTS idx_tasks_status ON ai_crm.tasks (status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON ai_crm.tasks (assigned_agent);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON ai_crm.tasks (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_yougile_id ON ai_crm.tasks (yougile_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_search ON ai_crm.tasks USING gin (to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Agents indexes
CREATE INDEX IF NOT EXISTS idx_agents_name ON ai_crm.agents (name);
CREATE INDEX IF NOT EXISTS idx_agents_available ON ai_crm.agents (is_available, is_active);
CREATE INDEX IF NOT EXISTS idx_agents_workload ON ai_crm.agents (current_workload);

-- Time-series indexes for analytics
CREATE INDEX IF NOT EXISTS idx_task_metrics_time ON analytics.task_metrics (recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_date ON analytics.agent_metrics (date DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_time ON analytics.system_metrics (recorded_at DESC);

-- ========================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ========================================

-- Update updated_at timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tasks table
DROP TRIGGER IF EXISTS update_tasks_updated_at ON ai_crm.tasks;
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON ai_crm.tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to agents table
DROP TRIGGER IF EXISTS update_agents_updated_at ON ai_crm.agents;
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON ai_crm.agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- INITIAL DATA
-- ========================================

-- Insert default agents (from config_enhanced.json)
INSERT INTO ai_crm.agents (name, description, keywords, specializations, tools) VALUES
('api-documenter', 'API documentation specialist', ARRAY['api', 'documentation', 'swagger', 'openapi'], ARRAY['API Design', 'Documentation'], ARRAY['OpenAPI', 'Swagger', 'Postman']),
('backend-architect', 'Backend system architecture expert', ARRAY['backend', 'architecture', 'microservices', 'api'], ARRAY['System Design', 'Architecture'], ARRAY['Docker', 'Kubernetes', 'Database Design']),
('business-analyst', 'Business requirements and analysis expert', ARRAY['business', 'analysis', 'requirements'], ARRAY['Business Analysis', 'Requirements'], ARRAY['JIRA', 'Confluence']),
('data-scientist', 'Data analysis and machine learning expert', ARRAY['data', 'analytics', 'ml', 'python'], ARRAY['Data Science', 'Machine Learning'], ARRAY['Python', 'SQL', 'Jupyter']),
('devops-troubleshooter', 'DevOps and infrastructure troubleshooting', ARRAY['devops', 'infrastructure', 'deployment'], ARRAY['DevOps', 'Infrastructure'], ARRAY['Docker', 'CI/CD', 'Monitoring']),
('frontend-developer', 'Frontend development specialist', ARRAY['frontend', 'react', 'javascript', 'ui'], ARRAY['Frontend Development', 'UI/UX'], ARRAY['React', 'JavaScript', 'CSS']),
('python-pro', 'Python development expert', ARRAY['python', 'backend', 'api', 'django'], ARRAY['Python Development', 'Backend'], ARRAY['Python', 'Django', 'FastAPI']),
('search-specialist', 'Search and information retrieval expert', ARRAY['search', 'elasticsearch', 'indexing'], ARRAY['Search Systems', 'Information Retrieval'], ARRAY['Elasticsearch', 'Solr'])
ON CONFLICT (name) DO NOTHING;

-- ========================================
-- FUNCTIONS FOR APPLICATION USE
-- ========================================

-- Function to get agent workload
CREATE OR REPLACE FUNCTION get_agent_workload(agent_name_param VARCHAR(100))
RETURNS TABLE (
    current_tasks INTEGER,
    workload_percentage DECIMAL(5,2),
    is_available BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.current_workload,
        CASE 
            WHEN a.max_concurrent_tasks > 0 
            THEN (a.current_workload::DECIMAL / a.max_concurrent_tasks * 100)
            ELSE 0
        END,
        a.is_available AND a.is_active AND a.current_workload < a.max_concurrent_tasks
    FROM ai_crm.agents a
    WHERE a.name = agent_name_param;
END;
$$ LANGUAGE plpgsql;

-- Function to update agent statistics
CREATE OR REPLACE FUNCTION update_agent_stats(
    agent_name_param VARCHAR(100),
    task_completed BOOLEAN DEFAULT TRUE,
    completion_time_hours DECIMAL(8,2) DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE ai_crm.agents 
    SET 
        total_tasks_completed = total_tasks_completed + CASE WHEN task_completed THEN 1 ELSE 0 END,
        avg_completion_time_hours = CASE 
            WHEN completion_time_hours IS NOT NULL AND total_tasks_completed > 0
            THEN (avg_completion_time_hours * total_tasks_completed + completion_time_hours) / (total_tasks_completed + 1)
            ELSE avg_completion_time_hours
        END,
        success_rate = CASE
            WHEN task_completed THEN
                (success_rate * total_tasks_completed + 100) / (total_tasks_completed + 1)
            ELSE
                success_rate * total_tasks_completed / (total_tasks_completed + 1)
        END
    WHERE name = agent_name_param;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- VIEWS FOR COMMON QUERIES
-- ========================================

-- Active tasks view
CREATE OR REPLACE VIEW active_tasks AS
SELECT 
    t.*,
    a.is_available as agent_available,
    a.current_workload as agent_workload
FROM ai_crm.tasks t
LEFT JOIN ai_crm.agents a ON t.assigned_agent = a.name
WHERE t.status IN ('TODO', 'IN_PROGRESS');

-- Agent performance view
CREATE OR REPLACE VIEW agent_performance AS
SELECT 
    a.name,
    a.description,
    a.is_available,
    a.current_workload,
    a.max_concurrent_tasks,
    CASE 
        WHEN a.max_concurrent_tasks > 0 
        THEN (a.current_workload::DECIMAL / a.max_concurrent_tasks * 100)
        ELSE 0
    END as workload_percentage,
    a.success_rate,
    a.avg_completion_time_hours,
    a.total_tasks_completed,
    COUNT(t.id) as total_assigned_tasks,
    COUNT(CASE WHEN t.status = 'DONE' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'IN_PROGRESS' THEN 1 END) as in_progress_tasks
FROM ai_crm.agents a
LEFT JOIN ai_crm.tasks t ON a.name = t.assigned_agent
GROUP BY a.name, a.description, a.is_available, a.current_workload, a.max_concurrent_tasks, a.success_rate, a.avg_completion_time_hours, a.total_tasks_completed;

-- ========================================
-- PERMISSIONS
-- ========================================

-- Grant permissions to ai_crm user
GRANT USAGE ON SCHEMA ai_crm TO ai_crm;
GRANT USAGE ON SCHEMA analytics TO ai_crm;
GRANT USAGE ON SCHEMA monitoring TO ai_crm;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai_crm TO ai_crm;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO ai_crm;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO ai_crm;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai_crm TO ai_crm;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO ai_crm;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO ai_crm;

-- Grant execute permissions on functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ai_crm TO ai_crm;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA ai_crm GRANT ALL ON TABLES TO ai_crm;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT ALL ON TABLES TO ai_crm;
ALTER DEFAULT PRIVILEGES IN SCHEMA monitoring GRANT ALL ON TABLES TO ai_crm;

-- ========================================
-- COMPLETION MESSAGE
-- ========================================

\echo 'AI-CRM database initialization completed successfully!'
\echo 'Schemas created: ai_crm, analytics, monitoring'
\echo 'Tables created: tasks, agents, task_assignments, agent_suggestions, pm_analysis'
\echo 'Default agents inserted and ready for use'
\echo 'Database is ready for AI-CRM production deployment!'