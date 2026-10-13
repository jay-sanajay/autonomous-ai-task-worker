"""
AgentOS - Advanced Platform Capabilities API Router.
Exposes endpoints for Memory Management, Safe Replay, Benchmarking Suite, and Granular Telemetry.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.memory.engine import MemoryEngine
from backend.app.observability.telemetry import ReplayEngine, TelemetryCollector
from backend.app.benchmarks.eval_suite import BenchmarkHarness

advanced_router = APIRouter(prefix="/api", tags=["Advanced Platform Capabilities"])


# 1. Memory Subsystem Endpoints
@advanced_router.get("/memory/episodic")
def get_episodic_memories(db: Session = Depends(get_db)):
    """Retrieve episodic memories of previous task executions and recovery methods."""
    return MemoryEngine.list_all_episodic(db)


@advanced_router.get("/memory/semantic")
def get_semantic_memories(db: Session = Depends(get_db)):
    """Retrieve semantic memories (approved procedures, workflows, and tool facts)."""
    return MemoryEngine.list_all_semantic(db)


@advanced_router.delete("/memory/episodic/{memory_id}")
def delete_episodic_memory(memory_id: int, db: Session = Depends(get_db)):
    """Delete an episodic memory record."""
    success = MemoryEngine.delete_episodic(db, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Episodic memory record not found.")
    return {"status": "success", "message": f"Episodic memory #{memory_id} deleted."}


@advanced_router.delete("/memory/semantic/{memory_id}")
def delete_semantic_memory(memory_id: int, db: Session = Depends(get_db)):
    """Delete a semantic memory record."""
    success = MemoryEngine.delete_semantic(db, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Semantic memory record not found.")
    return {"status": "success", "message": f"Semantic memory #{memory_id} deleted."}


# 2. Observability & Safe Execution Replay
@advanced_router.post("/tasks/{task_id}/replay")
def replay_task_execution(task_id: str, db: Session = Depends(get_db)):
    """
    Execute a safe replay of a completed task.
    Uses recorded historical trace without repeating irreversible database writes or side effects.
    """
    try:
        return ReplayEngine.replay_task(db, task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@advanced_router.get("/telemetry/dashboard")
def get_telemetry_metrics(db: Session = Depends(get_db)):
    """Retrieve comprehensive observable platform metrics."""
    return TelemetryCollector.get_dashboard_metrics(db)


# 3. Repeatable Benchmarking Suite
@advanced_router.post("/benchmarks/run")
@advanced_router.get("/benchmarks/run")
def run_evaluation_benchmarks():
    """Execute repeatable 10-scenario benchmark suite with fault injection and calculate scorecard."""
    return BenchmarkHarness.run_full_benchmark()


# 4. Multi-Agent Orchestration Endpoint
@advanced_router.post("/multi-agent/run")
def run_multi_agent_task(goal: str, auto_approve: bool = True, db: Session = Depends(get_db)):
    """
    Execute task using specialized multi-agent roles:
    PlannerRole, ResearcherRole, ExecutorRole, and VerifierCriticRole.
    """
    import uuid
    from backend.app.agent.multi_agent import ControlledMultiAgentOrchestrator
    orchestrator = ControlledMultiAgentOrchestrator()
    task_id = f"multi-{uuid.uuid4().hex[:8]}"
    return orchestrator.run_multi_agent_workflow(
        db=db,
        goal=goal,
        task_id=task_id,
        auto_approve=auto_approve
    )
