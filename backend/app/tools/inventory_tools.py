"""
AgentOS - Inventory and Supply Chain Tools.
Enables the autonomous agent to monitor stock levels and draft purchase requests.
"""

from __future__ import annotations
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.tools.base import ControlledBaseTool, ToolResult
from backend.app.database.models import InventoryItem, PurchaseRequest


class ListInventoryTool(ControlledBaseTool):
    name = "list_inventory"
    description = (
        "Inspect product inventory stock levels in the enterprise database. "
        "Flags low-stock items where current inventory is below the reorder threshold."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "low_stock_only": {"type": "boolean", "description": "Filter strictly to products requiring reorder", "default": False}
        }
    }

    def execute(self, db_session: Session, low_stock_only: bool = False) -> ToolResult:
        query = db_session.query(InventoryItem)
        if low_stock_only:
            query = query.filter(InventoryItem.current_stock <= InventoryItem.reorder_threshold)

        items = query.all()
        return ToolResult(
            success=True,
            data={
                "total_items": len(items),
                "items": [
                    {
                        "id": item.id,
                        "sku": item.sku,
                        "product_name": item.product_name,
                        "category": item.category,
                        "current_stock": item.current_stock,
                        "reorder_threshold": item.reorder_threshold,
                        "unit_price": item.unit_price,
                        "status": item.status,
                        "is_low_stock": item.current_stock <= item.reorder_threshold
                    }
                    for item in items
                ]
            }
        )


class CreatePurchaseRequestTool(ControlledBaseTool):
    name = "create_purchase_request"
    description = (
        "Create a draft purchase request for low-stock inventory replenishment. "
        "Requires approval if the total estimated cost exceeds enterprise safety thresholds."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "sku": {"type": "string", "description": "Product SKU"},
            "quantity": {"type": "integer", "description": "Quantity to order", "default": 5}
        },
        "required": ["sku"]
    }

    def execute(self, db_session: Session, sku: str, quantity: int = 5) -> ToolResult:
        item = db_session.query(InventoryItem).filter(InventoryItem.sku == sku.strip()).first()
        if not item:
            return ToolResult(success=False, error=f"Inventory item SKU '{sku}' not found.", retryable=False)

        req_code = f"PR-{uuid.uuid4().hex[:6].upper()}"
        total_cost = float(item.unit_price * quantity)

        pr = PurchaseRequest(
            request_code=req_code,
            item_id=item.id,
            product_name=item.product_name,
            quantity=quantity,
            unit_price=item.unit_price,
            estimated_total=total_cost,
            status="DRAFT",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(pr)
        db_session.commit()
        db_session.refresh(pr)

        return ToolResult(
            success=True,
            data={
                "purchase_request_id": pr.id,
                "request_code": pr.request_code,
                "product_name": pr.product_name,
                "quantity": pr.quantity,
                "estimated_total": total_cost,
                "status": pr.status,
                "message": f"Created draft purchase request {pr.request_code} for {quantity} units of '{item.product_name}' (Total: ${total_cost:,.2f})."
            }
        )
