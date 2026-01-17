# guards.py
# MVK-L1A — Hard boundary & forbidden path enforcement
# SECURITY-CRITICAL MODULE

from pathlib import Path
from .abort import abort


# -----------------------------
# Hard-forbidden system paths
# -----------------------------

FORBIDDEN_PATH_PREFIXES = [
    # Windows
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/System Volume Information"),
    Path("C:/$Recycle.Bin"),

    # Linux
    Path("/boot"),
    Path("/sys"),
    Path("/proc"),
    Path("/dev"),
    Path("/lib"),
    Path("/usr"),
    Path("/etc"),

    # macOS
    Path("/System"),
    Path("/Library"),
    Path("/Applications"),
    Path("/Volumes"),
]


# -----------------------------
# Guard function
# -----------------------------

def assert_path_allowed(root: Path) -> None:
    """
    HARD FAIL if approved root is inside or equal to
    any forbidden system directory.
    """

    if not isinstance(root, Path):
        abort("Root is not a Path object")

    try:
        resolved = root.resolve(strict=True)
    except Exception:
        abort("Failed to resolve approved root")

    for forbidden in FORBIDDEN_PATH_PREFIXES:
        try:
            forbidden_resolved = forbidden.resolve(strict=False)
        except Exception:
            continue

        # root == forbidden OR root inside forbidden
        if resolved == forbidden_resolved or forbidden_resolved in resolved.parents:
            abort(f"Approved root is forbidden system path: {resolved}")

    # If we reach here → root is allowed
    return
