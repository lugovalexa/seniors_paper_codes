"""
Retirement-age rules for France used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age
- SHARE wave (policy timing proxy)
- year of birth

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: wave, age, yrbirth

Returns:
- retirement age (float/int).

"""

def france_age(row):
    # Waves 1-2
    if row["wave"] < 4:
        return 60
    # Waves 4-6
    elif row["wave"] >= 4:
        if row["yrbirth"] <= 1952:
            return 60
        elif (row["yrbirth"] == 1953) or (row["yrbirth"] == 1954):
            return 61
        else:
            return 62

def france_age_early(row):
    # Waves 1-5
    if row["wave"] < 6:
        return 55
    # Wave 6
    else:
        return 60

