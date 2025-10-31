from typing import Dict, Any, List, Tuple, Optional
import re

# -------------------------------------------------------
# CRITICAL: The key information required before running RAG
# -------------------------------------------------------
# Only 'crop' is mandatory for now.
# Other details like region or season can be asked later if missing.
CRITICAL = ["crop"]

# -------------------------------------------------------
# ZIP Code Pattern
# -------------------------------------------------------
# A simple regex to detect 5-digit ZIP codes (and optional 4-digit extensions)
# Note: ZIP handling removed — chatbot now accepts only state (CA or TX)

# -------------------------------------------------------
# US State Name to Abbreviation Mapping
# -------------------------------------------------------
# This helps us identify the user's location more accurately.
# For now, only California and Texas are supported in the model scope.
US_STATES = {
    'california': 'CA',
    'texas': 'TX',
}

# -------------------------------------------------------
# Function: heuristic_extract
# -------------------------------------------------------
# Purpose:
# Automatically detect useful context details (crop, region, ZIP, season)
# from a user's message using simple word matching.
def heuristic_extract(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(context or {})   # Copy existing context to avoid overwriting
    msg = message.lower()       # Convert message to lowercase for easy search

    # --- Detect crop name ---
    for c in ["rice", "wheat", "corn", "maize", "soy", "soybean", "cotton", "sorghum"]:
        # If crop name appears in the message and not already set in context
        if c in msg and not out.get("crop"):
            out["crop"] = "rice" if c == "rice" else c

    # --- Detect region or state ---
    # Prefer full state names (like "texas") over ZIP codes
    for name, abbr in US_STATES.items():
        if name in msg and not out.get("region"):
            out["region"] = name.title()  # Save readable state name
            out["state"] = abbr           # Save 2-letter abbreviation
            break

        # ZIP handling removed — we only accept state names (California or Texas)

    # --- Detect season ---
    # Identify spring months/keywords
    if any(w in msg for w in ["spring", "march", "april", "may"]) and not out.get("season"):
        out["season"] = "spring"
    # Identify fall/autumn months/keywords
    if any(w in msg for w in ["fall", "autumn", "sept", "oct"]) and not out.get("season"):
        out["season"] = "fall"

    # Return the updated context dictionary
    return out


# -------------------------------------------------------
# Function: find_missing
# -------------------------------------------------------
# Purpose:
# Check which critical context fields (like 'crop') are still missing.
def find_missing(ctx: Dict[str, Any]) -> List[str]:
    return [f for f in CRITICAL if not ctx.get(f)]


# -------------------------------------------------------
# Function: next_followup
# -------------------------------------------------------
# Purpose:
# Suggest the next question the chatbot should ask the user.
# If critical info is missing, it asks directly.
# Otherwise, it prompts for extra details like region or season.
# def next_followup(missing: List[str], ctx: Dict[str, Any]) -> str:
#     # If all required info is available
#     if not missing:
#         if not ctx.get("region"):
#             return "Which state are you in? (California or Texas)"
#         elif not ctx.get("season"):
#             return "Which season or target planting window are you considering?"
#         return ""
def next_followup(missing: List[str], ctx: Dict[str, Any]) -> str:
    if not missing:
        return ""



    # If something critical is missing (like 'crop')
    prompts = {
        "crop": "Which crop are you asking about?",
    }
    return prompts[missing[0]]


# -------------------------------------------------------
# Function: ensure_context
# -------------------------------------------------------
# Purpose:
# Combine all helper functions to:
# 1. Extract context automatically
# 2. Find what info is missing
# 3. Suggest a follow-up question
def ensure_context(message: str, context: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str], str]:
    ctx = heuristic_extract(message, context or {})  # Step 1: Extract possible context
    missing = find_missing(ctx)                      # Step 2: Identify missing fields
    follow = next_followup(missing, ctx)             # Step 3: Get next follow-up question
    return ctx, missing, follow                      # Return all three results
