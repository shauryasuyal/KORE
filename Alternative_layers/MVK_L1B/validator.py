import os

class PlanValidator:
    def __init__(self, mvk_root: str):
        self.mvk_root = os.path.realpath(mvk_root)

    def validate(self, plan: dict):
        if plan.get("aborted"):
            raise RuntimeError("Plan is aborted. Refusing to execute.")

        if "operations" not in plan:
            raise RuntimeError("Invalid plan format: missing operations.")

        seen_destinations = set()

        for op in plan["operations"]:
            src = os.path.realpath(op["source"])
            dst = os.path.realpath(op["destination"])

            if src == dst:
                raise RuntimeError("Source and destination are identical.")

            if op.get("risk_flags"):
                raise RuntimeError("Operation has risk flags. Refusing to execute.")

            if dst in seen_destinations:
                raise RuntimeError("Two operations target the same destination.")

            seen_destinations.add(dst)
