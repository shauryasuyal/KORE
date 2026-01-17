import os
import json
import shutil
import time
from pathlib import Path

# -----------------------------
# Exceptions
# -----------------------------

class TransactionAbort(Exception):
    pass

# -----------------------------
# Forbidden system paths
# -----------------------------

FORBIDDEN_PATH_PREFIXES = [
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/System32"),
    Path("C:/$Recycle.Bin"),
    Path("C:/System Volume Information"),
]

# -----------------------------
# Plan Validator
# -----------------------------

class PlanValidator:
    def __init__(self, approved_root: str):
        self.root = Path(approved_root).resolve()

    def validate(self, plan: dict):
        if plan.get("aborted"):
            raise TransactionAbort("Plan is aborted")

        if "operations" not in plan or not isinstance(plan["operations"], list):
            raise TransactionAbort("Invalid plan format")

        seen_destinations = set()

        for i, op in enumerate(plan["operations"]):
            if "source" not in op or "destination" not in op:
                raise TransactionAbort(f"Invalid operation at index {i}")

            src = Path(op["source"]).resolve()
            dst = Path(op["destination"]).resolve()

            # Must be absolute
            if not src.is_absolute() or not dst.is_absolute():
                raise TransactionAbort("Paths must be absolute")

            # Must be inside approved root
            if self.root not in src.parents and src != self.root:
                raise TransactionAbort("Source escapes approved root")

            if self.root not in dst.parents and dst != self.root:
                raise TransactionAbort("Destination escapes approved root")

            # No identical source/destination
            if src == dst:
                raise TransactionAbort("Source and destination are identical")

            # No overwriting same destination
            if str(dst) in seen_destinations:
                raise TransactionAbort("Two operations target same destination")

            seen_destinations.add(str(dst))

# -----------------------------
# Safety Gatekeeper
# -----------------------------

class SafetyGatekeeper:
    def check_path(self, p: Path):
        for forbidden in FORBIDDEN_PATH_PREFIXES:
            try:
                f = forbidden.resolve()
            except Exception:
                continue

            if p == f or f in p.parents:
                raise TransactionAbort(f"Forbidden system path touched: {p}")

    def check_plan(self, plan: dict):
        for op in plan["operations"]:
            src = Path(op["source"]).resolve()
            dst = Path(op["destination"]).resolve()
            self.check_path(src)
            self.check_path(dst)

# -----------------------------
# Audit Logger (append-only)
# -----------------------------

class AuditLogger:
    def __init__(self, path="mvk_audit_log.jsonl"):
        self.path = path

    def log(self, record: dict):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

# -----------------------------
# Executor
# -----------------------------

class Executor:
    def execute_move(self, src: Path, dst: Path):
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Prepare undo info
        undo = {
            "type": "MOVE",
            "from": str(dst),
            "to": str(src),
        }

        shutil.move(str(src), str(dst))
        return undo

# -----------------------------
# Rollback Engine
# -----------------------------

class RollbackEngine:
    def rollback(self, undo_stack):
        for undo in reversed(undo_stack):
            if undo["type"] == "MOVE":
                src = Path(undo["from"])
                dst = Path(undo["to"])

                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))

# -----------------------------
# Transaction Controller
# -----------------------------

class TransactionController:
    def __init__(self, approved_root: str, plan: dict):
        self.approved_root = approved_root
        self.plan = plan

        self.validator = PlanValidator(approved_root)
        self.safety = SafetyGatekeeper()
        self.logger = AuditLogger()
        self.executor = Executor()
        self.rollback_engine = RollbackEngine()

    def execute(self):
        # 1. Validate
        self.validator.validate(self.plan)

        # 2. Safety check
        self.safety.check_plan(self.plan)

        undo_stack = []

        try:
            # 3. Execute operations
            for idx, op in enumerate(self.plan["operations"]):
                src = Path(op["source"]).resolve()
                dst = Path(op["destination"]).resolve()

                # Log PENDING
                self.logger.log({
                    "plan_id": self.plan.get("plan_id"),
                    "index": idx,
                    "source": str(src),
                    "destination": str(dst),
                    "timestamp": time.time(),
                    "status": "PENDING"
                })

                # Execute (MOVE only for now)
                undo = self.executor.execute_move(src, dst)
                undo_stack.append(undo)

                # Log DONE
                self.logger.log({
                    "plan_id": self.plan.get("plan_id"),
                    "index": idx,
                    "status": "DONE"
                })

            # 4. Commit success
            return True

        except Exception as e:
            # 5. Rollback everything
            self.rollback_engine.rollback(undo_stack)

            # Log failure
            self.logger.log({
                "plan_id": self.plan.get("plan_id"),
                "status": "FAILED",
                "error": str(e)
            })

            raise
