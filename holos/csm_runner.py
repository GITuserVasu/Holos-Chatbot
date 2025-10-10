import hashlib, json, time
from typing import Dict, Any
from functools import lru_cache

# -------------------------------------------------------
# Class: CSMRunner
# -------------------------------------------------------
# Purpose:
# Simulates the behavior of a Crop Simulation Model (CSM)
# such as DSSAT or APSIM.
# This version is a simplified "stub" version that mimics the
# model’s behavior using placeholder data.
class CSMRunner:
    def __init__(self, csm_dir: str = "data/csm/"):
        # Directory where CSM data or model files are stored
        self.csm_dir = csm_dir

    # ---------------------------------------------------
    # Function: _key
    # ---------------------------------------------------
    # Purpose:
    # Create a unique key (hash) from the input parameters.
    # This allows caching of results so that the same inputs
    # don’t need to be reprocessed each time.
    def _key(self, params: Dict[str, Any]) -> str:
        # Convert parameters to JSON string and hash them using SHA-256
        return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()

    # ---------------------------------------------------
    # Function: _cached_run
    # ---------------------------------------------------
    # Purpose:
    # A mock (temporary) simulation function that imitates
    # running a real CSM model. It is cached so that repeated
    # calls with the same key return instantly.
    @lru_cache(maxsize=256)
    def _cached_run(self, key: str) -> Dict[str, Any]:
        # Simulate computation delay (as if running a real simulation)
        time.sleep(0.3)

        # Return mock/stub results — in a real version, these would
        # come from an actual simulation output file.
        return {
            "sim_id": key[:8],                      # Short simulation ID
            "yield_kg_ha": 7800,                    # Example yield value
            "planting_date": "auto",                # Auto-selected planting date
            "maturity_date": "auto+120d",           # Simulated maturity period
            "irrigation_mm": 900,                   # Example irrigation value
            "ratoon_possible": True,                # Whether regrowth (ratoon) is possible
            "notes": "Stub CSM. Plug in your model in csm_runner.py."  # Reminder
        }

    # ---------------------------------------------------
    # Function: run
    # ---------------------------------------------------
    # Purpose:
    # Public function that runs the model for given parameters.
    # It generates a unique cache key and retrieves results
    # (either from cache or by calling the simulation stub).
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Generate unique hash for input parameters
        # and call the cached simulation function
        return self._cached_run(self._key(params))
