/*******************
Permutation tests (Figure E.1) for paper:

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

This do-file reproduces the permutation (randomization inference) tests behind Figure E.1.
It runs the baseline stacked SHARE regressions but uses ritest to permute the treatment
variable and store the distribution of the interaction coefficient.

Input (not provided in replication package):
- share_stacked.csv  (constructed from SHARE data; see share_preprocessing.py)

Outputs:
- Stata .dta files saved by ritest in the working directory:
    permutation_eurod_wh.dta
    permutation_eurodcat_wh.dta
    permutation_eurod_whcat.dta
    permutation_eurodcat_whcat.dta
    permutation_eurod_wh31.dta
    permutation_eurod_wh32.dta
    permutation_eurodcat_wh31.dta
    permutation_eurodcat_wh32.dta

******************************************************************************************/

* Set the directory to where your input CSV is stored
cd "/path/to/your/data"

local SHARE_FILE "share_stacked.csv"

capture confirm file "`SHARE_FILE'"
if _rc {
    di as err "ERROR: Cannot find `SHARE_FILE'."
    di as err "Place share_stacked.csv in the working directory or edit SHARE_FILE path."
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

*-------------------------------*
* 3) Permutation tests (Figure E.1)
*-------------------------------*

* --- WH continuous --- *

* Euro-D 0-12
ritest wh_change _b[c.wh_change#1.post], reps(5000) seed(123) ///
    saving(permutation_eurod_wh, replace): ///
    reghdfe eurod c.wh_change##i.post, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

* Euro-D >3
ritest wh_change _b[c.wh_change#1.post], reps(5000) seed(123) ///
    saving(permutation_eurodcat_wh, replace): ///
    reghdfe eurodcat c.wh_change##i.post, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)


* --- WH binary --- *

* Euro-D 0-12
ritest wh_change_bin _b[1.wh_change_bin#1.post], reps(5000) seed(123) ///
    saving(permutation_eurod_whcat, replace): ///
    reghdfe eurod i.wh_change_bin##i.post, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

* Euro-D >3
ritest wh_change_bin _b[1.wh_change_bin#1.post], reps(5000) seed(123) ///
    saving(permutation_eurodcat_whcat, replace): ///
    reghdfe eurodcat i.wh_change_bin##i.post, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)


* --- WH categoric (0, 1, >1) --- *

* Euro-D 0-12
ritest wh_change_cat _b[1.wh_change_cat#1.post], reps(5000) seed(123) ///
    saving(permutation_eurod_wh31, replace): ///
    reghdfe eurod i.wh_change_cat##i.post, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

ritest wh_change_cat _b[2.wh_change_cat#1.post], reps(5000) seed(123) ///
    saving(permutation_eurod_wh32, replace): ///
    reghdfe eurod i.wh_change_cat##i.post, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

* Euro-D >3
ritest wh_change_cat _b[1.wh_change_cat#1.post], reps(5000) seed(123) ///
    saving(permutation_eurodcat_wh31, replace): ///
    reghdfe eurodcat i.wh_change_cat##i.post, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)

ritest wh_change_cat _b[2.wh_change_cat#1.post], reps(5000) seed(123) ///
    saving(permutation_eurodcat_wh32, replace): ///
    reghdfe eurodcat i.wh_change_cat##i.post, ///
        absorb(cell_block_num post#block) ///
        vce(cluster cell_block_num mergeid)
