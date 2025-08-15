"""
Background Task Management Service

This service provides enhanced background task management for long-running operations
like crawl jobs, ensuring they run independently of HTTP request lifecycle.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTask:
    def __init__(self, task_id: str, name: str, func: Callable, *args, **kwargs):
        self.task_id = task_id
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Any = None
        self.asyncio_task: Optional[asyncio.Task] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "has_result": self.result is not None
        }


class BackgroundTaskService:
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self._cleanup_interval = 3600  # Clean up completed tasks after 1 hour
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the background task service"""
        if self._running:
            return
        
        self._running = True
        # Start periodic cleanup of old completed tasks
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("Background task service started")

    async def stop(self):
        """Stop the background task service and cancel all running tasks"""
        self._running = False
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Cancel all running tasks
        running_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]
        for task in running_tasks:
            if task.asyncio_task and not task.asyncio_task.done():
                task.asyncio_task.cancel()
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()

        logger.info(f"Background task service stopped. Cancelled {len(running_tasks)} running tasks")

    def create_task(self, name: str, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> str:
        """Create and start a new background task"""
        task_id = str(uuid.uuid4())
        background_task = BackgroundTask(task_id, name, func, *args, **kwargs)
        self.tasks[task_id] = background_task
        
        # Start the task immediately
        background_task.asyncio_task = asyncio.create_task(self._run_task(background_task))
        
        logger.info(f"Created background task: {task_id} - {name}")
        return task_id

    async def _run_task(self, background_task: BackgroundTask):
        """Execute a background task with proper error handling"""
        background_task.status = TaskStatus.RUNNING
        background_task.started_at = datetime.utcnow()
        
        try:
            logger.info(f"Starting background task: {background_task.task_id} - {background_task.name}")
            result = await background_task.func(*background_task.args, **background_task.kwargs)
            background_task.result = result
            background_task.status = TaskStatus.COMPLETED
            logger.info(f"Completed background task: {background_task.task_id} - {background_task.name}")
            
        except asyncio.CancelledError:
            background_task.status = TaskStatus.CANCELLED
            logger.info(f"Cancelled background task: {background_task.task_id} - {background_task.name}")
            raise
            
        except Exception as e:
            background_task.status = TaskStatus.FAILED
            background_task.error = str(e)
            logger.error(f"Failed background task: {background_task.task_id} - {background_task.name}: {e}")
            
        finally:
            background_task.completed_at = datetime.utcnow()

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get a specific background task"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, BackgroundTask]:
        """Get all background tasks"""
        return self.tasks.copy()

    def get_running_tasks(self) -> Dict[str, BackgroundTask]:
        """Get all currently running tasks"""
        return {
            task_id: task for task_id, task in self.tasks.items()
            if task.status == TaskStatus.RUNNING
        }

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running background task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
            
        if task.status == TaskStatus.RUNNING and task.asyncio_task:
            task.asyncio_task.cancel()
            return True
            
        return False

    async def _periodic_cleanup(self):
        """Periodically clean up old completed tasks"""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                if not self._running:
                    break
                    
                current_time = datetime.utcnow()
                to_remove = []
                
                for task_id, task in self.tasks.items():
                    if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                        task.completed_at and 
                        (current_time - task.completed_at).total_seconds() > self._cleanup_interval):
                        to_remove.append(task_id)
                
                for task_id in to_remove:
                    del self.tasks[task_id]
                    
                if to_remove:
                    logger.info(f"Cleaned up {len(to_remove)} old background tasks")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background task cleanup: {e}")


# Global background task service instance
background_task_service = BackgroundTaskService()
