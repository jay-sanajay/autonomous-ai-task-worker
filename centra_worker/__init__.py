"""
CentraWorker - Autonomous AI Task Worker
A goal-driven autonomous agent system for enterprise computer workflows.
"""

from centra_worker.engine.agent import AutonomousAgent
from centra_worker.models.task import TaskRequest, TaskResult, TaskStatus
from centra_worker.tools.registry import default_registry

__version__ = "1.0.0"
__all__ = ["AutonomousAgent", "TaskRequest", "TaskResult", "TaskStatus", "default_registry"]
