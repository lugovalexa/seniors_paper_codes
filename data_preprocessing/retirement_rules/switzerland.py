"""
Retirement-age rules for Switzerland used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age
- gender
- SHARE wave (policy timing proxy)

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: gender, wave, age

Returns:
- retirement age (float/int).

"""

def switzerland_age(row):
    # Male
    if row["gender"] == "Male":
        return 65

    # Female
    else:
        # Wave 1
        if row["wave"] == 1:
            return 63
        # Waves 2-6
        else:
            return 64


def switzerland_age_early(row):
    # Male
    if row["gender"] == "Male":
        return 63

    # Female
    else:
        return 62
