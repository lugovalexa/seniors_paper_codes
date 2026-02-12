/*******************
Heterogeneity analysis for paper:

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

This do-file reproduces the heterogeneity regressions where the effect of work-horizon changes
is estimated separately for below-median vs above-median job quality index values (median split), as presented in Tables 4 and 5 of the paper.

Inputs (not provided in replication package):
- share_ewcs_heterogeneity.csv (constructed by merging SHARE stacked data with EWCS JQI indices;
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
    jqi_intensity jqi_prospects jqi_working_time_quality
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
* 3) Heterogeneity regressions (median split) 
*-------------------------------*
* For each job quality index:
* 1) Compute the median
* 2) Run regressions separately for index < median and index > median

local indices jqi_physical_environment jqi_social_environment jqi_skills_discretion  ///
              jqi_working_time_quality jqi_intensity jqi_prospects 
			  
*--------------------------------------*
* Outcome: Euro-D (0-12) (Table 4)
*--------------------------------------*

foreach idx of local indices {

    di as txt "------------------------------------------------------------"
    di as txt "Heterogeneity split by: `idx' (median split)"
    di as txt "------------------------------------------------------------"

    * Compute median of current index (within the estimation sample)
    quietly su `idx', detail
    scalar median = r(p50)

    di as txt "Index: `idx'  | median = " %9.3f median "

    di as txt "==========================="
    di as txt "3.1 WH continuous"
    di as txt "==========================="
	
	di as txt "===* Below median *==="
    reghdfe eurod c.wh_change##i.post if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)
		
	di as txt "===* Above median *==="
    reghdfe eurod c.wh_change##i.post if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "==========================="
    di as txt "3.2 WH binary"
    di as txt "==========================="
    
	di as txt "===* Below median *==="
    reghdfe eurod i.wh_change_bin##i.post if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

	di as txt "===* Above median *==="
    reghdfe eurod i.wh_change_bin##i.post if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "==========================="
    di as txt "3.3 WH categoric"
    di as txt "==========================="

	di as txt "===* Below median *==="
    reghdfe eurod i.wh_change_cat##i.post if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "===* Above median *==="
    reghdfe eurod i.wh_change_cat##i.post if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)
		
}

*--------------------------------------*
* Outcome: Euro-D > 3 (Table 5)
*--------------------------------------*
foreach idx of local indices {

    di as txt "------------------------------------------------------------"
    di as txt "Heterogeneity split by: `idx' (median split)"
    di as txt "------------------------------------------------------------"

    * Compute median of current index (within the estimation sample)
    quietly su `idx', detail
    scalar median = r(p50)

    di as txt "Index: `idx'  | median = " %9.3f median "

    di as txt "==========================="
    di as txt "3.1 WH continuous"
    di as txt "==========================="
	
	di as txt "===* Below median *==="
    reghdfe eurodcat c.wh_change##i.post if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)
		
	di as txt "===* Above median *==="
    reghdfe eurodcat c.wh_change##i.post if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "==========================="
    di as txt "3.2 WH binary"
    di as txt "==========================="
    
	di as txt "===* Below median *==="
    reghdfe eurodcat i.wh_change_bin##i.post if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

	di as txt "===* Above median *==="
    reghdfe eurodcat i.wh_change_bin##i.post if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "==========================="
    di as txt "3.3 WH categoric"
    di as txt "==========================="

	di as txt "===* Below median *==="
    reghdfe eurodcat i.wh_change_cat##i.post if `idx' < median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

    di as txt "===* Above median *==="
    reghdfe eurodcat i.wh_change_cat##i.post if `idx' > median, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)
		
}
