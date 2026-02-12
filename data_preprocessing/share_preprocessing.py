#!/usr/bin/env python3
"""SHARE data preparation 

This script prepares SHARE Release 9.0.0 microdata for use in the analysis presented in paper: 

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement" 
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

It reproduces the sample selection, the construction of work-horizon
changes, and the stacked two-wave "blocks" used in the empirical design for baseline analysis.

It also supports data preprocessing for several tests presented in Appendix:

Test 1 (Table E.1, sample selection): include retirees 
Test 2 (Table E.2, sample selection): age restriction becomes age >= 50 (no upper bound)
Test 3 (Table E.3, sample selection): allow work horizon > 10 (no upper bound)
Test 4 (Table E.6, endogeneity of occupation choice): keep only workers with stable occupation from 5y before block pre-wave and through block 
Test 5 (Table F.1, Wing (2024)): recode yrscontribution into 5-year bands and midpoints 

Data access and redistribution
------------------------------
SHARE microdata are not redistributed. This code assumes you have lawful access to
SHARE and that you have downloaded the corresponding Stata files.

Expected inputs (not included)
------------------------------
1) Core survey files per wave:
   - cv_r.dta
   - ep.dta
   - gv_health.dta
   - gv_imputations.dta
   - gv_weights.dta  (wave-specific)
2) Job episodes panel (cross-wave file):
   - sharewX_rel9-0-0_gv_job_episodes_panel.dta

Output
------
For baseline results:
- share_stacked.csv
  A stacked individual-wave dataset with block and post indicators, health outcomes,
  work-horizon variables, and covariates (as in the empirical analysis). Used for baseline estimations. 
- share_long.csv
  An individual-wave dataset with original wave-by-wave structure (prior to stacking), including health outcomes,
  work-horizon variables, and covariates (as in the empirical analysis). Used for descriptive statistics of the sample.

For tests:
- share_stacked_T1.csv
  Same as share_stacked.csv, but not excluding retirees. 
- share_stacked_T2.csv
  Same as share_stacked.csv, but not limiting age to 54 years old.
- share_stacked_T3.csv
  Same as share_stacked.csv, but not limiting work horizon to 10 years. 
- share_stacked_T4.csv
  Same as share_stacked.csv, but excluding individuals with changes in ISCO from 5y before block pre-wave and through block.
- share_long_T5.csv
  Same as share_long.csv, but transforming year of contributions into 5-year bands.

Usage
----------
Baseline analysis:
    python share_preprocessing.py
Test 1:
    python share_preprocessing.py --test1
Test 2:
    python share_preprocessing.py --test2
Test 3:
    python share_preprocessing.py --test3
Test 4:
    python share_preprocessing.py --test4
Test 5:
    python share_preprocessing.py --test5

Environment variables
--------------------------------
    SHARE_DIR=/path/to/data
    OUT_DIR=/path/to/output
    SHARE_RELEASE=rel9-0-0
    JOB_EPISODES_FILE=/path/to/sharewX_rel9-0-0_gv_job_episodes_panel.dta

The script attempts to locate wave folders and files using glob patterns so it remains
robust to minor differences in local directory naming.

Notes on retirement-age rules
-----------------------------
Country-specific retirement-age functions are not inlined here to keep the replication
script readable. They are expected to live in a local Python package/folder, e.g.:

    retirement_rules/
        __init__.py
        austria.py    (austria_age, austria_age_early)
        belgium.py    (belgium_age, belgium_age_early)
        ...

and be importable on your PYTHONPATH. See the import section below.

"""

from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path
from typing import Iterable, List

src_path = os.path.abspath("../")
sys.path.append(src_path)

import numpy as np
import pandas as pd

import warnings
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------
# Retirement-age rules (kept external by design)
# ---------------------------------------------------------------------
try:
    from retirement_rules import *  
except Exception as exc:  
    raise ImportError(
        "Could not import retirement-age rule functions. "
        "Please ensure the folder 'retirement_rules' is available on your PYTHONPATH "
        "and defines the required functions (see docstring). Original error: "
        f"{exc}"
    )

# ---------------------------------------------------------------------
# Helper: locating SHARE Stata files
# ---------------------------------------------------------------------
def _find_wave_dir(share_dir: Path, wave: int, release: str) -> Path:
    """
    Locate the directory containing Stata (.dta) files for a given SHARE wave and release.

    The function searches recursively under `share_dir` using several filename
    patterns that match common SHARE folder naming conventions.

    Parameters
    ----------
    share_dir : Path
        Root directory containing SHARE data folders.
    wave : int
        Wave number (e.g., 1, 2, 3, ...).
    release : str
        Release identifier (e.g., "rel8-0-0").

    Returns
    -------
    Path
        Path to the directory containing Stata files for the specified wave.
    """
    patterns = [
        f"**/sharew{wave}_{release}*stata*",
        f"**/sharew{wave}_{release}*",
        f"**/*sharew{wave}*{release}*stata*",
        f"**/*sharew{wave}*{release}*",
    ]
    for pat in patterns:
        for p in share_dir.glob(pat):
            if p.is_dir() and any(p.glob("*.dta")):
                return p
    raise FileNotFoundError(
        f"Could not locate a Stata folder for wave {wave} under {share_dir} (release={release})."
    )

