"""
AgentOS - Checkpoint & Resumption Engine.
Persists execution state after every step to ensure tasks can resume safely
after server restarts, network interruptions, or model timeouts without
repeating confirmed non-idempotent actions.
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from backend.app.database.models import TaskCheckpoint, AgentTask, TaskStep
from backend.app.agent.dag_planner import PlanDAG, PlanStepNode, StepExecutionStatus


class CheckpointManager:
    """Handles snapshot persistence and state reconstruction for tasks."""

    @staticmethod
    def create_checkpoint(
        db: Session,
        task_id: str,
        step_number: int,
        status: str,
        dag: PlanDAG,
        working_memory: Dict[str, Any],
        confirmed_writes: List[str],
        idempotency_keys: List[str]
    ) -> TaskCheckpoint:
        """Serialize current execution state and store in SQLite task_checkpoints table."""
        dag_state = {
            s_id: {
                "step_id": n.step_id,
                "status": n.status.value,
                "is_confirmed_complete": n.is_confirmed_complete,
                "is_non_idempotent_write": n.is_non_idempotent_write,
                "output_data": n.output_data,
                "error_message": n.error_message,
                "retry_count": n.retry_count
            }
            for s_id, n in dag.nodes.items()
        }

        dag_json = json.dumps(dag_state, sort_keys=True)
        mem_json = json.dumps(working_memory, sort_keys=True, default=str)
        writes_json = json.dumps(confirmed_writes)
        keys_json = json.dumps(idempotency_keys)

        checksum = hashlib.sha256(f"{task_id}:{step_number}:{dag_json}:{writes_json}".encode()).hexdigest()

        checkpoint = TaskCheckpoint(
            task_id=task_id,
            step_number=step_number,
            status=status,
            dag_state_json=dag_json,
            working_memory_json=mem_json,
            confirmed_writes_json=writes_json,
            idempotency_keys_json=keys_json,
            checkpoint_hash=checksum,
            created_at=datetime.now(timezone.utc)
        )
        db.add(checkpoint)
        db.commit()
        db.refresh(checkpoint)
        return checkpoint

    @staticmethod
    def load_latest_checkpoint(db: Session, task_id: str) -> Optional[TaskCheckpoint]:
        """Fetch newest valid checkpoint snapshot for a task."""
        return db.query(TaskCheckpoint).filter(
            TaskCheckpoint.task_id == task_id
        ).order_by(TaskCheckpoint.step_number.desc()).first()

    @staticmethod
    def restore_dag_from_checkpoint(
        checkpoint: TaskCheckpoint,
        base_dag: PlanDAG
    ) -> Tuple[PlanDAG, Dict[str, Any], List[str]]:
        """
        Reconstitute DAG execution state from checkpoint.
        Guarantees that already confirmed successful non-idempotent writes are NOT repeated.
        """
        dag_state = json.loads(checkpoint.dag_state_json or "{}")
        working_memory = json.loads(checkpoint.working_memory_json or "{}")
        confirmed_writes = json.loads(checkpoint.confirmed_writes_json or "[]")

        for s_id, node_state in dag_state.items():
            if s_id in base_dag.nodes:
                node = base_dag.nodes[s_id]
                node.status = StepExecutionStatus(node_state.get("status", "PENDING"))
                node.is_confirmed_complete = node_state.get("is_confirmed_complete", False)
                node.output_data = node_state.get("output_data")
                node.error_message = node_state.get("error_message")
                node.retry_count = node_state.get("retry_count", 0)

        # Restore confirmed writes set
        base_dag.confirmed_writes = set(confirmed_writes)
        return base_dag, working_memory, confirmed_writes
