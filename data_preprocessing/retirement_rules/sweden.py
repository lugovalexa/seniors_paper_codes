"""
Retirement-age rules for Sweden used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: age

Returns:
- retirement age (float/int).

"""

def sweden_age(row):
    return 65


def sweden_age_early(row):
    return 61
