"""
Retirement-age rules for Spain used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age
- SHARE wave (policy timing proxy)
- years of contributions (minimum contribution requirement)

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: wave, age, yrscontribution

Returns:
- retirement age (float/int).

"""

def spain_age(row):
    if row["yrscontribution"] + 65 - row["age"] >= 15:
        return 65
    else:
        return row["age"] + 15 - row["yrscontribution"]


def spain_age_early(row):
    # Waves 1-4
    if row["wave"] <= 4:
        if row["yrscontribution"] + 61 - row["age"] >= 30:
            return 61
        else:
            return row["age"] + 30 - row["yrscontribution"]
    # Waves 5-6
    else:
        if row["yrscontribution"] + 61 - row["age"] >= 33:
            return 61
        else:
            return row["age"] + 33 - row["yrscontribution"]
