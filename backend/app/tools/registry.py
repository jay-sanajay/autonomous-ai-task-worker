"""
AgentOS - Controlled Tool Registry.
Registers all callable tools, exports OpenAPI schemas, and executes tools safely with validated inputs.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from backend.app.tools.base import ControlledBaseTool, ToolResult
from backend.app.tools.invoice_tools import ListInvoiceFilesTool, ReadInvoiceTool, ExtractInvoiceFieldsTool
from backend.app.tools.vendor_tools import SearchVendorTool
from backend.app.tools.payable_tools import SearchExistingInvoiceTool, CreatePayableTool, GetPayableTool, VerifyPayableTool
from backend.app.tools.approval_tools import RequestApprovalTool, ReportTaskResultTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ControlledBaseTool] = {}
        self.register_defaults()

    def register(self, tool: ControlledBaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ControlledBaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[ControlledBaseTool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def register_defaults(self):
        # The 10 required controlled tools
        self.register(ListInvoiceFilesTool())
        self.register(ReadInvoiceTool())
        self.register(ExtractInvoiceFieldsTool())
        self.register(SearchVendorTool())
        self.register(SearchExistingInvoiceTool())
        self.register(CreatePayableTool())
        self.register(GetPayableTool())
        self.register(VerifyPayableTool())
        self.register(RequestApprovalTool())
        self.register(ReportTaskResultTool())

    def execute(self, tool_name: str, db_session, arguments: Dict[str, Any]) -> ToolResult:
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Unregistered tool: '{tool_name}'. Allowed tools: {list(self._tools.keys())}",
                retryable=False
            )
        return tool.run_safe(db_session, **arguments)


default_tool_registry = ToolRegistry()
