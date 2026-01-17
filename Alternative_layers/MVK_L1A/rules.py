# rules.py
# MVK-L1A — Deterministic rule engine
# SECURITY-CRITICAL MODULE

from dataclasses import dataclass
from typing import List, Optional
from .abort import abort
from .snapshot import FileMeta


@dataclass(frozen=True)
class Rule:
    rule_id: str
    extension: List[str]
    path_prefix: str
    target: str


def classify(file_meta: FileMeta, rules: List[Rule]) -> Optional[Rule]:
    """
    Deterministically classify a file using rule-based logic.
    Returns exactly one Rule or aborts on ambiguity.
    """

    matches = []

    for rule in rules:
        # Extension match (deterministic, exact)
        if file_meta.extension not in rule.extension:
            continue

        # Path boundary match (absolute, string-based)
        if not file_meta.abs_path.startswith(rule.path_prefix):
            continue

        matches.append(rule)

    if len(matches) == 0:
        return None

    if len(matches) > 1:
        abort(
            f"Ambiguous classification for file: {file_meta.abs_path}"
        )

    return matches[0]
