import os
from pathlib import Path
from MVK_L1A.main import run
from MVK_L1A.rules import Rule

RAW_ROOT = r"C:\Users\Vedant\Desktop\MVK_ROOT_TEST"

root_path = Path(RAW_ROOT)

if not root_path.exists():
    raise RuntimeError(f"Approved root does not exist: {root_path}")

APPROVED_ROOT = str(root_path.resolve())
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

result = run(APPROVED_ROOT, RULESET)
print(result)
