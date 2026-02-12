"""
Retirement-age rules for Netherlands used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age
- SHARE wave (policy timing proxy)

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: wave, age

Returns:
- retirement age (float/int).

"""

def netherlands_age(row):
    # Waves 1-5
    if row["wave"] < 6:
        return 65
    # Wave 6
    else:
        return 66


def netherlands_age_early(row):
    return 60


