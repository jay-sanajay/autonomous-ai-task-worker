from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class VendorResponse(BaseModel):
    id: int
    vendor_code: str
    name: str
    aliases: Optional[str] = None
    payment_terms: str
    category: str
    status: str
    created_at: datetime


class InvoiceDocResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_type: str
    file_size_bytes: int
    vendor_name_hint: Optional[str] = None
    is_latest_for_vendor: bool
    created_at: datetime
