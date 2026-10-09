"""
CentraWorker - Interactive CLI Demo Runner.
Demonstrates autonomous execution, failure recovery, outcome verification,
and human-in-the-loop approvals.
"""

from __future__ import annotations
import sys
import os
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from centra_worker import AutonomousAgent, TaskRequest, TaskStatus
from simulated_company.erp_server import erp_db

console = Console()


def print_banner():
    banner = """
   ______           __             _       __           __             
  / ____/__  ____  / /__________ _/ /_  __/_/____  _____/ /_____  _____
 / /   / _ \\/ __ \\/ __/ ___/ __ `/ / / / / / __ \\/ ___/ //_/ _ \\/ ___/
/ /___/  __/ / / / /_/ /  / /_/ / / /_/ / / /_/ / /  / ,< /  __/ /    
\\____/\\___/_/ /_/\\__/_/   \\__,_/_/\\__,_/_/\\____/_/  /_/|_|\\___/_/     
   Autonomous AI Task Worker Prototype • CentrAlign AI Challenge
    """
    console.print(Panel(banner, style="bold cyan", border_style="bright_blue"))


def step_event_listener(event: dict):
    event_type = event.get("type")

    if event_type == "agent_thought":
        step_num = event.get("step")
        thought = event.get("thought")
        tool = event.get("tool_name")
        tool_input = event.get("tool_input")

        console.print(f"\n[bold yellow]▶ Step {step_num} Reasoning:[/bold yellow] [italic]{thought}[/italic]")
        if tool:
            console.print(f"  [bold cyan]Action:[/bold cyan] Calling tool [bold green]{tool}[/bold green] with parameters: {tool_input}")

    elif event_type == "failure_detected":
        tool = event.get("tool")
        err = event.get("error")
        rec = event.get("recovery_plan", {})
        console.print(Panel(
            f"[bold red]⚠ FAILURE DETECTED in tool '{tool}':[/bold red]\n{err}\n\n"
            f"[bold yellow]Autonomous Recovery Strategy:[/bold yellow] {rec.get('message')}",
            title="Self-Correction Engine",
            border_style="red"
        ))

    elif event_type == "step_completed":
        status = event.get("status")
        tool = event.get("tool_name")
        color = "green" if status in ("SUCCESS", "RECOVERED") else "yellow"
        console.print(f"  [bold {color}]✔ Observation ({status}):[/bold {color}] Tool {tool} completed.")


def display_results(result):
    console.print("\n" + "="*80 + "\n")
    if result.status == TaskStatus.WAITING_FOR_APPROVAL:
        app = result.pending_approval or {}
        console.print(Panel(
            f"[bold yellow]⏸ HUMAN APPROVAL REQUIRED[/bold yellow]\n\n"
            f"• Request ID: [bold]{app.get('approval_id')}[/bold]\n"
            f"• Action: [bold]{app.get('tool_name')}[/bold]\n"
            f"• Risk Level: [bold red]{app.get('risk_level')}[/bold red]\n"
            f"• Reason: {app.get('risk_reason')}\n"
            f"• Payload: {app.get('pending_payload')}",
            title="Human-in-the-Loop Safety Gate",
            border_style="yellow"
        ))
        return

    # Completion Card
    status_color = "bold green" if result.status == TaskStatus.COMPLETED else "bold red"
    console.print(Panel(
        f"[{status_color}]Task Status: {result.status.value}[/{status_color}]\n\n"
        f"{result.summary}\n\n"
        f"[dim]Total Steps Executed: {result.steps_executed} | Execution Time: {result.total_time_seconds}s[/dim]",
        title="Execution Summary",
        border_style="green" if result.status == TaskStatus.COMPLETED else "red"
    ))

    # Evidence Card
    if result.evidence:
        ev = result.evidence
        table = Table(title="Independent Ground-Truth Verification Receipt", box=box.ROUNDED)
        table.add_column("Attribute", style="cyan")
        table.add_column("Verified Value", style="white")

        table.add_row("Outcome Verified?", f"[bold green]{ev.verified}[/bold green]" if ev.verified else "[bold red]False[/bold red]")
        table.add_row("CentraERP Record ID", str(ev.record_id))
        table.add_row("Invoice Number", str(ev.invoice_number))
        table.add_row("Vendor Name", str(ev.vendor_name))
        table.add_row("Amount Verified", f"${ev.amount:,.2f} {ev.currency}" if ev.amount else "N/A")
        table.add_row("Due Date Verified", str(ev.due_date))
        table.add_row("Verification Token", str(ev.verification_hash))
        table.add_row("Timestamp", str(ev.verified_at))
        table.add_row("Audit Notes", str(ev.audit_notes))
        console.print(table)


