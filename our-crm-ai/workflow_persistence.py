#!/usr/bin/env python3
"""
Workflow Persistence Layer
Advanced state management for PM Agent Gateway workflows with multiple storage backends.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from typing import Any

import aiosqlite

from exceptions import ConfigurationError


class WorkflowStorageBackend(ABC):
    """Abstract base class for workflow storage backends."""

    @abstractmethod
    async def save_workflow(
        self, workflow_id: str, workflow_data: dict[str, Any]
    ) -> bool:
        """Save workflow state."""
        pass

    @abstractmethod
    async def load_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """Load workflow state."""
        pass

    @abstractmethod
    async def update_workflow(self, workflow_id: str, updates: dict[str, Any]) -> bool:
        """Update workflow state."""
        pass

    @abstractmethod
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow state."""
        pass

    @abstractmethod
    async def list_workflows(
        self, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List workflows with optional filtering."""
        pass

    @abstractmethod
    async def cleanup_old_workflows(self, days: int = 30) -> int:
        """Clean up old workflows and return count of cleaned up items."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check backend health."""
        pass


class FileWorkflowStorage(WorkflowStorageBackend):
    """File-based workflow storage backend."""

    def __init__(self, storage_dir: str = "workflow_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("file_workflow_storage")

    def _get_workflow_path(self, workflow_id: str) -> Path:
        """Get file path for workflow."""
        return self.storage_dir / f"{workflow_id}.json"

    async def save_workflow(
        self, workflow_id: str, workflow_data: dict[str, Any]
    ) -> bool:
        """Save workflow to JSON file."""
        try:
            workflow_path = self._get_workflow_path(workflow_id)

            # Add metadata
            enhanced_data = {
                **workflow_data,
                "workflow_id": workflow_id,
                "created_at": workflow_data.get(
                    "created_at", datetime.utcnow().isoformat()
                ),
                "updated_at": datetime.utcnow().isoformat(),
                "version": workflow_data.get("version", 1),
            }

            # Write atomically
            temp_path = workflow_path.with_suffix(".json.tmp")
            with open(temp_path, "w") as f:
                json.dump(enhanced_data, f, indent=2, default=str)

            temp_path.replace(workflow_path)

            self.logger.debug(f"Saved workflow {workflow_id} to {workflow_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save workflow {workflow_id}: {e}")
            return False

    async def load_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """Load workflow from JSON file."""
        try:
            workflow_path = self._get_workflow_path(workflow_id)

            if not workflow_path.exists():
                return None

            with open(workflow_path) as f:
                workflow_data = json.load(f)

            return workflow_data

        except Exception as e:
            self.logger.error(f"Failed to load workflow {workflow_id}: {e}")
            return None

    async def update_workflow(self, workflow_id: str, updates: dict[str, Any]) -> bool:
        """Update workflow in file."""
        try:
            # Load existing workflow
            existing_data = await self.load_workflow(workflow_id)
            if not existing_data:
                return False

            # Apply updates
            existing_data.update(updates)
            existing_data["updated_at"] = datetime.utcnow().isoformat()
            existing_data["version"] = existing_data.get("version", 1) + 1

            # Save updated data
            return await self.save_workflow(workflow_id, existing_data)

        except Exception as e:
            self.logger.error(f"Failed to update workflow {workflow_id}: {e}")
            return False

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow file."""
        try:
            workflow_path = self._get_workflow_path(workflow_id)

            if workflow_path.exists():
                workflow_path.unlink()
                self.logger.debug(f"Deleted workflow {workflow_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return False

    async def list_workflows(
        self, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List workflows from files."""
        workflows = []

        try:
            # Get all workflow files
            workflow_files = list(self.storage_dir.glob("*.json"))
            workflow_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Apply pagination
            start_idx = offset
            end_idx = offset + limit

            for workflow_file in workflow_files[start_idx:end_idx]:
                workflow_id = workflow_file.stem
                workflow_data = await self.load_workflow(workflow_id)

                if workflow_data:
                    # Apply status filter
                    if status is None or workflow_data.get("status") == status:
                        workflows.append(workflow_data)

            return workflows

        except Exception as e:
            self.logger.error(f"Failed to list workflows: {e}")
            return []

    async def cleanup_old_workflows(self, days: int = 30) -> int:
        """Clean up old workflow files."""
        cleaned_count = 0
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        try:
            workflow_files = list(self.storage_dir.glob("*.json"))

            for workflow_file in workflow_files:
                try:
                    # Check file modification time
                    file_time = datetime.fromtimestamp(workflow_file.stat().st_mtime)

                    if file_time < cutoff_time:
                        # Load to check status
                        workflow_data = await self.load_workflow(workflow_file.stem)

                        if workflow_data and workflow_data.get("status") in [
                            "completed",
                            "cancelled",
                        ]:
                            workflow_file.unlink()
                            cleaned_count += 1
                            self.logger.debug(
                                f"Cleaned up old workflow: {workflow_file.stem}"
                            )

                except Exception as e:
                    self.logger.warning(
                        f"Failed to cleanup workflow file {workflow_file}: {e}"
                    )

            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old workflows: {e}")
            return 0

    async def health_check(self) -> bool:
        """Check if storage directory is accessible."""
        try:
            return self.storage_dir.exists() and self.storage_dir.is_dir()
        except Exception:
            return False


class SQLiteWorkflowStorage(WorkflowStorageBackend):
    """SQLite-based workflow storage backend with advanced querying."""

    def __init__(self, db_path: str = "workflows.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger("sqlite_workflow_storage")
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database is initialized."""
        if not self._initialized:
            await self._initialize_database()
            self._initialized = True

    async def _initialize_database(self):
        """Initialize SQLite database with workflow schema."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS workflows (
                        workflow_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        priority TEXT,
                        complexity TEXT,
                        estimated_hours REAL,
                        workflow_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        version INTEGER DEFAULT 1
                    )
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at)
                """)

                await db.commit()

            self.logger.debug(f"Initialized workflow database: {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise ConfigurationError(f"Database initialization failed: {e!s}")

    async def save_workflow(
        self, workflow_id: str, workflow_data: dict[str, Any]
    ) -> bool:
        """Save workflow to SQLite database."""
        try:
            await self._ensure_initialized()

            async with aiosqlite.connect(self.db_path) as db:
                # Extract metadata for indexed columns
                title = workflow_data.get("title", "")
                description = workflow_data.get("description", "")
                status = workflow_data.get("status", "active")
                priority = workflow_data.get("priority", "medium")
                complexity = workflow_data.get("complexity", "moderate")
                estimated_hours = workflow_data.get("estimated_hours", 8.0)

                # Store complete data as JSON
                workflow_json = json.dumps(workflow_data, default=str)

                await db.execute(
                    """
                    INSERT OR REPLACE INTO workflows (
                        workflow_id, title, description, status, priority,
                        complexity, estimated_hours, workflow_data, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        workflow_id,
                        title,
                        description,
                        status,
                        priority,
                        complexity,
                        estimated_hours,
                        workflow_json,
                    ),
                )

                await db.commit()

            self.logger.debug(f"Saved workflow {workflow_id} to database")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save workflow {workflow_id}: {e}")
            return False

    async def load_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """Load workflow from SQLite database."""
        try:
            await self._ensure_initialized()

            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT workflow_data FROM workflows WHERE workflow_id = ?",
                    (workflow_id,),
                ) as cursor:
                    row = await cursor.fetchone()

                    if row:
                        return json.loads(row[0])

            return None

        except Exception as e:
            self.logger.error(f"Failed to load workflow {workflow_id}: {e}")
            return None

    async def update_workflow(self, workflow_id: str, updates: dict[str, Any]) -> bool:
        """Update workflow in database."""
        try:
            await self._ensure_initialized()

            # Load existing workflow
            existing_data = await self.load_workflow(workflow_id)
            if not existing_data:
                return False

            # Apply updates
            existing_data.update(updates)
            existing_data["updated_at"] = datetime.utcnow().isoformat()
            existing_data["version"] = existing_data.get("version", 1) + 1

            # Save updated data
            return await self.save_workflow(workflow_id, existing_data)

        except Exception as e:
            self.logger.error(f"Failed to update workflow {workflow_id}: {e}")
            return False

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow from database."""
        try:
            await self._ensure_initialized()

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM workflows WHERE workflow_id = ?", (workflow_id,)
                )
                await db.commit()

            self.logger.debug(f"Deleted workflow {workflow_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return False

    async def list_workflows(
        self, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List workflows from database with advanced filtering."""
        try:
            await self._ensure_initialized()

            # Build query
            query = "SELECT workflow_data FROM workflows"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            workflows = []
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        workflow_data = json.loads(row[0])
                        workflows.append(workflow_data)

            return workflows

        except Exception as e:
            self.logger.error(f"Failed to list workflows: {e}")
            return []

    async def cleanup_old_workflows(self, days: int = 30) -> int:
        """Clean up old workflows from database."""
        try:
            await self._ensure_initialized()

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            async with aiosqlite.connect(self.db_path) as db:
                # Delete old completed/cancelled workflows
                cursor = await db.execute(
                    """
                    DELETE FROM workflows 
                    WHERE created_at < ? 
                    AND status IN ('completed', 'cancelled')
                """,
                    (cutoff_date,),
                )

                deleted_count = cursor.rowcount
                await db.commit()

            self.logger.info(f"Cleaned up {deleted_count} old workflows")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old workflows: {e}")
            return 0

    async def health_check(self) -> bool:
        """Check database connectivity and integrity."""
        try:
            await self._ensure_initialized()

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("SELECT COUNT(*) FROM workflows")
                return True

        except Exception:
            return False

    async def get_workflow_statistics(self) -> dict[str, Any]:
        """Get workflow statistics from database."""
        try:
            await self._ensure_initialized()

            stats = {}
            async with aiosqlite.connect(self.db_path) as db:
                # Total workflows
                async with db.execute("SELECT COUNT(*) FROM workflows") as cursor:
                    row = await cursor.fetchone()
                    stats["total_workflows"] = row[0] if row else 0

                # Workflows by status
                async with db.execute("""
                    SELECT status, COUNT(*) FROM workflows GROUP BY status
                """) as cursor:
                    stats["by_status"] = {row[0]: row[1] async for row in cursor}

                # Workflows by complexity
                async with db.execute("""
                    SELECT complexity, COUNT(*) FROM workflows GROUP BY complexity
                """) as cursor:
                    stats["by_complexity"] = {row[0]: row[1] async for row in cursor}

                # Average estimated hours
                async with db.execute("""
                    SELECT AVG(estimated_hours) FROM workflows WHERE estimated_hours > 0
                """) as cursor:
                    row = await cursor.fetchone()
                    stats["average_estimated_hours"] = row[0] if row and row[0] else 0

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get workflow statistics: {e}")
            return {}


