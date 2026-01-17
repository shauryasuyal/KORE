from pathlib import Path


def actions_to_operations(snapshot, actions, approved_root: str):
    """
    Converts high-level ACTIONS into concrete filesystem OPERATIONS.
    This does NOT touch the filesystem.
    This does NOT validate safety (L1B will).
    This only translates intent → plan.
    """

    ops = []
    root = Path(approved_root)

    for action in actions:
        t = action["type"]

        # =========================
        # MKDIR
        # =========================
        if t == "MKDIR":
            rel = action.get("path")
            if not rel:
                raise RuntimeError("MKDIR missing path")

            dst = root / rel

            ops.append({
                "type": "MKDIR",
                "destination": str(dst),
                "meta": {},
                "risk_flags": []
            })

        # =========================
        # MOVE / COPY
        # =========================
        elif t in ("MOVE", "COPY"):
            exts = action.get("ext")
            target = action.get("target")

            if not exts or not target:
                raise RuntimeError(f"{t} action missing ext or target")

            exts = [("." + e.lower().lstrip(".")) for e in exts]
            dst_dir = root / target

            for file in snapshot.files:
                if file.extension.lower() in exts:
                    src = Path(file.abs_path)
                    dst = dst_dir / src.name

                    ops.append({
                        "type": t,
                        "source": str(src),
                        "destination": str(dst),
                        "meta": {},
                        "risk_flags": []
                    })

        # =========================
        # RENAME
        # =========================
        elif t == "RENAME":
            old = action.get("from")
            new = action.get("to")

            if not old or not new:
                raise RuntimeError("RENAME missing from/to")

            src = root / old
            dst = root / new

            ops.append({
                "type": "RENAME",
                "source": str(src),
                "destination": str(dst),
                "meta": {},
                "risk_flags": []
            })

        else:
            raise RuntimeError(f"Unknown action type: {t}")

    return ops
