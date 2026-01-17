# snapshot.py
# MVK-L1A — Read-only snapshot builder
# SECURITY-CRITICAL MODULE

from pathlib import Path
from dataclasses import dataclass
from typing import Tuple
import os
import uuid
import time

from .abort import abort
from .guards import assert_path_allowed


# -----------------------------
# Immutable data structures
# -----------------------------

@dataclass(frozen=True)
class FileMeta:
    abs_path: str
    size: int
    mtime: float
    extension: str


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    root: str
    created_at: float
    files: Tuple[FileMeta, ...]


# -----------------------------
# Snapshot builder
# -----------------------------

def build_snapshot(approved_root: Path) -> Snapshot:
    """
    Performs a SINGLE read-only scan of the approved root directory
    and returns an immutable snapshot of file metadata.

    HARD GUARANTEES:
    - No filesystem writes
    - No file contents read
    - No access outside approved root
    - Deterministic output
    """

    # Normalize & validate root
    if not isinstance(approved_root, Path):
        abort("Approved root is not a Path object")

    try:
        root = approved_root.resolve(strict=True)
    except Exception:
        abort("Approved root does not exist or cannot be resolved")

    assert_path_allowed(root)

    if not root.is_dir():
        abort("Approved root is not a directory")

    files = []

    # SINGLE filesystem traversal
    for path in root.rglob("*"):
        try:
            resolved = path.resolve(strict=True)
        except Exception:
            abort("Failed to resolve path during snapshot")

        # Boundary enforcement
        if root not in resolved.parents and resolved != root:
            abort("Path escaped approved root boundary")

        # Ignore directories
        if not resolved.is_file():
            continue

        # Collect metadata ONLY
        try:
            stat = resolved.stat()
        except Exception:
            abort("Failed to stat file during snapshot")

        extension = resolved.suffix.lower()  # ALWAYS instance-level

        files.append(
            FileMeta(
                abs_path=str(resolved),
                size=stat.st_size,
                mtime=stat.st_mtime,
                extension=extension
            )
        )

    # Freeze snapshot (immutability)
    return Snapshot(
        snapshot_id=str(uuid.uuid4()),
        root=str(root),
        created_at=time.time(),
        files=tuple(files)
    )
