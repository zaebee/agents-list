#!/usr/bin/env python3
"""
GitHub Integration for AI-CRM System
Intelligent GitHub App with automated task creation and workflow management.
"""

import asyncio
import json
import os
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import yaml

import aiohttp
from github import Github, Auth
from github.Webhook import Webhook


@dataclass
class GitHubConfig:
    """GitHub integration configuration."""

    app_id: str
    private_key: str
    webhook_secret: str
    client_id: str
    client_secret: str
    ai_crm_api_url: str
    ai_crm_api_key: str


class GitHubIntegration:
    """Comprehensive GitHub integration for AI-CRM system."""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.logger = self._setup_logging()

        # GitHub API setup
        self.auth = Auth.AppAuth(config.app_id, config.private_key)
        self.github = Github(auth=self.auth)

        # AI-CRM API integration
        self.ai_crm_base_url = config.ai_crm_api_url
        self.ai_crm_headers = {
            "Authorization": f"Bearer {config.ai_crm_api_key}",
            "Content-Type": "application/json",
        }

        # Webhook event handlers
        self.event_handlers = {
            "issues": self.handle_issue_event,
            "pull_request": self.handle_pull_request_event,
            "release": self.handle_release_event,
            "push": self.handle_push_event,
            "repository": self.handle_repository_event,
            "workflow_run": self.handle_workflow_event,
        }

        # Configuration cache
        self.repo_configs = {}

    def _setup_logging(self) -> logging.Logger:
        """Set up comprehensive logging."""
        logger = logging.getLogger("github_integration")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature."""
        if not signature.startswith("sha256="):
            return False

        expected_signature = hmac.new(
            self.config.webhook_secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature[7:], expected_signature)

    async def process_webhook(
        self, headers: Dict[str, str], payload: bytes
    ) -> Dict[str, Any]:
        """Process incoming GitHub webhook."""
        try:
            # Verify signature
            signature = headers.get("X-Hub-Signature-256", "")
            if not self.verify_webhook_signature(payload, signature):
                raise ValueError("Invalid webhook signature")

            # Parse payload
            event_type = headers.get("X-GitHub-Event")
            data = json.loads(payload.decode("utf-8"))

            self.logger.info(f"Processing GitHub event: {event_type}")

            # Route to appropriate handler
            if event_type in self.event_handlers:
                result = await self.event_handlers[event_type](data)
                return {"status": "processed", "event": event_type, "result": result}
            else:
                self.logger.info(f"Unhandled event type: {event_type}")
                return {"status": "ignored", "event": event_type}

        except Exception as e:
            self.logger.error(f"Error processing webhook: {e}")
            return {"status": "error", "error": str(e)}

    async def handle_issue_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub issues events."""
        action = data.get("action")
        issue = data.get("issue", {})
        repository = data.get("repository", {})

        self.logger.info(f"Issue event: {action} - {issue.get('title', 'N/A')}")

        if action == "opened":
            return await self.create_task_from_issue(issue, repository)
        elif action == "closed":
            return await self.close_task_from_issue(issue, repository)
        elif action == "labeled" or action == "unlabeled":
            return await self.update_task_from_issue(issue, repository)

        return {"action": action, "processed": False}

    async def handle_pull_request_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub pull request events."""
        action = data.get("action")
        pull_request = data.get("pull_request", {})
        repository = data.get("repository", {})

        self.logger.info(f"PR event: {action} - {pull_request.get('title', 'N/A')}")

        if action == "opened":
            return await self.create_task_from_pr(pull_request, repository)
        elif action == "ready_for_review":
            return await self.assign_reviewer_task(pull_request, repository)
        elif action == "closed" and pull_request.get("merged"):
            return await self.handle_pr_merge(pull_request, repository)

        return {"action": action, "processed": False}

    async def handle_release_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub release events."""
        action = data.get("action")
        release = data.get("release", {})
        repository = data.get("repository", {})

        self.logger.info(f"Release event: {action} - {release.get('name', 'N/A')}")

        if action == "published":
            return await self.create_deployment_tasks(release, repository)

        return {"action": action, "processed": False}

    async def create_task_from_issue(
        self, issue: Dict, repository: Dict
    ) -> Dict[str, Any]:
        """Create AI-CRM task from GitHub issue."""
        try:
            # Get repository configuration
            repo_config = await self.get_repository_config(repository["full_name"])

            # Check if task creation is enabled for this issue
            if not self.should_create_task_from_issue(issue, repo_config):
                return {"created": False, "reason": "filtered_by_config"}

            # Prepare task data
            task_data = {
                "title": f"GitHub Issue: {issue['title']}",
                "description": self.format_issue_description(issue, repository),
                "priority": self.determine_priority_from_labels(
                    issue.get("labels", [])
                ),
                "source": "github",
                "source_id": str(issue["id"]),
                "source_url": issue["html_url"],
                "pm_analysis": repo_config.get("auto_pm_analysis", True),
                "auto_assign": repo_config.get("auto_assign", True),
                "metadata": {
                    "repository": repository["full_name"],
                    "issue_number": issue["number"],
                    "author": issue["user"]["login"],
                    "labels": [label["name"] for label in issue.get("labels", [])],
                },
            }

            # Create task via AI-CRM API
            result = await self.create_ai_crm_task(task_data)

            # Add comment to GitHub issue with task link
            if result.get("task_id"):
                await self.add_github_comment(
                    repository["full_name"],
                    issue["number"],
                    f"✅ AI-CRM task created: {result['task_id']}\n"
                    f"🤖 Assigned to: {result.get('assigned_agent', 'Auto-detection')}\n"
                    f"📊 Priority: {result.get('priority', 'Medium')}",
                )

            return {
                "created": True,
                "task_id": result.get("task_id"),
                "agent": result.get("assigned_agent"),
            }

        except Exception as e:
            self.logger.error(f"Error creating task from issue: {e}")
            return {"created": False, "error": str(e)}

    async def create_task_from_pr(
        self, pull_request: Dict, repository: Dict
    ) -> Dict[str, Any]:
        """Create AI-CRM task from GitHub pull request."""
        try:
            # Get repository configuration
            repo_config = await self.get_repository_config(repository["full_name"])

            # Prepare task data for code review
            task_data = {
                "title": f"Code Review: {pull_request['title']}",
                "description": self.format_pr_description(pull_request, repository),
                "priority": "high",  # Code reviews are typically high priority
                "source": "github",
                "source_id": str(pull_request["id"]),
                "source_url": pull_request["html_url"],
                "pm_analysis": False,  # Skip PM analysis for code reviews
                "auto_assign": True,
                "agent_hint": "code-reviewer",  # Suggest code reviewer
                "metadata": {
                    "repository": repository["full_name"],
                    "pr_number": pull_request["number"],
                    "author": pull_request["user"]["login"],
                    "base_branch": pull_request["base"]["ref"],
                    "head_branch": pull_request["head"]["ref"],
                    "files_changed": pull_request.get("changed_files", 0),
                },
            }

            # Create task via AI-CRM API
            result = await self.create_ai_crm_task(task_data)

            # Add comment to GitHub PR
            if result.get("task_id"):
                await self.add_github_comment(
                    repository["full_name"],
                    pull_request["number"],
                    f"🔍 AI-CRM code review task created: {result['task_id']}\n"
                    f"👨‍💻 Reviewer: {result.get('assigned_agent', 'code-reviewer')}\n"
                    f"⏱️ Estimated review time: {result.get('estimated_hours', 2)} hours",
                    is_pr=True,
                )

            return {
                "created": True,
                "task_id": result.get("task_id"),
                "reviewer": result.get("assigned_agent"),
            }

        except Exception as e:
            self.logger.error(f"Error creating task from PR: {e}")
            return {"created": False, "error": str(e)}

    def should_create_task_from_issue(self, issue: Dict, repo_config: Dict) -> bool:
        """Determine if a task should be created from an issue based on configuration."""
        rules = repo_config.get("auto_task_creation", {}).get("rules", [])

        for rule in rules:
            if rule.get("trigger") == "issue_opened":
                conditions = rule.get("conditions", [])

                # Check label conditions
                issue_labels = [label["name"] for label in issue.get("labels", [])]

                for condition in conditions:
                    if "labels" in condition:
                        required_labels = condition["labels"]
                        if not any(label in issue_labels for label in required_labels):
                            continue

                    if "not_labels" in condition:
                        excluded_labels = condition["not_labels"]
                        if any(label in issue_labels for label in excluded_labels):
                            continue

                    # All conditions met
                    return True

        # Default to creating tasks if no specific rules
        return repo_config.get("auto_task_creation", {}).get("enabled", True)

    def format_issue_description(self, issue: Dict, repository: Dict) -> str:
        """Format GitHub issue for AI-CRM task description."""
        description = f"**GitHub Issue**: {issue['html_url']}\n"
        description += f"**Repository**: {repository['full_name']}\n"
        description += f"**Reporter**: {issue['user']['login']}\n"
        description += f"**Created**: {issue['created_at']}\n"

        if issue.get("labels"):
            labels = [label["name"] for label in issue["labels"]]
            description += f"**Labels**: {', '.join(labels)}\n"

        description += f"\n---\n\n{issue['body'] or 'No description provided.'}"

        return description

    def format_pr_description(self, pull_request: Dict, repository: Dict) -> str:
        """Format GitHub PR for AI-CRM task description."""
        description = f"**Pull Request**: {pull_request['html_url']}\n"
        description += f"**Repository**: {repository['full_name']}\n"
        description += f"**Author**: {pull_request['user']['login']}\n"
        description += f"**Base Branch**: {pull_request['base']['ref']}\n"
        description += f"**Head Branch**: {pull_request['head']['ref']}\n"
        description += (
            f"**Files Changed**: {pull_request.get('changed_files', 'N/A')}\n"
        )
        description += f"**Additions**: +{pull_request.get('additions', 0)}\n"
        description += f"**Deletions**: -{pull_request.get('deletions', 0)}\n"

        description += f"\n---\n\n{pull_request['body'] or 'No description provided.'}"

        return description

    def determine_priority_from_labels(self, labels: List[Dict]) -> str:
        """Determine task priority from GitHub labels."""
        label_names = [label["name"].lower() for label in labels]

        priority_mapping = {
            "critical": "urgent",
            "urgent": "urgent",
            "high": "high",
            "bug": "high",
            "security": "urgent",
            "enhancement": "medium",
            "feature": "medium",
            "documentation": "low",
            "question": "low",
        }

        # Check for priority labels
        for label_name in label_names:
            if label_name in priority_mapping:
                return priority_mapping[label_name]

        return "medium"  # Default priority

    async def get_repository_config(self, repo_full_name: str) -> Dict:
        """Get AI-CRM configuration for a repository."""
        if repo_full_name in self.repo_configs:
            return self.repo_configs[repo_full_name]

        try:
            # Try to fetch .github/ai-crm.yml from repository
            repo = self.github.get_repo(repo_full_name)
            config_file = repo.get_contents(".github/ai-crm.yml")
            config_content = config_file.decoded_content.decode("utf-8")
            config = yaml.safe_load(config_content)

            self.repo_configs[repo_full_name] = config
            return config

        except Exception as e:
            self.logger.info(
                f"No configuration found for {repo_full_name}, using defaults"
            )
            # Return default configuration
            default_config = {
                "auto_task_creation": {
                    "enabled": True,
                    "rules": [
                        {
                            "trigger": "issue_opened",
                            "conditions": [
                                {"labels": ["bug", "enhancement", "feature"]},
                                {"not_labels": ["wontfix", "duplicate", "invalid"]},
                            ],
                        }
                    ],
                },
                "auto_pm_analysis": True,
                "auto_assign": True,
                "code_review": {
                    "enabled": True,
                    "file_types": [".py", ".js", ".ts", ".go", ".java", ".rb"],
                },
            }

            self.repo_configs[repo_full_name] = default_config
            return default_config

    async def add_github_comment(
        self, repo_full_name: str, issue_number: int, comment: str, is_pr: bool = False
    ):
        """Add comment to GitHub issue or PR."""
        try:
            repo = self.github.get_repo(repo_full_name)

            if is_pr:
                pr = repo.get_pull(issue_number)
                pr.create_issue_comment(comment)
            else:
                issue = repo.get_issue(issue_number)
                issue.create_comment(comment)

            self.logger.info(f"Added comment to {repo_full_name}#{issue_number}")

        except Exception as e:
            self.logger.error(f"Error adding GitHub comment: {e}")

    async def create_ai_crm_task(self, task_data: Dict) -> Dict:
        """Create task via AI-CRM API."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ai_crm_base_url}/tasks",
                json=task_data,
                headers=self.ai_crm_headers,
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"AI-CRM API error: {response.status} - {error_text}"
                    )

    async def update_ai_crm_task_status(
        self, task_id: str, status: str, metadata: Dict = None
    ) -> Dict:
        """Update AI-CRM task status."""
        update_data = {"status": status}
        if metadata:
            update_data["metadata"] = metadata

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.ai_crm_base_url}/tasks/{task_id}",
                json=update_data,
                headers=self.ai_crm_headers,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"AI-CRM API error: {response.status} - {error_text}"
                    )

    async def handle_push_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub push events."""
        repository = data.get("repository", {})
        commits = data.get("commits", [])
        ref = data.get("ref", "")

        self.logger.info(
            f"Push event: {repository.get('full_name')} - {len(commits)} commits"
        )

        # Handle CI/CD triggers or automated task updates based on commit messages
        tasks_updated = []

        for commit in commits:
            message = commit.get("message", "")

            # Look for task references in commit messages (e.g., "fixes #123" or "closes task-456")
            task_refs = self.extract_task_references(message)

            for task_ref in task_refs:
                try:
                    # Update task status based on commit
                    result = await self.update_ai_crm_task_status(
                        task_ref["task_id"],
                        "completed"
                        if task_ref["action"] in ["fixes", "closes", "resolves"]
                        else "in_progress",
                        {
                            "github_commit": commit["id"],
                            "commit_message": message,
                            "author": commit["author"]["name"],
                        },
                    )
                    tasks_updated.append(task_ref)

                except Exception as e:
                    self.logger.error(f"Error updating task {task_ref['task_id']}: {e}")

        return {"commits_processed": len(commits), "tasks_updated": len(tasks_updated)}

    def extract_task_references(self, commit_message: str) -> List[Dict[str, str]]:
        """Extract task references from commit messages."""
        import re

        # Patterns for task references
        patterns = [
            r"(fixes|closes|resolves)\s+#(\d+)",
            r"(fixes|closes|resolves)\s+task[:\-\s]+([a-zA-Z0-9\-]+)",
            r"(updates?|refs?)\s+#(\d+)",
            r"(updates?|refs?)\s+task[:\-\s]+([a-zA-Z0-9\-]+)",
        ]

        references = []
        message_lower = commit_message.lower()

        for pattern in patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                references.append({"action": match.group(1), "task_id": match.group(2)})

        return references

    async def create_deployment_tasks(
        self, release: Dict, repository: Dict
    ) -> Dict[str, Any]:
        """Create deployment tasks from GitHub release."""
        try:
            # Create deployment task
            task_data = {
                "title": f"Deploy Release: {release['name']}",
                "description": self.format_release_description(release, repository),
                "priority": "high",
                "source": "github",
                "source_id": str(release["id"]),
                "source_url": release["html_url"],
                "pm_analysis": True,
                "auto_assign": True,
                "agent_hint": "deployment-engineer",
                "metadata": {
                    "repository": repository["full_name"],
                    "release_tag": release["tag_name"],
                    "release_name": release["name"],
                    "author": release["author"]["login"],
                    "prerelease": release.get("prerelease", False),
                },
            }

            # Create task via AI-CRM API
            result = await self.create_ai_crm_task(task_data)

            return {
                "created": True,
                "task_id": result.get("task_id"),
                "agent": result.get("assigned_agent"),
            }

        except Exception as e:
            self.logger.error(f"Error creating deployment task: {e}")
            return {"created": False, "error": str(e)}

    def format_release_description(self, release: Dict, repository: Dict) -> str:
        """Format GitHub release for AI-CRM task description."""
        description = f"**GitHub Release**: {release['html_url']}\n"
        description += f"**Repository**: {repository['full_name']}\n"
        description += f"**Tag**: {release['tag_name']}\n"
        description += f"**Author**: {release['author']['login']}\n"
        description += f"**Created**: {release['created_at']}\n"
        description += f"**Published**: {release['published_at']}\n"

        if release.get("prerelease"):
            description += f"**Type**: Pre-release\n"
        else:
            description += f"**Type**: Production release\n"

        description += f"\n---\n\n{release['body'] or 'No release notes provided.'}"

        return description


