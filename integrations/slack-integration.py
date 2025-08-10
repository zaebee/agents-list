#!/usr/bin/env python3
"""
Slack Integration for AI-CRM System
Enterprise-grade Slack bot with intelligent task management and PM Gateway integration.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError


@dataclass
class SlackConfig:
    """Slack integration configuration."""
    bot_token: str
    signing_secret: str
    app_token: str
    client_id: str
    client_secret: str
    ai_crm_api_url: str
    ai_crm_api_key: str


class SlackIntegration:
    """Comprehensive Slack integration for AI-CRM system."""
    
    def __init__(self, config: SlackConfig):
        self.config = config
        self.app = AsyncApp(
            token=config.bot_token,
            signing_secret=config.signing_secret,
            process_before_response=True
        )
        self.client = AsyncWebClient(token=config.bot_token)
        self.logger = self._setup_logging()
        self._setup_handlers()
        
        # AI-CRM API integration
        self.ai_crm_base_url = config.ai_crm_api_url
        self.ai_crm_headers = {
            'Authorization': f'Bearer {config.ai_crm_api_key}',
            'Content-Type': 'application/json'
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up comprehensive logging."""
        logger = logging.getLogger("slack_integration")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_handlers(self):
        """Set up Slack event and command handlers."""
        
        # Slash command handlers
        self.app.command("/ai-crm")(self.handle_slash_command)
        self.app.command("/aicrm")(self.handle_slash_command)  # Alternative command
        
        # Interactive component handlers
        self.app.action("task_create")(self.handle_task_creation)
        self.app.action("task_assign")(self.handle_task_assignment)
        self.app.action("task_status_update")(self.handle_status_update)
        self.app.action("agent_select")(self.handle_agent_selection)
        self.app.action("pm_analyze")(self.handle_pm_analysis)
        
        # Button handlers
        self.app.action({"action_id": "task_action"})(self.handle_task_action)
        self.app.action({"action_id": "quick_create"})(self.handle_quick_task_create)
        
        # Modal handlers
        self.app.view("task_creation_modal")(self.handle_task_creation_modal)
        self.app.view("pm_analysis_modal")(self.handle_pm_analysis_modal)
        
        # Event handlers
        self.app.event("app_mention")(self.handle_app_mention)
        self.app.event("message")(self.handle_direct_message)
        
        # Shortcut handlers
        self.app.shortcut("create_ai_task")(self.handle_create_task_shortcut)
        
    async def handle_slash_command(self, ack, command, respond):
        """Handle /ai-crm slash command with subcommands."""
        await ack()
        
        try:
            # Parse command arguments
            text = command.get("text", "").strip()
            args = text.split() if text else []
            
            if not args or args[0] == "help":
                await self.send_help_message(respond)
            elif args[0] == "task":
                await self.handle_task_command(args[1:], command, respond)
            elif args[0] == "pm":
                await self.handle_pm_command(args[1:], command, respond)
            elif args[0] == "agents":
                await self.handle_agents_command(args[1:], command, respond)
            elif args[0] == "status":
                await self.handle_status_command(args[1:], command, respond)
            else:
                await respond(f"Unknown command: {args[0]}. Use `/ai-crm help` for available commands.")
                
        except Exception as e:
            self.logger.error(f"Error handling slash command: {e}")
            await respond("❌ An error occurred processing your command. Please try again.")
    
    async def handle_task_command(self, args: List[str], command: Dict, respond):
        """Handle task-related commands."""
        if not args:
            await self.show_task_creation_modal(command)
            return
            
        subcommand = args[0]
        
        if subcommand == "create":
            await self.show_task_creation_modal(command)
        elif subcommand == "list":
            await self.show_task_list(args[1:], respond)
        elif subcommand == "status":
            if len(args) > 1:
                await self.show_task_status(args[1], respond)
            else:
                await respond("Please provide a task ID: `/ai-crm task status <task_id>`")
        else:
            await respond(f"Unknown task command: {subcommand}")
    
    async def handle_pm_command(self, args: List[str], command: Dict, respond):
        """Handle PM Gateway commands."""
        if not args:
            await self.show_pm_analysis_modal(command)
            return
            
        subcommand = args[0]
        
        if subcommand == "analyze":
            await self.show_pm_analysis_modal(command)
        elif subcommand == "dashboard":
            await self.show_pm_dashboard(respond)
        else:
            await respond(f"Unknown PM command: {subcommand}")
    
    async def handle_agents_command(self, args: List[str], respond):
        """Handle agent-related commands."""
        try:
            # Fetch agents from AI-CRM API
            agents_data = await self.fetch_agents_list()
            
            if args and args[0] == "categories":
                await self.show_agents_by_category(agents_data, respond)
            else:
                await self.show_agents_list(agents_data, respond)
                
        except Exception as e:
            self.logger.error(f"Error fetching agents: {e}")
            await respond("❌ Unable to fetch agents list. Please try again later.")
    
    async def handle_status_command(self, args: List[str], respond):
        """Handle system status commands."""
        if args and args[0] == "dashboard":
            dashboard_url = f"{self.ai_crm_base_url.replace('/api', '')}/dashboard"
            await respond(f"📊 **AI-CRM Dashboard**: {dashboard_url}")
        else:
            await self.show_system_status(respond)
    
    async def show_task_creation_modal(self, command: Dict):
        """Show interactive task creation modal."""
        modal_view = {
            "type": "modal",
            "callback_id": "task_creation_modal",
            "title": {"type": "plain_text", "text": "🤖 Create AI-CRM Task"},
            "submit": {"type": "plain_text", "text": "Create Task"},
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "task_title",
                        "placeholder": {"type": "plain_text", "text": "Enter task title"}
                    },
                    "label": {"type": "plain_text", "text": "Task Title"}
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "task_description",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "Describe the task in detail"}
                    },
                    "label": {"type": "plain_text", "text": "Description"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Priority Level*"},
                    "accessory": {
                        "type": "static_select",
                        "action_id": "task_priority",
                        "placeholder": {"type": "plain_text", "text": "Select priority"},
                        "options": [
                            {"text": {"type": "plain_text", "text": "🔥 Urgent"}, "value": "urgent"},
                            {"text": {"type": "plain_text", "text": "🚨 High"}, "value": "high"},
                            {"text": {"type": "plain_text", "text": "📋 Medium"}, "value": "medium"},
                            {"text": {"type": "plain_text", "text": "📝 Low"}, "value": "low"}
                        ]
                    }
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*AI Analysis*"},
                    "accessory": {
                        "type": "checkboxes",
                        "action_id": "analysis_options",
                        "options": [
                            {
                                "text": {"type": "mrkdwn", "text": "🎯 *PM Gateway Analysis*\nGet intelligent task breakdown and agent recommendations"},
                                "value": "pm_analysis"
                            },
                            {
                                "text": {"type": "mrkdwn", "text": "🤖 *Auto-assign Agent*\nAutomatically assign best-fit AI agent"},
                                "value": "auto_assign"
                            }
                        ]
                    }
                }
            ]
        }
        
        await self.client.views_open(
            trigger_id=command["trigger_id"],
            view=modal_view
        )
    
    async def handle_task_creation_modal(self, ack, body, view):
        """Handle task creation modal submission."""
        await ack()
        
        try:
            # Extract form values
            values = view["state"]["values"]
            
            title = values["task_title"]["task_title"]["value"]
            description = values["task_description"]["task_description"]["value"]
            priority = values["task_priority"]["task_priority"]["selected_option"]["value"] if values["task_priority"]["task_priority"]["selected_option"] else "medium"
            
            analysis_options = []
            if values.get("analysis_options") and values["analysis_options"]["analysis_options"]["selected_options"]:
                analysis_options = [opt["value"] for opt in values["analysis_options"]["analysis_options"]["selected_options"]]
            
            # Create task through AI-CRM API
            task_data = {
                "title": title,
                "description": description,
                "priority": priority,
                "pm_analysis": "pm_analysis" in analysis_options,
                "auto_assign": "auto_assign" in analysis_options,
                "source": "slack",
                "created_by": body["user"]["id"]
            }
            
            result = await self.create_ai_crm_task(task_data)
            
            # Send confirmation message
            user_id = body["user"]["id"]
            await self.client.chat_postMessage(
                channel=user_id,
                text=f"✅ Task created successfully: {title}",
                blocks=self.format_task_confirmation_blocks(result)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            await self.client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Failed to create task. Please try again."
            )
    
    async def handle_app_mention(self, event, say):
        """Handle @AI-CRM mentions in channels."""
        try:
            text = event.get("text", "").lower()
            
            # Simple command parsing from mentions
            if "create task" in text or "new task" in text:
                await say("I'll help you create a task! Use `/ai-crm task create` for the full form.")
            elif "help" in text:
                await say(self.get_quick_help_text())
            elif "status" in text:
                await self.show_system_status_in_channel(say)
            else:
                await say("Hi! I'm the AI-CRM bot. Use `/ai-crm help` to see what I can do!")
                
        except Exception as e:
            self.logger.error(f"Error handling app mention: {e}")
            await say("Sorry, I encountered an error. Please try again.")
    
    async def send_help_message(self, respond):
        """Send comprehensive help message."""
        help_blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🤖 AI-CRM Slack Bot Help"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Available Commands:*"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Task Management:*\n• `/ai-crm task create` - Create new task\n• `/ai-crm task list` - List your tasks\n• `/ai-crm task status <id>` - Get task status"},
                    {"type": "mrkdwn", "text": "*PM Gateway:*\n• `/ai-crm pm analyze` - Analyze task complexity\n• `/ai-crm pm dashboard` - View PM dashboard"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Agents:*\n• `/ai-crm agents` - List available agents\n• `/ai-crm agents categories` - View by category"},
                    {"type": "mrkdwn", "text": "*System:*\n• `/ai-crm status` - System health\n• `/ai-crm status dashboard` - Dashboard link"}
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Quick Actions:*"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🚀 Create Task"},
                    "action_id": "quick_create",
                    "style": "primary"
                }
            }
        ]
        
        await respond(blocks=help_blocks)
    
    def get_quick_help_text(self) -> str:
        """Get concise help text for mentions."""
        return """🤖 **AI-CRM Bot Commands:**
        
**Quick Commands:**
• `/ai-crm task create` - Create new task
• `/ai-crm pm analyze` - PM analysis  
• `/ai-crm agents` - List AI agents
• `/ai-crm status` - System status
• `/ai-crm help` - Full help

**Mention me** with "create task", "help", or "status" for quick actions!"""
    
    async def create_ai_crm_task(self, task_data: Dict) -> Dict:
        """Create task via AI-CRM API."""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ai_crm_base_url}/tasks",
                json=task_data,
                headers=self.ai_crm_headers
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"API error: {response.status}")
    
    async def fetch_agents_list(self) -> List[Dict]:
        """Fetch agents list from AI-CRM API."""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.ai_crm_base_url}/agents",
                headers=self.ai_crm_headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API error: {response.status}")
    
    def format_task_confirmation_blocks(self, task_result: Dict) -> List[Dict]:
        """Format task creation confirmation blocks."""
        return [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "✅ Task Created Successfully"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Task ID:*\n{task_result.get('task_id', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Assigned Agent:*\n{task_result.get('assigned_agent', 'None')}"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Title:* {task_result.get('title', 'N/A')}"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Task"},
                    "action_id": "view_task",
                    "value": task_result.get('task_id', '')
                }
            }
        ]
    
    async def start_socket_mode(self):
        """Start Slack app in Socket Mode."""
        from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
        
        handler = AsyncSocketModeHandler(self.app, self.config.app_token)
        await handler.start_async()
    
    async def start_http_mode(self, port: int = 3000):
        """Start Slack app in HTTP mode."""
        from aiohttp import web
        from slack_bolt.adapter.aiohttp.async_handler import AsyncSlackRequestHandler
        
        handler = AsyncSlackRequestHandler(self.app)
        
        app = web.Application()
        app.router.add_post("/slack/events", handler.handle)
        
        return web.AppRunner(app)


