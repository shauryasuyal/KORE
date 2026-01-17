import shutil
from pathlib import Path


class RollbackError(Exception):
    pass


class RollbackEngine:
    """
    Executes rollback actions in reverse order.
    Each rollback action is a dict produced by Executor.
    """

    def rollback_all(self, rollback_actions: list):
        """
        Roll back in reverse order.
        """
        for action in reversed(rollback_actions):
            self._execute_rollback(action)

    def _execute_rollback(self, action: dict):
        action_type = action.get("type")

        if action_type == "MOVE":
            self._rb_move(action)

        elif action_type == "RENAME":
            self._rb_rename(action)

        elif action_type == "RMDIR":
            self._rb_rmdir(action)

        elif action_type == "DELETE_FILE_OR_DIR":
            self._rb_delete_file_or_dir(action)

        else:
            raise RollbackError(f"Unknown rollback action: {action_type}")

    # -------------------------
    # Individual rollback ops
    # -------------------------

    def _rb_move(self, action: dict):
        src = Path(action["source"])
        dst = Path(action["destination"])

        if not src.exists():
            raise RollbackError(f"Rollback MOVE failed, source missing: {src}")

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    def _rb_rename(self, action: dict):
        # RENAME rollback is just MOVE semantics
        self._rb_move(action)

    def _rb_rmdir(self, action: dict):
        target = Path(action["target"])

        if target.exists():
            target.rmdir()

    def _rb_delete_file_or_dir(self, action: dict):
        """
        This is used ONLY for rollback of COPY.
        """
        target = Path(action["target"])

        if not target.exists():
            return

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
