"""
EWCS data preparation and construction of Job Quality Indices (JQI)

This script prepares European Working Conditions Survey (EWCS) microdata for use in the
analysis presented in paper: 

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

The script harmonizes EWCS microdata across the 2010 and 2015 waves, reconstructs selected
Job Quality Index components using a consistent set of questionnaire items available
in both years, and aggregates the resulting indices to the country × 3-digit ISCO level.

Data access and scope
---------------------
- EWCS microdata at 4-digit ISCO code level is required for this script. It is available upon request from Eurofound for research purposes. 
- This script assumes the user has lawful access to the EWCS 2010 and 2015 microdata files. No raw data are included in the replication package.

Main steps
----------
1. Load EWCS microdata for 2010 and 2015.
2. Harmonize identifiers, country codes, and occupation codes.
3. Construct selected JQI components using documented rules based on EWCS questionnaires.
4. Combine reconstructed components with pre-existing EWCS indices.
5. Compute an overall work quality index as an additive summary of components.
6. Collapse individual-level indices to country × 3-digit ISCO cells.
7. Export the final dataset for use in the empirical analysis.

Inputs (not included)
---------------------
- EWCS microdata for 2015 and 2010 (Stata .dta)
The dataset should contain microdata for 2010 and 2015. It should contain 4-digit ISCO codes.
Variable names (for survey questions) should be prefixed with "y10_" for 2010 and "y15_" for 2015.

Output
------
- ewcs_jqi.csv
  Country × 3-digit ISCO dataset containing average Job Quality Indices.

Usage
-----
    python ewcs_preprocessing.py

Environment variables
--------------------------------
    DATA_DIR=/path/to/data
    OUT_DIR=/path/to/output
"""


# Import libraries
import os
import sys
from pathlib import Path

src_path = os.path.abspath("../")
sys.path.append(src_path)

PROJECT_ROOT = Path(__file__).resolve().parent

import numpy as np
import pandas as pd
import pyreadstat

import warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------
# Helper functions 
# -------------------------------------------------------------------
def _clean_id(series: pd.Series) -> pd.Series:
    """Standardize EWCS respondent IDs across waves and file formats.

    To harmonize IDs, we:
      1) cast to string,
      2) drop a trailing ".0" when present,
      3) remove non-ASCII printable characters,
      4) strip leading/trailing whitespace.

    Parameters
    ----------
    series : pd.Series
        Raw ID column.

    Returns
    -------
    pd.Series
        Cleaned string IDs.
    """
    s = series.astype(str)
    s = s.apply(lambda x: x[:-2] if x.endswith(".0") else x)
    s = s.str.replace(r"[^ -~]+", "", regex=True)
    s = s.str.strip()
    return s


def ewcs_preprocessing(df: pd.DataFrame, meta) -> pd.DataFrame:
    """Harmonize EWCS variables and basic identifiers.

    This function standardizes variable names needed for the JQI indices and downstream
    aggregation.

    Key steps
    ---------
    - Rename EWCS-provided index columns to stable names used in the paper.
    - Replace numeric country codes (COUNTID) with country names using Stata metadata.
    - Restrict sample to the waves used in the paper (2010 and 2015).
    - Drop observations with missing ISCO codes.
    - Rename key identifier columns and clean respondent IDs.
    - Keep only countries that are present in SHARE.

    Notes
    -----
    - We do not impute missing values for the survey items here. Each index function
      handles missingness according to the JQI construction.
    - `meta` is the object returned by pyreadstat and contains value labels needed to map
      COUNTID to country names.

    Parameters
    ----------
    df : pd.DataFrame
        EWCS microdata.
    meta : pyreadstat metadata
        Metadata object from pyreadstat.read_dta().

    Returns
    -------
    pd.DataFrame
        Preprocessed EWCS microdata.
    """
    # Rename EWCS indices to paper naming convention.
    df = df.rename(
        columns={
            "adincome_mth": "jqi_monthly_earnings",
            "wq": "jqi_skills_discretion",
            "envsec": "jqi_physical_environment",
            "wlb_slim": "jqi_working_time_quality",
        }
    )

    # Map numeric country IDs to names using Stata value labels.
    if hasattr(meta, "value_labels") and "COUNTID" in meta.value_labels:
        countid_mapping = meta.value_labels["COUNTID"]
        df["countid"] = df["countid"].map(countid_mapping)

    # Keep waves 2010 and 2015.
    df = df.loc[df["year"].isin([2010, 2015])].reset_index(drop=True)

    # Drop missing occupation codes.
    df = df.dropna(subset=["ISCO_08"]).reset_index(drop=True)

    # Rename identifiers and clean ID.
    df = df.rename(columns={"countid": "country", "ISCO_08": "isco"})
    df["id"] = _clean_id(df["id"])

    return df


