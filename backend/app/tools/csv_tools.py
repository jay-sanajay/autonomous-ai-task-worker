"""
AgentOS - CSV Analysis and Report Generation Tools.
Performs data analysis with Pandas, calculates product rankings, and generates persistent reports.
"""

from __future__ import annotations
import os
import glob
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.tools.base import ControlledBaseTool, ToolResult

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CSV_DIR = os.path.join(PROJECT_ROOT, "sandbox_data", "csv")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "sandbox_data", "reports")


class ListCSVFilesTool(ControlledBaseTool):
    name = "list_csv_files"
    description = "List available CSV datasets in the repository, returning filenames, row counts, and column headers."
    parameters_schema = {
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Relative directory path (defaults to sandbox_data/csv)"}
        }
    }

    def execute(self, db_session: Session, directory: Optional[str] = None) -> ToolResult:
        target_dir = os.path.join(PROJECT_ROOT, directory) if directory else CSV_DIR
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        files = glob.glob(os.path.join(target_dir, "*.csv"))
        file_list = []
        for p in files:
            fn = os.path.basename(p)
            try:
                df = pd.read_csv(p)
                row_cnt = len(df)
                cols = list(df.columns)
            except Exception:
                row_cnt = 0
                cols = []

            file_list.append({
                "filename": fn,
                "path": os.path.relpath(p, PROJECT_ROOT).replace("\\", "/"),
                "size_bytes": os.path.getsize(p),
                "row_count": row_cnt,
                "columns": cols
            })

        return ToolResult(
            success=True,
            data={
                "directory": os.path.relpath(target_dir, PROJECT_ROOT).replace("\\", "/"),
                "count": len(file_list),
                "files": file_list
            }
        )



class InspectCSVTool(ControlledBaseTool):
    name = "inspect_csv"
    description = "Inspect CSV file structure: columns, row counts, data types, and check for missing values."
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Relative path to CSV file"}
        },
        "required": ["file_path"]
    }

    def execute(self, db_session: Session, file_path: str) -> ToolResult:
        full_path = os.path.join(PROJECT_ROOT, file_path) if not os.path.isabs(file_path) else file_path
        if not os.path.exists(full_path):
            return ToolResult(success=False, error=f"CSV file '{file_path}' does not exist.", retryable=False)

        try:
            df = pd.read_csv(full_path)
            missing = df.isnull().sum().to_dict()
            return ToolResult(
                success=True,
                data={
                    "file_path": file_path,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns),
                    "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "missing_values": missing,
                    "has_missing_data": sum(missing.values()) > 0
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Error reading CSV: {str(e)}", retryable=False)


class AnalyzeCSVTool(ControlledBaseTool):
    name = "analyze_csv"
    description = (
        "Perform structured Pandas calculations on sales data: "
        "identify top 5 products by revenue, regional breakdowns, and aggregate statistics."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Relative path to CSV file"},
            "top_n": {"type": "integer", "description": "Number of top records to rank", "default": 5}
        },
        "required": ["file_path"]
    }

    def execute(self, db_session: Session, file_path: str, top_n: int = 5) -> ToolResult:
        full_path = os.path.join(PROJECT_ROOT, file_path) if not os.path.isabs(file_path) else file_path
        if not os.path.exists(full_path):
            return ToolResult(success=False, error=f"CSV file '{file_path}' does not exist.", retryable=False)

        try:
            df = pd.read_csv(full_path)
            
            # Ensure Revenue column is numeric
            if "Revenue" in df.columns:
                df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce")
            elif "Units_Sold" in df.columns and "Unit_Price" in df.columns:
                df["Revenue"] = df["Units_Sold"] * df["Unit_Price"]

            total_revenue = float(df["Revenue"].sum())
            avg_revenue = float(df["Revenue"].mean())

            top_products = df.sort_values(by="Revenue", ascending=False).head(top_n)
            top_records = top_products[["Product", "Category", "Units_Sold", "Revenue"]].to_dict(orient="records")

            region_breakdown = df.groupby("Region")["Revenue"].sum().to_dict() if "Region" in df.columns else {}

            return ToolResult(
                success=True,
                data={
                    "total_revenue": total_revenue,
                    "average_revenue": avg_revenue,
                    "top_products": top_records,
                    "regional_breakdown": region_breakdown,
                    "record_count_analyzed": len(df)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"CSV analysis failed: {str(e)}", retryable=False)


class GenerateReportTool(ControlledBaseTool):
    name = "generate_report"
    description = "Generate and persist a structured markdown report file in the reports directory."
    parameters_schema = {
        "type": "object",
        "properties": {
            "report_title": {"type": "string", "description": "Title of the report"},
            "report_content": {"type": "string", "description": "Markdown formatted report content"},
            "filename": {"type": "string", "description": "Output report filename (e.g. sales_q3_report.md)"}
        },
        "required": ["report_title", "report_content"]
    }

    def execute(
        self,
        db_session: Session,
        report_title: str,
        report_content: str,
        filename: Optional[str] = None
    ) -> ToolResult:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        if not filename:
            filename = f"report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"

        report_path = os.path.join(REPORTS_DIR, filename)

        try:
            full_markdown = f"# {report_title}\n\n*Generated by AgentOS Autonomous Worker on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n---\n\n{report_content}\n"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(full_markdown)

            rel_path = os.path.relpath(report_path, PROJECT_ROOT).replace("\\", "/")
            return ToolResult(
                success=True,
                data={
                    "file_path": rel_path,
                    "report_title": report_title,
                    "file_size_bytes": os.path.getsize(report_path),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "message": f"Successfully generated report at '{rel_path}'."
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to generate report: {str(e)}", retryable=False)
