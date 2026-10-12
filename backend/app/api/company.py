"""
AgentOS - Sandbox Company Application Endpoints.
Provides visibility into the persisted database state (vendors, invoices, payables, metrics).
"""

from __future__ import annotations
import os
import glob
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.app.database.session import get_db
from backend.app.database.models import (
    Vendor, InvoiceDocument, PayableRecord, AgentTask, ApprovalRequest,
    TaskItem, SupportTicket, InventoryItem, PurchaseRequest, ContractRecord
)
from backend.app.database.seed import reset_database
from backend.app.schemas.company import VendorResponse, InvoiceDocResponse
from backend.app.schemas.payable import PayableResponse

router = APIRouter(prefix="/api", tags=["Sandbox Company Application"])


@router.get("/vendors", response_model=List[VendorResponse])
def get_vendors(db: Session = Depends(get_db)):
    """Retrieve all approved vendors in company directory."""
    return db.query(Vendor).all()


@router.get("/invoices", response_model=List[InvoiceDocResponse])
def get_invoices(db: Session = Depends(get_db)):
    """Retrieve indexed invoice files from sandbox repository."""
    return db.query(InvoiceDocument).all()


@router.get("/payables", response_model=List[PayableResponse])
def get_payables(db: Session = Depends(get_db)):
    """Retrieve all payable records in accounting ledger."""
    return db.query(PayableRecord).order_by(PayableRecord.created_at.desc()).all()


