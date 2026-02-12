"""
Retirement-age rules for Slovenia used to construct statutory old and early retirement ages in SHARE.

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

def slovenia_age(row):
    # Males
    if row["gender"] == "Male":
        return 65
    # Females
    else:
        if row["wave"] < 6:
            return 63
        else:
            return 65

def slovenia_age_early(row):
    # Males
    if row["gender"] == "Male":
        if row["wave"] < 6:
            return 58
        else:
            return 59
    # Females
    else:
        if row["wave"] <= 4:
            return 56
        elif row["wave"] == 5:
            return 57
        else:
            return 58
