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

# New Enterprise Suite Tools
from backend.app.tools.task_item_tools import CreateTaskItemTool, ListTaskItemsTool, VerifyTaskItemTool
from backend.app.tools.email_tools import ListEmailsTool, ReadEmailTool, ExtractEmailDetailsTool
from backend.app.tools.csv_tools import ListCSVFilesTool, InspectCSVTool, AnalyzeCSVTool, GenerateReportTool
from backend.app.tools.support_tools import ListSupportTicketsTool, UpdateSupportTicketTool
from backend.app.tools.inventory_tools import ListInventoryTool, CreatePurchaseRequestTool
from backend.app.tools.contract_tools import InspectDocumentTool, ListContractFilesTool, ExtractContractDetailsTool, VerifyContractTool


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
        # 1. Invoice & Financial Tools
        self.register(ListInvoiceFilesTool())
        self.register(ReadInvoiceTool())
        self.register(ExtractInvoiceFieldsTool())
        self.register(SearchVendorTool())
        self.register(SearchExistingInvoiceTool())
        self.register(CreatePayableTool())
        self.register(GetPayableTool())
        self.register(VerifyPayableTool())
        
        # 2. Email & Calendar / Task Tools
        self.register(ListEmailsTool())
        self.register(ReadEmailTool())
        self.register(ExtractEmailDetailsTool())
        self.register(CreateTaskItemTool())
        self.register(ListTaskItemsTool())
        self.register(VerifyTaskItemTool())

        # 3. CSV Analysis & Reporting Tools
        self.register(ListCSVFilesTool())
        self.register(InspectCSVTool())
        self.register(AnalyzeCSVTool())
        self.register(GenerateReportTool())

        # 4. Support Ticket Tools
        self.register(ListSupportTicketsTool())
        self.register(UpdateSupportTicketTool())

        # 5. Inventory & Supply Chain Tools
        self.register(ListInventoryTool())
        self.register(CreatePurchaseRequestTool())

        # 6. Universal Document Inspection & Legal Contract Tools
        self.register(InspectDocumentTool())
        self.register(ListContractFilesTool())
        self.register(ExtractContractDetailsTool())
        self.register(VerifyContractTool())

        # 7. Safety & Reporting Tools
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
