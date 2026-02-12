/*******************
TEST 5 (Table F.1) stacked DiD implementation (Wing et al., 2024) for paper:

"Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

This do-file implements the stacked difference-in-differences/event-study approach following
Wing et al. (2024), using cell-level aggregated outcomes and stacked "sub-experiments".

Input (not provided in replication package):
- share_long_T5.csv
  (constructed from proprietary SHARE data; see share_preprocessing.py)
  
Notes:
- The dataset used here is in "long" (unstacked) format.
- We define adoption year (adopt_year) as the first year in which wh_change > 0 within a cell.
- Controls are treated as "not-yet-treated within the observed period" (never-treated in sample).
- Time spacing between SHARE waves used here is 2 years; therefore kappa_pre=2 corresponds to one lagged wave.

Requirements:
- reghdfe installed (and dependencies)
    ssc install reghdfe, replace
    ssc install ftools, replace
    ssc install ivreg2, replace

******************************************************************************************/

clear all
set more off

* Set the directory to where your input CSV is stored
cd "/path/to/your/data"

*-------------------------------*
* 1) Import data
*-------------------------------*
local DATA_FILE "share_long_T5.csv"

capture confirm file "`DATA_FILE'"
if _rc {
    di as err "ERROR: Cannot find `DATA_FILE'."
    di as err "Place share_long_T5.csv in the working directory or edit DATA_FILE path."
    exit 601
}

import delimited "`DATA_FILE'", clear varn(1)

* Quick sanity checks: required variables
local reqvars cell year wave wh_change eurod eurodcat age gender job_status country yedu thinc yrbirth ///
             yrscontribution nchild
foreach v of local reqvars {
    capture confirm variable `v'
    if _rc {
        di as err "ERROR: Variable `v' not found in the dataset. Check column names."
        exit 198
    }
}

* Ensure required packages exist
capture which reghdfe
if _rc {
    di as err "ERROR: reghdfe is not installed."
    di as err "Install it with: ssc install reghdfe, replace"
    exit 199
}

*-------------------------------*
* 2) Sample definition for Test 5
*-------------------------------*
* In this dataset, wh_change is defined relative to the previous wave.
* We keep the baseline pre-treatment observations in wave 4 by dropping
* wave 4 observations that already show a positive change.
drop if wave == 4 & wh_change > 0

* Drop first_treat if it exists (we re-construct adoption year below)
capture confirm variable first_treat
if !_rc drop first_treat


*-------------------------------*
* 3) Define adoption year at the cell level
*-------------------------------*
* Adoption year is the first year in which wh_change > 0 for a given cell.
gen t = .
replace t = 2015 if year == 2015 & wh_change > 0
replace t = 2013 if year == 2013 & wh_change > 0

encode cell, gen(cell_num)
egen adopt_year = min(t), by(cell_num)

*-------------------------------*
* 4) Clean/prepare covariates
*-------------------------------*
capture confirm numeric variable yedu
if !_rc {
    replace yedu = 10 if yedu == 10.5
    replace yedu = 17 if yedu == 17.5
}

encode job_status, gen(job_status_num)
encode country, gen(country_num)

tab job_status_num, gen(job_status_d)
tab country_num, gen(country_num_d)
tab yrbirth, gen(yrbirth_d)

keep cell cell_num year adopt_year wh_change eurod eurodcat age gender ///
     job_status_d* yrscontribution nchild country_num_d* yedu thinc yrbirth_d*

*-------------------------------*
* 5) Define treatment versions and collapse to cell-year level
*-------------------------------*
* Categoric treatment versions
gen wh_change_cat = 0
replace wh_change_cat = 1 if wh_change == 1
replace wh_change_cat = 2 if wh_change > 1

* Count observations per cell-year (based on non-missing eurod)
gen count_obs = eurod

* Collapse to cell-year-adoption panel (cell-level means)
collapse (mean) eurod eurodcat age yrscontribution thinc yedu nchild wh_change wh_change_cat ///
        (median) gender job_status_d* country_num_d* yrbirth_d* ///
        (count) count_obs, by(cell_num year adopt_year)

sort cell_num year adopt_year
order cell_num year adopt_year


********************************************************************************
* 6) Create sub-experiment datasets (stacking procedure)
********************************************************************************

* Create output folder for temporary sub-experiment datasets
capture mkdir temp

* Clear programs
capture program drop _all

