/*******************
Heterogeneity robustness with controls (Tables E.7 and E.8) for paper:

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

This do-file reproduces the heterogeneity regressions (median split by each JQI index),
but in each regression it additionally controls for:
- all other job quality indices (excluding the split index), and
- montly earnings index (jqi_monthly_earnings)


Input (not provided):
- share_ewcs_heterogeneity.csv (constructed by merging SHARE stacked data with EWCS JQI indices,
see share_ewcs_merge.py)

******************************************************************************************/

* Set the directory to where your input CSV is stored
cd "/path/to/your/data"

*-------------------------------*
* 1) Import data
*-------------------------------*
local DATA_FILE "share_ewcs_heterogeneity.csv"

capture confirm file "`DATA_FILE'"
if _rc {
    di as err "ERROR: Cannot find `DATA_FILE'."
    di as err "Place share_ewcs_heterogeneity.csv in the working directory or edit DATA_FILE path."
    exit 601
}

import delimited "`DATA_FILE'", clear varn(1)

* Quick sanity checks: required variables
local reqvars eurod eurodcat wh_change wh_change_bin post block cell_block mergeid ///
    jqi_skills_discretion jqi_social_environment jqi_physical_environment ///
    jqi_intensity jqi_prospects jqi_working_time_quality jqi_monthly_earnings
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
capture confirm string variable cell_block
if !_rc {
    encode cell_block, gen(cell_block_num)
}
else {
    gen long cell_block_num = cell_block
}

* Work-horizon change category:
* 0 = no increase, 1 = +1 year, 2 = >1 year
capture confirm variable wh_change_cat
if _rc {
    gen byte wh_change_cat = 0
    replace wh_change_cat = 1 if wh_change == 1
    replace wh_change_cat = 2 if wh_change > 1

    label define whcat 0 "0" 1 "1" 2 ">1", replace
    label values wh_change_cat whcat
}

* JQI indices used for splits
local indices jqi_physical_environment jqi_social_environment jqi_skills_discretion ///
              jqi_working_time_quality jqi_intensity jqi_prospects

* Earnings control always included in robustness 
local earn_control jqi_monthly_earnings

* Helper: build the controls list = (all indices except `idx`) + earnings
* (Implemented inline inside loop using macro substitution.)

*-------------------------------*
* 3) Outcome: Euro-D (Table E.7)
*-------------------------------*
foreach idx of local indices {

    di as txt "------------------------------------------------------------"
    di as txt "Robust heterogeneity (with controls) split by: `idx' (median)"
    di as txt "Outcome: Euro-D (Table E.7)"
    di as txt "------------------------------------------------------------"

    quietly su `idx', detail
    scalar median = r(p50)
    di as txt "Index: `idx'  | median = " %9.3f median

    * Build controls list: all other indices except `idx`
    local controls ""
    foreach j of local indices {
        if "`j'" != "`idx'" local controls "`controls' c.`j'"
    }
    * Add earnings
    local controls "`controls' c.`earn_control'"

    di as txt "Controls included: `controls'"

    * --- WH continuous ---
    di as txt "=== WH continuous | Below median ==="
    reghdfe eurod c.wh_change##i.post `controls' if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "=== WH continuous | Above median ==="
    reghdfe eurod c.wh_change##i.post `controls' if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    * --- WH binary ---
    di as txt "=== WH binary | Below median ==="
    reghdfe eurod i.wh_change_bin##i.post `controls' if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "=== WH binary | Above median ==="
    reghdfe eurod i.wh_change_bin##i.post `controls' if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    * --- WH categorical ---
    di as txt "=== WH categorical | Below median ==="
    reghdfe eurod i.wh_change_cat##i.post `controls' if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "=== WH categorical | Above median ==="
    reghdfe eurod i.wh_change_cat##i.post `controls' if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)
}

*-------------------------------*
* 4) Outcome: Euro-D > 3 (Table E.8)
*-------------------------------*
foreach idx of local indices {

    di as txt "------------------------------------------------------------"
    di as txt "Robust heterogeneity (with controls) split by: `idx' (median)"
    di as txt "Outcome: Euro-D > 3 (Table E.8)"
    di as txt "------------------------------------------------------------"

    quietly su `idx', detail
    scalar median = r(p50)
    di as txt "Index: `idx'  | median = " %9.3f median

    * Build controls list: all other indices except `idx`
    local controls ""
    foreach j of local indices {
        if "`j'" != "`idx'" local controls "`controls' c.`j'"
    }
    * Add earnings
    local controls "`controls' c.`earn_control'"

    di as txt "Controls included: `controls'"

    * --- WH continuous ---
    di as txt "=== WH continuous | Below median ==="
    reghdfe eurodcat c.wh_change##i.post `controls' if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "=== WH continuous | Above median ==="
    reghdfe eurodcat c.wh_change##i.post `controls' if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    * --- WH binary ---
    di as txt "=== WH binary | Below median ==="
    reghdfe eurodcat i.wh_change_bin##i.post `controls' if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "=== WH binary | Above median ==="
    reghdfe eurodcat i.wh_change_bin##i.post `controls' if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    * --- WH categorical ---
    di as txt "=== WH categorical | Below median ==="
    reghdfe eurodcat i.wh_change_cat##i.post `controls' if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "=== WH categorical | Above median ==="
    reghdfe eurodcat i.wh_change_cat##i.post `controls' if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)
}
