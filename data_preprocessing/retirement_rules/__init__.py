from .austria import *
from .belgium import *
from .czech_republic import *
from .denmark import *
from .estonia import *
from .france import *
from .germany import *
from .italy import *
from .luxembourg import *
from .netherlands import *
from .slovenia import *
from .spain import *
from .sweden import *
from .switzerland import *

"""
Country-specific retirement age rules used in the SHARE analysis.

This package provides a collection of country-level functions that approximate statutory old and
early retirement ages for individuals observed in the SHARE data. Each country file implements
two main functions:

    - COUNTRY_age(row)
    - COUNTRY_age_early(row)

where COUNTRY denotes the country name (e.g. `austria_age`, `austria_age_early`).

The functions translate institutional retirement rules into individual-level retirement age
thresholds using respondent characteristics available in SHARE. 
 
The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Depending on country, retirement eligibility is modeled as a function of:

    - current age,
    - year of birth,
    - gender,
    - SHARE wave (used as a proxy for the relevant policy regime),
    - accumulated years of contributions,
    - number of children,
    - sector of employmnet.

Many statutory and early retirement systems impose a minimum number of contribution years.
In the functions provided here, this requirement is implemented as follows:

- If the respondent is expected to satisfy the minimum contribution requirement by the statutory
  (or early) retirement age, the function returns that statutory age.
- Otherwise, the function returns the age at which the minimum contribution requirement would
  be met, assuming that one additional year of age corresponds to one additional year of
  contributions, and assuming continuous employment until retirement.

This assumption allows us to approximate retirement eligibility using observed contribution
histories without modeling detailed future labor supply decisions.

Inputs and outputs
------------------
Each function takes a single argument:

    row : pandas.Series

which must contain the columns corresponding to retirement eligibility criteria in a given country.

The function returns a numeric value representing the implied retirement age for that individual.

Scope and limitations
---------------------
These functions are intended as an approximation suitable for cross-country comparative analysis.
They do not account for:
    - special occupational schemes,
    - disability or health-related retirement pathways,
    - country-specific exceptions beyond the main statutory and early retirement rules,
    - nonlinear or discontinuous future contribution paths.

Usage in the project
--------------------
The retirement age functions are used to compute work horizon measures and treatment definitions
in the SHARE-based empirical analysis. 

For detailed country-specific rules and wave mappings, see the individual country modules.
"""

