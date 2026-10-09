from __future__ import annotations
from typing import Dict, Any, List, Optional
from centra_worker.tools.base import BaseTool
from centra_worker.tools.file_tools import ListFilesTool, ReadFileTool, SearchFilesTool
from centra_worker.tools.erp_api_tools import ERPGetVendorsTool, ERPGetInvoicesTool, ERPSubmitInvoiceTool
from centra_worker.tools.browser_tools import BrowserNavigateTool, BrowserFillFormTool
from centra_worker.tools.verification_tools import ERPVerifyRecordTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self.register_defaults()

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def register_defaults(self):
        self.register(ListFilesTool())
        self.register(ReadFileTool())
        self.register(SearchFilesTool())
        self.register(ERPGetVendorsTool())
        self.register(ERPGetInvoicesTool())
        self.register(ERPSubmitInvoiceTool())
        self.register(BrowserNavigateTool())
        self.register(BrowserFillFormTool())
        self.register(ERPVerifyRecordTool())

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        tool = self.get(name)
        if not tool:
            return {"status": "error", "error": f"Tool '{name}' is not registered."}
        try:
            return tool.run(**arguments)
        except Exception as e:
            return {"status": "error", "error": f"Tool execution failed: {str(e)}"}


# Global default registry
default_registry = ToolRegistry()