def _find_file_in_dir(wave_dir: Path, file_name: str) -> Path:
    """
    Search for a file inside a directory by partial name match.

    The function looks for files in `wave_dir` whose names contain
    the given `file_name` string. If multiple matches are found,
    it returns the one with the shortest filename (as a simple
    heuristic to prefer the most standard/base file).

    Parameters
    ----------
    wave_dir : Path
        Directory in which to search.
    file_name : str
        Substring of the target filename (e.g., "gv_imputations.dta").

    Returns
    -------
    Path
        Path to the matched file.
    """
    matches = list(wave_dir.glob(f"*{file_name}"))
    if matches:
        return sorted(matches, key=lambda x: len(x.name))[0]
    raise FileNotFoundError(f"Could not find '{file_name}' in {wave_dir}")

def import_share_stata(
    share_dir: Path,
    file_names: List[str],
    waves: Iterable[int],
    release: str = "rel9-0-0",
    convert_categoricals: bool = False,
    *,
    optional_keys: List[str] | None = None,
    strict_base_keys: bool = True,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Import and merge SHARE Stata person-level datasets across multiple waves.

    For each requested wave, the function:
    1. Locates the corresponding SHARE release directory.
    2. Loads all Stata files whose filenames end with one of the specified
       suffixes in `file_names`.
    3. Keeps only person-level datasets (those containing 'mergeid').
    4. Harmonizes selected wave-specific identifiers (e.g., hhid{wave} → hhid).
    5. Merges datasets within the same wave using shared key variables.
    6. Stacks all waves into a single DataFrame.

    Parameters
    ----------
    share_dir : Path
        Root directory containing SHARE data folders.
    file_names : List[str]
        List of filename suffixes used to identify relevant Stata files
        (e.g., ["_gv_imputations.dta", "_cv_r.dta"]).
    waves : Iterable[int]
        SHARE wave numbers to import (e.g., [1, 2, 4, 5]).
    release : str, default "rel9-0-0"
        SHARE release version.
    convert_categoricals : bool, default False
        Whether to convert Stata categorical variables to pandas categoricals.
    optional_keys : List[str] | None
        Additional merge keys to use when available. Defaults to
        ["country", "language", "hhid", "mergeidp", "coupleid"].
    strict_base_keys : bool, default True
        If True, raise an error when required base keys are missing.
        If False, skip non-person-level datasets silently (optionally verbose).
    verbose : bool, default False
        If True, print progress information during loading and merging.

    Returns
    -------
    pd.DataFrame
        A stacked person-level dataset containing all requested waves,
        merged within waves and concatenated across waves.
    """
    if optional_keys is None:
        optional_keys = ["country", "language", "hhid", "mergeidp", "coupleid"]

    base_keys = ["mergeid", "wave"]
    candidate_keys = base_keys + optional_keys

    wave_dfs: List[pd.DataFrame] = []

    for wave in waves:
        wdir = _find_wave_dir(share_dir, wave, release)

        datasets: List[pd.DataFrame] = []
        matched_files: List[Path] = []

        for fname in os.listdir(wdir):
            if any(fname.endswith(sfx) for sfx in file_names):
                fp = Path(wdir) / fname
                matched_files.append(fp)

                d = pd.read_stata(str(fp), convert_categoricals=convert_categoricals)
                d["wave"] = wave
                d = d.rename(
                    columns={
                        f"hhid{wave}": "hhid",
                        f"mergeidp{wave}": "mergeidp",
                        f"coupleid{wave}": "coupleid",
                    }
                )

                if "mergeid" not in d.columns:
                    msg = (
                        f"Wave {wave}: skipping file with no 'mergeid' (likely macro/aux dataset): {fp.name}"
                    )
                    if strict_base_keys:
                        raise KeyError(msg + f". Columns start: {list(d.columns)[:20]} ...")
                    if verbose:
                        print(f"[import_share_stata] {msg}")
                    continue

                datasets.append(d)
                if verbose:
                    print(f"[import_share_stata] Wave {wave}: loaded {fp.name} (n={len(d):,}, p={d.shape[1]:,})")

        if not matched_files:
            raise FileNotFoundError(
                f"No files matching suffixes {file_names} were found in wave {wave} folder: {wdir}"
            )
        if not datasets:
            raise FileNotFoundError(
                f"Files matched {file_names} in wave {wave}, but none were person-level (no 'mergeid'). "
                f"Matched files: {[p.name for p in matched_files]}"
            )

        merged = datasets[0]
        for right in datasets[1:]:
            keys = [k for k in candidate_keys if k in merged.columns and k in right.columns]
            if not all(k in keys for k in base_keys):
                raise KeyError(
                    f"Wave {wave}: cannot merge because base keys {base_keys} are not jointly present. "
                    f"Left has {sorted(set(base_keys) & set(merged.columns))}, "
                    f"right has {sorted(set(base_keys) & set(right.columns))}."
                )
            if verbose:
                print(f"[import_share_stata] Wave {wave}: merging on keys={keys}")
            merged = merged.merge(right, on=keys)

        wave_dfs.append(merged)

    out = pd.concat(wave_dfs, ignore_index=True)
    if verbose:
        print(f"[import_share_stata] Final stacked dataset: n={len(out):,}, p={out.shape[1]:,}")
    return out

# ---------------------------------------------------------------------
# Other helper functions
# ---------------------------------------------------------------------
def isco(df: pd.DataFrame, job_episodes_path: Path) -> pd.DataFrame:
    """
    Construct wave-specific ISCO occupation codes from SHARE job episodes panel
    and merge them into a person-year panel.

    The function:
    1. Loads the SHARE job episodes panel.
    2. Cleans invalid or non-informative ISCO responses.
    3. For each target survey year (2004, 2007, 2011, 2013, 2015),
       selects the most recent valid ISCO code observed up to that year
       for each individual (mergeid).
    4. Creates a person-year dataset of ISCO codes.
    5. Merges the resulting ISCO information into the input DataFrame
       on ['mergeid', 'year'].

    Parameters
    ----------
    df : pd.DataFrame
        Person-year panel dataset containing at least 'mergeid' and 'year'.
    job_episodes_path : Path
        Path to the SHARE job episodes Stata file.

    Returns
    -------
    pd.DataFrame
        The input DataFrame augmented with an 'isco' column containing
        the most recent valid occupation code available up to each year.
    """
    history = pd.read_stata(job_episodes_path, convert_categoricals=True)

    invalid = {
        "Not applicable": np.nan,
        "Not yet coded": np.nan,
        "Not codable": np.nan,
        "Refusal": np.nan,
        "Homemaker": np.nan,
        "Don't know": np.nan,
    }

    isco_year = []
    for year in [2004, 2007, 2011, 2013, 2015]:
        tmp = history.loc[history["year"] <= year].sort_values(by=["mergeid", "year"]).copy()
        tmp["isco"] = tmp["isco"].replace(invalid)
        tmp = tmp.dropna(subset=["isco"])
        last_valid = tmp.groupby("mergeid").last().reset_index()[["mergeid", "isco"]]
        last_valid["year"] = year
        isco_year.append(last_valid)

    isco_full = pd.concat(isco_year, ignore_index=True)
    return df.merge(isco_full, on=["mergeid", "year"], how="left")

def weights(df: pd.DataFrame, share_dir: Path, waves: Iterable[int], release: str = "rel9-0-0") -> pd.DataFrame:
    """
    Import SHARE cross-sectional weights for selected waves and merge them
    into a person-level panel dataset.

    For each requested wave, the function:
    1. Locates the corresponding SHARE release directory.
    2. Loads the 'gv_weights.dta' file.
    3. Identifies the cross-sectional calibrated weight variable (starting with 'cciw').
    4. Renames it to 'w_cross'.
    5. Keeps only ['mergeid', 'w_cross'] and adds the wave indicator.
    6. Stacks all waves and merges the weights into the input DataFrame
       on ['mergeid', 'wave'].

    Parameters
    ----------
    df : pd.DataFrame
        Person-level panel dataset containing at least 'mergeid' and 'wave'.
    share_dir : Path
        Root directory containing SHARE data folders.
    waves : Iterable[int]
        SHARE wave numbers for which weights should be imported.
    release : str, default "rel9-0-0"
        SHARE release version.

    Returns
    -------
    pd.DataFrame
        The input DataFrame augmented with a 'w_cross' column containing
        the cross-sectional weight for each individual-wave observation.
    """
    w_dfs = []
    for wave in waves:
        wdir = _find_wave_dir(share_dir, wave, release)
        fp = _find_file_in_dir(wdir, "gv_weights.dta")
        w_df = pd.read_stata(fp, convert_categoricals=True)

        cciw_candidates = [c for c in w_df.columns if c.startswith("cciw")]
        cciw_col = cciw_candidates[0]
        w_df = w_df.rename(columns={cciw_col: "w_cross"})

        w_df = w_df[["w_cross", "mergeid"]].copy()
        w_df["wave"] = wave
        w_dfs.append(w_df)

    weights_full = pd.concat(w_dfs, ignore_index=True)
    return df.merge(weights_full, on=["mergeid", "wave"], how="left")

def calculate_retirement_age(row: pd.Series) -> int | None:
    """
    Compute the statutory old retirement age for an individual.

    The function dispatches the calculation to a country-specific
    retirement age function using the value in the 'country' column
    of the provided row.

    Parameters
    ----------
    row : pd.Series
        A row from a DataFrame containing at least a 'country' field,
        and any additional variables required by the country-specific
        retirement age functions (e.g., year of birth, gender, year).

    Returns
    -------
    int | None
        The calculated retirement age for the individual.
        Returns None if no corresponding function is defined.
    """
    country = row["country"]
    country_functions_age = {
        "Austria": austria_age,
        "Belgium": belgium_age,  
        "Czech Republic": czech_republic_age, 
        "Denmark": denmark_age, 
        "Estonia": estonia_age,  
        "France": france_age,  
        "Germany": germany_age,  
        "Italy": italy_age, 
        "Luxembourg": luxembourg_age,  
        "Netherlands": netherlands_age,  
        "Slovenia": slovenia_age,  
        "Spain": spain_age,  
        "Sweden": sweden_age,  
        "Switzerland": switzerland_age,  
    }
    fn = country_functions_age.get(country)
    return fn(row) if fn else None

def calculate_retirement_age_early(row: pd.Series) -> int | None:
    """
    Compute the statutory early retirement age for an individual.

    The function dispatches the calculation to a country-specific
    early retirement age function using the value in the 'country' column
    of the provided row.

    Parameters
    ----------
    row : pd.Series
        A row from a DataFrame containing at least a 'country' field,
        and any additional variables required by the country-specific
        early retirement age functions (e.g., year of birth, gender, year).

    Returns
    -------
    int | None
        The calculated retirement age for the individual.
        Returns None if no corresponding function is defined.
    """
    country = row["country"]
    country_functions_age = {
        "Austria": austria_age_early,  
        "Belgium": belgium_age_early, 
        "Czech Republic": czech_republic_age_early,  
        "Denmark": denmark_age_early,  
        "Estonia": estonia_age_early, 
        "France": france_age_early,  
        "Germany": germany_age_early,  
        "Italy": italy_age_early,  
        "Luxembourg": luxembourg_age_early,  
        "Netherlands": netherlands_age_early,  
        "Slovenia": slovenia_age_early, 
        "Spain": spain_age_early,  
        "Sweden": sweden_age_early,  
        "Switzerland": switzerland_age_early,  
    }
    fn = country_functions_age.get(country)
    return fn(row) if fn else None

# ---------------------------------------------------------------------
# Test utilities
# ---------------------------------------------------------------------
def apply_test5_wing_contribution_bands(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create contribution-year bands and replace the original contribution
    variable with band midpoints.

    The function:
    1. Preserves the original 'yrscontribution' values in
       'yrscontribution_real'.
    2. Groups contribution years into predefined 5-year intervals
       (e.g., 0–4, 5–9, ..., 50+).
    3. Creates a categorical band variable ('yrscontribution_band').
    4. Replaces 'yrscontribution' with the midpoint of each band.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing a numeric column 'yrscontribution'.

    Returns
    -------
    pd.DataFrame
        The modified DataFrame with:
        - 'yrscontribution_real' (original values),
        - 'yrscontribution_band' (categorical band),
        - 'yrscontribution' (band midpoint values).
    """
    # Preserve real values
    df["yrscontribution_real"] = df["yrscontribution"].copy()

    bins = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, float("inf")]
    labels = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50+"]

    df["yrscontribution_band"] = pd.cut(
        df["yrscontribution_real"], bins=bins, labels=labels, right=False
    )

    def midpoint(band):
        if pd.isna(band):
            return np.nan
        band = str(band)
        if band.endswith("+"):
            return float(band.replace("+", "")) + 2.5
        low, high = map(int, band.split("-"))
        return (low + high) / 2

    df["yrscontribution"] = df["yrscontribution_band"].apply(midpoint)
    return df

