import os
import pytest
from centra_worker.tools.file_tools import ListFilesTool, ReadFileTool, SearchFilesTool
from centra_worker.tools.erp_api_tools import ERPGetVendorsTool, ERPSubmitInvoiceTool
from centra_worker.tools.verification_tools import ERPVerifyRecordTool
from centra_worker.tools.browser_tools import BrowserNavigateTool, BrowserFillFormTool
from simulated_company.erp_server import erp_db


@pytest.fixture(autouse=True)
def setup_erp():
    erp_db.reset()


def test_list_and_read_files():
    list_tool = ListFilesTool()
    res = list_tool.run(directory="simulated_company/data_store/files/invoices", pattern="*.txt")
    assert res["status"] == "success"
    assert res["count"] >= 3

    read_tool = ReadFileTool()
    read_res = read_tool.run(file_path="simulated_company/data_store/files/invoices/INV-2024-089_CompanyX_Latest.txt")
    assert read_res["status"] == "success"
    assert "INV-2024-089" in read_res["content"]
    assert "14,850.00" in read_res["content"]


def test_search_files():
    search_tool = SearchFilesTool()
    res = search_tool.run(query="Company X", directory="simulated_company/data_store/files/invoices")
    assert res["status"] == "success"
    assert res["total_matches"] >= 2


def test_erp_tools_and_verification():
    erp_db.reset()
    vendors_tool = ERPGetVendorsTool()
    v_res = vendors_tool.run()
    assert v_res["status"] == "success"
    assert len(v_res["vendors"]) >= 1

    submit_tool = ERPSubmitInvoiceTool()
    sub_res = submit_tool.run(
        vendor_name="Company X Enterprise Solutions",
        invoice_number="INV-TEST-999",
        amount=1200.50,
        due_date="2024-12-31",
        po_number="PO-TEST"
    )
    assert sub_res["status"] == "success"
    assert sub_res["record"]["invoice_number"] == "INV-TEST-999"

    # Test verification
    verify_tool = ERPVerifyRecordTool()
    v_check = verify_tool.run(
        invoice_number="INV-TEST-999",
        expected_amount=1200.50,
        expected_due_date="2024-12-31"
    )
    assert v_check["verified"] is True
    assert "INVREC-" in v_check["record_id"]


def test_browser_tools():
    erp_db.reset()
    nav_tool = BrowserNavigateTool()
    nav_res = nav_tool.run(url="http://internal.centra/portal/invoices")
    assert nav_res["status"] == "success"
    assert len(nav_res["forms_detected"]) >= 1

    fill_tool = BrowserFillFormTool()
    fill_res = fill_tool.run(
        form_id="invoice-form",
        form_data={
            "vendor_name": "Company X Enterprise Solutions",
            "invoice_number": "INV-BROWSER-001",
            "amount": 3500.0,
            "due_date": "2024-11-15",
            "po_number": "PO-BRW-1"
        }
    )
    assert fill_res["status"] == "success"
    assert "INV-BROWSER-001" in fill_res["message"]