class WorkflowPersistenceManager:
    """
    High-level workflow persistence manager with multiple backend support.
    """

    def __init__(
        self,
        backend: WorkflowStorageBackend,
        enable_caching: bool = True,
        cache_ttl: int = 300,  # 5 minutes
    ):
        self.backend = backend
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.logger = logging.getLogger("workflow_persistence")

        # Simple in-memory cache
        self._cache: dict[str, tuple] = {}  # workflow_id -> (data, timestamp)

    def _is_cache_valid(self, workflow_id: str) -> bool:
        """Check if cached data is still valid."""
        if not self.enable_caching or workflow_id not in self._cache:
            return False

        _, timestamp = self._cache[workflow_id]
        return (datetime.utcnow() - timestamp).total_seconds() < self.cache_ttl

    def _cache_workflow(self, workflow_id: str, data: dict[str, Any]):
        """Cache workflow data."""
        if self.enable_caching:
            self._cache[workflow_id] = (data, datetime.utcnow())

    def _invalidate_cache(self, workflow_id: str):
        """Invalidate cached workflow."""
        if workflow_id in self._cache:
            del self._cache[workflow_id]

    async def save_workflow_state(
        self, task_id: str, title: str, description: str, workflow_data: dict[str, Any]
    ) -> bool:
        """Save comprehensive workflow state."""
        try:
            # Enrich workflow data with metadata
            enhanced_data = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                **workflow_data,
            }

            success = await self.backend.save_workflow(task_id, enhanced_data)

            if success:
                self._cache_workflow(task_id, enhanced_data)
                self.logger.info(f"Saved workflow state for task {task_id}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to save workflow state for {task_id}: {e}")
            return False

    async def load_workflow_state(self, task_id: str) -> dict[str, Any] | None:
        """Load workflow state with caching."""
        try:
            # Check cache first
            if self._is_cache_valid(task_id):
                data, _ = self._cache[task_id]
                self.logger.debug(f"Loaded workflow {task_id} from cache")
                return data

            # Load from backend
            data = await self.backend.load_workflow(task_id)

            if data:
                self._cache_workflow(task_id, data)
                self.logger.debug(f"Loaded workflow {task_id} from backend")

            return data

        except Exception as e:
            self.logger.error(f"Failed to load workflow state for {task_id}: {e}")
            return None

    async def update_workflow_status(
        self,
        task_id: str,
        status: str,
        additional_updates: dict[str, Any] | None = None,
    ) -> bool:
        """Update workflow status and additional fields."""
        try:
            updates = {"status": status}
            if additional_updates:
                updates.update(additional_updates)

            success = await self.backend.update_workflow(task_id, updates)

            if success:
                self._invalidate_cache(task_id)
                self.logger.info(f"Updated workflow {task_id} status to {status}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to update workflow status for {task_id}: {e}")
            return False

    async def complete_workflow(
        self, task_id: str, completion_data: dict[str, Any]
    ) -> bool:
        """Mark workflow as completed with results."""
        completion_updates = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "completion_data": completion_data,
        }

        return await self.update_workflow_status(
            task_id, "completed", completion_updates
        )

    async def cancel_workflow(self, task_id: str, reason: str) -> bool:
        """Cancel workflow with reason."""
        cancellation_updates = {
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancellation_reason": reason,
        }

        return await self.update_workflow_status(
            task_id, "cancelled", cancellation_updates
        )

    async def list_active_workflows(self, limit: int = 50) -> list[dict[str, Any]]:
        """List active workflows."""
        return await self.backend.list_workflows(status="active", limit=limit)

    async def cleanup_old_workflows(self, days: int = 30) -> int:
        """Clean up old workflows and clear cache."""
        cleaned_count = await self.backend.cleanup_old_workflows(days)

        if cleaned_count > 0:
            # Clear cache to avoid stale data
            self._cache.clear()
            self.logger.info(f"Cleaned up {cleaned_count} workflows and cleared cache")

        return cleaned_count

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check."""
        backend_healthy = await self.backend.health_check()

        return {
            "backend_healthy": backend_healthy,
            "cache_enabled": self.enable_caching,
            "cached_items": len(self._cache),
            "backend_type": type(self.backend).__name__,
        }


# Factory functions for creating persistence managers
def create_file_persistence_manager(
    storage_dir: str = "workflow_storage", enable_caching: bool = True
) -> WorkflowPersistenceManager:
    """Create file-based workflow persistence manager."""
    backend = FileWorkflowStorage(storage_dir)
    return WorkflowPersistenceManager(backend, enable_caching)


def create_sqlite_persistence_manager(
    db_path: str = "workflows.db", enable_caching: bool = True
) -> WorkflowPersistenceManager:
    """Create SQLite-based workflow persistence manager."""
    backend = SQLiteWorkflowStorage(db_path)
    return WorkflowPersistenceManager(backend, enable_caching)


# Default instance for backward compatibility
_default_persistence_manager = None


def get_default_persistence_manager() -> WorkflowPersistenceManager:
    """Get default persistence manager instance."""
    global _default_persistence_manager

    if _default_persistence_manager is None:
        _default_persistence_manager = create_file_persistence_manager()

    return _default_persistence_manager
