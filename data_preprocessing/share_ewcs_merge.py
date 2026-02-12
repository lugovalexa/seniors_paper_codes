"""
Construction of dataset for heterogeneity analysis: 
merging SHARE stacked data with EWCS job quality indices.

This script prepares the dataset used in the heterogeneity analysis by
merging individual-level SHARE data with occupation-country level job quality
indices constructed from the European Working Conditions Survey (EWCS).

The resulting dataset is used for heterogeneity analsyis in paper:

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

Data access and scope
---------------------
- SHARE microdata and EWCS microdata are cannot be redistributed by the authors. 
- This code assumes you have lawful access to both datasets, that you have downloaded the corresponding files,
and preproccessed them using ewcs_preprocessing.py and share_preprocessing.py.

Input
------
- share_stacked.csv - obtained by executing share_preprocessing.py
- ewcs_jqi.csv - obtained by executing ewcs_preprocessing.py

Main steps
----------
1. Load the stacked SHARE dataset.
2. Clean and harmonize ISCO codes to a 3-digit level.
3. Load the EWCS job quality indices (country × 3-digit ISCO).
4. Merge EWCS indices to SHARE data by country and occupation.
5. Restrict the sample to observations with available job quality information.

Output
------
- share_ewcs_heterogeneity.csv
  Individual-level SHARE data augmented with EWCS job quality indices,
  used for heterogeneity analyses in the paper.

Usage
-----
    python share_ewcs_merge.py

Environment variables (optional)
--------------------------------
    DATA_DIR=/path/to/input/data
    OUT_DIR=/path/to/output/data
"""

import os
from pathlib import Path

import pandas as pd


def main() -> None:
    # ------------------------------------------------------------------
    # Project paths
    # ------------------------------------------------------------------
    PROJECT_ROOT = Path(__file__).resolve().parent

    DATA_DIR = Path(
        os.getenv("DATA_DIR", PROJECT_ROOT / "data")
    ).expanduser().resolve()

    OUT_DIR = Path(
        os.getenv("OUT_DIR", PROJECT_ROOT / "data" / "results")
    ).expanduser().resolve()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Input files (not included in replication package)
    # ------------------------------------------------------------------
    SHARE_FILE = DATA_DIR / "share_stacked.csv"
    EWCS_FILE = DATA_DIR / "ewcs_jqi.csv"

    if not SHARE_FILE.exists():
        raise FileNotFoundError(f"SHARE stacked file not found: {SHARE_FILE}")
    if not EWCS_FILE.exists():
        raise FileNotFoundError(f"EWCS JQI file not found: {EWCS_FILE}")

    # ------------------------------------------------------------------
    # Load SHARE stacked data
    # ------------------------------------------------------------------
    df = pd.read_csv(SHARE_FILE)

    # Drop observations with missing ISCO codes
    df = df.dropna(subset=["isco"]).reset_index(drop=True)

    # Harmonize ISCO to 3 digits
    df["isco"] = df["isco"].astype("string").str[:3].str.zfill(3)

    # ------------------------------------------------------------------
    # Load EWCS job quality indices
    # ------------------------------------------------------------------
    jqi = pd.read_csv(EWCS_FILE)

    # Harmonize ISCO to 3 digits
    jqi["isco"] = jqi["isco"].astype("string").str[:3].str.zfill(3)

    # Check required columns
    required_cols = {"country", "isco", "jqi_sum"}
    missing = required_cols - set(jqi.columns)
    if missing:
        raise KeyError(f"EWCS JQI file missing required columns: {missing}")

    # ------------------------------------------------------------------
    # Merge SHARE with EWCS job quality indices
    # ------------------------------------------------------------------
    df = df.merge(
        jqi,
        on=["country", "isco"],
        how="left"  
    )

    # Drop observations without matched job quality information
    df = df.dropna(subset=["jqi_sum"]).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Save output
    # ------------------------------------------------------------------
    OUT_FILE = OUT_DIR / "share_ewcs_heterogeneity.csv"
    df.to_csv(OUT_FILE, index=False)

    print(f"Saved heterogeneity dataset: {OUT_FILE}")


if __name__ == "__main__":
    main()