def social_environment_index(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Construct the JQI Social Environment component for 2010 and 2015.

    Motivation
    ----------
    To obtain a comparable measure for 2010 and 2015, we reconstruct the index using the subset of
    questionnaire items that exist in both years.

    Construction 
    -------------------------
    - Select a common set of survey items for each year.
    - Apply validity filters to exclude non-substantive codes.
    - Reverse-code specific items so higher values consistently mean "better" social environment.
    - Sum the items to a raw score.
    - Linearly rescale the raw score to a 0–100 scale.

    Parameters
    ----------
    df : pd.DataFrame
        Preprocessed EWCS data containing 2010 (with y10_ prefixes) and 2015 variables (with y15_ prefixes).
    verbose : bool
        If True, prints summary statistics by year to help validate the construction.

    Returns
    -------
    pd.DataFrame
        Long-format index: [id, year, jqi_social_environment]
    """
    # -----------------------
    # 2010 items (q.. variables)
    # -----------------------
    cols10 = ["id", "y10_q70a", "y10_q70b", "y10_q70c", "y10_q71a", "y10_q71c", "y10_q71b", "y10_q58b", "y10_q58a", "y10_q51a", "y10_q51b"]
    soc10 = df[df["year"] == 2010].loc[:, cols10].dropna().copy()

    # Validity filter: keep responses in the expected range.
    for c in cols10:
        if c == "id":
            continue
        soc10[c] = soc10[c].astype(int)
        soc10 = soc10.loc[soc10[c] < 7]

    # Reverse-code so higher = better environment.
    soc10[["y10_q58a", "y10_q58b"]] = soc10[["y10_q58a", "y10_q58b"]].replace({1: 2, 2: 1})
    soc10[["y10_q51a", "y10_q51b"]] = soc10[["y10_q51a", "y10_q51b"]].replace({1: 5, 2: 4, 4: 2, 5: 1})

    # Raw sum score.
    soc10["jqi_social_environment"] = soc10[
        ["y10_q58a", "y10_q58b", "y10_q51a", "y10_q51b", "y10_q70a", "y10_q70b", "y10_q70c", "y10_q71a", "y10_q71b", "y10_q71c"]
    ].sum(axis=1)

    # Rescale to 0–100.
    old_min, old_max = soc10["jqi_social_environment"].min(), soc10["jqi_social_environment"].max()
    soc10["jqi_social_environment"] = (soc10["jqi_social_environment"] - old_min) / (old_max - old_min) * 100

    # Formatting.
    soc10 = soc10.loc[:, ["id", "jqi_social_environment"]]
    soc10["year"] = 2010

    # -----------------------
    # 2015 items (y15_ variables)
    # -----------------------
    cols15 = [
        "id", "y15_Q80a", "y15_Q80b", "y15_Q80c", "y15_Q81a", "y15_Q81b", "y15_Q81c",
        "y15_Q63a", "y15_Q63e", "y15_Q61a", "y15_Q61b",
    ]
    soc15 = df[df["year"] == 2015].loc[:, cols15].dropna().copy()

     # Validity filter: keep responses in the expected range.
    for c in cols15:
        if c == "id":
            continue
        soc15[c] = soc15[c].astype(int)
        soc15 = soc15.loc[soc15[c] < 7]

    # Reverse-code so higher = better environment.
    soc15[["y15_Q61a", "y15_Q61b", "y15_Q63a", "y15_Q63e"]] = soc15[
        ["y15_Q61a", "y15_Q61b", "y15_Q63a", "y15_Q63e"]
    ].replace({1: 5, 2: 4, 4: 2, 5: 1})

    # Raw sum score.
    soc15["jqi_social_environment"] = soc15[
        ["y15_Q80a", "y15_Q80b", "y15_Q80c", "y15_Q81a", "y15_Q81b", "y15_Q81c",
         "y15_Q63a", "y15_Q63e", "y15_Q61a", "y15_Q61b"]
    ].sum(axis=1)

    # Rescale to 0–100.
    old_min, old_max = soc15["jqi_social_environment"].min(), soc15["jqi_social_environment"].max()
    soc15["jqi_social_environment"] = (soc15["jqi_social_environment"] - old_min) / (old_max - old_min) * 100

    # Formatting.
    soc15 = soc15.loc[:, ["id", "jqi_social_environment"]]
    soc15["year"] = 2015

    # Concat 2010 and 2015.
    soc = pd.concat([soc10, soc15], axis=0, ignore_index=True)

    # Harmonize IDs to match the main EWCS file.
    soc["id"] = _clean_id(soc["id"])

    # Optional: show descriptive statistics by year to validate the construction.
    if verbose:
        print("JQI social environment (constructed)")
        print(soc.groupby("year")["jqi_social_environment"].describe())

    return soc


def prospects_index(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Construct the JQI Prospects component for 2010 and 2015.

    Motivation
    ----------
    To obtain a comparable measure for 2010 and 2015, we reconstruct the index using the subset of
    questionnaire items that exist in both years.

    Construction 
    -------------------------
    - Select a common set of survey items for each year.
    - Apply validity filters to exclude non-substantive codes.
    - Reverse-code specific items so higher values consistently mean "better" prospects.
    - Sum the items to a raw score.
    - Linearly rescale the raw score to a 0–100 scale.

    Parameters
    ----------
    df : pd.DataFrame
        Preprocessed EWCS data containing 2010 (with y10_ prefixes) and 2015 variables (with y15_ prefixes).
    verbose : bool
        If True, prints summary statistics by year to help validate the construction.

    Returns
    -------
    pd.DataFrame
        Long-format index: [id, year, jqi_prospects]
    """

    # -----------------------
    # 2010 items (q.. variables)
    # -----------------------
    # Select the relevant items and drop missing values. 
    pro10 = df[df["year"] == 2010].loc[:, ["id", "y10_q77c", "y10_q77a"]].dropna().copy()

    # Validity filter: keep responses in the expected range.
    for c in ["y10_q77c", "y10_q77a"]:
        pro10[c] = pro10[c].astype(int)
        pro10 = pro10.loc[pro10[c] < 7]

    # Reverse-code so higher = better prospects.
    pro10["y10_q77a"] = pro10["y10_q77a"].replace({1: 5, 2: 4, 4: 2, 5: 1})

    # Raw sum score.
    pro10["jqi_prospects"] = pro10[["y10_q77c", "y10_q77a"]].sum(axis=1)

    # Rescale to 0–100.
    old_min, old_max = pro10["jqi_prospects"].min(), pro10["jqi_prospects"].max()
    pro10["jqi_prospects"] = (pro10["jqi_prospects"] - old_min) / (old_max - old_min) * 100

    # Formatting.
    pro10 = pro10.loc[:, ["id", "jqi_prospects"]]
    pro10["year"] = 2010

    # -----------------------
    # 2015 items (y15_ variables)
    # -----------------------
    # Select the relevant items and drop missing values. 
    pro15 = df[df["year"] == 2015].loc[:, ["id", "y15_Q89b", "y15_Q89g"]].dropna().copy()

    # Validity filter: keep responses in the expected range.
    for c in ["y15_Q89b", "y15_Q89g"]:
        pro15[c] = pro15[c].astype(int)
        pro15 = pro15.loc[pro15[c] < 7]

    # Reverse-code so higher = better prospects.
    pro15["y15_Q89b"] = pro15["y15_Q89b"].replace({1: 5, 2: 4, 4: 2, 5: 1})

    # Raw sum score.
    pro15["jqi_prospects"] = pro15[["y15_Q89g", "y15_Q89b"]].sum(axis=1)

    # Rescale to 0–100.
    old_min, old_max = pro15["jqi_prospects"].min(), pro15["jqi_prospects"].max()
    pro15["jqi_prospects"] = (pro15["jqi_prospects"] - old_min) / (old_max - old_min) * 100

    # Formatting.
    pro15 = pro15.loc[:, ["id", "jqi_prospects"]]
    pro15["year"] = 2015

    # Concat 2010 and 2015.
    pro = pd.concat([pro10, pro15], axis=0, ignore_index=True)

    # Harmonize IDs to match the main EWCS file.
    pro["id"] = _clean_id(pro["id"])

    # Optional: show descriptive statistics by year to validate the construction.
    if verbose:
        print("JQI prospects (constructed)")
        print(pro.groupby("year")["jqi_prospects"].describe())

    return pro


def intensity_index(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Construct the JQI Work Intensity component for 2010 and 2015.

    Motivation
    ----------
    To obtain a comparable measure for 2010 and 2015, we reconstruct the index using the subset of
    questionnaire items that exist in both years.

    IMPORTANT CONVENTION
    --------------------
    The original JQI work intensity component is typically coded so that higher values mean
    more intensity (worse). In this project we keep the same direction as other indices:
    higher values = better working conditions = lower intensity.

    Construction 
    -------------------------
    - Select a common set of survey items for each year.
    - Apply validity filters to exclude non-substantive codes.
    - Reverse-code specific items so higher values consistently mean "better" prospects.
    - Sum the items to a raw score.
    - Linearly rescale the raw score to a 0–100 scale.

    Parameters
    ----------
    df : pd.DataFrame
        Preprocessed EWCS data containing 2010 (with y10_ prefixes) and 2015 variables (with y15_ prefixes).
        If True, prints summary statistics by year to help validate the construction.

    Returns
    -------
    pd.DataFrame
        Long-format index: [id, year, jqi_intensity]
    """
      
    # -----------------------
    # 2010 items (q.. variables)
    # -----------------------
    # Select the relevant items and drop missing values.
    cols10 = ["id", "y10_q45a", "y10_q45b", "y10_q51g", "y10_q46a", "y10_q46b", "y10_q46c", "y10_q46d", "y10_q46e", "y10_q51p", "y10_q24g", "y10_q47", "y10_q48"]
    int10 = df[df["year"] == 2010].loc[:, cols10].dropna().copy()

    # Validity filter: keep responses in the expected range.
    for c in cols10:
        if c == "id":
            continue
        int10[c] = int10[c].astype(int)
        if c == "y10_q46e":
            int10 = int10.loc[int10[c] < 7]
        else:
            int10 = int10.loc[int10[c] < 8]

    # Composite term.
    int10["y10_q4748"] = int10["y10_q47"] * int10["y10_q48"]

    # Multitasking indicator: start at 2, set to 1 if >=3 of the 5 items equal 1.
    multitask_items10 = ["y10_q46a", "y10_q46b", "y10_q46c", "y10_q46d", "y10_q46e"]
    multitask_count10 = (int10[multitask_items10] == 1).sum(axis=1)
    int10["y10_q46"] = np.where(multitask_count10 >= 3, 1, 2)

    # Reverse-code so higher = better.
    int10["y10_q51g"] = int10["y10_q51g"].replace({1: 5, 2: 4, 4: 2, 5: 1})

    # Raw sum score.
    int10["jqi_intensity"] = int10[
        ["y10_q45a", "y10_q45b", "y10_q51g", "y10_q46a", "y10_q46b", "y10_q46c", "y10_q46d", "y10_q46e", "y10_q46", "y10_q51p", "y10_q24g", "y10_q4748"]
    ].sum(axis=1)

    # Rescale to 0–100.
    old_min, old_max = int10["jqi_intensity"].min(), int10["jqi_intensity"].max()
    int10["jqi_intensity"] = (int10["jqi_intensity"] - old_min) / (old_max - old_min) * 100

    # Formatting.
    int10 = int10.loc[:, ["id", "jqi_intensity"]]
    int10["year"] = 2010

    # -----------------------
    # 2015 items (y15_ variables)
    # -----------------------
    # Select the relevant items and drop missing values.
    cols15 = ["id", "y15_Q49a", "y15_Q49b", "y15_Q61g", "y15_Q50a", "y15_Q50b", "y15_Q50c", "y15_Q50d", "y15_Q50e",
              "y15_Q61o", "y15_Q30g", "y15_Q51", "y15_Q52"]
    int15 = df[df["year"] == 2015].loc[:, cols15].dropna().copy()

    # Validity filter: keep responses in the expected range.
    for c in cols15:
        if c == "id":
            continue
        int15[c] = int15[c].astype(int)
        int15 = int15.loc[int15[c] < 7]

    # Composite term.
    int15["y15_Q5152"] = int15["y15_Q51"] * int15["y15_Q52"]

    # Multitasking indicator: start at 2, set to 1 if >=3 of the 5 items equal 1.
    multitask_items15 = ["y15_Q50a", "y15_Q50b", "y15_Q50c", "y15_Q50d", "y15_Q50e"]
    multitask_count15 = (int15[multitask_items15] == 1).sum(axis=1)

    # Note: In 2015, the multitasking indicator is coded so that 1 = better (more multitasking), 0 = worse.
    int15["y15_Q50"] = np.where(multitask_count15 >= 3, 1, 0)

    # Reverse-code so higher = better.
    int15["y15_Q61g"] = int15["y15_Q61g"].replace({1: 5, 2: 4, 4: 2, 5: 1})

    # Raw sum score.
    int15["jqi_intensity"] = int15[
        ["y15_Q49a", "y15_Q49b", "y15_Q61g", "y15_Q50a", "y15_Q50b", "y15_Q50c", "y15_Q50d", "y15_Q50e",
         "y15_Q50", "y15_Q61o", "y15_Q30g", "y15_Q5152"]
    ].sum(axis=1)

    # Rescale to 0–100.
    old_min, old_max = int15["jqi_intensity"].min(), int15["jqi_intensity"].max()
    int15["jqi_intensity"] = (int15["jqi_intensity"] - old_min) / (old_max - old_min) * 100

    # Formatting.
    int15 = int15.loc[:, ["id", "jqi_intensity"]]
    int15["year"] = 2015

    # Concat 2010 and 2015.
    out = pd.concat([int10, int15], axis=0, ignore_index=True)

    # Harmonize IDs to match the main EWCS file.
    out["id"] = _clean_id(out["id"])

    # Optional: show descriptive statistics by year to validate the construction.
    if verbose:
        print("JQI intensity (constructed; higher = better / lower intensity)")
        print(out.groupby("year")["jqi_intensity"].describe())

    return out


def sum_wq_index(df: pd.DataFrame) -> pd.DataFrame:
    """Compute an overall work quality index as the sum of JQI components (excluding earnings).

    The project uses a simple additive index over the main JQI components available in EWCS.
    We exclude monthly earnings and then linearly rescale to 0–100
    based on the observed distribution in the analytic sample.

    Columns required
    ---------------
      - jqi_skills_discretion
      - jqi_social_environment
      - jqi_physical_environment
      - jqi_intensity
      - jqi_prospects
      - jqi_working_time_quality

    Returns
    -------
    pd.DataFrame
        Input df with added columns:
          - jqi_sum   : rescaled 0–100 overall index 
    """
    components = [
        "jqi_skills_discretion",
        "jqi_social_environment",
        "jqi_physical_environment",
        "jqi_intensity",
        "jqi_prospects",
        "jqi_working_time_quality",
    ]

    # Check that all components are present before summing.
    missing = [c for c in components if c not in df.columns]
    if missing:
        raise KeyError(f"Cannot compute overall work quality: missing components {missing}")

    # Raw sum.
    df["jqi_sum"] = df[components].sum(axis=1)

    # Rescale overall index to 0–100.
    old_min, old_max = df["jqi_sum"].min(), df["jqi_sum"].max()
    df["jqi_sum"] = (df["jqi_sum"] - old_min) / (old_max - old_min) * 100

    print("Overall work quality index (constructed from components)")
    print(df["jqi_sum"].describe())

    return df



# -------------------------------------------------------------------
# Input data paths
# -------------------------------------------------------------------
# By default, this looks for data in ../data relative to the project root.
# You can override by setting an environment variable, e.g.:
#   export DATA_DIR="/path/to/your/data"
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data")).expanduser().resolve()

# NOTE: The following files are not included in the replication package.
# Please place them in DATA_DIR (or update the file names below).

    # Input files
    # ----------
    # EWCS: EWCS microdata for 2010 and 2015 (at 4-digit ISCO level).
    # Variable names (for survey questions) should be prefixed with "y10_" for 2010 and "y15_" for 2015.

EWCS = DATA_DIR / "EWCS.dta"

# Load data
ewcs, meta = pyreadstat.read_dta(str(EWCS))

# Harmonize EWCS variables across waves and apply consistent formatting.
ewcs = ewcs_preprocessing(ewcs, meta)

# Check required columns
required_cols = {'id', 'year', 'country', 'isco'}
missing = required_cols - set(ewcs.columns)
assert not missing, f"Preprocessed EWCS data missing required columns: {missing}"


# Social environment index (JQI component).
# Returns a country-year-person level index to be merged back to the EWCS microdata.
soc = social_environment_index(ewcs, verbose=True)
ewcs = ewcs.merge(soc, on=["id", "year"], how="left", validate="1:1")


# Prospects index (JQI component).
# Returns a country-year-person level index to be merged back to the EWCS microdata.
pro = prospects_index(ewcs, verbose=True)
ewcs = ewcs.merge(pro, on=["id", "year"], how="left", validate="1:1")


# Work intensity index (JQI component).
# Returns a country-year-person level index to be merged back to the EWCS microdata.
intensity = intensity_index(ewcs, verbose=True)
ewcs = ewcs.merge(intensity, on=["id", "year"], how="left", validate="1:1")

# Compute overall work quality index (adds column to `ewcs`).
ewcs = sum_wq_index(ewcs)

# Refresh the list of JQI columns to include the overall index created by the helper.
jqi_cols = sorted([c for c in ewcs.columns if c.startswith("jqi")])

# Convert ISCO to 3-digit level.
ewcs["isco"] = ewcs["isco"].astype("string").str[:3].str.zfill(3)

# Keep country × 3-digit ISCO cells with at least 10 observations.
ewcs = (
    ewcs.dropna(subset=["country", "isco"])
        .groupby(["country", "isco"])
        .filter(lambda x: len(x) >= 10)
        .reset_index(drop=True)
)

# Cell means.
ewcs_final = (
    ewcs.groupby(["country", "isco"], as_index=False)[jqi_cols]
        .mean()
)

# Keep only countries present in SHARE.
countries = [
    'Austria', 'Belgium', 'Czech Republic', 'Switzerland', 'Germany',
    'Denmark', 'Estonia', 'Spain', 'France', 'Italy',
    'Netherlands', 'Sweden', 'Slovenia', 'Luxembourg'
]

ewcs_final = ewcs_final[ewcs_final["country"].isin(countries)].reset_index(drop=True).copy()


# -------------------------------------------------------------------
# Output path
# -------------------------------------------------------------------
OUT_DIR = Path(os.getenv("OUT_DIR", PROJECT_ROOT / "data" / "results")).expanduser().resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "ewcs_jqi.csv"

ewcs_final.to_csv(OUT_FILE, index=False)
print(f"Saved: {OUT_FILE}")