def run_scenario(scenario_num: int):
    erp_db.reset()
    agent = AutonomousAgent(step_callback=step_event_listener)

    if scenario_num == 1:
        # Prompt from evaluation problem statement
        goal = "Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done."
        console.print(f"[bold magenta]▶ Executing Scenario 1 (Problem Statement Standard):[/bold magenta] \"{goal}\"")
        req = TaskRequest(goal=goal, auto_approve_high_risk=True)
        res = agent.run(req)
        display_results(res)

    elif scenario_num == 2:
        # Failure Recovery (Transient 503)
        goal = "Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done."
        console.print(f"[bold magenta]▶ Executing Scenario 2 (Fault Injection & Self-Correction):[/bold magenta]")
        console.print("[dim]Injecting transient 503 gateway failure into CentraERP on first attempt...[/dim]")
        req = TaskRequest(goal=goal, simulate_fault=True, auto_approve_high_risk=True)
        res = agent.run(req)
        display_results(res)

    elif scenario_num == 3:
        # Human in the loop approval gate
        goal = "Process invoice for Nexus Technologies high value hardware from simulated_company/data_store/files/invoices/INV-2024-099_NexusTech_HighValue.txt and enter into ERP."
        console.print(f"[bold magenta]▶ Executing Scenario 3 (Human-in-the-Loop High-Risk Approval):[/bold magenta]")
        req = TaskRequest(goal=goal, auto_approve_high_risk=False)
        res = agent.run(req)
        display_results(res)

        if res.status == TaskStatus.WAITING_FOR_APPROVAL:
            approved = Confirm.ask("Do you want to authorize this high-value disbursement as Finance Director?", default=True)
            resume_res = agent.resume_with_approval(
                approval_id=res.pending_approval["approval_id"],
                approved=approved,
                approver="Finance Director Marcus",
                feedback="Authorized under Capital IT Budget" if approved else "Rejected - exceeds Q3 limit"
            )
            display_results(resume_res)

    elif scenario_num == 4:
        # Browser Web Form Automation
        goal = "Use browser automation on internal web portal to enter the latest Company X invoice."
        console.print(f"[bold magenta]▶ Executing Scenario 4 (Browser Automation & Web Portal Form Entry):[/bold magenta]")
        req = TaskRequest(goal=goal, auto_approve_high_risk=True)
        res = agent.run(req)
        display_results(res)

    elif scenario_num == 5:
        # Custom Goal
        custom_goal = Prompt.ask("Enter custom natural language task")
        if custom_goal.strip():
            req = TaskRequest(goal=custom_goal, auto_approve_high_risk=True)
            res = agent.run(req)
            display_results(res)


def main():
    print_banner()
    while True:
        console.print("\n[bold cyan]Select Demonstration Scenario:[/bold cyan]")
        console.print("  [1] Standard Goal: Find latest Company X invoice, extract data, enter ERP & verify (Problem Statement)")
        console.print("  [2] Reliability & Recovery: Simulated 503 Gateway Failure with Exponential Backoff Self-Correction")
        console.print("  [3] Human-in-the-Loop Safety Gate: High-Value ($52,000) Invoice requiring interactive Sign-off")
        console.print("  [4] Browser Automation: Enter invoice via simulated company web portal HTML form")
        console.print("  [5] Custom Goal: Enter your own natural language instructions")
        console.print("  [q] Quit")

        choice = Prompt.ask("Your choice", choices=["1", "2", "3", "4", "5", "q"], default="1")
        if choice.lower() == "q":
            console.print("[green]Exiting CentraWorker demo. Good luck with the submission![/green]")
            break
        try:
            run_scenario(int(choice))
        except Exception as e:
            console.print(f"[bold red]Execution error: {e}[/bold red]")


if __name__ == "__main__":
    main()
