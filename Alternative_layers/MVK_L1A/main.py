# main.py
print(">>> MAIN.PY EXECUTED <<<")

from pathlib import Path
from .snapshot import build_snapshot
from .planner import generate_plan
from .rules import Rule
from .abort import MVKAbort


def run(approved_root: str, ruleset):
    try:
        snapshot = build_snapshot(Path(approved_root))
        plan = generate_plan(snapshot, ruleset)
        return plan
    except MVKAbort as e:
        return {
            "aborted": True,
            "reason": e.reason
        }


if __name__ == "__main__":
    # TEMPORARY test harness (safe)
    APPROVED_ROOT = r"C:\Users\Vedant\Desktop\MVK_TEST_ROOT"

    RULESET = [
        Rule(
            rule_id="pdf_docs",
            extension=[".pdf"],
            path_prefix=APPROVED_ROOT,
            target="Documents/PDF"
        ),
    ]

    result = run(APPROVED_ROOT, RULESET)
    print(result)