class GitHubWebhookHandler:
    """HTTP handler for GitHub webhooks."""

    def __init__(self, github_integration: GitHubIntegration):
        self.integration = github_integration
        self.logger = logging.getLogger("github_webhook_handler")

    async def handle_webhook(self, request) -> Dict[str, Any]:
        """Handle incoming webhook request."""
        try:
            # Get headers and payload
            headers = dict(request.headers)
            payload = await request.read()

            # Process webhook
            result = await self.integration.process_webhook(headers, payload)

            return result

        except Exception as e:
            self.logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "error": str(e)}


def create_github_integration() -> GitHubIntegration:
    """Create GitHub integration instance from environment variables."""
    config = GitHubConfig(
        app_id=os.getenv("GITHUB_APP_ID"),
        private_key=os.getenv("GITHUB_PRIVATE_KEY"),
        webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET"),
        client_id=os.getenv("GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
        ai_crm_api_url=os.getenv("AI_CRM_API_URL", "http://localhost:8000"),
        ai_crm_api_key=os.getenv("AI_CRM_API_KEY"),
    )

    return GitHubIntegration(config)


async def main():
    """Main function to run GitHub integration server."""
    import argparse
    from aiohttp import web

    parser = argparse.ArgumentParser(description="AI-CRM GitHub Integration")
    parser.add_argument("--port", type=int, default=3001, help="HTTP port for webhooks")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")

    args = parser.parse_args()

    # Create integration
    github_integration = create_github_integration()
    webhook_handler = GitHubWebhookHandler(github_integration)

    # Create web app
    app = web.Application()

    async def webhook_endpoint(request):
        """Webhook endpoint handler."""
        result = await webhook_handler.handle_webhook(request)
        return web.json_response(result)

    async def health_check(request):
        """Health check endpoint."""
        return web.json_response({"status": "healthy", "service": "github-integration"})

    # Routes
    app.router.add_post("/github/webhook", webhook_endpoint)
    app.router.add_get("/health", health_check)

    # Start server
    print(f"🚀 Starting AI-CRM GitHub Integration...")
    print(f"🌐 HTTP server starting on {args.host}:{args.port}")
    print(f"📡 GitHub webhook endpoint: /github/webhook")
    print(f"🏥 Health check endpoint: /health")

    try:
        web.run_app(app, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n👋 Shutting down GitHub integration...")


if __name__ == "__main__":
    asyncio.run(main())
