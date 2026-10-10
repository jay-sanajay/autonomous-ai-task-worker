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
        "Perform structured Pandas calculations on any CSV dataset: "
        "automatically detects primary metrics (Revenue, Budget, Amount, Value, Score), "
        "ranks top records by the detected primary metric, and computes summary statistics."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Relative path to CSV file"},
            "top_n": {"type": "integer", "description": "Number of top records to rank", "default": 5},
            "metric_column": {"type": "string", "description": "Optional specific column name to analyze/rank"}
        },
        "required": ["file_path"]
    }

    def execute(self, db_session: Session, file_path: str, top_n: int = 5, metric_column: Optional[str] = None) -> ToolResult:
        full_path = os.path.join(PROJECT_ROOT, file_path) if not os.path.isabs(file_path) else file_path
        if not os.path.exists(full_path):
            return ToolResult(success=False, error=f"CSV file '{file_path}' does not exist.", retryable=False)

        try:
            df = pd.read_csv(full_path)
            if df.empty:
                return ToolResult(success=False, error="CSV file is empty.", retryable=False)

            # 1. Identify primary numeric metric column
            target_metric = None
            if metric_column and metric_column in df.columns:
                target_metric = metric_column
            else:
                candidates = [
                    "Revenue", "Budget (INR)", "Budget", "Amount", "Total", "Price",
                    "Units_Sold", "Score", "Value", "Cost", "Sales"
                ]
                for c in candidates:
                    for col in df.columns:
                        if c.lower() == col.lower() or c.lower() in col.lower():
                            converted = pd.to_numeric(
                                df[col].astype(str).str.replace(r"[^\d.-]", "", regex=True),
                                errors="coerce"
                            )
                            if converted.notnull().sum() > 0:
                                target_metric = col
                                df[col] = converted
                                break
                    if target_metric:
                        break

            # Fallback: find any numeric column with variation
            if not target_metric:
                for col in df.columns:
                    converted = pd.to_numeric(
                        df[col].astype(str).str.replace(r"[^\d.-]", "", regex=True),
                        errors="coerce"
                    )
                    if converted.notnull().sum() > 0 and converted.nunique() > 1:
                        target_metric = col
                        df[col] = converted
                        break

            # 2. Identify entity / name column
            name_candidates = ["Product", "Name", "Lead", "Customer", "Item", "Title", "Company"]
            entity_col = None
            for nc in name_candidates:
                for col in df.columns:
                    if nc.lower() in col.lower():
                        entity_col = col
                        break
                if entity_col:
                    break
            if not entity_col:
                entity_col = df.columns[0]

            # 3. Identify category / group column
            cat_candidates = ["Category", "Location", "Region", "Priority", "Status", "Intent", "Department"]
            group_col = None
            for gc in cat_candidates:
                for col in df.columns:
                    if gc.lower() in col.lower() and col != entity_col:
                        group_col = col
                        break
                if group_col:
                    break

            # Compute statistics
            if target_metric:
                df[target_metric] = pd.to_numeric(df[target_metric], errors="coerce").fillna(0)
                total_metric = float(df[target_metric].sum())
                avg_metric = float(df[target_metric].mean())
                sorted_df = df.sort_values(by=target_metric, ascending=False).head(top_n)
            else:
                total_metric = float(len(df))
                avg_metric = 1.0
                sorted_df = df.head(top_n)

            # Build top records
            top_records = []
            for _, row in sorted_df.iterrows():
                val = float(row.get(target_metric, 0)) if target_metric else 1.0
                rec = {
                    "Product": str(row.get(entity_col, "Unknown")),
                    "Entity_Name": str(row.get(entity_col, "Unknown")),
                    "Category": str(row.get(group_col, "General")) if group_col else "General",
                    "Metric_Name": target_metric or "Records",
                    "Metric_Value": val,
                    "Revenue": val
                }
                if "Units_Sold" in df.columns:
                    rec["Units_Sold"] = int(row.get("Units_Sold", 0))
                top_records.append(rec)

            # Group breakdown
            breakdown = {}
            if group_col and target_metric:
                breakdown = df.groupby(group_col)[target_metric].sum().to_dict()
            elif group_col:
                breakdown = df[group_col].value_counts().to_dict()

            return ToolResult(
                success=True,
                data={
                    "file_path": file_path,
                    "target_metric": target_metric or "Row Count",
                    "entity_column": entity_col,
                    "group_column": group_col,
                    "total_metric_value": total_metric,
                    "total_revenue": total_metric,
                    "average_revenue": avg_metric,
                    "top_products": top_records,
                    "regional_breakdown": breakdown,
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
