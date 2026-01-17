# snapshot_types.py

from dataclasses import dataclass
from typing import Tuple
from datetime import datetime


@dataclass(frozen=True)
class FileMeta:
    path: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    extension: str
    is_symlink: bool


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    root: str
    created_at: datetime
    files: Tuple[FileMeta, ...]
