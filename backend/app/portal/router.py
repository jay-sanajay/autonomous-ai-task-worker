"""
AgentOS - Simulated Enterprise Company Portal.
Provides a realistic, controlled browser interface for invoices, support tickets,
and inventory operations to validate end-to-end browser automation workflows.
Features:
- Real-time interactive actions (Resolve tickets, restock inventory, register payables)
- Live auto-sync (background polling every 3 seconds to reflect autonomous agent actions live)
- Direct SQLite persistence across all modules
- Obsidian Intelligence theme
"""

from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.database.session import get_db
from backend.app.database.models import PayableRecord, SupportTicket, InventoryItem

portal_router = APIRouter(prefix="/portal", tags=["Simulated Enterprise Portal"])

# In-memory store alongside database records
portal_submissions = []


# --------------------------------------------------------------------------
# API Endpoints for Real-Time Interactive Updates
# --------------------------------------------------------------------------

class TicketUpdateRequest(BaseModel):
    ticket_code: str
    new_status: Optional[str] = None
    new_priority: Optional[str] = None

class TicketCreateRequest(BaseModel):
    customer_name: str
    subject: str
    description: str
    priority: str = "MEDIUM"

class InventoryRestockRequest(BaseModel):
    sku: str
    amount: int = 10

class InvoiceCreateRequest(BaseModel):
    vendor_name: str
    invoice_number: str
    amount: float


@portal_router.get("/api/tickets")
def api_get_tickets(db: Session = Depends(get_db)):
    tickets = db.query(SupportTicket).order_by(SupportTicket.id.desc()).all()
    return [
        {
            "id": t.id,
            "ticket_code": t.ticket_code,
            "customer_name": t.customer_name,
            "subject": t.subject,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
        }
        for t in tickets
    ]


@portal_router.post("/api/tickets/update")
def api_update_ticket(req: TicketUpdateRequest, db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_code == req.ticket_code.strip()).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if req.new_status:
        ticket.status = req.new_status.upper()
        if ticket.status == "RESOLVED":
            ticket.resolved_at = datetime.now(timezone.utc)
    if req.new_priority:
        ticket.priority = req.new_priority.upper()

    db.commit()
    db.refresh(ticket)
    return {
        "status": "success",
        "ticket": {
            "ticket_code": ticket.ticket_code,
            "status": ticket.status,
            "priority": ticket.priority
        }
    }


