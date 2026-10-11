"""
AgentOS - Simulated Enterprise Company Portal.
Provides a realistic, controlled browser interface for invoices, support tickets,
and inventory operations to validate end-to-end browser automation workflows.
"""

from __future__ import annotations
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

portal_router = APIRouter(prefix="/portal", tags=["Simulated Enterprise Portal"])

# In-memory portal submission store for browser workflow verification
portal_submissions = []

@portal_router.get("", response_class=HTMLResponse)
@portal_router.get("/", response_class=HTMLResponse)
def portal_index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CentrAlign Enterprise Portal</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }
    h1 { color: #38bdf8; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
    a { color: #818cf8; text-decoration: none; font-weight: bold; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>CentrAlign Enterprise Operations Portal</h1>
  <p>Simulated company internal portal for autonomous task verification.</p>
  <div class="card">
    <h2>Available Modules</h2>
    <ul>
      <li><a href="/portal/invoices" id="nav-invoices">Invoice Registration & Management</a></li>
      <li><a href="/portal/tickets" id="nav-tickets">Support Desk Queue</a></li>
      <li><a href="/portal/inventory" id="nav-inventory">Warehouse Stock Catalog</a></li>
    </ul>
  </div>
</body>
</html>"""


@portal_router.get("/invoices", response_class=HTMLResponse)
def portal_invoices():
    items_html = "".join([
        f"<tr><td>#{s['id']}</td><td>{s['vendor']}</td><td>${s['amount']:.2f}</td><td><span style='color: #4ade80;'>Registered</span></td></tr>"
        for s in portal_submissions
    ]) or "<tr><td colspan='4' style='color:#94a3b8; text-align:center;'>No recent browser submissions yet.</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Portal - Invoices</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }}
    h1 {{ color: #38bdf8; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
    input, button {{ padding: 10px 14px; border-radius: 8px; border: 1px solid #475569; font-size: 14px; margin-bottom: 12px; display: block; width: 100%; max-width: 400px; box-sizing: border-box; }}
    input {{ background: #0f172a; color: #f8fafc; }}
    button {{ background: #0284c7; color: white; font-weight: bold; cursor: pointer; border: none; }}
    button:hover {{ background: #0369a1; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ padding: 10px; border-bottom: 1px solid #334155; text-align: left; }}
    .alert-success {{ background: #064e3b; color: #4ade80; border: 1px solid #059669; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Invoice Processing System</h1>
  <div class="card">
    <h2>Register New Vendor Invoice</h2>
    <form id="invoice-form" method="POST" action="/portal/invoices">
      <label for="vendor_name">Vendor Name</label>
      <input type="text" id="vendor_name" name="vendor_name" placeholder="Enter vendor name (e.g. Acme Technologies)" required />
      
      <label for="invoice_number">Invoice Reference Number</label>
      <input type="text" id="invoice_number" name="invoice_number" placeholder="e.g. INV-2024-001" required />

      <label for="amount">Total Amount (USD)</label>
      <input type="number" step="0.01" id="amount" name="amount" placeholder="e.g. 2450.00" required />

      <button type="submit" id="submit-btn">Submit Invoice</button>
    </form>
  </div>

  <div class="card">
    <h2>Registered Invoices Ledger</h2>
    <table>
      <thead>
        <tr><th>ID</th><th>Vendor</th><th>Amount</th><th>Status</th></tr>
      </thead>
      <tbody id="invoice-list">
        {items_html}
      </tbody>
    </table>
  </div>
</body>
</html>"""


@portal_router.post("/invoices", response_class=HTMLResponse)
def portal_submit_invoice(
    vendor_name: str = Form(...),
    invoice_number: str = Form(...),
    amount: float = Form(...)
):
    sub_id = len(portal_submissions) + 1
    record = {
        "id": sub_id,
        "vendor": vendor_name.strip(),
        "invoice_number": invoice_number.strip(),
        "amount": amount,
        "status": "REGISTERED"
    }
    portal_submissions.append(record)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Invoice Submitted Successfully</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }}
    .success-card {{ background: #064e3b; border: 1px solid #059669; border-radius: 12px; padding: 24px; color: #f8fafc; }}
    a {{ color: #38bdf8; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="success-card" id="submission-result">
    <h2 id="success-banner">Successfully Registered Invoice #{invoice_number}</h2>
    <p>Vendor: <strong id="res-vendor">{vendor_name}</strong></p>
    <p>Amount: <strong id="res-amount">${amount:.2f} USD</strong></p>
    <p>Receipt ID: <span id="res-id">PORTAL-REC-{sub_id:04d}</span></p>
    <p><a href="/portal/invoices" id="back-link">Return to Invoices</a></p>
  </div>
</body>
</html>"""
