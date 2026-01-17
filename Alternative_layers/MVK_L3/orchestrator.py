from MVK_L1A.main import run as run_l1a
from MVK_L1B.main import run as run_l1b
from MVK_L1A.rules import Rule
from .ai_gemini import ask_gemini
from pathlib import Path


# =========================================================
# Backward-compatible: OLD MODE (targets -> rules -> MOVE)
# =========================================================

def rules_from_gemini(ai_result: dict, approved_root: str):
    """
    Convert Gemini's HIGH-LEVEL JSON output into MVK-L1A Rule objects.
    This is the OLD MODE: only MOVE operations.
    """

    rules = []

    if "targets" not in ai_result or not isinstance(ai_result["targets"], dict):
        raise RuntimeError("Invalid AI output: missing or invalid 'targets'")

    for ext, target in ai_result["targets"].items():
        ext = ext.lower().lstrip(".")

        if not ext:
            raise RuntimeError("Invalid file extension from AI")

        if not isinstance(target, str) or not target:
            raise RuntimeError("Invalid target path from AI")

        rules.append(
            Rule(
                rule_id=f"{ext}_docs",
                extension=[f".{ext}"],
                path_prefix=approved_root,
                target=target
            )
        )

    if not rules:
        raise RuntimeError("AI did not produce any valid rules")

    return rules


# =========================================================
# NEW MODE: ACTIONS (MKDIR, MOVE, COPY, RENAME, ...)
# =========================================================

def actions_from_ai(ai_result: dict):
    """
    Expected NEW AI format:

    {
      "actions": [
        { "type": "MKDIR", "path": "Pictures" },
        { "type": "MOVE", "ext": ["jpg", "png"], "target": "Pictures" }
      ]
    }
    """

    if "actions" not in ai_result:
        return None  # Means: fallback to old rule-based system

    actions = ai_result["actions"]

    if not isinstance(actions, list) or not actions:
        raise RuntimeError("Invalid AI output: 'actions' must be a non-empty list")

    normalized = []

    for act in actions:
        if not isinstance(act, dict):
            raise RuntimeError("Invalid action from AI")

        if "type" not in act:
            raise RuntimeError("Action missing 'type'")

        t = act["type"].upper().strip()

        normalized.append({"type": t, **act})

    return normalized


# =========================================================
# Translate ACTIONS -> CONCRETE OPERATIONS
# =========================================================

def build_operations_from_actions(snapshot, actions, approved_root: str):
    """
    Converts high-level actions into concrete L1B operations.
    """

    ops = []
    root = Path(approved_root)

    for action in actions:
        t = action["type"]

        # ---------- MKDIR ----------
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

        # ---------- MOVE / COPY ----------
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

        # ---------- RENAME ----------
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


# =========================================================
# ORCHESTRATOR
# =========================================================

class Orchestrator:
    def __init__(self, approved_root: str):
        self.approved_root = approved_root

    def run_ai_task(self):
        """
        Full AI-powered MVK flow:
        Human → Gemini → (Rules or Actions) → Plan → Preview → Execute
        """

        print("🤖 Tell Kore what you want to do.")
        user_prompt = input("> ").strip()

        if not user_prompt:
            print("❌ Empty request. Aborting.")
            return

        # 1. Ask Gemini
        print("\n🤖 Asking Gemini...")
        ai_result = ask_gemini(user_prompt)

        print("\n🧠 AI suggested this structure:")
        print(ai_result)

        # 2. Try NEW MODE first (actions)
        try:
            actions = actions_from_ai(ai_result)
        except Exception as e:
            print("❌ AI action format rejected:", e)
            return

        # ---------------------------------------------------
        # NEW MODE PATH
        # ---------------------------------------------------
        if actions is not None:
            print("\n🧠 Using NEW ACTION MODE")

            # Build snapshot using L1A
            from MVK_L1A.snapshot import build_snapshot
            snapshot = build_snapshot(Path(self.approved_root))

            try:
                operations = build_operations_from_actions(
                    snapshot, actions, self.approved_root
                )
            except Exception as e:
                print("❌ Failed to build operations:", e)
                return

            if not operations:
                print("ℹ️ Nothing to do.")
                return

            plan = {
                "plan_id": "AI-ACTIONS-PLAN",
                "snapshot_id": snapshot.snapshot_id,
                "generated_at": "now",
                "operations": operations,
                "aborted": False
            }

        # ---------------------------------------------------
        # OLD MODE PATH (rules -> L1A planner)
        # ---------------------------------------------------
        else:
            print("\n🧠 Using LEGACY RULE MODE")

            try:
                ruleset = rules_from_gemini(ai_result, self.approved_root)
            except Exception as e:
                print("❌ AI output rejected:", e)
                return

            print("\n🧪 Running MVK-L1A (safe planner)...")
            plan = run_l1a(self.approved_root, ruleset)

            if plan.get("aborted"):
                print("❌ MVK-L1A aborted:")
                print("Reason:", plan.get("reason"))
                return

        # 4. Show plan preview
        print("\n📋 PLAN PREVIEW:")

        if not plan["operations"]:
            print("ℹ️ Nothing to do.")
            return

        for i, op in enumerate(plan["operations"], 1):
            print(f"{i}. {op['type']}:")
            if "source" in op:
                print(f"    FROM: {op['source']}")
            if "destination" in op:
                print(f"    TO:   {op['destination']}")

        # 5. Human confirmation gate
        answer = input("\nExecute this plan? (y/n): ").strip().lower()
        if answer != "y":
            print("🚫 Cancelled by user. Nothing was changed.")
            return

        # 6. Execute via MVK-L1B
        print("\n💣 Executing via MVK-L1B (transactional, safe)...")
        try:
            run_l1b(plan)
        except Exception as e:
            print("❌ Execution failed:", e)
            return

        print("\n✅ Task completed safely.")
