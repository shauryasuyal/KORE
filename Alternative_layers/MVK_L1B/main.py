import json
from MVK_L1B.transaction import TransactionController

# You MUST pass the same root used by MVK-L1A
MVK_ROOT = r"C:\Users\Vedant\Desktop\MVK_ROOT_TEST"

def run(plan: dict):
    controller = TransactionController(
        MVK_ROOT,
        plan
    )
    controller.execute()

if __name__ == "__main__":
    # Example: load plan produced by MVK-L1A
    with open("plan.json", "r") as f:
        plan = json.load(f)

    run(plan)

