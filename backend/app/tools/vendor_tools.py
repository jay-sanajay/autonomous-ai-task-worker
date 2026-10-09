"""
AgentOS - Vendor Management Tools.
Implements search_vendor with fuzzy / alias matching and ambiguity detection.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.database.models import Vendor
from backend.app.tools.base import ControlledBaseTool, ToolResult


class SearchVendorTool(ControlledBaseTool):
    name = "search_vendor"
    description = (
        "Search the company database for matching vendors by name or alias. "
        "Handles similar vendor names and flags ambiguous matches."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "vendor_name": {
                "type": "string",
                "description": "Name or keyword of the vendor (e.g. 'Acme Technologies', 'Acme')"
            }
        },
        "required": ["vendor_name"]
    }

    def execute(self, db_session: Session, vendor_name: str) -> ToolResult:
        query_str = vendor_name.strip().lower()
        if not query_str:
            return ToolResult(success=False, error="Vendor name cannot be empty.")

        all_vendors = db_session.query(Vendor).all()
        exact_matches = []
        partial_matches = []

        for v in all_vendors:
            v_name_lower = v.name.lower()
            aliases = [a.strip().lower() for a in (v.aliases or "").split(",") if a.strip()]

            # Exact name or code match
            if v_name_lower == query_str or v.vendor_code.lower() == query_str:
                exact_matches.append(v)
            # Alias match
            elif query_str in aliases or any(query_str == a for a in aliases):
                exact_matches.append(v)
            # Partial name match
            elif query_str in v_name_lower or v_name_lower in query_str:
                partial_matches.append(v)

        selected_matches = exact_matches if exact_matches else partial_matches

        if not selected_matches:
            return ToolResult(
                success=False,
                error=f"No approved vendor matching '{vendor_name}' found in database.",
                data={"query": vendor_name, "matched_count": 0}
            )

        if len(selected_matches) == 1:
            v = selected_matches[0]
            return ToolResult(
                success=True,
                data={
                    "vendor_id": v.id,
                    "vendor_code": v.vendor_code,
                    "name": v.name,
                    "payment_terms": v.payment_terms,
                    "status": v.status,
                    "category": v.category,
                    "is_ambiguous": False
                }
            )

        # Ambiguous match (multiple vendors found)
        candidates = [
            {"vendor_id": v.id, "vendor_code": v.vendor_code, "name": v.name}
            for v in selected_matches
        ]
        return ToolResult(
            success=False,
            error=f"Ambiguous vendor match: '{vendor_name}' matched {len(candidates)} vendors.",
            data={
                "is_ambiguous": True,
                "candidates": candidates,
                "requires_clarification": True
            }
        )