def apply_test4_isco_stability_by_block(
    df_stacked: pd.DataFrame,
    jobs: pd.DataFrame,
) -> pd.DataFrame:
    """
    Enforce block-level occupation stability based on ISCO codes.

    For each (mergeid, block) pair in the stacked panel, the function checks
    whether the individual's occupation (ISCO) remains constant within a
    time window defined as: [pre_year - 5, post_year]

    where:
    - pre_year  = first observed year in the block (within df_stacked),
    - post_year = last observed year in the block.

    Occupation stability is evaluated using:
    1. Job history data (`jobs`), and
    2. The observed ISCO values in `df_stacked`.

    Parameters
    ----------
    df_stacked : pd.DataFrame
        Stacked person-year panel containing at least: 'mergeid', 'block', 'year', 'isco'
    jobs : pd.DataFrame
        Job history dataset containing: 'mergeid', 'year', 'isco'

    Returns
    -------
    pd.DataFrame
        Filtered version of df_stacked containing only stable
        (mergeid, block) pairs.
    """
    history = jobs.copy()

    # Clean ISCO 
    invalid = {
        "Not applicable": np.nan,
        "Not yet coded": np.nan,
        "Not codable": np.nan,
        "Refusal": np.nan,
        "Homemaker": np.nan,
        "Don't know": np.nan,
    }
    if "isco" not in history.columns:
        raise KeyError("jobs/history must include column 'isco' for Test 4.")

    history["isco"] = history["isco"].replace(invalid)
    history["isco"] = history["isco"].astype("string").str[:3].str.zfill(3)

    history["year"] = pd.to_numeric(history["year"], errors="coerce")
    df_stacked["year"] = pd.to_numeric(df_stacked["year"], errors="coerce")

    # Block windows (pre/post year)
    block_years = (
        df_stacked.groupby(["mergeid", "block"])
        .agg(pre_year=("year", "min"), post_year=("year", "max"))
        .reset_index()
    )
    block_years["start_year"] = block_years["pre_year"] - 5

    # Merge history into block windows and keep window years
    hist_win = history.merge(block_years, on="mergeid", how="inner")
    hist_win = hist_win[(hist_win["year"] >= hist_win["start_year"]) & (hist_win["year"] <= hist_win["post_year"])]
    hist_win = hist_win[["mergeid", "block", "year", "isco"]].copy()

    # Include observed ISCO in SHARE stacked years too
    df_iso = df_stacked[["mergeid", "block", "year", "isco"]].copy()

    combined = (
        pd.concat([hist_win, df_iso], ignore_index=True)
        .drop_duplicates(subset=["mergeid", "block", "year", "isco"])
    )

    # Count unique ISCO per (mergeid, block)
    isco_counts = (
        combined.groupby(["mergeid", "block"])["isco"]
        .nunique(dropna=True)
        .reset_index(name="isco_count")
    )

    stable_pairs = isco_counts.loc[isco_counts["isco_count"].isin([0, 1]), ["mergeid", "block"]]
    df_out = df_stacked.merge(stable_pairs, on=["mergeid", "block"], how="inner")
    return df_out

