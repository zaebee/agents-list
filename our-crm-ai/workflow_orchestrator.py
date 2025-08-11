#!/usr/bin/env python3
"""
Multi-Agent Workflow Orchestrator - AI Project Manager Phase 3

Advanced orchestration system that manages complex multi-agent workflows with
seamless handoffs, progress tracking, and business context preservation.

Key Features:
- Intelligent agent handoff management
- Context preservation between agent interactions
- Real-time progress tracking and reporting
- Quality gates and validation checkpoints
- Exception handling and escalation workflows
- Business stakeholder notifications
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging

from business_pm_gateway import BusinessPMGateway, ProjectPlan
from workflow_persistence import WorkflowStorageBackend, FileWorkflowStorage
from analytics_engine import AnalyticsEngine


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(Enum):
    """Agent task status."""

    AVAILABLE = "available"
    BUSY = "busy"
    BLOCKED = "blocked"
    OFFLINE = "offline"


@dataclass
class AgentTask:
    """Individual agent task within a workflow."""

    task_id: str
    agent_name: str
    title: str
    description: str
    estimated_hours: float
    actual_hours: float = 0.0
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[Dict] = None
    context: Optional[Dict] = None
    quality_score: float = 0.0
    business_value: float = 0.0


@dataclass
class WorkflowExecution:
    """Complete workflow execution tracking."""

    workflow_id: str
    project_id: str
    project_name: str
    status: WorkflowStatus
    tasks: List[AgentTask]
    current_task_index: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_estimated_hours: float = 0.0
    total_actual_hours: float = 0.0
    business_context: Optional[Dict] = None
    progress_percentage: float = 0.0
    next_milestone: Optional[str] = None


class WorkflowOrchestrator:
    """Advanced multi-agent workflow orchestration system."""

    def __init__(self, storage_backend: Optional[WorkflowStorageBackend] = None):
        self.storage = storage_backend or FileWorkflowStorage()
        self.business_gateway = BusinessPMGateway()
        self.analytics = AnalyticsEngine()
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.agent_status: Dict[str, AgentStatus] = {}

        # Workflow event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "workflow_started": [],
            "task_started": [],
            "task_completed": [],
            "task_failed": [],
            "workflow_completed": [],
            "workflow_failed": [],
            "milestone_reached": [],
        }

        # Quality gates configuration
        self.quality_gates = {
            "code_review": {
                "required_score": 0.8,
                "validator_agent": "code-reviewer",
                "blocking": True,
            },
            "security_review": {
                "required_score": 0.9,
                "validator_agent": "security-auditor",
                "blocking": True,
            },
            "performance_check": {
                "required_score": 0.7,
                "validator_agent": "performance-engineer",
                "blocking": False,
            },
        }

        self.logger = logging.getLogger("workflow_orchestrator")

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler for workflow events."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)

    async def create_workflow_from_project_plan(self, project_plan: ProjectPlan) -> str:
        """Create and initialize workflow from business project plan."""
        workflow_id = str(uuid.uuid4())

        # Convert project phases to agent tasks
        tasks = []
        for i, phase in enumerate(project_plan.technical_phases):
            task_id = str(uuid.uuid4())

            agent_task = AgentTask(
                task_id=task_id,
                agent_name=phase["agent"],
                title=f"{project_plan.project_name} - {phase['phase']}",
                description=f"Phase {i + 1}: {phase['phase']}",
                estimated_hours=phase["duration_hours"],
                context={
                    "phase_number": i + 1,
                    "total_phases": len(project_plan.technical_phases),
                    "business_context": asdict(project_plan.business_context),
                    "dependencies": phase.get("dependencies", []),
                    "business_impact": phase.get("business_tracking", []),
                },
            )
            tasks.append(agent_task)

        # Create workflow execution
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            project_id=str(uuid.uuid4()),  # Could link to actual project ID
            project_name=project_plan.project_name,
            status=WorkflowStatus.PENDING,
            tasks=tasks,
            total_estimated_hours=sum(task.estimated_hours for task in tasks),
            business_context={
                "roi_projection": project_plan.roi_projection,
                "risk_assessment": project_plan.risk_assessment,
                "success_criteria": project_plan.success_criteria,
                "estimated_cost": project_plan.estimated_cost,
            },
        )

        # Store workflow
        await self.storage.save_workflow(workflow_id, asdict(workflow))
        self.active_workflows[workflow_id] = workflow

        self.logger.info(
            f"Created workflow {workflow_id} for project '{project_plan.project_name}'"
        )
        return workflow_id

    async def start_workflow(self, workflow_id: str) -> bool:
        """Start workflow execution."""
        workflow = await self._get_workflow(workflow_id)
        if not workflow:
            return False

        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()

        # Emit workflow started event
        await self._emit_event(
            "workflow_started",
            {
                "workflow_id": workflow_id,
                "project_name": workflow.project_name,
                "total_tasks": len(workflow.tasks),
                "estimated_hours": workflow.total_estimated_hours,
            },
        )

        # Start first task
        if workflow.tasks:
            await self._start_next_task(workflow)

        # Update storage
        await self.storage.update_workflow(workflow_id, asdict(workflow))

        self.logger.info(f"Started workflow {workflow_id}")
        return True

    async def _start_next_task(self, workflow: WorkflowExecution) -> bool:
        """Start the next available task in workflow."""
        if workflow.current_task_index >= len(workflow.tasks):
            # Workflow completed
            await self._complete_workflow(workflow)
            return False

        current_task = workflow.tasks[workflow.current_task_index]

        # Check agent availability
        agent_status = self.agent_status.get(
            current_task.agent_name, AgentStatus.AVAILABLE
        )
        if agent_status == AgentStatus.BUSY:
            self.logger.warning(
                f"Agent {current_task.agent_name} is busy, queuing task"
            )
            return False

        # Start task
        current_task.status = WorkflowStatus.RUNNING
        current_task.started_at = datetime.now()
        self.agent_status[current_task.agent_name] = AgentStatus.BUSY

        # Emit task started event
        await self._emit_event(
            "task_started",
            {
                "workflow_id": workflow.workflow_id,
                "task_id": current_task.task_id,
                "agent_name": current_task.agent_name,
                "task_title": current_task.title,
                "estimated_hours": current_task.estimated_hours,
            },
        )

        # Simulate task execution (in real implementation, this would delegate to actual agents)
        asyncio.create_task(self._simulate_task_execution(workflow, current_task))

        return True

    async def _simulate_task_execution(
        self, workflow: WorkflowExecution, task: AgentTask
    ):
        """Simulate agent task execution (replace with real agent integration)."""
        try:
            # Simulate work time (shortened for demo)
            execution_time = min(
                task.estimated_hours * 3, 10
            )  # Max 10 seconds for demo
            await asyncio.sleep(execution_time)

            # Simulate successful completion
            task.status = WorkflowStatus.COMPLETED
            task.completed_at = datetime.now()
            task.actual_hours = task.estimated_hours * (
                0.8 + (hash(task.task_id) % 40) / 100
            )  # 80-120% of estimate
            task.quality_score = 0.7 + (hash(task.task_id) % 30) / 100  # 70-99%
            task.business_value = task.estimated_hours * 150  # $150/hour business value
            task.output = {
                "status": "completed",
                "deliverables": [f"{task.title} completed successfully"],
                "notes": f"Task completed by {task.agent_name}",
                "metrics": {
                    "quality_score": task.quality_score,
                    "efficiency": task.estimated_hours / task.actual_hours
                    if task.actual_hours > 0
                    else 1.0,
                },
            }

            self.agent_status[task.agent_name] = AgentStatus.AVAILABLE

            # Check quality gates
            await self._check_quality_gates(workflow, task)

            # Emit task completed event
            await self._emit_event(
                "task_completed",
                {
                    "workflow_id": workflow.workflow_id,
                    "task_id": task.task_id,
                    "agent_name": task.agent_name,
                    "actual_hours": task.actual_hours,
                    "quality_score": task.quality_score,
                    "business_value": task.business_value,
                },
            )

            # Update progress
            await self._update_workflow_progress(workflow)

            # Move to next task
            workflow.current_task_index += 1
            await self._start_next_task(workflow)

        except Exception as e:
            # Handle task failure
            task.status = WorkflowStatus.FAILED
            task.output = {"error": str(e), "status": "failed"}
            self.agent_status[task.agent_name] = AgentStatus.AVAILABLE

            await self._emit_event(
                "task_failed",
                {
                    "workflow_id": workflow.workflow_id,
                    "task_id": task.task_id,
                    "agent_name": task.agent_name,
                    "error": str(e),
                },
            )

            # Handle failure recovery
            await self._handle_task_failure(workflow, task)

    async def _check_quality_gates(self, workflow: WorkflowExecution, task: AgentTask):
        """Check quality gates for completed task."""
        for gate_name, gate_config in self.quality_gates.items():
            if (
                gate_name.lower() in task.title.lower()
                or gate_name.lower() in task.description.lower()
            ):
                if task.quality_score < gate_config["required_score"]:
                    if gate_config["blocking"]:
                        # Failing quality gate blocks progress
                        task.status = WorkflowStatus.FAILED
                        task.output = task.output or {}
                        task.output["quality_gate_failure"] = {
                            "gate": gate_name,
                            "required_score": gate_config["required_score"],
                            "actual_score": task.quality_score,
                            "blocking": True,
                        }
                        self.logger.warning(
                            f"Task {task.task_id} failed quality gate: {gate_name}"
                        )
                    else:
                        # Non-blocking quality gate, just log warning
                        self.logger.warning(
                            f"Task {task.task_id} quality warning: {gate_name}"
                        )

    async def _update_workflow_progress(self, workflow: WorkflowExecution):
        """Update workflow progress and milestones."""
        completed_tasks = sum(
            1 for task in workflow.tasks if task.status == WorkflowStatus.COMPLETED
        )
        workflow.progress_percentage = (
            (completed_tasks / len(workflow.tasks)) * 100 if workflow.tasks else 0
        )

        workflow.total_actual_hours = sum(task.actual_hours for task in workflow.tasks)

        # Check milestones
        milestone_thresholds = [25, 50, 75, 90]
        for threshold in milestone_thresholds:
            if workflow.progress_percentage >= threshold and (
                not hasattr(workflow, "last_milestone")
                or workflow.last_milestone < threshold
            ):
                workflow.last_milestone = threshold
                workflow.next_milestone = next(
                    (t for t in milestone_thresholds if t > threshold), None
                )

                await self._emit_event(
                    "milestone_reached",
                    {
                        "workflow_id": workflow.workflow_id,
                        "milestone": threshold,
                        "progress_percentage": workflow.progress_percentage,
                        "completed_tasks": completed_tasks,
                        "total_tasks": len(workflow.tasks),
                    },
                )

        # Update storage
        await self.storage.update_workflow(workflow.workflow_id, asdict(workflow))

    async def _complete_workflow(self, workflow: WorkflowExecution):
        """Complete workflow execution."""
        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = datetime.now()
        workflow.progress_percentage = 100.0

        # Calculate final metrics
        total_business_value = sum(task.business_value for task in workflow.tasks)
        avg_quality_score = (
            sum(task.quality_score for task in workflow.tasks) / len(workflow.tasks)
            if workflow.tasks
            else 0
        )

        # Emit workflow completed event
        await self._emit_event(
            "workflow_completed",
            {
                "workflow_id": workflow.workflow_id,
                "project_name": workflow.project_name,
                "duration_hours": workflow.total_actual_hours,
                "business_value": total_business_value,
                "quality_score": avg_quality_score,
                "cost": workflow.total_actual_hours * 150,  # $150/hour
            },
        )

        # Update storage
        await self.storage.update_workflow(workflow.workflow_id, asdict(workflow))

        self.logger.info(f"Completed workflow {workflow.workflow_id}")

    async def _handle_task_failure(
        self, workflow: WorkflowExecution, failed_task: AgentTask
    ):
        """Handle task failure with recovery strategies."""
        # Simple recovery: retry with different agent or escalate
        self.logger.error(f"Task {failed_task.task_id} failed, implementing recovery")

        # For demo, mark workflow as failed
        workflow.status = WorkflowStatus.FAILED

        await self._emit_event(
            "workflow_failed",
            {
                "workflow_id": workflow.workflow_id,
                "failed_task_id": failed_task.task_id,
                "error": failed_task.output.get("error", "Unknown error")
                if failed_task.output
                else "Unknown error",
            },
        )

    async def _emit_event(self, event_type: str, data: Dict):
        """Emit workflow event to registered handlers."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                self.logger.error(f"Event handler failed for {event_type}: {e}")

    async def _get_workflow(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Get workflow from memory or storage."""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]

        workflow_data = await self.storage.load_workflow(workflow_id)
        if workflow_data:
            # Reconstruct workflow object
            tasks = [AgentTask(**task_data) for task_data in workflow_data["tasks"]]
            workflow = WorkflowExecution(
                workflow_id=workflow_data["workflow_id"],
                project_id=workflow_data["project_id"],
                project_name=workflow_data["project_name"],
                status=WorkflowStatus(workflow_data["status"]),
                tasks=tasks,
                current_task_index=workflow_data["current_task_index"],
                total_estimated_hours=workflow_data["total_estimated_hours"],
                total_actual_hours=workflow_data["total_actual_hours"],
                business_context=workflow_data.get("business_context"),
                progress_percentage=workflow_data.get("progress_percentage", 0.0),
            )

            # Parse datetime fields
            if workflow_data.get("started_at"):
                workflow.started_at = datetime.fromisoformat(
                    workflow_data["started_at"]
                )
            if workflow_data.get("completed_at"):
                workflow.completed_at = datetime.fromisoformat(
                    workflow_data["completed_at"]
                )

            self.active_workflows[workflow_id] = workflow
            return workflow

        return None

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current workflow status and progress."""
        workflow = await self._get_workflow(workflow_id)
        if not workflow:
            return None

        return {
            "workflow_id": workflow.workflow_id,
            "project_name": workflow.project_name,
            "status": workflow.status.value,
            "progress_percentage": workflow.progress_percentage,
            "current_task": workflow.tasks[workflow.current_task_index].title
            if workflow.current_task_index < len(workflow.tasks)
            else "Completed",
            "completed_tasks": sum(
                1 for task in workflow.tasks if task.status == WorkflowStatus.COMPLETED
            ),
            "total_tasks": len(workflow.tasks),
            "estimated_hours": workflow.total_estimated_hours,
            "actual_hours": workflow.total_actual_hours,
            "next_milestone": workflow.next_milestone,
        }

    async def list_active_workflows(self) -> List[Dict]:
        """List all active workflows."""
        workflows = []
        for workflow_id, workflow in self.active_workflows.items():
            workflows.append(
                {
                    "workflow_id": workflow_id,
                    "project_name": workflow.project_name,
                    "status": workflow.status.value,
                    "progress_percentage": workflow.progress_percentage,
                    "started_at": workflow.started_at.isoformat()
                    if workflow.started_at
                    else None,
                    "estimated_hours": workflow.total_estimated_hours,
                    "actual_hours": workflow.total_actual_hours,
                }
            )
        return workflows


# Event handlers for business notifications
async def business_stakeholder_notification_handler(data: Dict):
    """Handle business stakeholder notifications."""
    event_type = data.get("event_type", "unknown")

    notifications = {
        "workflow_started": f"🚀 Project '{data.get('project_name')}' has started with {data.get('total_tasks')} phases",
        "milestone_reached": f"📈 Project milestone reached: {data.get('milestone')}% complete ({data.get('completed_tasks')}/{data.get('total_tasks')} tasks)",
        "workflow_completed": f"🎉 Project '{data.get('project_name')}' completed! Business value: ${data.get('business_value', 0):,.0f}",
        "workflow_failed": f"🚨 Project workflow failed at task {data.get('failed_task_id')}: {data.get('error')}",
    }

    message = notifications.get(event_type, f"Project update: {event_type}")

    # In real implementation, this would send to Slack, email, etc.
    print(f"📧 Stakeholder Notification: {message}")


def create_orchestrator_with_business_handlers() -> WorkflowOrchestrator:
    """Create orchestrator with business-focused event handlers."""
    orchestrator = WorkflowOrchestrator()

    # Register business notification handlers
    orchestrator.register_event_handler(
        "workflow_started", business_stakeholder_notification_handler
    )
    orchestrator.register_event_handler(
        "milestone_reached", business_stakeholder_notification_handler
    )
    orchestrator.register_event_handler(
        "workflow_completed", business_stakeholder_notification_handler
    )
    orchestrator.register_event_handler(
        "workflow_failed", business_stakeholder_notification_handler
    )

    return orchestrator


async def main():
    """Demo workflow orchestration."""
    print("🎯 Multi-Agent Workflow Orchestrator - Demo")
    print("=" * 50)

    # Create orchestrator with business handlers
    orchestrator = create_orchestrator_with_business_handlers()

    # Create sample project plan
    business_gateway = BusinessPMGateway()
    project_plan = business_gateway.create_business_project_plan(
        "AI-Powered Task Manager",
        "Business Goal: $500K ARR, 5K users, SaaS platform with AI features, 4 months timeline",
    )

    print("\n📋 Creating workflow from project plan...")
    workflow_id = await orchestrator.create_workflow_from_project_plan(project_plan)
    print(f"✅ Created workflow: {workflow_id}")

    print("\n🚀 Starting workflow execution...")
    await orchestrator.start_workflow(workflow_id)

    print("\n⏱️  Monitoring workflow progress...")
    # Monitor for 30 seconds
    for i in range(10):
        await asyncio.sleep(3)
        status = await orchestrator.get_workflow_status(workflow_id)
        if status:
            print(
                f"   📊 {status['project_name']}: {status['progress_percentage']:.1f}% - {status['current_task']}"
            )
            if status["status"] in ["completed", "failed"]:
                break

    print("\n📈 Final workflow status:")
    final_status = await orchestrator.get_workflow_status(workflow_id)
    if final_status:
        print(f"   Status: {final_status['status']}")
        print(f"   Progress: {final_status['progress_percentage']:.1f}%")
        print(
            f"   Completed: {final_status['completed_tasks']}/{final_status['total_tasks']} tasks"
        )
        print(
            f"   Time: {final_status['actual_hours']:.1f}h / {final_status['estimated_hours']:.1f}h estimated"
        )


if __name__ == "__main__":
    asyncio.run(main())
