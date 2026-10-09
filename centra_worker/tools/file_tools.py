from __future__ import annotations
import os
import glob
from typing import Dict, Any, List
from centra_worker.tools.base import BaseTool

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve_path(path: str) -> str:
    """Safely resolve path within the project workspace."""
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(PROJECT_ROOT, path))


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files in a directory to discover incoming documents, invoices, or records."
    parameters_schema = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Path to the directory, e.g. 'simulated_company/data_store/files/invoices'"
            },
            "pattern": {
                "type": "string",
                "description": "Optional glob pattern, e.g. '*.txt' or '*CompanyX*'",
                "default": "*"
            }
        },
        "required": ["directory"]
    }

    def run(self, directory: str, pattern: str = "*") -> Dict[str, Any]:
        target_dir = _resolve_path(directory)
        if not os.path.exists(target_dir):
            return {"status": "error", "error": f"Directory not found: {directory}"}
        if not os.path.isdir(target_dir):
            return {"status": "error", "error": f"Path is not a directory: {directory}"}

        matches = glob.glob(os.path.join(target_dir, pattern))
        results = []
        for p in matches:
            if os.path.isfile(p):
                stat = os.stat(p)
                results.append({
                    "filename": os.path.basename(p),
                    "path": os.path.relpath(p, PROJECT_ROOT).replace("\\", "/"),
                    "size_bytes": stat.st_size,
                    "modified_time": stat.st_mtime
                })
        return {
            "status": "success",
            "directory": directory,
            "count": len(results),
            "files": results
        }


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file (e.g. invoice, contract, email, JSON, CSV)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read, e.g. 'simulated_company/data_store/files/invoices/INV-2024-089_CompanyX_Latest.txt'"
            }
        },
        "required": ["file_path"]
    }

    def run(self, file_path: str) -> Dict[str, Any]:
        resolved = _resolve_path(file_path)
        if not os.path.exists(resolved):
            return {"status": "error", "error": f"File does not exist: {file_path}"}
        if not os.path.isfile(resolved):
            return {"status": "error", "error": f"Path is not a file: {file_path}"}

        try:
            with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {
                "status": "success",
                "file_path": file_path,
                "size_bytes": len(content),
                "content": content
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search across text files in a directory for specific keywords or vendor names."
    parameters_schema = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Directory to search within",
                "default": "simulated_company/data_store/files/invoices"
            },
            "query": {
                "type": "string",
                "description": "Text query or vendor name to search for, e.g. 'Company X'"
            }
        },
        "required": ["query"]
    }

    def run(self, query: str, directory: str = "simulated_company/data_store/files/invoices") -> Dict[str, Any]:
        target_dir = _resolve_path(directory)
        if not os.path.exists(target_dir):
            return {"status": "error", "error": f"Directory not found: {directory}"}

        hits = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                        if query.lower() in text.lower():
                            hits.append({
                                "filename": file,
                                "path": os.path.relpath(full_path, PROJECT_ROOT).replace("\\", "/"),
                                "snippet": text[:300] + ("..." if len(text) > 300 else "")
                            })
                except Exception:
                    pass

        return {
            "status": "success",
            "query": query,
            "total_matches": len(hits),
            "matches": hits
        }
