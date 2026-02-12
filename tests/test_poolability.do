/*******************
Poolability test (Tables E.4 and E.5) for paper:

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

This do-file re-runs the baseline Table 3 regressions repeatedly, each time excluding
ONE country from the sample (leave-one-country-out).

Input (not provided in replication package):
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

* Quick sanity checks
local reqvars eurod eurodcat wh_change wh_change_bin post block cell_block mergeid country
foreach v of local reqvars {
    capture confirm variable `v'
    if _rc {
        di as err "ERROR: Variable `v' not found in the dataset. Check column names."
        exit 198
    }
}

*-------------------------------*
* 2) Prepare identifiers / controls
*-------------------------------*
* cell_block FE & clustering key
capture confirm string variable cell_block
if !_rc {
    encode cell_block, gen(cell_block_num)
}
else {
    gen long cell_block_num = cell_block
}

* WH categorical (0, 1, >1)
capture confirm variable wh_change_cat
if _rc {
    gen byte wh_change_cat = 0
    replace wh_change_cat = 1 if wh_change == 1
    replace wh_change_cat = 2 if wh_change > 1

    label define whcat 0 "0" 1 "1" 2 ">1", replace
    label values wh_change_cat whcat
}

* Make sure country is a clean string (import delimited usually makes it string; this is defensive)
capture confirm string variable country
if _rc {
    tostring country, replace force
}

* Encode country to numeric with value labels
capture drop country_id
encode country, gen(country_id)

* Get numeric levels
quietly levelsof country_id, local(country_ids)

di as txt "Countries in sample (value label):"
foreach id of local country_ids {
    local cname : label (country_id) `id'
    di as txt " - `cname'"
}

*-------------------------------*
* 3) Leave-one-country-out loop
*-------------------------------*
foreach id of local country_ids {

    local cname : label (country_id) `id'

    preserve
        keep if country_id != `id'

        di as txt _n "=================================================="
        di as txt "Poolability test: EXCLUDING country = `cname'"
        di as txt "Remaining N = " _N
        di as txt "=================================================="

        * --- WH continuous --- *
        reghdfe eurod c.wh_change##i.post, ///
            absorb(cell_block_num post#block) ///
            vce(cluster cell_block_num mergeid)

        reghdfe eurodcat c.wh_change##i.post, ///
            absorb(cell_block_num post#block) ///
            vce(cluster cell_block_num mergeid)

        * --- WH binary --- *
        reghdfe eurod i.wh_change_bin##i.post, ///
            absorb(cell_block_num post#block) ///
            vce(cluster cell_block_num mergeid)

        reghdfe eurodcat i.wh_change_bin##i.post, ///
            absorb(cell_block_num post#block) ///
            vce(cluster cell_block_num mergeid)

        * --- WH categorical (0, 1, >1) --- *
        reghdfe eurod i.wh_change_cat##i.post, ///
            absorb(cell_block_num post#block) ///
            vce(cluster cell_block_num mergeid)

        reghdfe eurodcat i.wh_change_cat##i.post, ///
            absorb(cell_block_num post#block) ///
            vce(cluster cell_block_num mergeid)

    restore
}