# ---------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments controlling robustness tests and output naming.

    This function defines optional flags corresponding to different
    specification checks (e.g., alternative sample restrictions or
    variable constructions). These flags allow the user to reproduce
    robustness tables by activating specific tests.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments with boolean flags for each test
        and an optional suffix string.
    """
    p = argparse.ArgumentParser()
    p.add_argument("--test1", action="store_true", help="Include retirees (skip retiree exclusion) [Table E.1]")
    p.add_argument("--test2", action="store_true", help="Relax age restriction to age>=50 [Table E.2]")
    p.add_argument("--test3", action="store_true", help="Relax work_horizon cap (no upper bound) [Table E.3]")
    p.add_argument("--test4", action="store_true", help="ISCO stability by block (5y pre through post) [Table E.6]")
    p.add_argument("--test5", action="store_true", help="Wing contribution bands + midpoints (yrscontribution)")

    p.add_argument("--suffix", type=str, default="", help="Optional filename suffix, e.g. _T1")
    return p.parse_args()

def main() -> None:
    """
    Run the full SHARE data construction pipeline and export analysis-ready CSVs.

    Workflow
    --------
    1) Parse CLI flags selecting robustness tests (Tests 1–5) and build an
       output filename suffix automatically when needed.

    2) Resolve input/output paths from environment variables.

    3) Load and merge person-level SHARE Stata datasets for selected waves
       using `import_share_stata`.

    4) Construct and format key variables.

    5) Add cross-sectional weights and occupation (ISCO) codes.

    6) Apply sample restrictions (with test-specific relaxations).

    7) Construct work-horizon measures and policy-change exposure.

    8) Construct cells and build stacked two-wave blocks.

    9) Export outputs:
       - Baseline: exports long (share_long.csv) and stacked (share_stacked.csv)
       - Test 5: exports long structure only (share_long{suffix}.csv)
       - Tests 1–4: exports stacked structure only (share_stacked{suffix}.csv)

    Returns
    -------
    None
        Writes one or more CSV files into OUT_DIR and prints saved paths.
    """

    args = parse_args()

    # Auto suffix if not provided but tests are on
    if args.suffix:
        suffix = args.suffix
    else:
        tests = []
        if args.test1: tests.append("T1")
        if args.test2: tests.append("T2")
        if args.test3: tests.append("T3")
        if args.test4: tests.append("T4")
        if args.test5: tests.append("T5")
        suffix = ("_" + "_".join(tests)) if tests else ""

    # -------------------------
    # Paths
    # -------------------------
    project_root = Path(__file__).resolve().parent
    SHARE_DIR = Path(os.getenv("SHARE_DIR", project_root / "data" / "share")).expanduser().resolve()
    OUT_DIR = Path(os.getenv("OUT_DIR", project_root / "results")).expanduser().resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    RELEASE = os.getenv("SHARE_RELEASE", "rel9-0-0")
    WAVES = [1, 2, 4, 5, 6]

    JOB_EPISODES_FILE = Path(
        os.getenv("JOB_EPISODES_FILE", SHARE_DIR / f"sharewX_{RELEASE}_gv_job_episodes_panel.dta")
    ).expanduser().resolve()

    if not JOB_EPISODES_FILE.exists():
        matches = list(SHARE_DIR.glob(f"**/sharewX_{RELEASE}*job_episodes_panel*.dta"))
        if matches:
            JOB_EPISODES_FILE = matches[0]
        else:
            raise FileNotFoundError(
                "Could not find job episodes panel file. Set JOB_EPISODES_FILE explicitly, "
                f"or place the file under SHARE_DIR. Expected something like sharewX_{RELEASE}_gv_job_episodes_panel.dta"
            )

    # -------------------------
    # 1) Load and merge SHARE data
    # -------------------------
    df = import_share_stata(
        share_dir=SHARE_DIR,
        file_names=["cv_r.dta", "ep.dta", "gv_health.dta"],
        waves=WAVES,
        release=RELEASE,
        convert_categoricals=True,
    )

    imputations = import_share_stata(
        share_dir=SHARE_DIR,
        file_names=["gv_imputations.dta"],
        waves=WAVES,
        release=RELEASE,
        convert_categoricals=True,
    )
    imputations = imputations[imputations["implicat"] == 3].copy()

    jobs = pd.read_stata(JOB_EPISODES_FILE)

    # -------------------------
    # 2) Variables definition and formatting
    # -------------------------
    # Variables from cover screen
    wave_to_year = {1:2004, 2:2007, 4: 2011, 5: 2013, 6: 2015}
    df["year"] = df["wave"].map(wave_to_year).astype(int)

    age_cols = ["age2004", "age2007", "age2011", "age2013", "age2015"]
    df["age"] = df[age_cols].replace({"Don't know": np.nan, "Refusal": np.nan}).bfill(axis=1).iloc[:, 0]
    df["age"] = df["age"].astype("Int64")

    df["job_status"] = df["ep009_"].replace(
        {"Don't know": np.nan, "Refusal": np.nan, "Employee": "Private sector employee"}
    )

    # Variables from imputations
    imputations["tiinc"] = imputations["ydip"].combine_first(imputations["yind"])
    df = df.merge(
        imputations[["mergeid", "wave", "tiinc", "thinc", "yedu", "cjs", "nchild"]],
        on=["mergeid", "wave"],
        how="left",
    )

    # Variables from JEP
    # Years of contributions
    contributions = []
    for y in [2004, 2007, 2011, 2013, 2015]:
        cont = jobs.loc[jobs["year"] <= y].groupby("mergeid")["working"].sum().reset_index()
        cont["year"] = y
        contributions.append(cont)
    contributions_full = pd.concat(contributions, ignore_index=True)
    df = df.merge(
        contributions_full.rename(columns={"working": "yrscontribution"}),
        on=["mergeid", "year"],
        how="left",
    )

    # Test 5 (Wing): recode yrscontribution 
    if args.test5:
        df = apply_test5_wing_contribution_bands(df)

    # Earliest working age
    first_work_age = jobs.loc[jobs["working"] == 1].groupby("mergeid")["age"].min()
    df["first_work_age"] = df["mergeid"].map(first_work_age)

    # Number of children 
    kids_year = []
    for year in [2004, 2007, 2011, 2013, 2015]:
        kids = jobs[jobs.year <= year].groupby("mergeid")["nchildren"].max().reset_index()
        kids["year"] = year
        kids_year.append(kids)
    kids_full = pd.concat(kids_year, ignore_index=True)
    df = df.merge(kids_full.rename(columns={"nchildren": "nb_children"}), on=["mergeid", "year"], how="left")

    # Variables from gv_health module
    df["eurod"] = df["eurod"].replace({"Not depressed": 0, "Very depressed": 12})
    df["eurodcat"] = df["eurodcat"].replace({"Yes": 1, "No": 0})

    # -------------------------
    # 3) Weights + ISCO codes
    # -------------------------
    df = weights(df, share_dir=SHARE_DIR, waves=WAVES, release=RELEASE)
    df = isco(df, job_episodes_path=JOB_EPISODES_FILE)
    df["isco"] = df["isco"].astype("string").str[:3].str.zfill(3) # convert to 3 digits

    # -------------------------
    # 4) Sample restrictions
    # -------------------------
    # Keep only individuals aged 50-54 (50+ for test 2)
    if args.test2:
        df = df.loc[(df["age"] >= 50)].reset_index(drop=True)
    else:
        df = df.loc[(df["age"] >= 50) & (df["age"] <= 54)].reset_index(drop=True)

    # Exclude countries present in only one wave or not present in EWCS
    df = df[~df.country.isin(["Ireland", "Croatia", "Hungary", "Israel", "Greece", "Portugal", "Poland"])]

    # Exclude those with less than 10 years of contributions (different naming for test 5)
    if args.test5:
        df = df[~(df["yrscontribution_real"] < 10)].reset_index(drop=True)
    else:
        df = df[~(df["yrscontribution"] < 10)].reset_index(drop=True)

    # Exclude if earliest working age before 10
    df = df.loc[~(df["first_work_age"] < 10)].reset_index(drop=True)

    # Exclude if special pension conditions
    df = df[~(df.ep098d3 == "Selected")].reset_index(drop=True)

    # Exclude retirees (skip this for test 1)
    if not args.test1:
        df = df[~(
            (df.ep005_ == "Retired") |
            (df.ep005_ == "Don't know") |
            (df.ep005_ == "Refusal") |
            (df.ep005_.isna()) |
            (df.ep110d1 == "Selected") |
            (df.ep110d2 == "Selected")
        )].reset_index(drop=True)

    # Exclude if missing Euro-D scores
    df = df.dropna(subset=["eurod"]).reset_index(drop=True)

    # Drop if missing variables needed for country-specific work horizon definition
    countries = ["Austria", "Belgium", "Estonia", "Greece", "Spain", "Czech Republic", "Italy", "Germany"]
    df = df[~((df["yrscontribution"].isna()) & (df["country"].isin(countries)))].reset_index(drop=True)
    df = df[~((df["nb_children"].isna()) & (df["country"] == "Czech Republic") & (df["gender"] == "Female"))].reset_index(drop=True)

    # Drop if missing weights
    df = df.dropna(subset="w_cross").reset_index(drop=True)

    # -------------------------
    # 5) Work-horizon construction and change
    # -------------------------
    df["retirement_age"] = df.apply(calculate_retirement_age, axis=1)
    df["retirement_age_early"] = df.apply(calculate_retirement_age_early, axis=1)
    df["retirement_age_minimum"] = df.apply(lambda row: min(row["retirement_age"], row["retirement_age_early"]), axis=1)
    df["work_horizon"] = df["retirement_age_minimum"] - df["age"]

    # Counterfactual "old" rules: shift wave index and recompute.
    df["wave_old"] = df["wave"]
    df["wave"] = df["wave"].replace({6:5, 5:4, 4:2, 2:1}).astype("int")

    df["retirement_age_old"] = df.apply(calculate_retirement_age, axis=1)
    df["retirement_age_early_old"] = df.apply(calculate_retirement_age_early, axis=1)
    df["retirement_age_minimum_old"] = df.apply(lambda row: min(row["retirement_age_old"], row["retirement_age_early_old"]), axis=1)
    df["work_horizon_old"] = df["retirement_age_minimum_old"] - df["age"]

    df = df.drop(columns=["wave"]).rename(columns={"wave_old": "wave"})
    df["wh_change"] = df["work_horizon"] - df["work_horizon_old"]

    # recompute current 
    df["retirement_age"] = df.apply(calculate_retirement_age, axis=1)
    df["retirement_age_early"] = df.apply(calculate_retirement_age_early, axis=1)

    # Limit work horizon to 1-10 years (no upper limit for test 3)
    if args.test3:
        df = df[(df["work_horizon"] > 0)].reset_index(drop=True)
    else:
        df = df[(df["work_horizon"] <= 10) & (df["work_horizon"] > 0)].reset_index(drop=True)

    # -------------------------
    # 6) Cell construction 
    # -------------------------
    bins = [-1, 0, 1, 2, 4, np.inf]
    labels = ["No child", "1 child", "2 children", "3–4 children", "5 or more children"]
    df["nb_children"] = pd.cut(df["nb_children"], bins=bins, labels=labels, ordered=True)
    df["job_status"] = df["job_status"].replace({"Public sector employee": "Civil servant"})

    # Depends on country-specific criteria of retirement eligibility
    def create_cells(row):
        if row["country"] in ["Denmark", "Sweden", "Netherlands", "France"]:
            return f"{row['country']}_age{row['age']}"
        elif row["country"] in ["Germany", "Luxembourg", "Poland", "Slovenia", "Switzerland", "Israel"]:
            return f"{row['country']}_age{row['age']}_gender{row['gender']}"
        elif row["country"] == "Spain":
            return f"{row['country']}_age{row['age']}_yrs{row['yrscontribution']}"
        elif row["country"] in ["Austria", "Belgium", "Estonia", "Greece"]:
            return f"{row['country']}_age{row['age']}_gender{row['gender']}_yrs{row['yrscontribution']}"
        elif row["country"] == "Italy":
            return f"{row['country']}_age{row['age']}_gender{row['gender']}_yrs{row['yrscontribution']}_{row['job_status']}"
        else:
            if row["gender"] == "Male":
                return f"{row['country']}_age{row['age']}_gender{row['gender']}_yrs{row['yrscontribution']}"
            else:
                return f"{row['country']}_age{row['age']}_gender{row['gender']}_yrs{row['yrscontribution']}_children{row['nb_children']}"

    df["cell"] = df.apply(create_cells, axis=1)

    # -------------------------
    # 7) Final formatting and variables
    # -------------------------
    df["gender"] = df["gender"].replace({"Male": 0, "Female": 1}).astype(int)

    df["wh_change_bin"] = df["wh_change"].apply(lambda x: 1 if x >= 1 else 0).astype(int)
    df["treat_wave"] = df["wave"].where(df["wh_change_bin"] == 1)
    df["first_treat"] = df.groupby("mergeid")["treat_wave"].transform("min")

    # Long dataframe (for descriptive statistics and Wing model (test 5))
    df_long = df[df["year"] >= 2011].copy()

    # -------------------------
    # 8) Stacked blocks
    # -------------------------
    # Define pairs of waves to build blocks
    df_waves = df_long.sort_values(["mergeid", "wave"])
    waves_present = sorted(df_waves["wave"].unique())
    wave_pairs = [(waves_present[i], waves_present[i + 1]) for i in range(len(waves_present) - 1)]

    stacked_list = []
    for w1, w2 in wave_pairs:
        sub = df_long.loc[df_long["wave"].isin([w1, w2])].copy()
        max_wave = max(w1, w2)

        # Keep only never treated or first treated in the post-wave of the block
        sub = sub.loc[(sub["first_treat"].isna()) | (sub["first_treat"] == max_wave)].copy()
        sub["block"] = int(w1)
        stacked_list.append(sub)

    df_stacked = pd.concat(stacked_list, ignore_index=True)

    # Drop singleton cells within each block
    valid_cells = (
        df_stacked.groupby(["cell", "block"])
        .agg(n_waves=("wave", "nunique"), n_mergeids=("mergeid", "nunique"))
        .query("n_mergeids >= 2")
        .reset_index()[["cell", "block"]]
    )
    df_stacked = df_stacked.merge(valid_cells, on=["cell", "block"], how="inner")

    # Make wh_change fixed within cell-block
    block_max = df_stacked.groupby("block")["wave"].max().reset_index(name="wave_max")
    df_stacked = df_stacked.merge(block_max, on="block", how="left")

    wh_change_post = (
        df_stacked.loc[df_stacked["wave"] == df_stacked["wave_max"], ["cell", "block", "wh_change", "wh_change_bin"]]
        .drop_duplicates(["cell", "block"])
    )
    df_stacked = df_stacked.drop(columns=["wh_change", "wh_change_bin"]).merge(
        wh_change_post, on=["cell", "block"], how="left"
    )

    df_stacked["wh_change"] = df_stacked["wh_change"].fillna(0)
    df_stacked["wh_change_bin"] = df_stacked["wh_change_bin"].fillna(0)

    block_max_wave = df_stacked.groupby("block")["wave"].transform("max")
    df_stacked["post"] = (df_stacked["wave"] == block_max_wave).astype(int)

    df_stacked["cell_block"] = df_stacked["cell"].astype(str) + "_" + df_stacked["block"].astype(str)

    # -------------------------
    # Test 4: ISCO stability filter 
    # -------------------------
    if args.test4:
        df_stacked = apply_test4_isco_stability_by_block(df_stacked=df_stacked, jobs=jobs)

    # -------------------------
    # 9) Keep final variables and export
    # -------------------------
    keep_cols = [
        "mergeid", "wave", "year", "w_cross", "block", "post",
        "eurod", "eurodcat",
        "country", "gender", "age", "yrbirth", "nchild",
        "tiinc", "thinc", "yedu", "job_status", "isco",
        "yrscontribution",
        "retirement_age", "retirement_age_early", "retirement_age_minimum",
        "work_horizon", "wh_change", "wh_change_bin", "first_treat",
        "cell", "cell_block",
        # Test 5 extras (only present if enabled)
        "yrscontribution_real", "yrscontribution_band",
    ]

    is_baseline = not (args.test1 or args.test2 or args.test3 or args.test4 or args.test5)

    if is_baseline:
        # Save both long and stacked for baseline replication
        keep_cols_long = [c for c in keep_cols if c in df_long.columns]
        df_long_out = df_long.loc[:, keep_cols_long].copy()

        out_file_long = OUT_DIR / "share_long.csv"
        df_long_out.to_csv(out_file_long, index=False)
        print(f"Saved: {out_file_long}")

        keep_cols_stacked = [c for c in keep_cols if c in df_stacked.columns]
        df_stacked_out = df_stacked.loc[:, keep_cols_stacked].copy()
        
        out_file_stacked = OUT_DIR / "share_stacked.csv"
        df_stacked_out.to_csv(out_file_stacked, index=False)
        print(f"Saved: {out_file_stacked}")

    elif args.test5:
        # For Test 5: keep the long (wave-by-wave) structure 
        keep_cols_long = [c for c in keep_cols if c in df_long.columns]
        df_test = df_long.loc[:, keep_cols_long].copy()

        out_file = OUT_DIR / f"share_long{suffix}.csv"
        df_test.to_csv(out_file, index=False)
        print(f"Saved: {out_file}")

    else:
        # For Tests 1–4: keep the stacked structure only
        keep_cols_stacked = [c for c in keep_cols if c in df_stacked.columns]
        df_test = df_stacked.loc[:, keep_cols_stacked].copy()

        out_file = OUT_DIR / f"share_stacked{suffix}.csv"
        df_test.to_csv(out_file, index=False)
        print(f"Saved: {out_file}")

    

if __name__ == "__main__":
    main()
