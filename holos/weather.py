import json, os
from typing import Dict, Any

# -------------------------------------------------------
# Function: load_weather
# -------------------------------------------------------
# Purpose:
# Loads weather data for a given region or state from local JSON files.
# The function tries multiple file options in order of priority:
# 1. region-level file (e.g., data/weather/dallas.json)
# 2. state-level file (e.g., data/weather/texas.json)
# 3. default fallback file (data/weather/default.json)
#
# Returns:
# A dictionary with weather data (if found), otherwise a message note.
def load_weather(context: Dict[str, Any]) -> Dict[str, Any]:
    # Get region and state names from context (convert to lowercase and safe filenames)
    region = (context.get("region") or "").lower().replace(" ", "_")
    state = (context.get("state") or "").lower().replace(" ", "_")

    # Build a list of possible file paths in order of importance
    candidates = []
    if region:
        candidates.append(f"data/weather/{region}.json")  # Highest priority: specific region
    if state:
        candidates.append(f"data/weather/{state}.json")   # Next: state-level weather file
    candidates.append("data/weather/default.json")         # Fallback default weather file

    # Try loading each file until one is found and successfully opened
    for p in candidates:
        if os.path.exists(p):  # Check if file exists
            try:
                return json.load(open(p))  # Load and return weather data as dictionary
            except Exception:
                pass  # If file is corrupted or invalid JSON, skip to next option

    # If no file was found or successfully loaded, return a fallback message
    return {
        "note": "No weather file found; add JSON to data/weather/ (region.json or state.json)."
    }
