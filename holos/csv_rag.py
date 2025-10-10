import os
from typing import Dict, Any, Optional, List
import duckdb
import pandas as pd

# -------------------------------------------------------
# Class: CSVEngine
# -------------------------------------------------------
# Purpose:
# Handles reading, filtering, and summarizing CSV files
# containing crop or regional datasets for the chatbot.
# This acts like a small data analysis engine.
class CSVEngine:
    def __init__(self, csv_dir: str = "data/docs/"):
        # Folder where all CSV data files are stored
        self.csv_dir = csv_dir

    # ---------------------------------------------------
    # Function: _pick_file
    # ---------------------------------------------------
    # Purpose:
    # Choose the right CSV file based on the user's context.
    # If a crop name (like rice or corn) appears in the filename,
    # that file is selected. Otherwise, it picks the first CSV found.
    def _pick_file(self, context: Dict[str, Any]) -> Optional[str]:
        crop = (context.get("crop") or "").lower()  # Get crop name in lowercase

        # Check if the directory exists
        if not os.path.exists(self.csv_dir):
            return None

        # Get all CSV files in the directory
        files = [f for f in os.listdir(self.csv_dir) if f.lower().endswith(".csv")]
        if not files:
            return None  # Return None if no CSV files exist

        # Try to find a file matching the crop name (e.g., rice.csv)
        if crop:
            for f in files:
                if crop in f.lower():
                    # Return the matched file path
                    return os.path.join(self.csv_dir, f)

        # If no crop match found, just pick the first CSV file
        return os.path.join(self.csv_dir, files[0])

    # ---------------------------------------------------
    # Function: summarize
    # ---------------------------------------------------
    # Purpose:
    # Generate a summary of a selected CSV file:
    # - Count rows and columns
    # - Detect numeric columns and summarize statistics
    # - Filter by region if possible
    def summarize(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Select which file to read based on crop or context
        path = self._pick_file(context)
        if not path:
            return {"summary": "No CSV datasets found.", "rows": 0}

        # Try reading the CSV file safely
        try:
            df = pd.read_csv(path)
        except Exception as e:
            return {"dataset": path, "error": f"Failed to read CSV: {str(e)}"}

        # Basic dataset info
        out: Dict[str, Any] = {
            "dataset": os.path.basename(path),  # File name
            "rows": int(len(df)),               # Total number of rows
            "columns": list(df.columns)         # List of column names
        }

        # ------------------------------------------------
        # Region Filtering (if user mentioned a location)
        # ------------------------------------------------
        region = (context.get("region") or "").lower()
        # Check if the dataset has region-like columns (e.g., state, county, zip)
        for col in df.columns:
            cl = col.lower()
            if cl in {"county", "region", "state", "zip", "zipcode"} and region:
                try:
                    # Find rows matching the region name or ZIP code
                    sub = df[df[col].astype(str).str.lower().str.contains(region, na=False)]
                    out["region_rows"] = int(len(sub))  # Count matching rows
                except Exception:
                    pass
                break  # Stop after first region match

        # ------------------------------------------------
        # Numeric Summary (statistics for numeric columns)
        # ------------------------------------------------
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            # Use pandas describe() to get summary stats (mean, min, max, etc.)
            desc = df[numeric_cols].describe().to_dict()

            # Convert all numeric values to float for JSON compatibility
            out["numeric_summary"] = {
                k: {m: float(v) for m, v in stats.items()} for k, stats in desc.items()
            }

        # Return the summary dictionary
        return out
