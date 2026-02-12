This repository contains the full replication code used to produce the
main empirical results and appendix analyses for the paper:

**"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"**
**by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy**

The package includes:

-   Python scripts for SHARE and EWCS preprocessing
-   Stata do-files for main analyses and tests 
-   Python and R scripts for figures

------------------------------------------------------------------------

## 1. Data Requirements

This replication package does **not** redistribute microdata.

You must obtain lawful access to:

-   **SHARE Release 9.0.0 (rel9-0-0)** microdata
-   **SHARE job episodes panel**
-   **EWCS microdata for 2010 and 2015 with 4-digit ISCO codes**

Place the downloaded files in your local data directories before running
any scripts.

------------------------------------------------------------------------

## 2. Software Requirements

### Python (3.9+ recommended)

Required packages: - pandas - numpy - matplotlib - seaborn -
pyreadstat - pypandoc

Install example: pip install pandas numpy matplotlib seaborn pyreadstat
pypandoc

### Stata (16+ recommended)

Required packages: - reghdfe - ftools - ritest - ivreg2

Install inside Stata: ssc install ftools, replace ssc install reghdfe,
replace ssc install ritest, replace ssc install ivreg2, replace

### R (4.0+ recommended)

Required packages: - ggplot2 - dplyr - tidyr

Install example: install.packages(c("ggplot2","dplyr","tidyr"))

------------------------------------------------------------------------

## 3. Python Data Preparation Scripts ("data_preprocessing"" folder)

### share_preprocessing.py

Prepares SHARE Release 9.0.0 microdata.

Outputs (baseline): - share_stacked.csv - share_long.csv

Appendix test outputs: - share_stacked_T1.csv - share_stacked_T2.csv -
share_stacked_T3.csv - share_stacked_T4.csv - share_long_T5.csv

Example usage: python share_preprocessing.py python
share_preprocessing.py --test1 python share_preprocessing.py --test5

Environment variables: - SHARE_DIR - OUT_DIR - SHARE_RELEASE -
JOB_EPISODES_FILE

### ewcs_preprocessing.py

Cleans EWCS microdata and constructs job-quality indices.

Outputs: - ewcs_jqi.csv 

Example usage: python ewcs_preprocessing.py

Environment variables: - DATA_DIR - OUT_DIR

### share_ewcs_merge.py

Merges SHARE stacked data with EWCS job-quality indices.

Outputs: - share_ewcs_heterogeneity.csv 

Example usage: python share_ewcs_merge.py


Environment variables: - DATA_DIR - OUT_DIR

### "retirement_rules"" folder

Contains country-specific Python scripts for definition of 
statutory old and early retirement ages (based on MISSOC tables). 

------------------------------------------------------------------------

## 4. Stata Analysis Files 

## "main_analyses" folder

### baseline_analysis.do

Reproduces baseline regressions (Table 3).

### heterogeneity_analysis.do

Reproduces heterogeneity regressions (Tables 4 and 5).

## "tests" folder

### Appendix Tests

-   tests_sample_endogeneity.do
-   test_gender.do
-   test_poolability.do
-   test_controls.do
-   test_permutation.do
-   test_wing.do

------------------------------------------------------------------------

## 5. Figures ("figures" folder)

### figures_1\_e1.py

Reproduces: - Permutation test density panels (Figure E.1) - Distribution
of JQI by ISCO 1-digit (Figure 1)

### figures_2\_3.R

Reproduces Figures 2 and 3 (heterogeneity results).

------------------------------------------------------------------------

## 6. Replication Workflow

Step 1 -- Build SHARE datasets: python share_preprocessing.py

Step 2 -- Build EWCS dataset and merge: python ewcs_preprocessing.py
python share_ewcs_merge.py

Step 3 -- Run Stata regressions: do baseline_analysis.do do
heterogeneity_analysis.do

Step 4 -- Run Stata tests: do tests_sample_endogeneity.do test_gender.do
test_poolability.do test_controls.do test_permutation.do test_wing.do

Step 5 -- Generate figures: python figures_1\_e1.py
source("figures_2\_3.R")

------------------------------------------------------------------------

This replication package requires lawful access to SHARE and EWCS data.
Please cite SHARE and EWCS according to their official guidelines.
