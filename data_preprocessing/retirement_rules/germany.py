"""
Retirement-age rules for Germany used to construct statutory old and early retirement ages in SHARE.

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

def germany_age(row):
    # Waves 1-4
    if row["wave"] <= 4:
        if row["yrscontribution"] + 65 - row["age"] >= 5:
            return 65
        else:
            return row["age"] + 5 - row["yrscontribution"]
    # Waves 5 and 6
    else:
        if row["yrscontribution"] + 67 - row["age"] >= 5:
            return 67
        else:
            return row["age"] + 5 - row["yrscontribution"]
    

def germany_age_early(row):
    # Males
    if row["gender"] == "Male":
        if row["yrscontribution"] + 63 - row["age"] >= 5:
            return 63
        else:
            return row["age"] + 5 - row["yrscontribution"]
    # Females
    else:
        # Wave 1
        if row["wave"] == 1:
            if row["yrscontribution"] + 62 - row["age"] >= 5:
                return 62
            else:
                return row["age"] + 5 - row["yrscontribution"]
        # Waves 2-6
        else:
            if row["yrscontribution"] + 63 - row["age"] >= 5:
                return 63
            else:
                return row["age"] + 5 - row["yrscontribution"]


 