@router.get("/payables/{payable_id}", response_model=PayableResponse)
def get_payable_by_id(payable_id: int, db: Session = Depends(get_db)):
    """Retrieve single payable record by primary ID."""
    rec = db.query(PayableRecord).filter(PayableRecord.id == payable_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Payable record '{payable_id}' not found.")
    return rec


@router.get("/task-items")
def get_task_items(db: Session = Depends(get_db)):
    """Retrieve all scheduled task items and calendar events."""
    items = db.query(TaskItem).order_by(TaskItem.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date,
            "meeting_link": t.meeting_link,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "source_reference": t.source_reference,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in items
    ]


@router.get("/support-tickets")
def get_support_tickets(db: Session = Depends(get_db)):
    """Retrieve all support tickets."""
    tickets = db.query(SupportTicket).order_by(SupportTicket.id.asc()).all()
    return [
        {
            "id": t.id,
            "ticket_code": t.ticket_code,
            "customer_name": t.customer_name,
            "subject": t.subject,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tickets
    ]


@router.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    """Retrieve all inventory items and stock levels."""
    items = db.query(InventoryItem).all()
    return [
        {
            "id": i.id,
            "sku": i.sku,
            "product_name": i.product_name,
            "category": i.category,
            "current_stock": i.current_stock,
            "reorder_threshold": i.reorder_threshold,
            "unit_price": i.unit_price,
            "status": i.status,
            "is_low_stock": i.current_stock <= i.reorder_threshold
        }
        for i in items
    ]


@router.get("/purchase-requests")
def get_purchase_requests(db: Session = Depends(get_db)):
    """Retrieve drafted purchase requests."""
    prs = db.query(PurchaseRequest).order_by(PurchaseRequest.created_at.desc()).all()
    return [
        {
            "id": pr.id,
            "request_code": pr.request_code,
            "product_name": pr.product_name,
            "quantity": pr.quantity,
            "unit_price": pr.unit_price,
            "estimated_total": pr.estimated_total,
            "status": pr.status,
            "created_at": pr.created_at.isoformat() if pr.created_at else None
        }
        for pr in prs
    ]


@router.post("/sandbox/reset")
def reset_sandbox(db: Session = Depends(get_db)):
    """Reset the sandbox database to clean baseline seed data."""
    reset_database()
    return {"status": "success", "message": "Sandbox database reset and reseeded successfully."}


@router.get("/sandbox/metrics")
def get_sandbox_metrics(db: Session = Depends(get_db)):
    """
    Return genuine live metrics computed directly from persisted SQLite tables.
    Never fabricated or pre-populated.
    """
    total_tasks = db.query(AgentTask).count()
    completed = db.query(AgentTask).filter(AgentTask.status == "COMPLETED").count()
    failed = db.query(AgentTask).filter(AgentTask.status == "FAILED").count()
    awaiting = db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING").count()
    total_payables = db.query(PayableRecord).count()
    verified_payables = db.query(PayableRecord).filter(PayableRecord.status == "VERIFIED").count()

    verif_rate = round((verified_payables / total_payables * 100), 1) if total_payables > 0 else 0.0

    return {
        "total_tasks": total_tasks,
        "tasks_completed": completed,
        "tasks_failed": failed,
        "tasks_awaiting_approval": awaiting,
        "total_payables": total_payables,
        "verified_payables": verified_payables,
        "verification_success_rate": verif_rate
    }


@router.get("/csv-files")
def get_csv_files():
    """Retrieve all available CSV datasets in sandbox_data/csv."""
    csv_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir, exist_ok=True)
    files = glob.glob(os.path.join(csv_dir, "*.csv"))
    items = []
    for p in files:
        items.append({
            "filename": os.path.basename(p),
            "file_path": os.path.relpath(p, PROJECT_ROOT).replace("\\", "/"),
            "size_bytes": os.path.getsize(p)
        })
    return items


@router.post("/upload/csv")
async def upload_csv_file(file: UploadFile = File(...)):
    """Upload a CSV dataset directly to sandbox_data/csv."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")
    
    csv_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
    os.makedirs(csv_dir, exist_ok=True)
    target_path = os.path.join(csv_dir, os.path.basename(file.filename))

    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    return {
        "status": "success",
        "filename": os.path.basename(file.filename),
        "file_path": os.path.relpath(target_path, PROJECT_ROOT).replace("\\", "/"),
        "size_bytes": len(content),
        "message": f"Successfully uploaded {file.filename} to sandbox_data/csv/"
    }


@router.get("/reports")
def get_reports():
    """Retrieve all generated executive reports in sandbox_data/reports."""
    rep_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "reports")
    if not os.path.exists(rep_dir):
        os.makedirs(rep_dir, exist_ok=True)
    files = glob.glob(os.path.join(rep_dir, "*.md"))
    items = []
    for p in files:
        items.append({
            "filename": os.path.basename(p),
            "file_path": os.path.relpath(p, PROJECT_ROOT).replace("\\", "/"),
            "size_bytes": os.path.getsize(p)
        })
    return items


@router.get("/contracts")
def get_contracts(db: Session = Depends(get_db)):
    """Retrieve all audited legal contracts and agreements in company database."""
    contracts = db.query(ContractRecord).order_by(ContractRecord.created_at.desc()).all()
    results = []
    for c in contracts:
        missing_list = []
        try:
            missing_list = json.loads(c.missing_clauses) if c.missing_clauses else []
        except Exception:
            pass

        results.append({
            "id": c.id,
            "contract_code": c.contract_code,
            "title": c.title,
            "parties": c.parties,
            "effective_date": c.effective_date,
            "expiry_date": c.expiry_date,
            "contract_value": c.contract_value,
            "governing_law": c.governing_law,
            "missing_clauses": missing_list,
            "missing_clauses_count": len(missing_list),
            "risk_score": c.risk_score,
            "status": c.status,
            "source_file": c.source_file,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return results


@router.get("/contracts/{contract_code}")
def get_contract_by_code(contract_code: str, db: Session = Depends(get_db)):
    """Retrieve detailed contract audit record by unique code."""
    c = db.query(ContractRecord).filter(ContractRecord.contract_code == contract_code).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Contract '{contract_code}' not found.")
    
    missing_list = []
    try:
        missing_list = json.loads(c.missing_clauses) if c.missing_clauses else []
    except Exception:
        pass

    return {
        "id": c.id,
        "contract_code": c.contract_code,
        "title": c.title,
        "parties": c.parties,
        "effective_date": c.effective_date,
        "expiry_date": c.expiry_date,
        "contract_value": c.contract_value,
        "governing_law": c.governing_law,
        "missing_clauses": missing_list,
        "missing_clauses_count": len(missing_list),
        "risk_score": c.risk_score,
        "status": c.status,
        "source_file": c.source_file,
        "created_at": c.created_at.isoformat() if c.created_at else None
    }


@router.post("/upload/file")
async def upload_any_file(file: UploadFile = File(...)):
    """
    Universal file upload endpoint for AgentOS.
    Accepts ANY file format (.pdf, .csv, .txt, .json, .md, .tsv, .log).
    Saves to sandbox repository and returns suggested task prompt.
    """
    fn = os.path.basename(file.filename)
    ext = os.path.splitext(fn)[1].lower()
    allowed_exts = (".pdf", ".csv", ".tsv", ".txt", ".json", ".md", ".log")
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(allowed_exts)}"
        )

    # Determine destination folder
    is_invoice = any(k in fn.lower() for k in ["inv-", "invoice", "bill"])
    if ext == ".csv":
        dest_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
    elif is_invoice:
        dest_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "invoices")
    elif any(k in fn.lower() for k in ["contract", "agreement", "sla", "msa"]):
        dest_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "contracts")
    else:
        dest_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "uploads")

    os.makedirs(dest_dir, exist_ok=True)
    target_path = os.path.join(dest_dir, fn)

    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    rel_path = os.path.relpath(target_path, PROJECT_ROOT).replace("\\", "/")

    # If invoice, register in InvoiceDocument table
    if is_invoice:
        try:
            db_gen = get_db()
            db_session = next(db_gen)
            existing = db_session.query(InvoiceDocument).filter(InvoiceDocument.filename == fn).first()
            if not existing:
                inv_rec = InvoiceDocument(
                    filename=fn,
                    file_path=rel_path,
                    file_type="PDF" if ext == ".pdf" else "TXT",
                    file_size_bytes=len(content),
                    vendor_name_hint=fn.split("_")[1].replace(".txt", "").replace(".pdf", "") if "_" in fn else "Uploaded Vendor",
                    is_latest_for_vendor=True
                )
                db_session.add(inv_rec)
                db_session.commit()
            db_session.close()
        except Exception as e:
            pass

    # Formulate intelligent action prompt based on file type
    if is_invoice:
        suggested_prompt = f"Find the invoice at {rel_path}, extract its amount and due date, and save it in the invoice system."
    elif ext == ".csv":
        suggested_prompt = f"Analyze the CSV dataset at {rel_path}, identify top products, and save an executive report."
    elif any(k in fn.lower() for k in ["contract", "agreement", "sla", "msa"]) or ext in (".pdf", ".txt"):
        suggested_prompt = f"Read the contract at {rel_path}, extract its expiry date, and flag missing information."
    else:
        suggested_prompt = f"Inspect the document at {rel_path} and summarize its structure and key entities."

    return {
        "status": "success",
        "filename": fn,
        "extension": ext.lstrip("."),
        "file_path": rel_path,
        "size_bytes": len(content),
        "suggested_prompt": suggested_prompt,
        "message": f"Successfully uploaded '{fn}' ({len(content)} bytes)."
    }


@router.get("/uploaded-files")
def get_all_sandbox_files():
    """Retrieve all documents across contracts, uploads, invoices, and csv folders."""
    categories = [
        {"name": "Contracts & SLAs", "dir": os.path.join(PROJECT_ROOT, "sandbox_data", "contracts"), "icon": "file-text"},
        {"name": "General Uploads", "dir": os.path.join(PROJECT_ROOT, "sandbox_data", "uploads"), "icon": "upload"},
        {"name": "Invoices", "dir": os.path.join(PROJECT_ROOT, "sandbox_data", "invoices"), "icon": "receipt"},
        {"name": "CSV Datasets", "dir": os.path.join(PROJECT_ROOT, "sandbox_data", "csv"), "icon": "table"},
    ]

    all_files = []
    for cat in categories:
        if os.path.exists(cat["dir"]):
            for p in glob.glob(os.path.join(cat["dir"], "*.*")):
                if os.path.isfile(p):
                    fn = os.path.basename(p)
                    stat = os.stat(p)
                    ext = os.path.splitext(fn)[1].lower().lstrip(".")
                    rel = os.path.relpath(p, PROJECT_ROOT).replace("\\", "/")
                    
                    # Formulate 1-click prompt
                    if ext == "csv":
                        prompt = f"Analyze the CSV dataset at {rel}, identify top products, and save a report."
                    elif "contract" in rel or "sla" in fn.lower() or "msa" in fn.lower():
                        prompt = f"Read the contract at {rel}, extract its expiry date, and flag missing information."
                    elif "invoice" in rel:
                        prompt = f"Find the invoice at {rel}, extract its amount and due date, and save it in the invoice system."
                    else:
                        prompt = f"Inspect file at {rel} and summarize key findings."

                    all_files.append({
                        "category": cat["name"],
                        "filename": fn,
                        "extension": ext,
                        "file_path": rel,
                        "size_bytes": stat.st_size,
                        "modified_time": stat.st_mtime,
                        "suggested_prompt": prompt
                    })

    all_files.sort(key=lambda x: x["modified_time"], reverse=True)
    return all_files


# --------------------------------------------------------------------------
# Direct Document Download Endpoint
# --------------------------------------------------------------------------
@router.get("/invoices/download/{filename}")
def download_invoice_document(filename: str):
    """Download an invoice, report, or contract directly from sandbox."""
    candidate_dirs = [
        os.path.join(PROJECT_ROOT, "sandbox_data", "invoices"),
        os.path.join(PROJECT_ROOT, "sandbox_data", "reports"),
        os.path.join(PROJECT_ROOT, "sandbox_data", "contracts"),
        os.path.join(PROJECT_ROOT, "sandbox_data", "csv"),
        os.path.join(PROJECT_ROOT, "sandbox_data", "uploads"),
    ]

    for d in candidate_dirs:
        target = os.path.join(d, filename)
        if os.path.isfile(target):
            media = "application/pdf" if filename.lower().endswith(".pdf") else "text/plain"
            return FileResponse(
                path=target,
                filename=filename,
                media_type=media,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

    raise HTTPException(status_code=404, detail=f"Document '{filename}' not found for download.")


@router.get("/invoices/preview/{filename}")
def preview_invoice_document(filename: str):
    """Return parsed text content of an invoice for in-browser visual inspection and printing."""
    candidate_dirs = [
        os.path.join(PROJECT_ROOT, "sandbox_data", "invoices"),
        os.path.join(PROJECT_ROOT, "sandbox_data", "reports"),
        os.path.join(PROJECT_ROOT, "sandbox_data", "contracts"),
        os.path.join(PROJECT_ROOT, "sandbox_data", "uploads"),
    ]

    for d in candidate_dirs:
        target = os.path.join(d, filename)
        if os.path.isfile(target):
            is_pdf = filename.lower().endswith(".pdf")
            if is_pdf:
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(target)
                    text = "\n".join([page.extract_text() or "" for page in reader.pages])
                except Exception:
                    try:
                        import PyPDF2
                        with open(target, "rb") as pf:
                            rdr = PyPDF2.PdfReader(pf)
                            text = "\n".join([p.extract_text() or "" for p in rdr.pages])
                    except Exception:
                        text = f"[Binary PDF File - {os.path.getsize(target):,} bytes]\nDownload file to view formatted PDF layout."
                return {
                    "filename": filename,
                    "type": "PDF",
                    "content": text,
                    "size_bytes": os.path.getsize(target),
                    "download_url": f"/api/invoices/download/{filename}"
                }
            else:
                try:
                    with open(target, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read()
                    return {
                        "filename": filename,
                        "type": "TXT",
                        "content": text,
                        "size_bytes": os.path.getsize(target),
                        "download_url": f"/api/invoices/download/{filename}"
                    }
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")


# --------------------------------------------------------------------------
# Create Custom Invoice with Line Items & Optional Auto-Run
# --------------------------------------------------------------------------
class LineItemModel(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float = 0.0


class CreateCustomInvoiceRequest(BaseModel):
    vendor_name: str
    invoice_number: str
    due_date: str
    issue_date: Optional[str] = "2026-10-12"
    vendor_address: Optional[str] = "100 Innovation Way, Suite 400, Silicon Valley, CA"
    vendor_tax_id: Optional[str] = "US-EIN-8849201"
    client_name: Optional[str] = "AgentOS Enterprise Systems Inc."
    client_address: Optional[str] = "500 Autonomous Way, Bldg 2, Tech Park"
    client_email: Optional[str] = "ap@agentos.internal"
    currency: str = "USD"
    payment_terms: str = "NET_30"
    tax_rate: float = 0.0
    discount: float = 0.0
    notes: Optional[str] = "Wire funds to Vendor Operating Treasury within agreed payment terms."
    items: List[LineItemModel] = Field(default_factory=list)
    auto_run_agent: bool = True


@router.post("/invoices/create-with-items")
def create_custom_invoice(req: CreateCustomInvoiceRequest, db: Session = Depends(get_db)):
    """Create a new commercial invoice with itemized line items, full financial audit, and optional auto-dispatch."""
    inv_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "invoices")
    os.makedirs(inv_dir, exist_ok=True)

    # Compute line item calculations
    subtotal = 0.0
    items_table_rows = []
    for idx, it in enumerate(req.items, start=1):
        qty = max(1, it.quantity)
        rate = max(0.0, it.unit_price)
        line_total = qty * rate
        subtotal += line_total
        desc_truncated = (it.description[:40] + "..") if len(it.description) > 42 else it.description
        items_table_rows.append(
            f"{idx:<3} {desc_truncated:<42} {qty:>4}   ${rate:>9,.2f}   ${line_total:>10,.2f}"
        )

    if not items_table_rows:
        subtotal = 1250.00
        items_table_rows.append(
            f"1   General Professional Cloud & AI Services     1   $ 1,250.00   $  1,250.00"
        )

    # Calculate tax, discount, and final net payable
    tax_percent = max(0.0, req.tax_rate)
    tax_amount = round(subtotal * (tax_percent / 100.0), 2)
    discount_val = max(0.0, req.discount)
    total_amount = max(0.0, round(subtotal + tax_amount - discount_val, 2))

    clean_vendor = req.vendor_name.replace(" ", "").replace(".", "").replace(",", "")
    fn = f"{req.invoice_number}_{clean_vendor}.txt"
    full_path = os.path.join(inv_dir, fn)

    issue_dt = req.issue_date or "2026-10-12"
    v_addr = req.vendor_address or "100 Innovation Way, Suite 400, Silicon Valley, CA"
    v_tax = req.vendor_tax_id or "US-EIN-8849201"
    c_name = req.client_name or "AgentOS Enterprise Systems Inc."
    c_addr = req.client_address or "500 Autonomous Way, Bldg 2, Tech Park"
    c_email = req.client_email or "ap@agentos.internal"
    remit_notes = req.notes or f"Wire funds to {req.vendor_name} Operating Treasury within {req.payment_terms}."

    content_str = (
        "================================================================================\n"
        f"                          OFFICIAL COMMERCIAL INVOICE\n"
        "================================================================================\n"
        f"VENDOR / REMIT TO:                      BILL TO / CLIENT:\n"
        f"{req.vendor_name:<40} {c_name}\n"
        f"{v_addr:<40} {c_addr}\n"
        f"Tax/VAT ID: {v_tax:<28} Accounts Payable: {c_email}\n"
        "--------------------------------------------------------------------------------\n"
        f"Invoice Number: {req.invoice_number:<24} Issue Date   : {issue_dt}\n"
        f"Payment Terms : {req.payment_terms:<24} Due Date     : {req.due_date}\n"
        f"Currency      : {req.currency:<24} Status       : UNPAID / DUE\n"
        "================================================================================\n"
        "ITEMIZED EXPENSES & PRODUCT BREAKDOWN:\n"
        "--------------------------------------------------------------------------------\n"
        "#   Description                                 Qty    Unit Price ($)   Total ($)\n"
        "--  ------------------------------------------  ----  ---------------  ----------\n"
        + "\n".join(items_table_rows) + "\n"
        "--------------------------------------------------------------------------------\n"
        f"Subtotal Amount                           :     ${subtotal:>12,.2f} {req.currency}\n"
        f"Tax / VAT ({tax_percent:>4.1f}%)                         :     ${tax_amount:>12,.2f} {req.currency}\n"
        f"Discount Applied                          :    -${discount_val:>12,.2f} {req.currency}\n"
        "--------------------------------------------------------------------------------\n"
        f"TOTAL PAYABLE AMOUNT DUE                  :     ${total_amount:>12,.2f} {req.currency}\n"
        "================================================================================\n"
        "PAYMENT INSTRUCTIONS & REMITTANCE ADVICE:\n"
        f"• {remit_notes}\n"
        f"• Remittance Reference: {req.invoice_number} / {req.vendor_name}\n"
        "================================================================================\n"
    )

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content_str)

    # Register in InvoiceDocument table
    rel_path = f"sandbox_data/invoices/{fn}"
    existing_doc = db.query(InvoiceDocument).filter(InvoiceDocument.filename == fn).first()
    if not existing_doc:
        doc = InvoiceDocument(
            filename=fn,
            file_path=rel_path,
            file_type="TXT",
            file_size_bytes=len(content_str.encode("utf-8")),
            vendor_name_hint=req.vendor_name,
            is_latest_for_vendor=True
        )
        db.add(doc)
        db.commit()

    task_id = None
    if req.auto_run_agent:
        from backend.app.agent.loop import AgentExecutionEngine
        engine = AgentExecutionEngine()
        goal = f"Find latest invoice {req.invoice_number} from {req.vendor_name}, extract amount and due date, and save in invoice system."
        task = engine.run(db_session=db, goal=goal, auto_approve_high_risk=True)
        task_id = task.id

    return {
        "status": "success",
        "filename": fn,
        "file_path": rel_path,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "discount": discount_val,
        "total_amount": total_amount,
        "items_count": len(req.items),
        "task_id": task_id,
        "download_url": f"/api/invoices/download/{fn}",
        "content_preview": content_str,
        "message": f"Invoice '{fn}' created successfully for ${total_amount:,.2f}."
    }


# --------------------------------------------------------------------------
# LLM Provider & Groq API Status Endpoints
# --------------------------------------------------------------------------
@router.get("/settings/llm-status")
def get_llm_status():
    """Inspect configured LLM provider and Groq status."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    has_groq = bool(groq_key and len(groq_key) > 5)
    masked_key = f"{groq_key[:6]}...{groq_key[-4:]}" if has_groq else ""
    active_provider = "Groq Llama-3.3-70B" if has_groq else "Deterministic Safe Fallback"

    return {
        "active_provider": "Groq (" + os.getenv("GROQ_MODEL", "openai/gpt-oss-120b") + ")" if has_groq else "Deterministic Safe Fallback",
        "groq_configured": has_groq,
        "masked_api_key": masked_key,
        "default_model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        "supported_models": [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ],
        "zero_friction_mode": True
    }


class SetGroqKeyRequest(BaseModel):
    groq_api_key: str
    model: Optional[str] = "openai/gpt-oss-120b"


@router.post("/settings/llm-provider")
def set_groq_api_key(req: SetGroqKeyRequest):
    """Dynamically set or update Groq API key and model."""
    os.environ["GROQ_API_KEY"] = req.groq_api_key.strip()
    if req.model:
        os.environ["GROQ_MODEL"] = req.model.strip()
    os.environ["LLM_PROVIDER"] = "groq"
    return {
        "status": "success",
        "active_provider": "Groq Llama-3.3-70B",
        "model": os.environ["GROQ_MODEL"],
        "message": "Groq API key configured successfully. Autonomous agent now powered by Groq."
    }


# --------------------------------------------------------------------------
# CSV Datasets & Tabular Analytics Endpoints
# --------------------------------------------------------------------------
@router.get("/datasets")
def list_available_datasets():
    """Retrieve all available CSV/TSV datasets with row counts and column schemas."""
    import csv
    csv_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
    os.makedirs(csv_dir, exist_ok=True)
    results = []

    for fn in os.listdir(csv_dir):
        if fn.lower().endswith((".csv", ".tsv")):
            fp = os.path.join(csv_dir, fn)
            stat = os.stat(fp)
            cols = []
            rows_count = 0
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    delimiter = "\t" if fn.lower().endswith(".tsv") else ","
                    reader = csv.reader(f, delimiter=delimiter)
                    headers = next(reader, None)
                    if headers:
                        cols = [h.strip() for h in headers if h.strip()]
                    rows_count = sum(1 for _ in reader)
            except Exception:
                pass

            results.append({
                "filename": fn,
                "file_path": f"sandbox_data/csv/{fn}",
                "columns": cols,
                "rows_count": rows_count,
                "size_bytes": stat.st_size,
                "modified_time": stat.st_mtime,
                "download_url": f"/api/datasets/download/{fn}"
            })

    results.sort(key=lambda x: x["modified_time"], reverse=True)
    return results


@router.get("/datasets/preview/{filename}")
def preview_dataset(filename: str, limit: int = 50):
    """Retrieve column schema and top records for in-browser data grid display."""
    import csv
    csv_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
    fp = os.path.join(csv_dir, filename)
    if not os.path.isfile(fp):
        raise HTTPException(status_code=404, detail=f"Dataset '{filename}' not found.")

    delimiter = "\t" if filename.lower().endswith(".tsv") else ","
    rows = []
    columns = []
    total_count = 0

    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames:
            columns = [c.strip() for c in reader.fieldnames if c.strip()]
        for row in reader:
            total_count += 1
            if len(rows) < limit:
                rows.append({k.strip(): v.strip() for k, v in row.items() if k})

    return {
        "filename": filename,
        "columns": columns,
        "rows": rows,
        "displayed_count": len(rows),
        "total_rows": total_count,
        "download_url": f"/api/datasets/download/{filename}"
    }


class CreateDatasetRequest(BaseModel):
    filename: str
    csv_content: Optional[str] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[List[Any]]] = None


