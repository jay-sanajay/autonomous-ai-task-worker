import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import ContractRecord, VerificationResult, AgentTask
from backend.app.agent.loop import AgentExecutionEngine
from backend.app.tools.contract_tools import InspectDocumentTool, ExtractContractDetailsTool, VerifyContractTool


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_universal_document_inspection_tool():
    """Test universal document inspection across multiple file types (PDF, CSV, TXT)."""
    db = SessionLocal()
    try:
        insp = InspectDocumentTool()

        # 1. Test TXT Inspection
        res_txt = insp.execute(db, "sandbox_data/contracts/Master_Services_Agreement_CentrAlign_Acme.txt")
        assert res_txt.success is True
        assert res_txt.data["document_type"] == "contract"
        assert res_txt.data["extension"] == "txt"
        assert res_txt.data["line_count"] > 10

        # 2. Test PDF Inspection
        res_pdf = insp.execute(db, "sandbox_data/contracts/Master_Services_Agreement_CentrAlign_Acme.pdf")
        assert res_pdf.success is True
        assert res_pdf.data["document_type"] == "contract"
        assert res_pdf.data["extension"] == "pdf"
        assert res_pdf.data["page_count"] >= 1

        # 3. Test CSV Dataset Inspection
        res_csv = insp.execute(db, "sandbox_data/csv/sales_data_q3.csv")
        assert res_csv.success is True
        assert res_csv.data["document_type"] == "tabular_dataset"
        assert "row_count" in res_csv.data["metadata"]
        assert res_csv.data["metadata"]["row_count"] > 0
    finally:
        db.close()


def test_extract_contract_details_tool():
    """Test extraction of contract parameters and missing clause audits."""
    db = SessionLocal()
    try:
        ext_tool = ExtractContractDetailsTool()

        # 1. Audit Master Services Agreement
        res_msa = ext_tool.execute(db, "sandbox_data/contracts/Master_Services_Agreement_CentrAlign_Acme.txt")
        assert res_msa.success is True
        assert res_msa.data["contract_code"] == "CTR-2024-MSA-088"
        assert "January 14, 2025" in res_msa.data["expiry_date"]
        assert res_msa.data["contract_value"] == 120000.0
        assert res_msa.data["missing_clauses_count"] >= 2
        assert any(c["clause"] == "Limitation of Liability" for c in res_msa.data["missing_clauses"])
        assert any(c["clause"] == "Force Majeure" for c in res_msa.data["missing_clauses"])

        # 2. Audit Vendor SLA Agreement
        res_sla = ext_tool.execute(db, "sandbox_data/contracts/Vendor_SLA_Agreement_Incomplete.txt")
        assert res_sla.success is True
        assert res_sla.data["contract_code"] == "SLA-2024-NEXUS-014"
        assert "February 28, 2026" in res_sla.data["expiry_date"]
        assert res_sla.data["contract_value"] == 48500.0
        assert "New York" in res_sla.data["governing_law"]
    finally:
        db.close()


def test_verify_contract_tool():
    """Test ground-truth verification against SQLite database records."""
    db = SessionLocal()
    try:
        ext_tool = ExtractContractDetailsTool()
        ext_res = ext_tool.execute(db, "sandbox_data/contracts/Master_Services_Agreement_CentrAlign_Acme.txt")
        assert ext_res.success is True

        ver_tool = VerifyContractTool()
        v_res = ver_tool.execute(db, contract_code="CTR-2024-MSA-088", expected_expiry_date="January 14, 2025")
        assert v_res.success is True
        assert v_res.data["verified"] is True
        assert "VERIFIED-CONTRACT-CTR-2024-MSA-088-" in v_res.data["verification_token"]

        # Assert database record was updated to VERIFIED
        rec = db.query(ContractRecord).filter(ContractRecord.contract_code == "CTR-2024-MSA-088").first()
        assert rec is not None
        assert rec.status == "VERIFIED"
    finally:
        db.close()


def test_contract_agent_workflow_end_to_end():
    """
    Test end-to-end execution of the Master Prompt contract workflow:
    'Read a contract, extract its expiry date, and flag missing information.'
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Read a contract, extract its expiry date, and flag missing information."

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        assert task.steps_count >= 4

        # Verify contract record in SQLite database
        contract = db.query(ContractRecord).order_by(ContractRecord.id.desc()).first()
        assert contract is not None
        assert "January 14, 2025" in contract.expiry_date
        assert contract.status == "VERIFIED"
        assert contract.risk_score in ("HIGH", "CRITICAL")

        # Verify independent ground-truth verification result
        v_res = db.query(VerificationResult).filter(VerificationResult.task_id == task.id).first()
        assert v_res is not None
        assert v_res.verified is True
        assert v_res.contract_id == contract.id
        assert "VERIFIED-CONTRACT-" in v_res.verification_token

        # Verify final summary
        assert task.final_summary is not None
        assert "January 14, 2025" in task.final_summary
        assert "Limitation of Liability" in task.final_summary
        assert v_res.verification_token in task.final_summary
    finally:
        db.close()


def test_contract_sla_workflow_explicit_file():
    """Test autonomous contract audit targeting specific SLA document."""
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Read the contract at sandbox_data/contracts/Vendor_SLA_Agreement_Incomplete.txt, extract its expiry date, and flag missing information."

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        assert "February 28, 2026" in task.final_summary
        assert "SLA-2024-NEXUS-014" in task.final_summary

        contract = db.query(ContractRecord).filter(ContractRecord.contract_code == "SLA-2024-NEXUS-014").first()
        assert contract is not None
        assert contract.expiry_date == "February 28, 2026"
    finally:
        db.close()
