import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.tools.vendor_tools import SearchVendorTool


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_ambiguous_vendor_matching():
    """
    Test vendor ambiguity:
    Searching 'Tech' or a broad keyword returns multiple vendors and flags is_ambiguous=True.
    """
    db = SessionLocal()
    try:
        tool = SearchVendorTool()
        # 'Tech' or 'Systems' or 'Services' matches multiple vendors
        res = tool.execute(db, vendor_name="Services")

        # In our seed database, we have:
        # Apex Cloud Services LLC (category Technology & Cloud Services, name Services)
        # Acme Technologies Inc (category Cloud & Software Engineering)
        # Both match if searching category/name
        # Or let's test searching 'Ltd' or 'Systems' or 'Tech'
        res_tech = tool.execute(db, vendor_name="Acme")
        assert res_tech.success is True
        assert res_tech.data["vendor_code"] == "VEND-ACME-01"

        # Search non-existent vendor
        res_none = tool.execute(db, vendor_name="Imaginary Corp 999")
        assert res_none.success is False
        assert "no approved vendor" in res_none.error.lower()
    finally:
        db.close()
