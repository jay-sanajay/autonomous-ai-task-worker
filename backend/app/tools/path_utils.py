"""
AgentOS - Universal Sandbox File Path Resolver.
Cleans raw LLM outputs, extracts file paths from freeform prompt strings,
and resolves files across all sandbox directories (reports, uploads, csv, invoices, contracts, emails).
"""

from __future__ import annotations
import os
import re
import tempfile
from typing import Optional, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

CANDIDATE_SUBDIRS = ["reports", "uploads", "csv", "invoices", "contracts", "emails", "screenshots"]


def resolve_sandbox_file_path(path: str, default_sub: str = "") -> str:
    """
    Robustly resolve a file path in the sandbox repository.
    Handles:
    - Trailing prompt text: "sandbox_data/uploads/foo.md and summarize key findings." -> "sandbox_data/uploads/foo.md"
    - Mismatched directories: "sandbox_data/uploads/foo_report.md" -> "sandbox_data/reports/foo_report.md"
    - Space vs underscore slug variants: "foo (1).csv" vs "foo_(1).csv"
    - Absolute and relative paths
    - Temp directory fallbacks for read-only / serverless containers
    """
    if not path or not isinstance(path, str):
        if default_sub:
            return os.path.join(PROJECT_ROOT, "sandbox_data", default_sub)
        return PROJECT_ROOT

    cleaned = path.strip().strip("'\"`").rstrip(".").rstrip(",")

    # Extract actual path terminating at a valid file extension
    pat = r"((?:sandbox_data/[^,'\"\r\n]+?|[A-Za-z0-9_ .()-]+?)\.(?:txt|pdf|csv|json|md|log|tsv))"
    match = re.search(pat, cleaned, re.IGNORECASE)
    target = match.group(1).strip() if match else cleaned

    # 1. Direct absolute path
    if os.path.isabs(target) and os.path.exists(target):
        return target

    # 2. Relative to PROJECT_ROOT
    direct = os.path.normpath(os.path.join(PROJECT_ROOT, target))
    if os.path.exists(direct):
        return direct

    # 3. Base filename lookup across all candidate subdirs
    fn = os.path.basename(target)
    for sub in CANDIDATE_SUBDIRS:
        p1 = os.path.join(PROJECT_ROOT, "sandbox_data", sub, fn)
        if os.path.isfile(p1):
            return p1
        p2 = os.path.join(tempfile.gettempdir(), "agentos", "sandbox_data", sub, fn)
        if os.path.isfile(p2):
            return p2

    # 4. Fuzzy slug / space variants
    fn_variations = [
        fn.replace(" ", "_"),
        fn.replace("_", " "),
        fn.replace("_(1)_", " (1) "),
        fn.replace("_(1)_", " (1)_"),
        fn.replace(" (1) ", "_(1)_"),
        fn.replace(" (1)", "_(1)"),
        fn.replace("_(1)", " (1)"),
        fn.replace("__1", " (1)"),
        fn.replace(" (1)", "__1"),
    ]
    for sub in CANDIDATE_SUBDIRS:
        for alt in fn_variations:
            p1 = os.path.join(PROJECT_ROOT, "sandbox_data", sub, alt)
            if os.path.isfile(p1):
                return p1
            p2 = os.path.join(tempfile.gettempdir(), "agentos", "sandbox_data", sub, alt)
            if os.path.isfile(p2):
                return p2

    # 5. Check if default_sub has it directly
    if default_sub:
        p_def = os.path.join(PROJECT_ROOT, "sandbox_data", default_sub, fn)
        if os.path.isfile(p_def):
            return p_def

    return direct