program define create_sub_exp
    syntax, timeID(string) groupID(string) adoptionTime(string) focalAdoptionTime(int) ///
           kappa_pre(integer) kappa_post(integer)

    quietly {
        preserve

        * Determine time range for feasibility checks
        summarize `timeID'
        local minTime = r(min)
        local maxTime = r(max)

        * Identify the sub-experiment: treated at focalAdoptionTime + controls that adopt late enough.
        gen sub_exp = `focalAdoptionTime' if `adoptionTime' == `focalAdoptionTime'
        replace sub_exp = `focalAdoptionTime' if `adoptionTime' > `focalAdoptionTime' + `kappa_post'
        keep if sub_exp != .

        * Treatment indicator within sub-experiment
        gen treat = (`adoptionTime' == `focalAdoptionTime')

        * Event time relative to sub-experiment adoption year
        gen event_time = `timeID' - sub_exp

        * Post indicator
        gen post = (event_time >= 0)

        * Keep event window [-kappa_pre, +kappa_post]
        keep if inrange(event_time, -`kappa_pre', `kappa_post')

        * Feasibility: drop adoptions too early to have pre-period
        drop if `adoptionTime' < `minTime' + `kappa_pre'

        compress
        save subexp`focalAdoptionTime', replace
        restore
    }
end

* Parameters:
* Because SHARE waves here are spaced by 2 years, kappa_pre=2 corresponds to one pre wave.
local kappa_pre  2
local kappa_post 0

* Loop over adoption years present in the data
levelsof adopt_year, local(alist)
di as txt "Adoption years found: `alist'"

quietly {
    foreach j of numlist `alist' {
        preserve
        create_sub_exp, ///
            timeID(year) ///
            groupID(cell_num) ///
            adoptionTime(adopt_year) ///
            focalAdoptionTime(`j') ///
            kappa_pre(`kappa_pre') ///
            kappa_post(`kappa_post')
        restore
    }
}

* Append feasible stacks together
quietly {
    summarize year
    local minTime = r(min)
    local maxTime = r(max)

    gen feasible_year = adopt_year
    replace feasible_year = . if adopt_year < `minTime' + `kappa_pre'
    replace feasible_year = . if adopt_year > `maxTime' - `kappa_post'

    summarize feasible_year
    local minadopt = r(min)

    levelsof feasible_year, local(flist)
    clear

    foreach j of numlist `flist' {
        di as txt "Appending sub-experiment: `j'"
        if `j' == `minadopt' use subexp`j', clear
        else append using subexp`j'
    }
}

********************************************************************************
* 7) Panel restrictions and treatment coding
********************************************************************************

* Keep only cells with sufficient observations in each cell-year
keep if count_obs >= 10

* Each cell must be observed both pre and post within each sub-experiment
egen n_min = min(event_time), by(cell_num sub_exp)
egen n_max = max(event_time), by(cell_num sub_exp)
keep if n_min == -2 & n_max == 0
drop n_min n_max

* Treatment intensity variables at the cell level
egen treat_cat  = max(wh_change_cat), by(cell_num)
egen treat_cont = max(wh_change),     by(cell_num)

* Summary: treated/control counts by sub-experiment
preserve
keep if event_time == 0
gen N_treated  = treat
gen N_control  = 1 - treat
gen N_total    = 1
collapse (sum) N_treated N_control N_total, by(sub_exp)
list sub_exp N_treated N_control N_total
restore


********************************************************************************
* 8) Weights for stacked regression (Wing et al. approach)
********************************************************************************
capture program drop compute_weights
program define compute_weights
    syntax, treatedVar(string) eventTimeVar(string) groupID(string) subexpVar(string)

    * Count treated units per sub-experiment and overall
    bysort `subexpVar' `groupID': gen counter_treat = _n if `treatedVar' == 1
    egen n_treat_tot = total(counter_treat)
    by `subexpVar': egen n_treat_sub = total(counter_treat)

    * Count control units per sub-experiment and overall
    bysort `subexpVar' `groupID': gen counter_control = _n if `treatedVar' == 0
    egen n_control_tot = total(counter_control)
    by `subexpVar': egen n_control_sub = total(counter_control)

    * Define weights: treated weight = 1, controls reweighted by treated/control shares
    gen stack_weight = 1 if `treatedVar' == 1
    replace stack_weight = (n_treat_sub/n_treat_tot)/(n_control_sub/n_control_tot) if `treatedVar' == 0
end

compute_weights, ///
    treatedVar(treat) ///
    eventTimeVar(event_time) ///
    groupID(cell_num) ///
    subexpVar(sub_exp)


********************************************************************************
* 9) Stacked regressions
********************************************************************************

* Create dummy variables for event-time (omit -2 as baseline)
char event_time[omit] -2
xi i.event_time

*----------------------------------*
* 9.1 Binary treatment (treat)
*----------------------------------*
reghdfe eurod i.treat##i._I* [aw = stack_weight], cluster(cell_num)

reghdfe eurodcat i.treat##i._I* [aw = stack_weight], cluster(cell_num)

*----------------------------------*
* 9.2 Categorical treatment (treat_cat)
*----------------------------------*
reghdfe eurod i.treat_cat##i._I* [aw = stack_weight], cluster(cell_num)

reghdfe eurodcat i.treat_cat##i._I* [aw = stack_weight], cluster(cell_num)

*----------------------------------*
* 9.3 Continuous treatment (treat_cont)
*----------------------------------*
reghdfe eurod c.treat_cont##i._I* [aw = stack_weight], cluster(cell_num)

reghdfe eurodcat c.treat_cont##i._I* [aw = stack_weight], cluster(cell_num)
