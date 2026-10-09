"""
AgentOS — Autonomous AI Task Worker
Interactive CLI Demo Runner

Demonstrates autonomous execution, failure recovery, idempotency,
independent SQLite ground-truth verification, and human-in-the-loop approvals.
"""

from __future__ import annotations
import sys
import os
import time

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from backend.app.database.session import SessionLocal, init_db
from backend.app.database.seed import seed_database, reset_database
from backend.app.database.models import AgentTask, TaskStep, PayableRecord, VerificationResult
from backend.app.agent.loop import AgentExecutionEngine
from backend.app.agent.state import TaskStatus

console = Console(highlight=False)


def print_banner():
    banner = """
   ___                    _    ____   _____ 
  / _ \\                  | |  / __ \\ / ____|
 / /_\\ \\ __ _  ___ _ __  | |_| |  | | (___  
 |  _  |/ _` |/ _ \\ '_ \\ | __| |  | |\\___ \\ 
 | | | | (_| |  __/ | | || |_| |__| |____) |
 \\_| |_/\\__, |\\___|_| |_| \\__|\\____/ |_____/ 
         __/ |                              
        |___/   Autonomous AI Task Worker
    "From instructions to verified outcomes."
    CentrAlign AI Engineering Intern Evaluation
"""
    console.print(Panel(banner, style="bold cyan", border_style="bright_blue"))


def display_task_trace(task_id: str, db):
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    if not task:
        console.print("[red]Task not found.[/red]")
        return

    steps = db.query(TaskStep).filter(TaskStep.task_id == task_id).order_by(TaskStep.step_number).all()
    console.print(f"\n[bold cyan]Execution Trace ({len(steps)} steps executed):[/bold cyan]")

    for step in steps:
        console.print(f"\n[bold yellow]>> Step {step.step_number} Reasoning:[/bold yellow] [italic]{step.thought}[/italic]")
        if step.tool_name:
            console.print(f"  [bold cyan]Action:[/bold cyan] Invoked [bold green]{step.tool_name}[/bold green] (latency: {step.latency_ms}ms)")
            if step.tool_input:
                console.print(f"  [dim]Input: {step.tool_input}[/dim]")
            if step.tool_output:
                console.print(f"  [dim]Output: {step.tool_output}[/dim]")
        
        if step.status == "FAILED":
            console.print(f"  [bold red][FAILED][/bold red] {step.error_message}")
        elif step.status == "RECOVERED":
            console.print(f"  [bold green][RECOVERED][/bold green] Retry succeeded via exponential backoff.")
        elif step.status == "WAITING_APPROVAL":
            console.print(f"  [bold yellow][PAUSED][/bold yellow] Waiting for human authorization.")
        else:
            console.print(f"  [bold green][{step.status}][/bold green]")

    # Summary Panel
    status_style = "bold green" if task.status == TaskStatus.COMPLETED.value else ("bold yellow" if task.status == TaskStatus.WAITING_FOR_APPROVAL.value else "bold red")
    console.print("\n" + "="*80)
    console.print(Panel(
        f"[{status_style}]Status: {task.status}[/{status_style}]\n\n"
        f"[bold]Summary:[/bold] {task.final_summary or task.error_message or 'In progress'}\n\n"
        f"[dim]Task ID: {task.id} | Steps: {task.steps_count} | Created: {task.created_at}[/dim]",
        title="AgentOS Execution Summary",
        border_style="green" if task.status == TaskStatus.COMPLETED.value else "yellow"
    ))

    # Evidence Verification Card
    verif = db.query(VerificationResult).filter(VerificationResult.task_id == task_id).first()
    if verif:
        table = Table(title="Independent Ground-Truth Verification Receipt", box=box.ROUNDED)
        table.add_column("Attribute", style="cyan")
        table.add_column("Verified Value", style="white")

        table.add_row("SQLite Verified?", f"[bold green]{verif.verified}[/bold green]" if verif.verified else "[bold red]False[/bold red]")
        table.add_row("Payable Record ID", str(verif.payable_id or "N/A"))
        table.add_row("Cryptographic Token", str(verif.verification_token or "N/A"))
        table.add_row("Audit Notes", str(verif.audit_notes or "N/A"))
        table.add_row("Timestamp", str(verif.created_at))

        if verif.field_comparisons:
            for k, comp in verif.field_comparisons.items():
                match = comp.get("match", False)
                symbol = "[green][MATCH][/green]" if match else "[red][MISMATCH][/red]"
                table.add_row(f"Field: {k}", f"Extracted: '{comp.get('extracted')}' vs DB: '{comp.get('persisted')}' ({symbol})")

        console.print(table)


