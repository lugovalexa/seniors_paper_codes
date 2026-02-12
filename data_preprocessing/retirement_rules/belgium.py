"""
Retirement-age rules for Belgium used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age
- gender
- SHARE wave (policy timing proxy)
- years of contributions (minimum contribution requirement)

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: gender, wave, age, yrscontribution

Returns:
- retirement age (float/int).

"""

def belgium_age(row):
    # Male
    if row["gender"] == "Male":
        return 65
    # Female
    else:
        # Wave 1
        if row["wave"] == 1:
            return 63
        # Wave 2
        elif row["wave"] == 2:
            return 64
        # Waves 4-6
        else:
            return 65

def belgium_age_early(row):
    # Wave 1
    if row["wave"] == 1:
        if row["yrscontribution"] + 60 - row["age"] >= 34:
            return 60
        else:
            return row["age"] + 34 - row["yrscontribution"]
    # Waves 2 and 4
    elif (row["wave"] == 2) or (row["wave"] == 4):
        if row["yrscontribution"] + 60 - row["age"] >= 35:
            return 60
        else:
            return row["age"] + 35 - row["yrscontribution"]
    # Wave 5
    elif row["wave"] == 5:
        if row["yrscontribution"] + 60 - row["age"] >= 38:
            return 60
        else:
            return row["age"] + 38 - row["yrscontribution"]
    # Wave 6
    else:
        if row["yrscontribution"] + 61 - row["age"] >= 40:
            return 61
        else:
            return row["age"] + 40 - row["yrscontribution"]


        