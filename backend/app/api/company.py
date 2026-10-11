"""
AgentOS - Sandbox Company Application Endpoints.
Provides visibility into the persisted database state (vendors, invoices, payables, metrics).
"""

from __future__ import annotations
import os
import glob
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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
    if ext == ".csv":
        dest_dir = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
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

    # Formulate intelligent action prompt based on file type
    if ext == ".csv":
        suggested_prompt = f"Analyze the CSV at {rel_path}, identify top performers, and save an executive report."
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