def run_scenario(choice: int):
    # Ensure fresh DB state for scenario
    reset_database()

    engine = AgentExecutionEngine()

    if choice == 1:
        goal = (
            "Find the latest invoice from Acme Technologies, extract the invoice number, amount, "
            "due date, and vendor, create a payable record in the company system, verify that the "
            "record was saved correctly, and summarize the result."
        )
        console.print(f"\n[bold magenta]>> Running Scenario 1 (Primary Acme Workflow):[/bold magenta]\n[italic]{goal}[/italic]\n")
        with SessionLocal() as db:
            task = engine.run(db_session=db, goal=goal, auto_approve_high_risk=True)
            display_task_trace(task.id, db)

    elif choice == 2:
        goal = "Process latest invoice from Acme Technologies and register as payable."
        console.print(f"\n[bold magenta]>> Running Scenario 2 (Transient 503 Fault & Auto-Recovery):[/bold magenta]")
        console.print("[dim]Simulating 503 Service Unavailable on first tool call attempt...[/dim]\n")
        with SessionLocal() as db:
            task = engine.run(db_session=db, goal=goal, auto_approve_high_risk=True, simulate_fault=True)
            display_task_trace(task.id, db)

    elif choice == 3:
        goal = "Process high value invoice INV-2024-099 from Nexus Hardware Systems ($48,500.00)."
        console.print(f"\n[bold magenta]>> Running Scenario 3 (Human-in-the-Loop Safety Gate):[/bold magenta]\n")
        with SessionLocal() as db:
            task = engine.run(db_session=db, goal=goal, auto_approve_high_risk=False)
            display_task_trace(task.id, db)

            if task.status == TaskStatus.WAITING_FOR_APPROVAL.value:
                console.print("\n[bold yellow]Safety Rule Triggered: Transaction exceeds $10,000 disbursement threshold.[/bold yellow]")
                approved = Confirm.ask("Authorize this high-value payment as Finance Director?", default=True)
                feedback = Prompt.ask("Approval Audit Note", default="Authorized under Q4 Infrastructure Expansion")

                res2 = engine.resume_task(
                    db_session=db,
                    task_id=task.id,
                    approved=approved,
                    approver="Finance Director Marcus (CLI)",
                    feedback=feedback
                )
                console.print("\n[bold cyan]Resuming AgentOS Execution Loop...[/bold cyan]")
                display_task_trace(task.id, db)

    elif choice == 4:
        goal = "Process old invoice INV-2023-042 from Acme Technologies and register as payable."
        console.print(f"\n[bold magenta]>> Running Scenario 4 (Idempotency & Duplicate Prevention):[/bold magenta]\n")
        with SessionLocal() as db:
            task = engine.run(db_session=db, goal=goal, auto_approve_high_risk=True)
            display_task_trace(task.id, db)

    elif choice == 5:
        goal = "Process invoice INV-2024-002 from Acme Technologies and register as payable."
        console.print(f"\n[bold magenta]>> Running Scenario 5 (Missing Field Safety - No Hallucination):[/bold magenta]\n")
        with SessionLocal() as db:
            task = engine.run(db_session=db, goal=goal, auto_approve_high_risk=True)
            display_task_trace(task.id, db)

    elif choice == 6:
        custom_goal = Prompt.ask("\nEnter custom natural language instructions")
        if custom_goal.strip():
            with SessionLocal() as db:
                task = engine.run(db_session=db, goal=custom_goal, auto_approve_high_risk=True)
                display_task_trace(task.id, db)


def main():
    print_banner()
    while True:
        console.print("\n[bold cyan]Select Demonstration Scenario:[/bold cyan]")
        console.print("  [1] Primary Acme Workflow: Find latest invoice, extract data, enter ERP & verify (Core Problem Statement)")
        console.print("  [2] Reliability & Recovery: Simulated 503 Transient Failure with Exponential Backoff Self-Correction")
        console.print("  [3] Human-in-the-Loop Gate: High-Value ($48,500.00) Invoice requiring interactive Sign-off")
        console.print("  [4] Idempotency Guarantee: Duplicate invoice detection & database constraint protection")
        console.print("  [5] Missing Field Safety: Unextractable amount detected without hallucinating values")
        console.print("  [6] Custom Goal: Enter your own natural language instructions")
        console.print("  [q] Quit")

        choice = Prompt.ask("Your choice", choices=["1", "2", "3", "4", "5", "6", "q"], default="1")
        if choice.lower() == "q":
            console.print("[green]Exiting AgentOS. Ready for evaluation![/green]")
            break
        try:
            run_scenario(int(choice))
        except Exception as e:
            console.print(f"[bold red]Execution error: {e}[/bold red]")


if __name__ == "__main__":
    main()
