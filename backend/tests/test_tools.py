import os
import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.tools.registry import default_tool_registry


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_list_and_read_invoice_tools():
    db = SessionLocal()
    try:
        list_res = default_tool_registry.execute("list_invoice_files", db, {"directory": "sandbox_data/invoices"})
        assert list_res.success is True
        assert list_res.data["count"] >= 4

        # Test reading text invoice
        read_txt = default_tool_registry.execute(
            "read_invoice", db, {"file_path": "sandbox_data/invoices/INV-2024-001_AcmeTechnologies_Latest.txt"}
        )
        assert read_txt.success is True
        assert "INV-2026-001" in read_txt.data["text"] or "INV-2024-001" in read_txt.data["text"]

        # Test reading real PDF invoice!
        pdf_path = "sandbox_data/invoices/INV-2024-001_AcmeTechnologies_Latest.pdf"
        if os.path.exists(pdf_path):
            read_pdf = default_tool_registry.execute("read_invoice", db, {"file_path": pdf_path})
            assert read_pdf.success is True
            assert "INV-2026-001" in read_pdf.data["text"] or "INV-2024-001" in read_pdf.data["text"]
    finally:
        db.close()


def test_extract_invoice_fields_tool():
    db = SessionLocal()
    try:
        sample_text = (
            "Invoice Number: INV-9901\n"
            "Vendor: Acme Technologies Inc.\n"
            "Due Date: 2024-12-15\n"
            "Invoice Date: 2024-11-15\n"
            "Total Amount: $12,500.00 USD\n"
            "Payment Terms: Net 30\n"
            "PO: PO-9901\n"
        )
        res = default_tool_registry.execute("extract_invoice_fields", db, {"document_text": sample_text})
        assert res.success is True
        fields = res.data["extracted_fields"]
        assert fields["invoice_number"] == "INV-9901"
        assert fields["amount"] == 12500.00
        assert fields["due_date"] == "2024-12-15"
        assert fields["currency"] == "USD"
    finally:
        db.close()


def test_payable_lifecycle_tools():
    db = SessionLocal()
    try:
        # Create
        c_res = default_tool_registry.execute(
            "create_payable",
            db,
            {
                "vendor_name": "Acme Technologies Inc.",
                "invoice_number": "INV-LIFECYCLE-01",
                "amount": 4500.00,
                "due_date": "2024-12-31"
            }
        )
        assert c_res.success is True
        p_id = c_res.data["payable_id"]

        # Get
        g_res = default_tool_registry.execute("get_payable", db, {"payable_id": p_id})
        assert g_res.success is True
        assert g_res.data["invoice_number"] == "INV-LIFECYCLE-01"

        # Verify
        v_res = default_tool_registry.execute(
            "verify_payable",
            db,
            {
                "invoice_number": "INV-LIFECYCLE-01",
                "expected_amount": 4500.00,
                "expected_due_date": "2024-12-31",
                "expected_vendor": "Acme Technologies Inc."
            }
        )
        assert v_res.success is True
        assert v_res.data["verified"] is True
    finally:
        db.close()
