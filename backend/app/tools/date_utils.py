"""
AgentOS - Real-time 2026 Date Utility.
Ensures all business workflow dates (invoices, payables, schedules, task items)
strictly adhere to the current real-time 2026 calendar, with due dates guaranteed
to be on or after the issue/current date.
"""

from __future__ import annotations
import re
from datetime import datetime, timezone, timedelta
from typing import Optional


IST_TZ = timezone(timedelta(hours=5, minutes=30), name="IST")


def get_current_realtime_date() -> datetime:
    """Return current Indian Standard Time (IST, UTC+05:30) datetime shifted to year 2026 or later."""
    now = datetime.now(IST_TZ)
    target_year = max(2026, now.year)
    try:
        return now.replace(year=target_year)
    except ValueError:
        # Handle leap year Feb 29 edge cases
        return now.replace(year=target_year, day=28)


def get_current_ist_str() -> str:
    """Return formatted IST timestamp string (e.g. '2026-10-14 02:20:00 IST')."""
    return get_current_realtime_date().strftime("%Y-%m-%d %H:%M:%S IST")


def get_realtime_date_str(days_offset: int = 0) -> str:
    """Return formatted YYYY-MM-DD date for 2026 in Indian Standard Time."""
    base = get_current_realtime_date()
    target = base + timedelta(days=days_offset)
    return target.strftime("%Y-%m-%d")


def sanitize_date_to_2026(
    date_str: Optional[str],
    min_date_str: Optional[str] = None,
    default_days_ahead: int = 0
) -> str:
    """
    Sanitize and enforce:
    1. Year >= 2026.
    2. Valid YYYY-MM-DD.
    3. If min_date_str is given (e.g. invoice issue date or today), date must be >= min_date_str.
    """
    today_str = get_realtime_date_str(0)
    baseline_min = min_date_str.strip() if min_date_str and len(min_date_str.strip()) >= 10 else today_str

    if not date_str or not str(date_str).strip():
        return get_realtime_date_str(default_days_ahead)

    cleaned = str(date_str).strip()
    # Replace any past years 2010-2025 with 2026
    cleaned = re.sub(r"\b20[0-2][0-5]\b", "2026", cleaned)

    match = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", cleaned)
    if match:
        y = max(2026, int(match.group(1)))
        m = max(1, min(12, int(match.group(2))))
        d = max(1, min(31, int(match.group(3))))
        try:
            parsed = datetime(y, m, d, tzinfo=timezone.utc)
            parsed_str = parsed.strftime("%Y-%m-%d")
            # If minimum date constraint exists and parsed date is before min_date
            if baseline_min and parsed_str < baseline_min:
                try:
                    min_dt = datetime.strptime(baseline_min[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    parsed_str = (min_dt + timedelta(days=max(0, default_days_ahead))).strftime("%Y-%m-%d")
                except Exception:
                    parsed_str = baseline_min
            return parsed_str
        except ValueError:
            pass

    return get_realtime_date_str(default_days_ahead)


def sanitize_invoice_number(inv_num: str) -> str:
    """Sanitize invoice numbers like INV-2024-001 -> INV-2026-001."""
    if not inv_num:
        return "INV-2026-001"
    cleaned = inv_num.strip().upper()
    return re.sub(r"INV-202[0-5]-", "INV-2026-", cleaned)
