import pytest
from centra_worker.engine.verifier import OutcomeVerifier
from simulated_company.erp_server import erp_db, InvoiceSubmission


@pytest.fixture(autouse=True)
def setup_erp():
    erp_db.reset()


def test_outcome_verification_success():
    # Insert ground truth record
    sub = InvoiceSubmission(
        vendor_name="Company X Enterprise Solutions",
        invoice_number="INV-VERIFY-001",
        amount=5400.0,
        due_date="2024-11-30"
    )
    erp_db.add_invoice(sub)

    verifier = OutcomeVerifier()
    receipt = verifier.verify_invoice_completion(
        invoice_number="INV-VERIFY-001",
        expected_amount=5400.0,
        expected_due_date="2024-11-30",
        vendor_name="Company X Enterprise Solutions"
    )

    assert receipt.verified is True
    assert receipt.invoice_number == "INV-VERIFY-001"
    assert receipt.amount == 5400.0
    assert "VERIFIED-" in receipt.verification_hash


def test_outcome_verification_failure_on_amount_mismatch():
    sub = InvoiceSubmission(
        vendor_name="Company X Enterprise Solutions",
        invoice_number="INV-VERIFY-002",
        amount=5400.0,
        due_date="2024-11-30"
    )
    erp_db.add_invoice(sub)

    verifier = OutcomeVerifier()
    receipt = verifier.verify_invoice_completion(
        invoice_number="INV-VERIFY-002",
        expected_amount=9999.0,  # Wrong amount
        expected_due_date="2024-11-30"
    )

    assert receipt.verified is False
    assert "mismatch" in receipt.audit_notes.lower()
