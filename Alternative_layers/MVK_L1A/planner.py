# planner.py
# MVK-L1A — Dry-run planner
# SECURITY-CRITICAL MODULE

from typing import List, Dict
from pathlib import Path
import uuid
import datetime

from .snapshot import Snapshot, FileMeta
from .rules import Rule, classify
from .abort import abort


def generate_plan(snapshot: Snapshot, rules: List[Rule]) -> Dict:
    """
    Generate a deterministic, read-only plan based on a snapshot.
    NO filesystem operations are performed.
    """

    operations = []

    for file_meta in snapshot.files:
        rule = classify(file_meta, rules)

        if rule is None:
            continue

        # Extract filename safely from absolute path
        filename = Path(file_meta.abs_path).name

        destination = str(
            Path(snapshot.root)
            / rule.target
            / filename
        )

        operations.append(
    {
        "type": "MOVE",
        "source": file_meta.abs_path,
        "destination": destination,
        "rule_id": rule.rule_id,
        "classification_reason": f"extension == {file_meta.extension}",
        "meta": {},
        "risk_flags": []
    }
)


    return {
        "plan_id": str(uuid.uuid4()),
        "snapshot_id": snapshot.snapshot_id,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "operations": operations,
        "aborted": False
    }
