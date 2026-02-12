/*******************
Baseline analysis for paper:

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

This do-file reproduces the baseline regressions reported in Table 3 using the stacked SHARE dataset.

Inputs (not provided in replication package):
- share_stacked.csv  (constructed from SHARE data; see share_preprocessing.py)

******************************************************************************************/

* Set the directory to where your input CSV is stored
cd "/path/to/your/data"

*-------------------------------*
* 1) Import data
*-------------------------------*
local SHARE_FILE "share_stacked.csv"


capture confirm file "`SHARE_FILE'"
if _rc {
    di as err "ERROR: Cannot find `SHARE_FILE'."
    di as err "Place share_stacked.csv in the working directory or edit SHARE_FILE path."
    exit 601
}

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


* --- 4.2 WH binary --- *
reghdfe eurod i.wh_change_bin##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)

reghdfe eurodcat i.wh_change_bin##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)


* --- 4.3 WH categorical (0, 1, >1) --- *
reghdfe eurod i.wh_change_cat##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)

reghdfe eurodcat i.wh_change_cat##i.post, ///
    absorb(cell_block_num post#block) ///
    vce(cluster cell_block_num mergeid)
