#!/usr/bin/env python3
"""
Paper visualisations: Figures 1 and E.1

This script generates Figures 1 and E.1 used in paper:
"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

Currently implemented:
1) Figure E.1: Permutation (randomization inference) densities from Stata ritest outputs
   - Requires .dta files saved by test_permutation.do (ritest saving(...))

2) Figure 1: Distribution of EWCS job quality indices by ISCO-1 group
   - Requires the clean EWCS file produced by ewcs_preprocessing.py

Usage
-----
# Figure E.1 (permutation tests)
python paper_visualisations.py permutation \
  --perm-dir "/path/to/permutation_dtas" \
  --out "/path/to/images/permutation_tests.png"

# Figure 1 (JQI distributions by ISCO-1)
python paper_visualisations.py jqi_isco \
  --ewcs-file "/path/to/ewcs_jqi.csv" \
  --isco-col "isco" \
  --out "/path/to/images/jqi_by_isco1.png"
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# -------------------------------
# Helpers
# -------------------------------
def _ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")


def _read_perm_coefs(dta_path: Path) -> np.ndarray:
    """
    Read ritest saving() output and return permutation coefficients array.
    ritest stores draws in variable _pm_1.
    """
    _ensure_exists(dta_path)
    df = pd.read_stata(dta_path)

    # Most common ritest output column name:
    if "_pm_1" in df.columns:
        vals = df["_pm_1"].to_numpy()
    else:
        # Fallback: pick the first numeric column
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            raise ValueError(f"No numeric columns found in {dta_path}. Columns={list(df.columns)}")
        vals = df[num_cols[0]].to_numpy()

    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        raise ValueError(f"No finite permutation draws found in {dta_path}")
    return vals


def ri_p_value(perm_coefs: np.ndarray, obs_coef: float) -> tuple[float, float]:
    """
    Two-sided randomization inference p-value, plus its Monte Carlo SE.
    """
    abs_perms = np.abs(perm_coefs)
    obs_abs = abs(obs_coef)
    p = float((abs_perms >= obs_abs).sum() / len(abs_perms))
    se = float(np.sqrt(p * (1 - p) / len(abs_perms)))
    return p, se


# -------------------------------
# Figure E.1: Permutation tests
# -------------------------------
def plot_permutation_figure(
    perm_dir: Path,
    out_path: Path,
    *,
    reps_expected: int | None = 5000,
    dpi: int = 600,
) -> None:
    """
    Create a 2x4 panel KDE figure of permutation distributions with observed coefficient lines.
    """

    files = [
        ("permutation_eurod_wh.dta",        0.0946, "[ΔWH]×POST",   "Euro-D (0–12)"),
        ("permutation_eurod_whcat.dta",     0.1691, "[ΔWH>0]×POST", "Euro-D (0–12)"),
        ("permutation_eurod_wh31.dta",      0.0724, "[ΔWH=1]×POST", "Euro-D (0–12)"),
        ("permutation_eurod_wh32.dta",      0.3903, "[ΔWH>1]×POST", "Euro-D (0–12)"),

        ("permutation_eurodcat_wh.dta",     0.0184, "[ΔWH]×POST",   "Euro-D > 3"),
        ("permutation_eurodcat_whcat.dta",  0.0278, "[ΔWH>0]×POST", "Euro-D > 3"),
        ("permutation_eurodcat_wh31.dta",   0.0039, "[ΔWH=1]×POST", "Euro-D > 3"),
        ("permutation_eurodcat_wh32.dta",   0.0826, "[ΔWH>1]×POST", "Euro-D > 3"),
    ]

    perm_dir = perm_dir.expanduser().resolve()
    out_path = out_path.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sns.set(style="whitegrid", font_scale=0.95)

    # Precompute p-values 
    results = []
    for fname, obs_coef, label, outcome in files:
        dta_path = perm_dir / fname
        perm = _read_perm_coefs(dta_path)
        p, se = ri_p_value(perm, obs_coef)
        results.append({"file": fname, "label": label, "outcome": outcome, "p_value": p, "se_p": se, "n": len(perm)})

    # Plot: 2 rows x 4 cols
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()

    for i, (fname, obs_coef, label, outcome) in enumerate(files):
        dta_path = perm_dir / fname
        perm = _read_perm_coefs(dta_path)

        p_val, _ = ri_p_value(perm, obs_coef)

        ax = axes[i]
        sns.kdeplot(perm, fill=True, ax=ax)  # do not force colors; seaborn default

        # Observed coefficient
        ax.axvline(x=obs_coef, linestyle="-")

        # Percentile reference lines 
        for pctl in [90, 95, 99]:
            perc = np.percentile(perm, pctl)
            ax.axvline(x=perc, linestyle="--", alpha=0.7)

        # Annotation
        ax.text(
            0.95, 0.92,
            f"RI p = {p_val:.4f}",
            transform=ax.transAxes,
            ha="right", va="top",
            fontsize=10, fontweight="bold",
        )

        ax.set_title(label, fontsize=12, fontweight="bold")
        ax.set_xlabel("Coefficient", fontsize=11)
        ax.set_ylabel("Density", fontsize=11)

    # Row headings
    fig.text(0.5, 0.99, "Outcome: Euro-D (0–12)", ha="center", va="top", fontsize=14, fontweight="bold")
    fig.text(0.5, 0.505, "Outcome: Euro-D > 3",   ha="center", va="top", fontsize=14, fontweight="bold")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    # Print p-values table to console
    res_df = pd.DataFrame(results)
    print("\nPermutation test RI p-values (two-sided):")
    print(res_df[["outcome", "label", "p_value", "se_p", "n", "file"]].to_string(index=False))


# -------------------------------
# Figure 1: EWCS JQI distributions by ISCO-1
# -------------------------------
def plot_jqi_by_isco1(
    ewcs_file: Path,
    out_path: Path,
    *,
    isco_col: str = "isco",
    dpi: int = 600,
) -> None:
    """
    Plot stacked histograms of JQI distributions by ISCO-1 major group (1-digit).
    Converts 3-digit ISCO codes to 1-digit major group.
    """

    ewcs_file = ewcs_file.expanduser().resolve()
    out_path = out_path.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    _ensure_exists(ewcs_file)

    # Read file
    if ewcs_file.suffix.lower() == ".dta":
        df = pd.read_stata(ewcs_file)
    else:
        df = pd.read_csv(ewcs_file)

    # ---------------------------
    # Convert ISCO → 1-digit
    # ---------------------------
    if isco_col not in df.columns:
        raise KeyError(f"Column '{isco_col}' not found in EWCS file.")

    # Convert to string, keep first 3 digits safely
    df["_isco_str"] = (
        df[isco_col]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.zfill(3)
    )

    # Extract 1-digit major group
    df["isco_1digit"] = df["_isco_str"].str[0]

    # Keep valid ISCO groups 1–9
    df = df[df["isco_1digit"].isin([str(i) for i in range(1, 10)])].copy()
    df["isco_1digit"] = df["isco_1digit"].astype(int)

    # Sort ISCO groups numerically
    df = df.sort_values("isco_1digit")

    # ---------------------------
    # Plot
    # ---------------------------
    variables = [
        "jqi_physical_environment",
        "jqi_social_environment",
        "jqi_skills_discretion",
        "jqi_working_time_quality",
        "jqi_intensity",
        "jqi_prospects",
    ]
    x_labels = [
        "Physical environment",
        "Social environment",
        "Skills and discretion",
        "Working time quality",
        "Intensity",
        "Prospects",
    ]

    missing = [v for v in variables if v not in df.columns]
    if missing:
        raise KeyError(f"Missing JQI variables: {missing}")

    sns.set(style="whitegrid", font_scale=0.95)

    fig, axes = plt.subplots(2, 3, figsize=(15, 10), sharey=True)
    axes_flat = axes.flatten()

    for ax, var, label in zip(axes_flat, variables, x_labels):
        sns.histplot(
            data=df,
            x=var,
            hue="isco_1digit",
            multiple="stack",
            ax=ax,
        )

        ax.set_xlabel(label, fontsize=14)
        ax.set_ylabel("Count", fontsize=14)
        ax.tick_params(axis="both", labelsize=12)
        ax.set_xticks(range(0, 101, 20))
        ax.set_xlim(0, 100)

        leg = ax.get_legend()
        if leg:
            leg.set_title("ISCO major group (1-digit)", prop={"size": 12})
            for t in leg.get_texts():
                t.set_fontsize(11)

    plt.tight_layout()
    plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

# -------------------------------
# CLI
# -------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper figures.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("permutation", help="Figure E.1 permutation test KDE panels")
    p1.add_argument("--perm-dir", type=str, required=True, help="Directory containing permutation_*.dta files")
    p1.add_argument("--out", type=str, required=True, help="Output image path (png)")
    p1.add_argument("--dpi", type=int, default=600)

    p2 = sub.add_parser("jqi_isco", help="Figure 1: JQI distributions by ISCO-1")
    p2.add_argument("--ewcs-file", type=str, required=True, help="Clean EWCS file (.csv or .dta)")
    p2.add_argument("--isco-col", type=str, default="isco", help="Column name for ISCO-1 group")
    p2.add_argument("--out", type=str, required=True, help="Output image path (png)")
    p2.add_argument("--dpi", type=int, default=600)

    args = parser.parse_args()

    if args.cmd == "permutation":
        plot_permutation_figure(
            perm_dir=Path(args.perm_dir),
            out_path=Path(args.out),
            dpi=args.dpi,
        )
    elif args.cmd == "jqi_isco":
        plot_jqi_by_isco1(
            ewcs_file=Path(args.ewcs_file),
            out_path=Path(args.out),
            isco_col=args.isco_col,
            dpi=args.dpi,
        )
    else:
        raise RuntimeError("Unknown command")


if __name__ == "__main__":
    main()
