"""
AgentOS - Sandbox Company Data Seeder.
Initializes vendors, document index, and existing payable records for repeatable evaluations.
"""

from __future__ import annotations
import os
import glob
from sqlalchemy.orm import Session
from backend.app.database.models import (
    Base, Vendor, InvoiceDocument, PayableRecord, AgentTask, TaskStep, ApprovalRequest, VerificationResult,
    TaskItem, SupportTicket, InventoryItem, PurchaseRequest
)
from backend.app.database.session import SessionLocal, engine

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
INVOICE_DIR = os.path.join(PROJECT_ROOT, "sandbox_data", "invoices")


def seed_database(db: Session):
    """Seed sandbox vendors, documents, and historical baseline records."""
    # 1. Vendors
    if db.query(Vendor).count() == 0:
        vendors = [
            Vendor(
                vendor_code="VEND-ACME-01",
                name="Acme Technologies Inc.",
                aliases="Acme, Acme Tech, Acme Technologies, Acme Tech Inc",
                payment_terms="Net 30",
                category="Cloud & Software Engineering",
                status="APPROVED"
            ),
            Vendor(
                vendor_code="VEND-GLOG-02",
                name="Global Logistics Freight Ltd",
                aliases="Global Logistics, GL Freight, Global Logistics Ltd",
                payment_terms="Net 30",
                category="Freight & Shipping",
                status="APPROVED"
            ),
            Vendor(
                vendor_code="VEND-NEXUS-09",
                name="Nexus Hardware Systems",
                aliases="Nexus, Nexus Hardware, Nexus Systems",
                payment_terms="Net 30",
                category="Server & GPU Infrastructure",
                status="APPROVED"
            ),
            Vendor(
                vendor_code="VEND-APEX-03",
                name="Apex Cloud Services LLC",
                aliases="Apex, Apex Cloud, Apex Services",
                payment_terms="Net 15",
                category="Data Center Operations",
                status="APPROVED"
            )
        ]
        db.add_all(vendors)
        db.commit()

    # 2. Invoice Documents index
    if db.query(InvoiceDocument).count() == 0 and os.path.exists(INVOICE_DIR):
        doc_files = glob.glob(os.path.join(INVOICE_DIR, "*.*"))
        docs = []
        for p in doc_files:
            fn = os.path.basename(p)
            ext = os.path.splitext(fn)[1].lstrip(".")
            sz = os.path.getsize(p)
            is_latest = "Latest" in fn
            hint = "Acme Technologies Inc." if "Acme" in fn else ("Global Logistics" if "Logistics" in fn else "Nexus")
            docs.append(
                InvoiceDocument(
                    filename=fn,
                    file_path=os.path.relpath(p, PROJECT_ROOT).replace("\\", "/"),
                    file_type=ext,
                    file_size_bytes=sz,
                    vendor_name_hint=hint,
                    is_latest_for_vendor=is_latest
                )
            )
        if docs:
            db.add_all(docs)
            db.commit()

    # 3. Seed historical payable record for INV-2023-042 (to test duplicate detection!)
    acme = db.query(Vendor).filter(Vendor.vendor_code == "VEND-ACME-01").first()
    if acme and db.query(PayableRecord).filter(PayableRecord.invoice_number == "INV-2023-042").count() == 0:
        historic_payable = PayableRecord(
            vendor_id=acme.id,
            vendor_name=acme.name,
            invoice_number="INV-2023-042",
            amount=3200.00,
            currency="USD",
            invoice_date="2023-11-15",
            due_date="2023-12-15",
            payment_terms="Net 30",
            po_number="PO-ACME-710",
            idempotency_key="ACME_INV-2023-042",
            status="VERIFIED",
            created_by="Historical_Migration",
            notes="Archived 2023 payable record for duplicate testing",
            verification_hash="HASH_HISTORIC_VERIFIED_042"
        )
        db.add(historic_payable)
        db.commit()

    # 4. Seed sample Task Items
    if db.query(TaskItem).count() == 0:
        initial_tasks = [
            TaskItem(
                title="Complete Q3 System Architecture Review",
                description="Finalize AgentOS documentation and ReAct execution diagram.",
                due_date="2026-10-18",
                meeting_link="https://meet.google.com/q3-review-arch",
                status="COMPLETED",
                priority="HIGH",
                source_reference="Internal Calendar"
            )
        ]
        db.add_all(initial_tasks)
        db.commit()

    # 5. Seed Support Tickets
    if db.query(SupportTicket).count() == 0:
        tickets = [
            SupportTicket(
                ticket_code="TICK-101",
                customer_name="CloudNet Systems",
                subject="API Gateway Latency Spike",
                description="Experiencing intermittent 500ms delays on payments endpoint",
                priority="HIGH",
                status="OPEN"
            ),
            SupportTicket(
                ticket_code="TICK-102",
                customer_name="DataFlow Analytics",
                subject="SSO SAML configuration",
                description="Need assistance setting up Okta SAML integration",
                priority="MEDIUM",
                status="OPEN"
            ),
            SupportTicket(
                ticket_code="TICK-103",
                customer_name="Apex Logistics",
                subject="Database cluster failover error",
                description="Master replica failover triggered in eu-west-1",
                priority="CRITICAL",
                status="OPEN"
            )
        ]
        db.add_all(tickets)
        db.commit()

    # 6. Seed Inventory Items
    if db.query(InventoryItem).count() == 0:
        inventory = [
            InventoryItem(
                sku="HW-GPU-800",
                product_name="NVIDIA H100 Tensor Core GPU",
                category="Compute",
                current_stock=2,
                reorder_threshold=5,
                unit_price=30000.00,
                status="LOW_STOCK"
            ),
            InventoryItem(
                sku="HW-SRV-200",
                product_name="Enterprise 2U Rack Server",
                category="Infrastructure",
                current_stock=4,
                reorder_threshold=10,
                unit_price=4500.00,
                status="LOW_STOCK"
            ),
            InventoryItem(
                sku="HW-SW-100",
                product_name="100GbE Managed Top-of-Rack Switch",
                category="Networking",
                current_stock=18,
                reorder_threshold=8,
                unit_price=2200.00,
                status="IN_STOCK"
            )
        ]
        db.add_all(inventory)
        db.commit()


def reset_database():
    """Drop and recreate all tables with fresh seed data."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    seed_database(db_session)
    db_session.close()
    print("AgentOS Sandbox Database initialized and seeded successfully.")