class SlackNotificationService:
    """Service for sending notifications to Slack channels."""
    
    def __init__(self, client: AsyncWebClient):
        self.client = client
        self.logger = logging.getLogger("slack_notifications")
    
    async def send_task_assignment_notification(
        self, 
        channel: str, 
        task: Dict, 
        assignee_slack_id: str
    ):
        """Send task assignment notification."""
        blocks = [
            {
                "type": "header", 
                "text": {"type": "plain_text", "text": "🎯 New Task Assignment"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"<@{assignee_slack_id}> has been assigned a new task:"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{task['title']}*\n{task['description'][:200]}..."}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Task"},
                        "action_id": "view_task",
                        "value": task['id']
                    },
                    {
                        "type": "button", 
                        "text": {"type": "plain_text", "text": "Accept"},
                        "action_id": "accept_task",
                        "value": task['id'],
                        "style": "primary"
                    }
                ]
            }
        ]
        
        await self.client.chat_postMessage(channel=channel, blocks=blocks)
    
    async def send_task_status_update(
        self,
        channel: str,
        task: Dict,
        old_status: str,
        new_status: str,
        updated_by: str
    ):
        """Send task status update notification."""
        status_emoji = {
            "To Do": "📋",
            "In Progress": "🔄", 
            "Done": "✅",
            "Blocked": "🚫"
        }
        
        message = f"{status_emoji.get(new_status, '📌')} **Task Update**: {task['title']}\n"
        message += f"Status changed from *{old_status}* to *{new_status}* by <@{updated_by}>"
        
        await self.client.chat_postMessage(
            channel=channel,
            text=message,
            unfurl_links=False
        )
    
    async def send_pm_analysis_result(
        self,
        channel: str,
        task_title: str,
        analysis_result: Dict
    ):
        """Send PM analysis result notification."""
        complexity = analysis_result.get('complexity', 'Unknown')
        estimated_hours = analysis_result.get('estimated_hours', 0)
        recommended_agent = analysis_result.get('recommended_agent', 'None')
        priority = analysis_result.get('priority', 'Medium')
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🎯 PM Analysis Complete"}
            },
            {
                "type": "section", 
                "text": {"type": "mrkdwn", "text": f"*Task:* {task_title}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Complexity:*\n{complexity}"},
                    {"type": "mrkdwn", "text": f"*Estimated Time:*\n{estimated_hours} hours"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Priority:*\n{priority}"},
                    {"type": "mrkdwn", "text": f"*Recommended Agent:*\n{recommended_agent}"}
                ]
            }
        ]
        
        if analysis_result.get('risk_factors'):
            risk_text = '\n'.join(f"• {risk}" for risk in analysis_result['risk_factors'])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*⚠️ Risk Factors:*\n{risk_text}"}
            })
        
        await self.client.chat_postMessage(channel=channel, blocks=blocks)


