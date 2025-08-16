#!/usr/bin/env python3
"""
API Documentation Generator for AI-CRM Phase 2A

This module generates comprehensive OpenAPI/Swagger documentation
for all API endpoints including billing, analytics, and agent management.
"""

import json

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
import yaml


def generate_openapi_spec(app: FastAPI) -> dict:
    """Generate comprehensive OpenAPI specification."""
    return get_openapi(
        title="AI-CRM API Documentation",
        version="2.0.0",
        description="""
# AI-CRM API Documentation

The AI-CRM API provides comprehensive access to our AI-powered project management system with support for:

## Core Features
- **Multi-Provider AI Agents**: Access to 59+ specialized AI agents across Anthropic, OpenAI, and Mistral
- **Task Management**: Create, execute, and monitor tasks with intelligent agent assignment
- **Real-time Updates**: WebSocket connections for live task and system updates
- **Analytics**: Comprehensive metrics and performance monitoring
- **Billing System**: Tiered subscription management with Stripe integration

## Authentication
All API endpoints require authentication using JWT Bearer tokens:
```
Authorization: Bearer <your-jwt-token>
```

## Rate Limits
- **Free Tier**: 10 tasks/month, 100 API calls/hour
- **Pro Tier**: Unlimited tasks, 1000 API calls/hour  
- **Enterprise**: Unlimited tasks and API calls

## Error Handling
The API uses standard HTTP status codes and returns error responses in JSON format:
```json
{
    "error": "Error description",
    "code": "ERROR_CODE",
    "details": {}
}
```

## Base URL
- Production: `https://api.aicrm.com`
- Staging: `https://staging-api.aicrm.com`
- Development: `http://localhost:5001`
        """,
        routes=app.routes,
        servers=[
            {"url": "https://api.aicrm.com", "description": "Production server"},
            {"url": "https://staging-api.aicrm.com", "description": "Staging server"},
            {"url": "http://localhost:5001", "description": "Development server"},
        ],
        contact={
            "name": "AI-CRM Support",
            "url": "https://aicrm.com/support",
            "email": "support@aicrm.com"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        }
    )

