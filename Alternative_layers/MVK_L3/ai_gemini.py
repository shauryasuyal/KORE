import os
import json
import re

# Try to import the modern Gemini SDK
try:
    from google import genai
    from google.genai.errors import ClientError
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False


# ==============================
# Configuration
# ==============================

API_KEY = os.getenv("GEMINI_API_KEY")

# Use a widely available model (if quota allows)
MODEL_NAME = "gemini-2.0-flash"


# ==============================
# Initialize Gemini client (if possible)
# ==============================

_client = None

if GENAI_AVAILABLE and API_KEY:
    try:
        _client = genai.Client(api_key=API_KEY)
    except Exception:
        _client = None


# ==============================
# Prompt Template
# ==============================

GEMINI_PROMPT_TEMPLATE = """
You are an assistant that converts user intent into file organization instructions.

User says:
{user_request}

Return STRICT JSON in this format:

{{
  "targets": {{
    "pdf": "Documents/PDF",
    "txt": "Documents/Text"
  }}
}}

Rules:
- Do NOT include absolute paths
- Do NOT include system folders (Windows, Program Files, etc)
- Do NOT include explanations
- Do NOT include markdown
- Output ONLY valid JSON
"""


# ==============================
# Fallback: Local Intent Parser
# ==============================

def _fallback_intent_parser(user_request: str) -> dict:
    """
    VERY SIMPLE, VERY SAFE local parser.
    This guarantees MVK keeps working even without AI or internet.
    """

    text = user_request.lower()

    targets = {}

    # Common image types
    if any(ext in text for ext in ["jpg", "jpeg", "png", "image", "photo", "picture"]):
        targets["jpg"] = "Pictures"
        targets["jpeg"] = "Pictures"
        targets["png"] = "Pictures"

    # Documents
    if "pdf" in text:
        targets["pdf"] = "Documents/PDF"

    if "txt" in text or "text" in text or "note" in text:
        targets["txt"] = "Documents/Text"

    # If nothing matched, give a safe default
    if not targets:
        # Extremely conservative default
        targets["txt"] = "Documents/Text"

    return {"targets": targets}


# ==============================
# Main API: ask_gemini
# ==============================

def ask_gemini(user_request: str) -> dict:
    """
    Returns a dict in the form:
    {
      "targets": {
         "pdf": "Documents/PDF",
         "txt": "Documents/Text"
      }
    }

    This function:
    - Tries Gemini first
    - If ANY error happens → falls back to local parser
    """

    # If Gemini is not available at all → fallback immediately
    if _client is None:
        print("⚠️ Gemini not available (no SDK or no API key). Using fallback parser.")
        return _fallback_intent_parser(user_request)

    prompt = GEMINI_PROMPT_TEMPLATE.format(user_request=user_request)

    try:
        response = _client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        text = response.text.strip()

        # Try to parse JSON
        data = json.loads(text)

        # Basic validation
        if not isinstance(data, dict):
            raise ValueError("Gemini output is not a JSON object")

        if "targets" not in data or not isinstance(data["targets"], dict):
            raise ValueError("Gemini JSON missing 'targets'")

        # Sanitize: ensure keys are extensions, values are relative paths
        clean_targets = {}

        for ext, target in data["targets"].items():
            if not isinstance(ext, str) or not isinstance(target, str):
                continue

            ext = ext.lower().lstrip(".").strip()

            # Block any suspicious target
            if ":" in target or target.startswith("/") or target.startswith("\\"):
                continue

            if any(bad in target.lower() for bad in ["windows", "program files", "system32", "boot", "efi"]):
                continue

            if ext:
                clean_targets[ext] = target

        if not clean_targets:
            raise ValueError("Gemini returned no safe targets")

        print("🤖 Gemini output accepted.")
        return {"targets": clean_targets}

    except Exception as e:
        # ANY failure → fallback
        print("⚠️ Gemini failed or quota exceeded.")
        print("⚠️ Reason:", e)
        print("⚠️ Falling back to local intent parser.")

        return _fallback_intent_parser(user_request)
