"""
Retirement-age rules for Luxembourg used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age
- gender

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: gender, age

Returns:
- retirement age (float/int).

"""

def luxembourg_age(row):
    return 65


def luxembourg_age_early(row):
    # Female
    if row["gender"] == "Female":
        return 60
    # Male
    else:
        return 57