def create_api_documentation_endpoints(app: FastAPI):
    """Add custom documentation endpoints."""

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI with enhanced styling."""
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="AI-CRM API Documentation",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_ui_parameters={
                "deepLinking": True,
                "displayRequestDuration": True,
                "docExpansion": "list",
                "operationsSorter": "method",
                "filter": True,
                "tryItOutEnabled": True
            }
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        """Alternative documentation using ReDoc."""
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="AI-CRM API Documentation",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
        )

    @app.get("/openapi.yaml", include_in_schema=False)
    async def get_openapi_yaml():
        """Get OpenAPI spec in YAML format."""
        openapi_spec = generate_openapi_spec(app)
        yaml_str = yaml.dump(openapi_spec, default_flow_style=False)
        return HTMLResponse(content=yaml_str, media_type="application/x-yaml")

    @app.get("/api-guide", include_in_schema=False)
    async def api_guide():
        """Comprehensive API usage guide."""
        guide_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI-CRM API Guide</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }
                .code { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
                .endpoint { background: #e3f2fd; padding: 10px; margin: 10px 0; border-left: 4px solid #2196f3; }
                .method { font-weight: bold; color: #2196f3; }
                .section { margin: 30px 0; }
                h1, h2, h3 { color: #333; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f5f5f5; }
            </style>
        </head>
        <body>
            <h1>AI-CRM API Usage Guide</h1>
            
            <div class="section">
                <h2>Quick Start</h2>
                <p>Get started with the AI-CRM API in 5 minutes:</p>
                
                <h3>1. Authentication</h3>
                <div class="code">
curl -X POST https://api.aicrm.com/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "your-username", "password": "your-password"}'
                </div>
                
                <h3>2. List Available Agents</h3>
                <div class="code">
curl -X GET https://api.aicrm.com/api/agents \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
                </div>
                
                <h3>3. Create and Execute a Task</h3>
                <div class="code">
curl -X POST https://api.aicrm.com/api/tasks \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "description": "Review this code for security vulnerabilities",
    "agent_id": "security-auditor",
    "context": {"language": "python", "priority": "high"}
  }'
                </div>
            </div>
            
            <div class="section">
                <h2>Core API Endpoints</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> /api/agents - List all available AI agents
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> /api/tasks - Create a new task
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> /api/tasks/{id} - Get task details and results
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> /api/agents/analyze - Get agent recommendations for a task
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> /api/analytics - Get system analytics and metrics
                </div>
            </div>
            
            <div class="section">
                <h2>Billing API Endpoints</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> /api/billing/pricing - Get pricing plans
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> /api/billing/subscription - Get current subscription
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> /api/billing/subscription - Create/update subscription
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> /api/billing/usage - Get usage statistics
                </div>
            </div>
            
            <div class="section">
                <h2>Agent Specializations</h2>
                <table>
                    <tr><th>Agent Type</th><th>Specializations</th><th>Best For</th></tr>
                    <tr><td>code-reviewer</td><td>Code review, quality assurance</td><td>Pull request reviews</td></tr>
                    <tr><td>security-auditor</td><td>Security analysis, vulnerability detection</td><td>Security assessments</td></tr>
                    <tr><td>data-scientist</td><td>Data analysis, ML models</td><td>Data insights</td></tr>
                    <tr><td>business-analyst</td><td>Requirements, market research</td><td>Business planning</td></tr>
                    <tr><td>frontend-developer</td><td>UI/UX, React, JavaScript</td><td>Frontend development</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>WebSocket Real-time Updates</h2>
                <p>Connect to real-time task updates:</p>
                <div class="code">
const socket = io('wss://api.aicrm.com', {
  auth: { token: 'YOUR_JWT_TOKEN' }
});

// Listen for task updates
socket.on('task_updated', (data) => {
  console.log('Task updated:', data);
});

// Join specific rooms
socket.emit('join_room', 'tasks');
socket.emit('join_room', 'agents');
                </div>
            </div>
            
            <div class="section">
                <h2>SDKs and Libraries</h2>
                <h3>JavaScript/Node.js</h3>
                <div class="code">
npm install @aicrm/api-client

import { AICRMClient } from '@aicrm/api-client';
const client = new AICRMClient('YOUR_API_KEY');
                </div>
                
                <h3>Python</h3>
                <div class="code">
pip install aicrm-api

from aicrm_api import AICRMClient
client = AICRMClient(api_key='YOUR_API_KEY')
                </div>
            </div>
            
            <div class="section">
                <h2>Error Codes</h2>
                <table>
                    <tr><th>Code</th><th>Status</th><th>Description</th></tr>
                    <tr><td>INVALID_TOKEN</td><td>401</td><td>JWT token is invalid or expired</td></tr>
                    <tr><td>RATE_LIMIT_EXCEEDED</td><td>429</td><td>API rate limit exceeded</td></tr>
                    <tr><td>AGENT_NOT_FOUND</td><td>404</td><td>Requested agent does not exist</td></tr>
                    <tr><td>TASK_LIMIT_REACHED</td><td>402</td><td>Monthly task limit reached</td></tr>
                    <tr><td>INSUFFICIENT_CREDITS</td><td>402</td><td>Not enough credits for operation</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Support</h2>
                <ul>
                    <li><strong>Documentation:</strong> <a href="/docs">Interactive API Docs</a></li>
                    <li><strong>Support:</strong> support@aicrm.com</li>
                    <li><strong>Status Page:</strong> https://status.aicrm.com</li>
                    <li><strong>GitHub:</strong> https://github.com/aicrm/api-examples</li>
                </ul>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=guide_html)

# Example usage for integrating with existing FastAPI app
def setup_api_documentation(app: FastAPI):
    """Setup comprehensive API documentation."""

    # Override the default OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = generate_openapi_spec(app)

        # Add custom schema components
        openapi_schema["components"] = {
            "schemas": {
                "Agent": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Agent unique identifier"},
                        "name": {"type": "string", "description": "Agent display name"},
                        "provider": {"type": "string", "enum": ["anthropic", "openai", "mistral"]},
                        "model": {"type": "string", "description": "AI model used by agent"},
                        "specializations": {"type": "array", "items": {"type": "string"}},
                        "status": {"type": "string", "enum": ["available", "busy", "offline"]},
                        "cost_per_token": {"type": "number", "format": "float"}
                    }
                },
                "Task": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Task unique identifier"},
                        "description": {"type": "string", "description": "Task description"},
                        "agent_id": {"type": "string", "description": "Assigned agent ID"},
                        "status": {"type": "string", "enum": ["pending", "running", "completed", "failed"]},
                        "created_at": {"type": "string", "format": "date-time"},
                        "completed_at": {"type": "string", "format": "date-time"},
                        "result": {"type": "object", "description": "Task execution result"},
                        "tokens_used": {"type": "integer"},
                        "cost": {"type": "number", "format": "float"}
                    }
                },
                "SubscriptionPlan": {
                    "type": "object",
                    "properties": {
                        "tier": {"type": "string", "enum": ["free", "pro", "enterprise"]},
                        "name": {"type": "string"},
                        "price_monthly": {"type": "number", "format": "float"},
                        "price_annual": {"type": "number", "format": "float"},
                        "max_tasks": {"type": "integer", "nullable": True},
                        "agent_count": {"type": "integer"},
                        "features": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }

        # Add security requirement globally
        openapi_schema["security"] = [{"bearerAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    create_api_documentation_endpoints(app)

if __name__ == "__main__":
    # Generate standalone documentation files
    from api import app

    # Generate OpenAPI spec
    openapi_spec = generate_openapi_spec(app)

    # Save as JSON
    with open("openapi.json", "w") as f:
        json.dump(openapi_spec, f, indent=2)

    # Save as YAML
    with open("openapi.yaml", "w") as f:
        yaml.dump(openapi_spec, f, default_flow_style=False)

    print("📚 API documentation generated:")
    print("  - openapi.json")
    print("  - openapi.yaml")
    print("  - Visit /docs for interactive documentation")
    print("  - Visit /api-guide for comprehensive guide")
