import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import PayableRecord
from backend.app.tools.payable_tools import VerifyPayableTool, CreatePayableTool
from backend.app.verification.verifier import IndependentVerificationCritic


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_independent_verification_success():
    """
    Test that ground truth verification succeeds when all attributes match.
    """
    db = SessionLocal()
    try:
        # Create a payable
        create_tool = CreatePayableTool()
        create_res = create_tool.execute(
            db,
            vendor_name="Acme Technologies Inc.",
            invoice_number="INV-VERIF-100",
            amount=5000.00,
            due_date="2024-11-30"
        )
        assert create_res.success is True

        # Independent Critic
        critic = IndependentVerificationCritic()
        result = critic.verify(
            db_session=db,
            invoice_number="INV-VERIF-100",
            expected_amount=5000.00,
            expected_due_date="2024-11-30",
            expected_vendor="Acme Technologies Inc."
        )

        assert result["verified"] is True
        assert result["checks"]["amount"]["match"] is True
        assert result["checks"]["due_date"]["match"] is True
        assert result["checks"]["vendor"]["match"] is True
    finally:
        db.close()


def test_independent_verification_mismatch_detection():
    """
    Test that verification critic catches discrepancies (e.g. amount mismatch).
    Must not falsely declare task success.
    """
    db = SessionLocal()
    try:
        create_tool = CreatePayableTool()
        create_tool.execute(
            db,
            vendor_name="Acme Technologies Inc.",
            invoice_number="INV-VERIF-200",
            amount=5000.00,
            due_date="2024-11-30"
        )

        critic = IndependentVerificationCritic()
        # Verify with wrong amount ($9,999.00 instead of $5,000.00)
        result = critic.verify(
            db_session=db,
            invoice_number="INV-VERIF-200",
            expected_amount=9999.00,
            expected_due_date="2024-11-30"
        )

        assert result["verified"] is False
        assert result["checks"]["amount"]["match"] is False
    finally:
        db.close()