def create_slack_integration() -> SlackIntegration:
    """Create Slack integration instance from environment variables."""
    config = SlackConfig(
        bot_token=os.getenv("SLACK_BOT_TOKEN"),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET"), 
        app_token=os.getenv("SLACK_APP_TOKEN"),
        client_id=os.getenv("SLACK_CLIENT_ID"),
        client_secret=os.getenv("SLACK_CLIENT_SECRET"),
        ai_crm_api_url=os.getenv("AI_CRM_API_URL", "http://localhost:8000"),
        ai_crm_api_key=os.getenv("AI_CRM_API_KEY")
    )
    
    return SlackIntegration(config)


async def main():
    """Main function to run Slack integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-CRM Slack Integration")
    parser.add_argument("--mode", choices=["socket", "http"], default="socket",
                       help="Connection mode (socket or http)")
    parser.add_argument("--port", type=int, default=3000,
                       help="HTTP port (for http mode)")
    
    args = parser.parse_args()
    
    # Create integration
    slack_integration = create_slack_integration()
    
    print("🚀 Starting AI-CRM Slack Integration...")
    print(f"📡 Mode: {args.mode}")
    
    try:
        if args.mode == "socket":
            # Socket Mode (for development)
            await slack_integration.start_socket_mode()
        else:
            # HTTP Mode (for production)
            runner = await slack_integration.start_http_mode(args.port)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", args.port)
            await site.start()
            
            print(f"🌐 HTTP server started on port {args.port}")
            print("📡 Slack events endpoint: /slack/events")
            
            # Keep server running
            while True:
                await asyncio.sleep(3600)
                
    except KeyboardInterrupt:
        print("\n👋 Shutting down Slack integration...")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())