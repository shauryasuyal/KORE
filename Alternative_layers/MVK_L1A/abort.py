# abort.py

class MVKAbort(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def abort(reason: str) -> None:
    """
    Immediately halts MVK-L1A execution.
    No cleanup, no filesystem access, no logging side effects.
    """
    raise MVKAbort(reason)