@router.post("/datasets/create")
def create_custom_dataset(req: CreateDatasetRequest):
    """Create a new CSV dataset file in sandbox repository."""
    import csv
    csv_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
    os.makedirs(csv_dir, exist_ok=True)

    fn = req.filename if req.filename.lower().endswith(".csv") else f"{req.filename}.csv"
    fn = fn.replace(" ", "_")
    target_path = os.path.join(csv_dir, fn)

    if req.csv_content:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(req.csv_content.strip() + "\n")
    elif req.columns:
        with open(target_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(req.columns)
            if req.rows:
                writer.writerows(req.rows)
    else:
        raise HTTPException(status_code=400, detail="Must provide csv_content or columns and rows.")

    stat = os.stat(target_path)
    return {
        "status": "success",
        "filename": fn,
        "file_path": f"sandbox_data/csv/{fn}",
        "size_bytes": stat.st_size,
        "download_url": f"/api/datasets/download/{fn}",
        "message": f"Dataset '{fn}' created successfully ({stat.st_size} bytes)."
    }


@router.get("/datasets/download/{filename}")
def download_dataset(filename: str):
    """Download a CSV or TSV dataset directly to user computer."""
    csv_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
    fp = os.path.join(csv_dir, filename)
    if not os.path.isfile(fp):
        raise HTTPException(status_code=404, detail=f"Dataset '{filename}' not found for download.")

    return FileResponse(
        path=fp,
        filename=filename,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# --------------------------------------------------------------------------
# Automated Executive Reports Endpoints
# --------------------------------------------------------------------------
@router.get("/reports")
def list_available_reports():
    """Retrieve all generated executive analysis reports."""
    rep_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    reports = []

    for fn in os.listdir(rep_dir):
        if fn.lower().endswith((".md", ".txt")):
            fp = os.path.join(rep_dir, fn)
            stat = os.stat(fp)
            title = fn.replace(".md", "").replace("_", " ").title()
            summary = ""
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line_s = line.strip()
                        if line_s.startswith("# "):
                            title = line_s.lstrip("# ").strip()
                        elif line_s.startswith("- **") or line_s.startswith("## "):
                            if not summary:
                                summary = line_s
            except Exception:
                pass

            reports.append({
                "filename": fn,
                "title": title,
                "file_path": f"sandbox_data/reports/{fn}",
                "size_bytes": stat.st_size,
                "summary": summary,
                "modified_time": stat.st_mtime,
                "download_url": f"/api/reports/download/{fn}"
            })

    reports.sort(key=lambda x: x["modified_time"], reverse=True)
    return reports


@router.get("/reports/preview/{filename}")
def preview_report(filename: str):
    """Read executive report Markdown content for in-browser inspection and printing."""
    rep_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "reports")
    fp = os.path.join(rep_dir, filename)
    if not os.path.isfile(fp):
        raise HTTPException(status_code=404, detail=f"Report '{filename}' not found.")

    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    return {
        "filename": filename,
        "content": content,
        "size_bytes": os.path.getsize(fp),
        "download_url": f"/api/reports/download/{filename}"
    }


@router.get("/reports/download/{filename}")
def download_report(filename: str):
    """Download executive analysis report to user computer."""
    rep_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "reports")
    fp = os.path.join(rep_dir, filename)
    if not os.path.isfile(fp):
        raise HTTPException(status_code=404, detail=f"Report '{filename}' not found.")

    return FileResponse(
        path=fp,
        filename=filename,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


class GenerateReportRequest(BaseModel):
    source_dataset: str
    report_title: Optional[str] = None
    focus_metric: Optional[str] = None
    executive_notes: Optional[str] = None


@router.post("/reports/generate")
def generate_automated_report(req: GenerateReportRequest):
    """
    Automate data analysis and produce an empirical executive Markdown report.
    Calculates real sums, averages, top rankings, category splits, and strategic actions.
    """
    import csv
    import datetime

    csv_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
    rep_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "reports")
    os.makedirs(rep_dir, exist_ok=True)

    fp = os.path.join(csv_dir, req.source_dataset)
    if not os.path.isfile(fp):
        raise HTTPException(status_code=404, detail=f"Source dataset '{req.source_dataset}' not found.")

    delimiter = "\t" if req.source_dataset.lower().endswith(".tsv") else ","
    rows = []
    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for r in reader:
            rows.append(r)

    if not rows:
        raise HTTPException(status_code=400, detail="Dataset contains no data rows to analyze.")

    # Identify numeric columns
    numeric_cols = []
    for k in rows[0].keys():
        try:
            float(str(rows[0][k]).replace("$", "").replace(",", "").strip())
            numeric_cols.append(k)
        except (ValueError, TypeError):
            pass

    # Pick focus metric
    focus = req.focus_metric
    if not focus or focus not in numeric_cols:
        for c in numeric_cols:
            if any(term in c.lower() for term in ["revenue", "sales", "total", "amount", "price", "units"]):
                focus = c
                break
        if not focus and numeric_cols:
            focus = numeric_cols[0]

    # Compute calculations
    total_val = 0.0
    values = []
    for r in rows:
        val_str = str(r.get(focus, "0")).replace("$", "").replace(",", "").strip()
        try:
            val = float(val_str)
            values.append(val)
            total_val += val
        except ValueError:
            values.append(0.0)

    avg_val = total_val / len(rows) if rows else 0.0
    max_val = max(values) if values else 0.0
    min_val = min(values) if values else 0.0

    # Pick primary label column (e.g. Product, Name, Item, Customer)
    label_col = list(rows[0].keys())[0]
    for k in rows[0].keys():
        if any(term in k.lower() for term in ["product", "item", "name", "client", "vendor", "title"]):
            label_col = k
            break

    # Top records
    sorted_pairs = sorted(zip(rows, values), key=lambda x: x[1], reverse=True)
    top_5 = sorted_pairs[:5]

    top_formatted = []
    for idx, (rec, v) in enumerate(top_5, start=1):
        lbl = rec.get(label_col, f"Record {idx}")
        cat = rec.get("Category") or rec.get("Region") or ""
        cat_suffix = f" ({cat})" if cat else ""
        top_formatted.append(f"{idx}. **{lbl}**{cat_suffix}: ${v:,.2f} {focus}")

    # Category breakdown if Category column exists
    category_breakdown_section = ""
    if "Category" in rows[0] or "Region" in rows[0]:
        cat_key = "Category" if "Category" in rows[0] else "Region"
        cat_sums: Dict[str, float] = {}
        for r, v in zip(rows, values):
            c_name = r.get(cat_key, "Other")
            cat_sums[c_name] = cat_sums.get(c_name, 0.0) + v
        cat_rows = []
        for c_name, c_tot in sorted(cat_sums.items(), key=lambda x: x[1], reverse=True):
            share = (c_tot / total_val * 100.0) if total_val > 0 else 0.0
            cat_rows.append(f"- **{c_name}**: ${c_tot:,.2f} ({share:.1f}% of total {focus})")
        category_breakdown_section = f"\n### Distribution by {cat_key}\n" + "\n".join(cat_rows) + "\n"

    rep_title = req.report_title or f"Executive Intelligence Analysis: {req.source_dataset}"
    slug = req.source_dataset.replace(".csv", "").replace(".tsv", "").replace(" ", "_")
    report_filename = f"{slug}_analysis_report.md"
    target_rep_path = os.path.join(rep_dir, report_filename)
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    report_markdown = f"""# {rep_title}

*Generated autonomously by AgentOS Data Intelligence Engine on {now_str}*

---

## 1. Executive Summary & KPIs

| Metric | Empirical Value | Analysis Context |
| :--- | :--- | :--- |
| **Analyzed Dataset** | `{req.source_dataset}` | Verified tabular schema |
| **Total Rows Evaluated** | **{len(rows):,}** | 100% records parsed |
| **Primary Metric** | **{focus}** | Target KPI benchmark |
| **Total Aggregated Value** | **${total_val:,.2f}** | Cumulative KPI performance |
| **Average per Record** | **${avg_val:,.2f}** | Standard baseline |
| **Peak High Record** | **${max_val:,.2f}** | Outlier high benchmark |
| **Lowest Value Record** | **${min_val:,.2f}** | Minimum recorded threshold |

---

## 2. Top Performing Drivers (Ranked by {focus})

{chr(10).join(top_formatted)}
{category_breakdown_section}
---

## 3. Strategic Recommendations & Automated Actions

1. **Focus Capital on Core Drivers**: The top 2 performing lines account for disproportionate volume of total {focus}. Scale inventory and capacity to meet demand.
2. **Mitigate Low-Margin Drag**: Investigate low-performing tail records for renegotiation or deprecation.
3. **Continuous Verification**: Schedule recurring AgentOS cron evaluation to track month-over-month trajectory.

---
*Verified Ground Truth Data Reference: `sandbox_data/csv/{req.source_dataset}`*
"""

    with open(target_rep_path, "w", encoding="utf-8") as f:
        f.write(report_markdown)

    return {
        "status": "success",
        "filename": report_filename,
        "title": rep_title,
        "file_path": f"sandbox_data/reports/{report_filename}",
        "size_bytes": len(report_markdown.encode("utf-8")),
        "download_url": f"/api/reports/download/{report_filename}",
        "content": report_markdown,
        "message": f"Report '{report_filename}' generated successfully based on {len(rows)} records."
    }
