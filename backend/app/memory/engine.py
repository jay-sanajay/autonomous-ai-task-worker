"""
AgentOS - Three-Tier Persistent Memory Subsystem.
Implements:
  1. Working Memory: Task-scoped active state, DAG plan, extracted values, pending questions.
  2. Episodic Memory: Historical task outcomes, failed strategies, recovery methods, verification tokens.
  3. Semantic Memory: Curated facts about tools, application workflows, and approved procedures.

Includes relevance-based retrieval, secret redaction, and revalidation hooks.
"""

from __future__ import annotations
import re
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.database.models import EpisodicMemory, SemanticMemory, AgentTask, TaskStep, VerificationResult

# Secret and credential redaction patterns
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key\s*[:=]\s*['\"]?)([\w\-]{8,})(['\"]?)", r"\1[REDACTED_API_KEY]\3"),
    (r"(?i)(password\s*[:=]\s*['\"]?)([^'\"\s]{4,})(['\"]?)", r"\1[REDACTED_PASSWORD]\3"),
    (r"(?i)(bearer\s+)([\w\-\.]{15,})", r"\1[REDACTED_BEARER_TOKEN]"),
    (r"(?i)(cookie\s*[:=]\s*['\"]?)([^'\"\n]+)(['\"]?)", r"\1[REDACTED_COOKIE]\3"),
    (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[REDACTED_CREDIT_CARD]"),
]


def redact_sensitive_data(text: str) -> str:
    """Strip API keys, passwords, authentication cookies, and credit card numbers from stored memory."""
    if not isinstance(text, str):
        return text
    clean = text
    for pattern, repl in SECRET_PATTERNS:
        clean = re.sub(pattern, repl, clean)
    return clean


class MemoryEngine:
    """Manages recording, relevance filtering, and administration of agent memories."""

    @staticmethod
    def record_episodic_memory(
        db: Session,
        task_id: str,
        goal: str,
        outcome: str,
        failed_strategies: Optional[List[str]] = None,
        recovery_methods: Optional[List[str]] = None,
        verification_token: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EpisodicMemory:
        """Store historical task outcome and recovery experiences for future learning."""
        sanitized_goal = redact_sensitive_data(goal)
        record = EpisodicMemory(
            task_id=task_id,
            goal=sanitized_goal,
            outcome=outcome,
            failed_strategies=json.dumps(failed_strategies or []),
            recovery_methods=json.dumps(recovery_methods or []),
            verification_token=verification_token,
            metadata_json=redact_sensitive_data(json.dumps(metadata or {})),
            created_at=datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def seed_default_semantic_memory(db: Session):
        """Seed foundational enterprise facts and approved procedures if not already present."""
        existing_count = db.query(SemanticMemory).count()
        if existing_count > 0:
            return

        defaults = [
            (
                "APPROVED_PROCEDURE",
                "invoice_processing_rule",
                "For invoices exceeding $10,000.00 USD, AgentOS must submit a formal approval request and pause execution before registering payable.",
                "Corporate Governance Policy v4.2"
            ),
            (
                "APPROVED_PROCEDURE",
                "duplicate_prevention_rule",
                "Before posting any payable or commitment, the agent must query existing records by vendor and invoice number to prevent duplicate payouts.",
                "Financial Controls Manual"
            ),
            (
                "TOOL_FACT",
                "portal_invoice_url",
                "The simulated company portal invoices page is located at http://127.0.0.1:8000/portal/invoices and supports accessible field selectors #vendor_name, #invoice_number, #amount, and #submit-btn.",
                "IT Infrastructure Specs"
            ),
            (
                "TOOL_FACT",
                "contract_compliance_rule",
                "Commercial contracts must be audited for Limitation of Liability, Force Majeure, Termination Notice, Dispute Resolution, and Confidentiality clauses.",
                "Legal & Risk Management Standards"
            ),
            (
                "WORKFLOW",
                "sales_dataset_analysis",
                "Tabular CSV datasets should be analyzed for total revenue, top products, missing records, and summarized into a persistent markdown report.",
                "Analytics Workflow Standard"
            )
        ]

        for cat, key, content, prov in defaults:
            mem = SemanticMemory(
                category=cat,
                fact_key=key,
                fact_content=content,
                provenance=prov,
                verified=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(mem)
        db.commit()

    @staticmethod
    def retrieve_relevant_memories(
        db: Session,
        goal: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant episodic and semantic memories matching the current task.
        Extracts tokens and searches for corresponding past solutions and facts.
        """
        # Ensure default facts are seeded
        MemoryEngine.seed_default_semantic_memory(db)

        words = [w.lower() for w in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", goal)]
        keywords = [w for w in words if w not in {"the", "and", "for", "with", "from", "that", "this", "each", "all"}]

        # 1. Search Semantic Memory (Approved procedures & facts)
        semantic_results = []
        if keywords:
            query = db.query(SemanticMemory)
            filters = [SemanticMemory.fact_content.ilike(f"%{kw}%") for kw in keywords[:5]]
            query = query.filter(or_(*filters))
            semantic_results = query.limit(limit).all()

        # 2. Search Episodic Memory (Previous similar tasks)
        episodic_results = []
        if keywords:
            query = db.query(EpisodicMemory)
            filters = [EpisodicMemory.goal.ilike(f"%{kw}%") for kw in keywords[:4]]
            query = query.filter(or_(*filters))
            episodic_results = query.order_by(EpisodicMemory.created_at.desc()).limit(limit).all()

        return {
            "query_keywords": keywords,
            "semantic_memories": [
                {
                    "id": m.id,
                    "category": m.category,
                    "key": m.fact_key,
                    "content": m.fact_content,
                    "provenance": m.provenance,
                    "requires_revalidation": True  # Crucial requirement: memories are hypotheses, not blind ground truth!
                }
                for m in semantic_results
            ],
            "episodic_memories": [
                {
                    "id": e.id,
                    "task_id": e.task_id,
                    "goal": e.goal,
                    "outcome": e.outcome,
                    "failed_strategies": json.loads(e.failed_strategies or "[]"),
                    "recovery_methods": json.loads(e.recovery_methods or "[]"),
                    "verification_token": e.verification_token
                }
                for e in episodic_results
            ]
        }

    @staticmethod
    def list_all_episodic(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        records = db.query(EpisodicMemory).order_by(EpisodicMemory.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "task_id": r.task_id,
                "goal": r.goal,
                "outcome": r.outcome,
                "failed_strategies": json.loads(r.failed_strategies or "[]"),
                "recovery_methods": json.loads(r.recovery_methods or "[]"),
                "verification_token": r.verification_token,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]

    @staticmethod
    def list_all_semantic(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        MemoryEngine.seed_default_semantic_memory(db)
        records = db.query(SemanticMemory).order_by(SemanticMemory.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "category": r.category,
                "fact_key": r.fact_key,
                "fact_content": r.fact_content,
                "provenance": r.provenance,
                "verified": r.verified,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]

    @staticmethod
    def delete_episodic(db: Session, memory_id: int) -> bool:
        record = db.query(EpisodicMemory).filter(EpisodicMemory.id == memory_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True

    @staticmethod
    def delete_semantic(db: Session, memory_id: int) -> bool:
        record = db.query(SemanticMemory).filter(SemanticMemory.id == memory_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True
