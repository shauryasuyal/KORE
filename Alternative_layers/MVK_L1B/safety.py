import os

FORBIDDEN = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\System32",
    r"C:\System Volume Information",
    r"C:\$Recycle.Bin"
]

class SafetyGatekeeper:
    def __init__(self, mvk_root: str):
        self.mvk_root = os.path.realpath(mvk_root)

    def _is_inside_root(self, path: str) -> bool:
        return os.path.commonpath([path, self.mvk_root]) == self.mvk_root

    def _is_forbidden(self, path: str) -> bool:
        for bad in FORBIDDEN:
            bad_real = os.path.realpath(bad)
            if path.startswith(bad_real):
                return True
        return False

    def check_plan(self, plan: dict):
        for op in plan["operations"]:
            src = os.path.realpath(op["source"])
            dst = os.path.realpath(op["destination"])

            if self._is_forbidden(src) or self._is_forbidden(dst):
                raise RuntimeError("Forbidden system path detected.")

            if not self._is_inside_root(src) or not self._is_inside_root(dst):
                raise RuntimeError("Path escapes MVK approved root.")
