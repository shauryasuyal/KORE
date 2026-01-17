from .orchestrator import Orchestrator

APPROVED_ROOT = r"C:\Users\Vedant\Desktop\MVK_ROOT_TEST"

def main():
    print("=== MVK-L3 (AI Mode) ===")

    orch = Orchestrator(APPROVED_ROOT)
    orch.run_ai_task()

if __name__ == "__main__":
    main()
