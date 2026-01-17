from MVK_L1A.main import run as run_l1a
from MVK_L1A.rules import Rule
from MVK_L1B.main import run as run_l1b

APPROVED_ROOT = r"C:\Users\Vedant\Desktop\MVK_ROOT_TEST"

RULESET = [
    Rule(
        rule_id="pdf_docs",
        extension=[".pdf"],
        path_prefix=APPROVED_ROOT,
        target="Documents/PDF"
    ),
    Rule(
        rule_id="text_docs",
        extension=[".txt"],
        path_prefix=APPROVED_ROOT,
        target="Documents/Text"
    ),
]

def main():
    print("=== STEP 1: Running MVK-L1A (Planner) ===")
    plan = run_l1a(APPROVED_ROOT, RULESET)

    # Safety check
    if plan.get("aborted"):
        print("❌ Plan aborted by L1A:", plan.get("reason"))
        return

    print("=== STEP 2: Showing plan preview ===")
    for op in plan["operations"]:
        print(f"MOVE: {op['source']} -> {op['destination']}")

    input("\nPress ENTER to execute, Ctrl+C to cancel...")

    print("=== STEP 3: Running MVK-L1B (Executor) ===")
    run_l1b(plan)

    print("✅ All done.")

if __name__ == "__main__":
    main()
