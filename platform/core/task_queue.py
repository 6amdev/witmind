#!/usr/bin/env python3
"""
6AMDev AI Platform - Task Queue
Redis-based task queue for agent communication
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger('task_queue')


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    id: str
    type: str
    agent_id: str
    project_id: str
    payload: Dict
    status: TaskStatus
    priority: TaskPriority
    created_at: str
    updated_at: str
    result: Optional[Dict] = None
    error: Optional[str] = None


class TaskQueue:
    """
    Task queue for managing agent tasks.
    Uses Redis if available, falls back to file-based queue.
    """

    def __init__(self, redis_url: str = None):
        self.redis_client = None
        self.use_redis = False

        # Try to connect to Redis
        redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379')
        try:
            import redis
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis not available, using file-based queue: {e}")
            self.queue_path = os.path.join(os.environ.get('WITMIND_ROOT', str(Path.home() / 'witmind-data')), 'logs/queue')
            os.makedirs(self.queue_path, exist_ok=True)

        self.handlers: Dict[str, Callable] = {}

    def create_task(
        self,
        task_type: str,
        agent_id: str,
        project_id: str,
        payload: Dict,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> Task:
        """Create a new task"""
        task = Task(
            id=f"task-{uuid.uuid4().hex[:8]}",
            type=task_type,
            agent_id=agent_id,
            project_id=project_id,
            payload=payload,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self._save_task(task)
        logger.info(f"Created task: {task.id} for agent: {agent_id}")

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self._load_task(task_id)

    def get_pending_tasks(self, agent_id: str = None) -> List[Task]:
        """Get all pending tasks, optionally filtered by agent"""
        tasks = self._get_all_tasks()
        pending = [t for t in tasks if t.status == TaskStatus.PENDING]

        if agent_id:
            pending = [t for t in pending if t.agent_id == agent_id]

        # Sort by priority (highest first) then by created_at
        pending.sort(key=lambda t: (-t.priority.value, t.created_at))

        return pending

    def claim_task(self, task_id: str) -> Optional[Task]:
        """Claim a task for processing"""
        task = self._load_task(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.now().isoformat()
            self._save_task(task)
            logger.info(f"Task claimed: {task_id}")
            return task
        return None

    def complete_task(self, task_id: str, result: Dict) -> Optional[Task]:
        """Mark a task as completed"""
        task = self._load_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.updated_at = datetime.now().isoformat()
            self._save_task(task)
            logger.info(f"Task completed: {task_id}")
            return task
        return None

    def fail_task(self, task_id: str, error: str) -> Optional[Task]:
        """Mark a task as failed"""
        task = self._load_task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
            task.updated_at = datetime.now().isoformat()
            self._save_task(task)
            logger.error(f"Task failed: {task_id} - {error}")
            return task
        return None

    def send_message(self, from_agent: str, to_agent: str, message_type: str, payload: Dict):
        """Send a message between agents"""
        message = {
            'id': f"msg-{uuid.uuid4().hex[:8]}",
            'from': from_agent,
            'to': to_agent,
            'type': message_type,
            'payload': payload,
            'timestamp': datetime.now().isoformat()
        }

        if self.use_redis:
            channel = f"agent:{to_agent}"
            self.redis_client.publish(channel, json.dumps(message))
        else:
            # File-based messaging
            msg_file = f"{self.queue_path}/msg_{message['id']}.json"
            with open(msg_file, 'w') as f:
                json.dump(message, f)

        logger.info(f"Message sent: {from_agent} -> {to_agent}")

    def subscribe(self, agent_id: str, handler: Callable):
        """Subscribe to messages for an agent"""
        self.handlers[agent_id] = handler

        if self.use_redis:
            # Redis pub/sub would be implemented here
            pass

    def get_stats(self) -> Dict:
        """Get queue statistics"""
        tasks = self._get_all_tasks()

        stats = {
            'total': len(tasks),
            'pending': len([t for t in tasks if t.status == TaskStatus.PENDING]),
            'in_progress': len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
            'completed': len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            'failed': len([t for t in tasks if t.status == TaskStatus.FAILED]),
        }

        return stats

    def _save_task(self, task: Task):
        """Save task to storage"""
        if self.use_redis:
            key = f"task:{task.id}"
            data = asdict(task)
            data['status'] = task.status.value
            data['priority'] = task.priority.value
            self.redis_client.set(key, json.dumps(data))
            self.redis_client.sadd('tasks:all', task.id)
        else:
            task_file = f"{self.queue_path}/task_{task.id}.json"
            data = asdict(task)
            data['status'] = task.status.value
            data['priority'] = task.priority.value
            with open(task_file, 'w') as f:
                json.dump(data, f, indent=2)

    def _load_task(self, task_id: str) -> Optional[Task]:
        """Load task from storage"""
        try:
            if self.use_redis:
                key = f"task:{task_id}"
                data = self.redis_client.get(key)
                if data:
                    data = json.loads(data)
                else:
                    return None
            else:
                task_file = f"{self.queue_path}/task_{task_id}.json"
                if os.path.exists(task_file):
                    with open(task_file, 'r') as f:
                        data = json.load(f)
                else:
                    return None

            return Task(
                id=data['id'],
                type=data['type'],
                agent_id=data['agent_id'],
                project_id=data['project_id'],
                payload=data['payload'],
                status=TaskStatus(data['status']),
                priority=TaskPriority(data['priority']),
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                result=data.get('result'),
                error=data.get('error')
            )
        except Exception as e:
            logger.error(f"Error loading task {task_id}: {e}")
            return None

    def _get_all_tasks(self) -> List[Task]:
        """Get all tasks from storage"""
        tasks = []

        if self.use_redis:
            task_ids = self.redis_client.smembers('tasks:all')
            for task_id in task_ids:
                task = self._load_task(task_id.decode() if isinstance(task_id, bytes) else task_id)
                if task:
                    tasks.append(task)
        else:
            import glob
            for task_file in glob.glob(f"{self.queue_path}/task_*.json"):
                task_id = os.path.basename(task_file).replace('task_', '').replace('.json', '')
                task = self._load_task(task_id)
                if task:
                    tasks.append(task)

        return tasks

    def cleanup_old_tasks(self, days: int = 7):
        """Clean up completed/failed tasks older than specified days"""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        tasks = self._get_all_tasks()

        removed = 0
        for task in tasks:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task_date = datetime.fromisoformat(task.updated_at)
                if task_date < cutoff:
                    self._delete_task(task.id)
                    removed += 1

        logger.info(f"Cleaned up {removed} old tasks")
        return removed

    def _delete_task(self, task_id: str):
        """Delete a task from storage"""
        if self.use_redis:
            self.redis_client.delete(f"task:{task_id}")
            self.redis_client.srem('tasks:all', task_id)
        else:
            task_file = f"{self.queue_path}/task_{task_id}.json"
            if os.path.exists(task_file):
                os.remove(task_file)
