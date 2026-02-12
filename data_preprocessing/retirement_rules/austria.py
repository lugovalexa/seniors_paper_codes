"""
Retirement-age rules for Austria used to construct statutory old and early retirement ages in SHARE.

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

def austria_age(row):
    # Male
    if row["gender"] == "Male":
        if row["yrscontribution"] + 65 - row["age"] >= 15:
            return 65
        else:
            return row["age"] + 15 - row["yrscontribution"]

    # Female
    else:
        if row["yrscontribution"] + 60 - row["age"] >= 15:
            return 60
        else:
            return row["age"] + 15 - row["yrscontribution"]
        
def austria_age_early(row):
    # Wave 1
    if row["wave"] == 1:
        # Male
        if row["gender"] == "Male":
            if row["yrscontribution"] + 61 - row["age"] >= 15:
                return 61
            else:
                return row["age"] + 15 - row["yrscontribution"]
        # Female
        else:
            if row["yrscontribution"] + 56 - row["age"] >= 15:
                return 56
            else:
                return row["age"] + 15 - row["yrscontribution"]
    # Waves 2 and 4
    elif (row["wave"] == 2) or (row["wave"] == 4):
        # Male
        if row["gender"] == "Male":
            if row["yrscontribution"] + 62 - row["age"] >= 15:
                return 62
            else:
                return row["age"] + 15 - row["yrscontribution"]
        # Female
        else:
            if row["yrscontribution"] + 57 - row["age"] >= 15:
                return 57
            else:
                return row["age"] + 15 - row["yrscontribution"]
    # Wave 5
    elif row["wave"] == 5:
        # Male
        if row["gender"] == "Male":
            if row["yrscontribution"] + 63 - row["age"] >= 15:
                return 63
            else:
                return row["age"] + 15 - row["yrscontribution"]

        # Female
        else:
            if row["yrscontribution"] + 58 - row["age"] >= 15:
                return 58
            else:
                return row["age"] + 15 - row["yrscontribution"]
    # Wave 6
    else:
        # Male
        if row["gender"] == "Male":
            if row["yrscontribution"] + 64 - row["age"] >= 15:
                return 64
            else:
                return row["age"] + 15 - row["yrscontribution"]

        # Female
        else:
            if row["yrscontribution"] + 59 - row["age"] >= 15:
                return 59
            else:
                return row["age"] + 15 - row["yrscontribution"]
            

