/******************************************************************************************
Baseline + Appendix tests (Tables E.1–E.3, E.6) using stacked SHARE, datasets for paper:

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

This do-file reproduces the baseline regressions (Table 3 specification) and runs the same
specification on alternative stacked datasets for 3 sample selection tests (Tables E.1-E.3) and a test for endogeneity of occupational choice (Table E.6) by swapping the input CSV.

Inputs (not included - see share_preprocessing.py for details):
- share_stacked.csv      (baseline)
- share_stacked_T1.csv   (Test 1: include retirees)
- share_stacked_T2.csv   (Test 2: age>=50, no upper cap)
- share_stacked_T3.csv   (Test 3: work_horizon>0, no upper cap)
- share_stacked_T4.csv   (Test 4: ISCO-stable workers)

How to run:
1) Set cd to where the CSV files are stored.
2) Set local TEST to: BASE, T1, T2, T3, or T4.
3) Run: do this_file.do

******************************************************************************************/

* Set the directory to where your input CSV is stored
cd "/path/to/your/data"

* Choose ONE: BASE / T1 / T2 / T3 / T4
local TEST "T4"

* Map test -> file
local SHARE_FILE "share_stacked.csv"
if "`TEST'" == "T1" local SHARE_FILE "share_stacked_T1.csv"
if "`TEST'" == "T2" local SHARE_FILE "share_stacked_T2.csv"
if "`TEST'" == "T3" local SHARE_FILE "share_stacked_T3.csv"
if "`TEST'" == "T4" local SHARE_FILE "share_stacked_T4.csv"

di as txt "Running test setting: `TEST'"
di as txt "Using dataset: `SHARE_FILE'"

capture confirm file "`SHARE_FILE'"
if _rc {
    di as err "ERROR: Cannot find `SHARE_FILE'."
    di as err "Place the selected CSV in the working directory or edit the path."
    exit 601
}

*-------------------------------*
* 1) Import data
*-------------------------------*
import delimited "`SHARE_FILE'", clear varn(1)

* Quick sanity checks: required variables
local reqvars eurod eurodcat wh_change wh_change_bin post block cell_block mergeid
foreach v of local reqvars {
    capture confirm variable `v'
    if _rc {
        di as err "ERROR: Variable `v' not found in the dataset. Check column names."
        exit 198
    }
}

*-------------------------------*
* 2) Key identifiers and controls
*-------------------------------*

* cell_block is used as a high-dimensional fixed effect and for clustering.
capture confirm string variable cell_block
if !_rc {
    encode cell_block, gen(cell_block_num)
}
else {
    * If cell_block is already numeric, just copy it.
    gen long cell_block_num = cell_block
}

* Work-horizon change category:
* 0 = no increase, 1 = +1 year, 2 = >1 year
gen byte wh_change_cat = 0
replace wh_change_cat = 1 if wh_change == 1
replace wh_change_cat = 2 if wh_change > 1

label define whcat 0 "0" 1 "1" 2 ">1", replace
label values wh_change_cat whcat

*-------------------------------*
* 3) Baseline regressions (Table 3)
*-------------------------------*

* --- 3.1 WH continuous --- *
reghdfe eurod c.wh_change##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)

reghdfe eurodcat c.wh_change##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)

* --- 3.2 WH binary --- *
reghdfe eurod i.wh_change_bin##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)

reghdfe eurodcat i.wh_change_bin##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)

* --- 3.3 WH categorical (0, 1, >1) --- *
reghdfe eurod i.wh_change_cat##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)

reghdfe eurodcat i.wh_change_cat##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)
