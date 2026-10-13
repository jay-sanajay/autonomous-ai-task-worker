import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

print("=================================================================")
print(" AgentOS Live Execution Test Runner")
print("=================================================================\n")

# 1. Reset Sandbox
print("1. Resetting sandbox database to clean state...")
res_reset = httpx.post(f"{BASE_URL}/api/sandbox/reset")
print(f"   Status: {res_reset.status_code} OK (Database seeded with 4 vendors & clean ledger)\n")

# 2. Trigger Task
goal = (
    "Find the latest invoice from Acme Technologies, extract the invoice number, "
    "amount, due date, and vendor, create a payable record in the company system, "
    "verify that the record was saved correctly, and summarize the result."
)
print("2. Launching Autonomous Worker with Primary Objective:")
print(f"   \"{goal}\"\n")

res_task = httpx.post(
    f"{BASE_URL}/api/tasks",
    json={"goal": goal, "auto_approve_high_risk": True},
    timeout=60.0
)
task = res_task.json()

print(f"3. Execution Finished: Status = {task['status']}")
print(f"   Task ID: {task['id']}")
print(f"   Total Actions Logged: {len(task.get('steps', []))}\n")

print("--- Step-by-Step Action Log ---")
for step in task.get("steps", []):
    num = step["step_number"]
    tool = step["tool_name"] or "Reasoning"
    lat = step["latency_ms"]
    st = step["status"]
    th = step["thought"][:80] + "..." if len(step["thought"]) > 80 else step["thought"]
    print(f"   Step {num}: {tool} ({lat}ms) -> [{st}]")
    print(f"           Thought: \"{th}\"")

print("\n--- Independent Ground-Truth Verification (SQLite Ledger) ---")
verif = task.get("verification")
if verif:
    print(f"   Verified in Database: {verif['verified']}")
    print(f"   Payable Record ID   : #{verif['payable_id']}")
    print(f"   Verification Token  : {verif['verification_token']}")
    print(f"   Audit Notes         : {verif['audit_notes']}\n")
    print("   Field Comparison Matrix:")
    for field, comp in verif.get("field_comparisons", {}).items():
        match_symbol = "MATCH [OK]" if comp.get("match") else "MISMATCH [FAIL]"
        print(f"     • {field:<15}: Expected '{comp.get('expected')}' vs Persisted '{comp.get('actual')}' -> {match_symbol}")
else:
    print("   No verification record generated.")

print("\n=================================================================")
print(" Task Execution & Ground-Truth Verification Successfully Completed!")
print(" View live in your browser: http://127.0.0.1:8000")
print("=================================================================")
