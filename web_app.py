"""
CentraWorker - FastAPI Web Application & API Gateway.
Hosts both the interactive Agent Dashboard and the simulated CentraERP web portal.
"""

from __future__ import annotations
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from centra_worker import AutonomousAgent, TaskRequest, TaskResult
from simulated_company.erp_server import erp_db, InvoiceSubmission

app = FastAPI(
    title="CentraWorker - Autonomous AI Task Worker",
    description="Autonomous Agent prototype for enterprise workflows (CentrAlign AI challenge)",
    version="1.0.0"
)

# Mount static files
static_dir = os.path.join(PROJECT_ROOT, "frontend", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Keep active agent instance in memory for approval workflow
active_agent = AutonomousAgent()


class ApprovalResolution(BaseModel):
    approval_id: str
    approved: bool
    approver: Optional[str] = "Manager"
    feedback: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    dashboard_path = os.path.join(PROJECT_ROOT, "frontend", "templates", "dashboard.html")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/portal/invoices", response_class=HTMLResponse)
async def get_erp_portal():
    portal_path = os.path.join(PROJECT_ROOT, "simulated_company", "web_portal", "invoices.html")
    with open(portal_path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------
# CentraERP Simulated REST Endpoints
# ---------------------------------------------------------
@app.get("/api/erp/health")
async def erp_health():
    return {"status": "ok", "system": "CentraERP Operations Gateway", "version": "4.2.0"}


@app.get("/api/erp/vendors")
async def erp_vendors():
    return erp_db.get_vendors()


@app.get("/api/erp/invoices")
async def erp_invoices(vendor: Optional[str] = None, invoice_num: Optional[str] = None):
    return erp_db.get_invoices(vendor=vendor, invoice_num=invoice_num)


@app.post("/api/erp/invoices")
async def erp_create_invoice(sub: InvoiceSubmission):
    try:
        rec = erp_db.add_invoice(sub, actor="WebAPI_User")
        return rec
    except ConnectionError as ce:
        raise HTTPException(status_code=503, detail=str(ce))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/erp/reset")
async def erp_reset():
    erp_db.reset()
    return {"status": "success", "message": "CentraERP database restored to clean seed state."}


@app.post("/api/erp/simulate-fault")
async def erp_simulate_fault():
    erp_db.force_transient_error = True
    return {"status": "success", "message": "Transient 503 gateway fault enabled for next submission attempt."}


# ---------------------------------------------------------
# CentraWorker Autonomous Agent Endpoints
# ---------------------------------------------------------
@app.post("/api/agent/run")
async def run_agent_task(req: TaskRequest):
    global active_agent
    # Spin up fresh agent session
    active_agent = AutonomousAgent(auto_approve_high_risk=req.auto_approve_high_risk)
    result = active_agent.run(req)
    return result.model_dump()


@app.post("/api/agent/approve")
async def approve_agent_task(resolution: ApprovalResolution):
    global active_agent
    try:
        result = active_agent.resume_with_approval(
            approval_id=resolution.approval_id,
            approved=resolution.approved,
            approver=resolution.approver or "Executive",
            feedback=resolution.feedback
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("\nStarting CentraWorker Web Dashboard & CentraERP...")
    print("Dashboard URL: http://localhost:8000")
    print("CentraERP Web Portal: http://localhost:8000/portal/invoices\n")
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
