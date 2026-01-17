import shutil
from pathlib import Path


class ExecutionError(Exception):
    pass


class Executor:
    """
    Executes filesystem operations.
    DOES NOT decide safety.
    DOES NOT do logging.
    DOES NOT do rollback.
    Only executes one operation.
    """

    def execute(self, op: dict):
        op_type = op.get("type")

        if op_type == "MOVE":
            return self._move(op)

        elif op_type == "COPY":
            return self._copy(op)

        elif op_type == "RENAME":
            return self._rename(op)

        elif op_type == "MKDIR":
            return self._mkdir(op)

        else:
            raise ExecutionError(f"Unknown operation type: {op_type}")

    # -------------------------
    # Individual operations
    # -------------------------

    def _move(self, op: dict):
        src = Path(op["source"])
        dst = Path(op["destination"])

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

        # Rollback = move back
        return {
            "type": "MOVE",
            "source": str(dst),
            "destination": str(src),
        }

    def _copy(self, op: dict):
        src = Path(op["source"])
        dst = Path(op["destination"])

        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

        # Rollback = delete copied target
        return {
            "type": "DELETE_FILE_OR_DIR",
            "target": str(dst),
        }

    def _rename(self, op: dict):
        src = Path(op["source"])
        dst = Path(op["destination"])

        src.rename(dst)

        # Rollback = rename back
        return {
            "type": "RENAME",
            "source": str(dst),
            "destination": str(src),
        }

    def _mkdir(self, op: dict):
        dst = Path(op["destination"])

        dst.mkdir(parents=True, exist_ok=False)

        # Rollback = remove dir
        return {
            "type": "RMDIR",
            "target": str(dst),
        }