@portal_router.post("/api/tickets/create")
def api_create_ticket(req: TicketCreateRequest, db: Session = Depends(get_db)):
    code = f"TICK-{100 + db.query(SupportTicket).count() + 1}"
    new_ticket = SupportTicket(
        ticket_code=code,
        customer_name=req.customer_name.strip(),
        subject=req.subject.strip(),
        description=req.description.strip(),
        priority=req.priority.upper(),
        status="OPEN",
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return {"status": "success", "ticket_code": code}


@portal_router.get("/api/inventory")
def api_get_inventory(db: Session = Depends(get_db)):
    items = db.query(InventoryItem).order_by(InventoryItem.current_stock.asc()).all()
    return [
        {
            "id": it.id,
            "sku": it.sku,
            "product_name": it.product_name,
            "category": it.category,
            "current_stock": it.current_stock,
            "reorder_threshold": it.reorder_threshold,
            "unit_price": it.unit_price,
            "status": it.status
        }
        for it in items
    ]


@portal_router.post("/api/inventory/restock")
def api_restock_inventory(req: InventoryRestockRequest, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.sku == req.sku.strip()).first()
    if not item:
        raise HTTPException(status_code=404, detail="SKU not found")

    item.current_stock += max(req.amount, 1)
    if item.current_stock > item.reorder_threshold:
        item.status = "IN_STOCK"
    db.commit()
    db.refresh(item)
    return {"status": "success", "sku": item.sku, "current_stock": item.current_stock, "status_text": item.status}


@portal_router.get("/api/invoices")
def api_get_invoices(db: Session = Depends(get_db)):
    db_payables = db.query(PayableRecord).order_by(PayableRecord.created_at.desc()).limit(20).all()
    return [
        {
            "id": p.id,
            "vendor_name": p.vendor_name,
            "invoice_number": p.invoice_number,
            "amount": p.amount,
            "status": p.status,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else ""
        }
        for p in db_payables
    ]


@portal_router.post("/api/invoices/create")
def api_create_invoice(req: InvoiceCreateRequest, db: Session = Depends(get_db)):
    # Check if duplicate already exists
    existing = db.query(PayableRecord).filter(
        PayableRecord.vendor_name == req.vendor_name.strip(),
        PayableRecord.invoice_number == req.invoice_number.strip()
    ).first()
    if existing:
        return {"status": "success", "id": existing.id, "invoice_number": existing.invoice_number}

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    idem_key = f"{req.vendor_name.strip()}:{req.invoice_number.strip()}"
    new_payable = PayableRecord(
        vendor_name=req.vendor_name.strip(),
        invoice_number=req.invoice_number.strip(),
        amount=float(req.amount),
        currency="USD",
        invoice_date=now_str,
        due_date=now_str,
        payment_terms="Net 30",
        idempotency_key=idem_key,
        status="RECORDED",
        created_by="Portal_User_Jay",
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_payable)
    db.commit()
    db.refresh(new_payable)

    sub_id = len(portal_submissions) + 1
    portal_submissions.append({
        "id": sub_id,
        "vendor": req.vendor_name.strip(),
        "invoice_number": req.invoice_number.strip(),
        "amount": req.amount,
        "status": "RECORDED"
    })
    return {"status": "success", "id": new_payable.id, "invoice_number": new_payable.invoice_number}


# --------------------------------------------------------------------------
# UI Styling & Layout
# --------------------------------------------------------------------------

SHARED_STYLES = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif;
        background: #080D0B;
        color: #F0F7F2;
        padding: 28px;
        min-height: 100vh;
    }
    .header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid #263A2E;
    }
    .header-title { font-size: 18px; font-weight: 700; color: #55E6A5; display: flex; align-items: center; gap: 8px; }
    .header-sub { font-size: 12px; color: #A0B2A6; margin-top: 4px; }
    .admin-badge {
        font-size: 11px;
        background: #142019;
        border: 1px solid #263A2E;
        color: #55E6A5;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .live-dot {
        width: 7px;
        height: 7px;
        background: #55E6A5;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #55E6A5;
        animation: pulse 1.8s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.7; }
        50% { transform: scale(1.3); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.7; }
    }
    .nav-tabs {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .nav-btn {
        background: #101914;
        border: 1px solid #263A2E;
        color: #A0B2A6;
        padding: 8px 14px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 12px;
        font-weight: 600;
        transition: all 0.15s;
    }
    .nav-btn:hover, .nav-btn.active {
        background: #1C2D24;
        color: #55E6A5;
        border-color: #55E6A5;
    }
    .card {
        background: #101914;
        border: 1px solid #263A2E;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 15px;
        font-weight: 700;
        color: #F0F7F2;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    input, select, textarea {
        background: #080D0B;
        color: #F0F7F2;
        border: 1px solid #263A2E;
        padding: 9px 12px;
        border-radius: 8px;
        font-size: 12px;
        width: 100%;
        margin-top: 6px;
        margin-bottom: 12px;
        display: block;
    }
    input:focus, select:focus, textarea:focus {
        outline: none;
        border-color: #55E6A5;
    }
    label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: #718278;
    }
    button, .action-btn {
        background: #55E6A5;
        color: #080D0B;
        font-weight: 700;
        padding: 8px 14px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.15s;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    button:hover, .action-btn:hover {
        background: #35D993;
        transform: translateY(-1px);
    }
    .btn-sm {
        padding: 4px 8px;
        font-size: 11px;
        border-radius: 6px;
    }
    .btn-secondary {
        background: #142019;
        color: #F0F7F2;
        border: 1px solid #263A2E;
    }
    .btn-secondary:hover {
        background: #1C2D24;
        border-color: #55E6A5;
    }
    .btn-amber {
        background: #FFC66D;
        color: #080D0B;
    }
    .btn-amber:hover {
        background: #e6b260;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        margin-top: 8px;
    }
    th {
        background: #142019;
        color: #718278;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 10px;
        letter-spacing: 0.05em;
        padding: 10px 12px;
        border-bottom: 1px solid #263A2E;
        text-align: left;
    }
    td {
        padding: 10px 12px;
        border-bottom: 1px solid #1C2D24;
        color: #F0F7F2;
        vertical-align: middle;
    }
    tr:hover td {
        background: #142019;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .badge-jade { background: rgba(85, 230, 165, 0.12); color: #55E6A5; border: 1px solid rgba(85, 230, 165, 0.3); }
    .badge-amber { background: rgba(255, 198, 109, 0.12); color: #FFC66D; border: 1px solid rgba(255, 198, 109, 0.3); }
    .badge-iris { background: rgba(169, 155, 255, 0.12); color: #A99BFF; border: 1px solid rgba(169, 155, 255, 0.3); }
    .badge-error { background: rgba(255, 119, 119, 0.12); color: #FF7777; border: 1px solid rgba(255, 119, 119, 0.3); }
    .grid-3 {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
    }
    .flash-update {
        animation: flashGreen 1s ease-out;
    }
    @keyframes flashGreen {
        0% { background: rgba(85, 230, 165, 0.3); }
        100% { background: transparent; }
    }
"""


def render_portal_layout(title: str, active_tab: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - AgentOS Enterprise Portal</title>
  <style>{SHARED_STYLES}</style>
</head>
<body>
  <div class="header-bar">
    <div>
      <div class="header-title">
        <span>⚡</span> AgentOS Enterprise Operations Portal
      </div>
      <div class="header-sub">Simulated enterprise web portal with real-time bidirectional synchronization & live action controls.</div>
    </div>
    <div style="display:flex; align-items:center; gap: 12px;">
      <div class="admin-badge">
        <span class="live-dot"></span>
        <span>Real-Time Sync</span>
      </div>
      <a href="http://localhost:5173" class="nav-btn" style="color: #55E6A5; border-color: rgba(85, 230, 165, 0.3);">← Back to AgentOS Dashboard</a>
      <div class="admin-badge">Jay • Administrator</div>
    </div>
  </div>

  <div class="nav-tabs">
    <a href="/portal" class="nav-btn {'active' if active_tab == 'home' else ''}" id="nav-home">Overview</a>
    <a href="/portal/invoices" class="nav-btn {'active' if active_tab == 'invoices' else ''}" id="nav-invoices">Invoices & Payables</a>
    <a href="/portal/tickets" class="nav-btn {'active' if active_tab == 'tickets' else ''}" id="nav-tickets">Support Desk Queue</a>
    <a href="/portal/inventory" class="nav-btn {'active' if active_tab == 'inventory' else ''}" id="nav-inventory">Warehouse Inventory</a>
  </div>

  {content}
</body>
</html>"""


# --------------------------------------------------------------------------
# Route 1: Portal Overview Dashboard
# --------------------------------------------------------------------------

@portal_router.get("", response_class=HTMLResponse)
@portal_router.get("/", response_class=HTMLResponse)
def portal_index(db: Session = Depends(get_db)):
    payables_count = db.query(PayableRecord).count()
    tickets_count = db.query(SupportTicket).count()
    inventory_count = db.query(InventoryItem).count()

    content = f"""
    <div class="grid-3">
      <div class="card">
        <div class="card-title">
          <span>Invoices & Payables</span>
          <span class="badge badge-jade" id="stat-payables">{payables_count} Records</span>
        </div>
        <p style="font-size: 13px; color: #A0B2A6; margin-bottom: 16px; line-height: 1.5;">
          Submit and audit vendor invoices. Live persistence into SQLite with automated verification checks.
        </p>
        <a href="/portal/invoices" class="action-btn">Open Invoices Module →</a>
      </div>

      <div class="card">
        <div class="card-title">
          <span>Support Desk Queue</span>
          <span class="badge badge-amber" id="stat-tickets">{tickets_count} Active</span>
        </div>
        <p style="font-size: 13px; color: #A0B2A6; margin-bottom: 16px; line-height: 1.5;">
          Live queue of customer support requests. Resolve tickets in real time, adjust priority, or add new tickets.
        </p>
        <a href="/portal/tickets" class="action-btn">Open Support Queue →</a>
      </div>

      <div class="card">
        <div class="card-title">
          <span>Warehouse Inventory</span>
          <span class="badge badge-iris" id="stat-inventory">{inventory_count} SKUs</span>
        </div>
        <p style="font-size: 13px; color: #A0B2A6; margin-bottom: 16px; line-height: 1.5;">
          Monitor real-time warehouse stock, track replenishment thresholds, and trigger instant restock actions.
        </p>
        <a href="/portal/inventory" class="action-btn">Open Warehouse Catalog →</a>
      </div>
    </div>
    """
    return render_portal_layout("Overview", "home", content)


# --------------------------------------------------------------------------
# Route 2: Support Desk Queue (Live & Interactive)
# --------------------------------------------------------------------------

@portal_router.get("/tickets", response_class=HTMLResponse)
def portal_tickets(db: Session = Depends(get_db)):
    content = """
    <div class="card">
      <div class="card-title">
        <div style="display:flex; align-items:center; gap:10px;">
          <span>Support Desk Ticket Queue</span>
          <span class="badge badge-amber" id="ticket-count-badge">Loading...</span>
        </div>
        <div style="display:flex; gap: 8px;">
          <button onclick="toggleNewTicketModal()" class="action-btn btn-sm">
            <span>+ New Ticket</span>
          </button>
          <button onclick="fetchTickets(true)" class="action-btn btn-sm btn-secondary">
            <span>↺ Refresh</span>
          </button>
        </div>
      </div>

      <!-- Quick Ticket Creation Form (Collapsible) -->
      <div id="new-ticket-box" style="display:none; background:#142019; border:1px solid #263A2E; border-radius:10px; padding:16px; margin-bottom:16px;">
        <div style="font-weight:bold; font-size:13px; color:#55E6A5; margin-bottom:10px;">Create New Customer Support Ticket</div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
          <div>
            <label>Customer / Account Name</label>
            <input type="text" id="new-cust" placeholder="e.g. Acme Corp" />
          </div>
          <div>
            <label>Priority</label>
            <select id="new-priority">
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM" selected>Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>
        <div>
          <label>Subject</label>
          <input type="text" id="new-subject" placeholder="e.g. SSO Integration Timeout" />
        </div>
        <div>
          <label>Description Details</label>
          <input type="text" id="new-desc" placeholder="Details of the issue..." />
        </div>
        <div style="display:flex; gap:8px; margin-top:8px;">
          <button onclick="submitNewTicket()" class="action-btn btn-sm">Save & Dispatch Ticket</button>
          <button onclick="toggleNewTicketModal()" class="action-btn btn-sm btn-secondary">Cancel</button>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Ticket ID</th>
            <th>Customer</th>
            <th>Subject & Details</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Real-Time Actions</th>
          </tr>
        </thead>
        <tbody id="tickets-tbody">
          <tr><td colspan="6" style="text-align:center; color:#718278;">Connecting to live database...</td></tr>
        </tbody>
      </table>
    </div>

    <script>
      function toggleNewTicketModal() {
        const box = document.getElementById('new-ticket-box');
        box.style.display = box.style.display === 'none' ? 'block' : 'none';
      }

      async function fetchTickets(isManual = false) {
        try {
          const res = await fetch('/portal/api/tickets');
          const data = await res.json();
          renderTickets(data);
          document.getElementById('ticket-count-badge').textContent = data.length + ' Active Tickets';
        } catch (err) {
          console.error('Failed to sync tickets:', err);
        }
      }

      function renderTickets(tickets) {
        const tbody = document.getElementById('tickets-tbody');
        if (!tickets || tickets.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#718278;">No tickets in queue.</td></tr>';
          return;
        }

        tbody.innerHTML = tickets.map(t => {
          let priorityClass = 'badge-iris';
          if (t.priority === 'CRITICAL') priorityClass = 'badge-error';
          else if (t.priority === 'HIGH') priorityClass = 'badge-amber';
          else if (t.priority === 'LOW') priorityClass = 'badge-jade';

          const isResolved = t.status === 'RESOLVED';
          const isInProgress = t.status === 'IN_PROGRESS';
          const statusClass = isResolved ? 'badge-jade' : (isInProgress ? 'badge-amber' : 'badge-error');

          let actionButtons = '';
          if (!isResolved) {
            actionButtons = `
              <button onclick="updateTicketStatus('${t.ticket_code}', 'RESOLVED')" class="action-btn btn-sm" style="background:#55E6A5; color:#080D0B;">
                ✓ Resolve
              </button>
              ${!isInProgress ? `
                <button onclick="updateTicketStatus('${t.ticket_code}', 'IN_PROGRESS')" class="action-btn btn-sm btn-secondary">
                  ▶ In Progress
                </button>
              ` : ''}
              <button onclick="escalateTicket('${t.ticket_code}')" class="action-btn btn-sm btn-secondary" title="Escalate Priority">
                ⚡ Escalate
              </button>
            `;
          } else {
            actionButtons = `
              <button onclick="updateTicketStatus('${t.ticket_code}', 'OPEN')" class="action-btn btn-sm btn-secondary">
                ↺ Re-Open
              </button>
            `;
          }

          return `
            <tr id="row-${t.ticket_code}">
              <td><span style="font-family:monospace; font-weight:bold; color:#55E6A5;">${t.ticket_code}</span></td>
              <td><strong>${escapeHtml(t.customer_name)}</strong></td>
              <td>
                <div style="font-weight:600; color:#F0F7F2;">${escapeHtml(t.subject)}</div>
                <div style="color:#718278; font-size:11px; margin-top:2px;">${escapeHtml(t.description)}</div>
              </td>
              <td><span class="badge ${priorityClass}">${t.priority}</span></td>
              <td><span class="badge ${statusClass}">${t.status}</span></td>
              <td>
                <div style="display:flex; gap:6px; flex-wrap:wrap;">
                  ${actionButtons}
                </div>
              </td>
            </tr>
          `;
        }).join('');
      }

      async function updateTicketStatus(code, newStatus) {
        const row = document.getElementById('row-' + code);
        if (row) row.classList.add('flash-update');
        try {
          const res = await fetch('/portal/api/tickets/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticket_code: code, new_status: newStatus })
          });
          if (res.ok) {
            await fetchTickets();
          }
        } catch (err) {
          alert('Failed to update ticket: ' + err);
        }
      }

      async function escalateTicket(code) {
        try {
          const res = await fetch('/portal/api/tickets/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticket_code: code, new_priority: 'CRITICAL', new_status: 'IN_PROGRESS' })
          });
          if (res.ok) {
            await fetchTickets();
          }
        } catch (err) {
          alert('Failed to escalate: ' + err);
        }
      }

      async function submitNewTicket() {
        const customer = document.getElementById('new-cust').value.trim();
        const subject = document.getElementById('new-subject').value.trim();
        const description = document.getElementById('new-desc').value.trim();
        const priority = document.getElementById('new-priority').value;

        if (!customer || !subject) {
          alert('Please enter customer and subject.');
          return;
        }

        try {
          const res = await fetch('/portal/api/tickets/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ customer_name: customer, subject: subject, description: description, priority: priority })
          });
          if (res.ok) {
            document.getElementById('new-cust').value = '';
            document.getElementById('new-subject').value = '';
            document.getElementById('new-desc').value = '';
            toggleNewTicketModal();
            await fetchTickets();
          }
        } catch (err) {
          alert('Failed to create ticket: ' + err);
        }
      }

      function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
      }

      // Initial load
      fetchTickets();
      // Live Auto-Sync every 3 seconds
      setInterval(fetchTickets, 3000);
    </script>
    """
    return render_portal_layout("Customer Support Desk", "tickets", content)


# --------------------------------------------------------------------------
# Route 3: Invoices & Payables (Live & Interactive)
# --------------------------------------------------------------------------

@portal_router.get("/invoices", response_class=HTMLResponse)
def portal_invoices(db: Session = Depends(get_db)):
    content = """
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px;">
      <!-- Registration Form -->
      <div class="card">
        <div class="card-title">Register New Vendor Invoice</div>
        <form id="invoice-form" onsubmit="handleInvoiceSubmit(event)">
          <label for="vendor_name">Vendor Name</label>
          <input type="text" id="vendor_name" name="vendor_name" placeholder="e.g. Acme Technologies Inc." required />

          <label for="invoice_number">Invoice Reference Number</label>
          <input type="text" id="invoice_number" name="invoice_number" placeholder="e.g. INV-2024-001" required />

          <label for="amount">Total Amount (USD)</label>
          <input type="number" step="0.01" id="amount" name="amount" placeholder="e.g. 2450.00" required />

          <button type="submit" id="submit-btn" style="width: 100%;">
            <span>⚡ Register in Database</span>
          </button>
        </form>

        <div id="invoice-msg" style="display:none; margin-top:12px; padding:10px; border-radius:8px; font-size:12px; font-weight:bold;"></div>
      </div>

      <!-- Ledger Table -->
      <div class="card">
        <div class="card-title">
          <div style="display:flex; align-items:center; gap:10px;">
            <span>Invoices Ledger</span>
            <span class="badge badge-jade" id="invoices-count-badge">Loading...</span>
          </div>
          <button onclick="fetchInvoices(true)" class="action-btn btn-sm btn-secondary">
            <span>↺ Refresh</span>
          </button>
        </div>

        <table>
          <thead>
            <tr><th>Ref</th><th>Vendor</th><th>Invoice #</th><th>Amount</th><th>Status</th><th>Timestamp</th></tr>
          </thead>
          <tbody id="invoices-tbody">
            <tr><td colspan="6" style="text-align:center; color:#718278;">Connecting to live database...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <script>
      async function fetchInvoices() {
        try {
          const res = await fetch('/portal/api/invoices');
          const data = await res.json();
          renderInvoices(data);
          document.getElementById('invoices-count-badge').textContent = data.length + ' Records';
        } catch (err) {
          console.error('Failed to sync invoices:', err);
        }
      }

      function renderInvoices(items) {
        const tbody = document.getElementById('invoices-tbody');
        if (!items || items.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#718278;">No invoices found.</td></tr>';
          return;
        }

        tbody.innerHTML = items.map(it => `
          <tr id="inv-row-${it.id}">
            <td><span style="font-family:monospace; color:#A0B2A6;">#${it.id}</span></td>
            <td><strong style="color:#F0F7F2;">${escapeHtml(it.vendor_name)}</strong></td>
            <td><span style="font-family:monospace; color:#55E6A5;">${escapeHtml(it.invoice_number)}</span></td>
            <td style="font-weight:600; color:#55E6A5;">$${parseFloat(it.amount).toLocaleString('en-US', {minimumFractionDigits: 2})} USD</td>
            <td><span class="badge ${it.status === 'RECORDED' ? 'badge-jade' : 'badge-amber'}">${it.status}</span></td>
            <td style="font-size:11px; color:#718278;">${it.created_at || 'Just now'}</td>
          </tr>
        `).join('');
      }

      async function handleInvoiceSubmit(e) {
        e.preventDefault();
        const vendor = document.getElementById('vendor_name').value.trim();
        const invNum = document.getElementById('invoice_number').value.trim();
        const amount = parseFloat(document.getElementById('amount').value);

        const msgBox = document.getElementById('invoice-msg');
        msgBox.style.display = 'block';
        msgBox.style.background = '#142019';
        msgBox.style.color = '#FFC66D';
        msgBox.style.border = '1px solid #263A2E';
        msgBox.textContent = 'Saving to database...';

        try {
          const res = await fetch('/portal/api/invoices/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vendor_name: vendor, invoice_number: invNum, amount: amount })
          });
          const result = await res.json();
          if (res.ok) {
            msgBox.style.background = 'rgba(85, 230, 165, 0.15)';
            msgBox.style.color = '#55E6A5';
            msgBox.style.border = '1px solid #55E6A5';
            msgBox.textContent = `✔ Successfully recorded Invoice #${result.invoice_number} in SQLite database!`;
            document.getElementById('vendor_name').value = '';
            document.getElementById('invoice_number').value = '';
            document.getElementById('amount').value = '';
            await fetchInvoices();
          } else {
            throw new Error(result.detail || 'Failed');
          }
        } catch (err) {
          msgBox.style.background = 'rgba(255, 119, 119, 0.15)';
          msgBox.style.color = '#FF7777';
          msgBox.style.border = '1px solid #FF7777';
          msgBox.textContent = 'Error: ' + err.message;
        }
      }

      function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
      }

      fetchInvoices();
      setInterval(fetchInvoices, 3000);
    </script>
    """
    return render_portal_layout("Invoices & Payables", "invoices", content)


# --------------------------------------------------------------------------
# Route 4: Warehouse Stock Catalog (Live & Interactive)
# --------------------------------------------------------------------------

@portal_router.get("/inventory", response_class=HTMLResponse)
def portal_inventory(db: Session = Depends(get_db)):
    content = """
    <div class="card">
      <div class="card-title">
        <div style="display:flex; align-items:center; gap:10px;">
          <span>Warehouse Stock Catalog & Live Replenishment</span>
          <span class="badge badge-iris" id="inv-count-badge">Loading...</span>
        </div>
        <button onclick="fetchInventory(true)" class="action-btn btn-sm btn-secondary">
          <span>↺ Refresh</span>
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Product Name</th>
            <th>Category</th>
            <th>Stock Level</th>
            <th>Reorder Point</th>
            <th>Unit Price</th>
            <th>Status</th>
            <th>Real-Time Replenish</th>
          </tr>
        </thead>
        <tbody id="inventory-tbody">
          <tr><td colspan="8" style="text-align:center; color:#718278;">Connecting to live database...</td></tr>
        </tbody>
      </table>
    </div>

    <script>
      async function fetchInventory() {
        try {
          const res = await fetch('/portal/api/inventory');
          const data = await res.json();
          renderInventory(data);
          document.getElementById('inv-count-badge').textContent = data.length + ' SKUs Tracked';
        } catch (err) {
          console.error('Failed to sync inventory:', err);
        }
      }

      function renderInventory(items) {
        const tbody = document.getElementById('inventory-tbody');
        if (!items || items.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#718278;">No inventory items found.</td></tr>';
          return;
        }

        tbody.innerHTML = items.map(it => {
          const isLow = it.current_stock <= it.reorder_threshold;
          const statusBadge = isLow ? 'badge-error' : 'badge-jade';
          const stockColor = isLow ? '#FF7777' : '#55E6A5';

          return `
            <tr id="row-sku-${it.sku}">
              <td><span style="font-family:monospace; font-weight:bold; color:#A99BFF;">${it.sku}</span></td>
              <td><strong style="color:#F0F7F2;">${escapeHtml(it.product_name)}</strong></td>
              <td style="color:#A0B2A6;">${escapeHtml(it.category)}</td>
              <td><span style="font-family:monospace; font-weight:bold; font-size:13px; color:${stockColor};">${it.current_stock}</span></td>
              <td style="color:#718278;">${it.reorder_threshold}</td>
              <td style="color:#F0F7F2;">$${parseFloat(it.unit_price).toFixed(2)}</td>
              <td><span class="badge ${statusBadge}">${it.status}</span></td>
              <td>
                <div style="display:flex; gap:6px;">
                  <button onclick="restockSku('${it.sku}', 10)" class="action-btn btn-sm" title="Add 10 units to warehouse">
                    + Restock (+10)
                  </button>
                  <button onclick="restockSku('${it.sku}', 25)" class="action-btn btn-sm btn-secondary" title="Add 25 units">
                    +25
                  </button>
                </div>
              </td>
            </tr>
          `;
        }).join('');
      }

      async function restockSku(sku, amount) {
        const row = document.getElementById('row-sku-' + sku);
        if (row) row.classList.add('flash-update');

        try {
          const res = await fetch('/portal/api/inventory/restock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sku: sku, amount: amount })
          });
          if (res.ok) {
            await fetchInventory();
          }
        } catch (err) {
          alert('Failed to restock: ' + err);
        }
      }

      function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
      }

      fetchInventory();
      setInterval(fetchInventory, 3000);
    </script>
    """
    return render_portal_layout("Warehouse Inventory", "inventory", content)
