"""
Retirement-age rules for Estonia used to construct statutory old and early retirement ages in SHARE.

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

def estonia_age(row):
    # Male
    if row["gender"] == "Male":
        if row["yrscontribution"] + 63 - row["age"] >= 15:
            return 63
        else:
            return row["age"] + 15 - row["yrscontribution"]

    # Female
    else:
        # Waves 1-2
        if row["wave"] < 4:
            if row["yrscontribution"] + 60 - row["age"] >= 15:
                return 60
            else:
                return row["age"] + 15 - row["yrscontribution"]
        # Wave 4
        elif row["wave"] == 4:
            if row["yrscontribution"] + 61 - row["age"] >= 15:
                return 61
            else:
                return row["age"] + 15 - row["yrscontribution"]    
        # Waves 5-6
        else:
            if row["yrscontribution"] + 62 - row["age"] >= 15:
                return 62
            else:
                return row["age"] + 15 - row["yrscontribution"]


def estonia_age_early(row):
    # Male
    if row["gender"] == "Male":
        if row["yrscontribution"] + 60 - row["age"] >= 15:
            return 60
        else:
            return row["age"] + 15 - row["yrscontribution"]

    # Female
    else:
        # Waves 1-2
        if row["wave"] < 4:
            if row["yrscontribution"] + 57 - row["age"] >= 15:
                return 57
            else:
                return row["age"] + 15 - row["yrscontribution"]
        # Wave 4
        elif row["wave"] == 4:
            if row["yrscontribution"] + 58 - row["age"] >= 15:
                return 58
            else:
                return row["age"] + 15 - row["yrscontribution"]    
        # Waves 5-6
        else:
            if row["yrscontribution"] + 59 - row["age"] >= 15:
                return 59
            else:
                return row["age"] + 15 - row["yrscontribution"]
