"""
Retirement-age rules for Czech Republic used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age
- gender
- SHARE wave (policy timing proxy)
- years of contributions (minimum contribution requirement)
- number of children (for women only)

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: gender, wave, age, yrscontribution, nb_children

Returns:
- retirement age (float/int).

"""

def czech_republic_age(row):
    # Male
    if row["gender"] == "Male":
        # Waves 1-2
        if row["wave"] < 4:
            if row["yrscontribution"] + 61 - row["age"] >= 25:
                return 61
            else:
                return row["age"] + 25 - row["yrscontribution"]
        # Waves 4-6
        elif row["wave"] >= 4:
            if row["yrscontribution"] + 62 - row["age"] >= 35:
                return 62
            else:
                return row["age"] + 35 - row["yrscontribution"]

    # Female
    else:
        # Wave 1
        if row["wave"] == 1:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 59 - row["age"] >= 25:
                    return 59
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 58 - row["age"] >= 25:
                    return 58
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 57 - row["age"] >= 25:
                    return 57
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 56 - row["age"] >= 25:
                    return 56
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 55 - row["age"] >= 25:
                    return 55
                else:
                    return row["age"] + 25 - row["yrscontribution"]
        # Wave 2
        elif row["wave"] == 2:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 60 - row["age"] >= 25:
                    return 60
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 59 - row["age"] >= 25:
                    return 59
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 58 - row["age"] >= 25:
                    return 58
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 57 - row["age"] >= 25:
                    return 57
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 56 - row["age"] >= 25:
                    return 56
                else:
                    return row["age"] + 25 - row["yrscontribution"]
        # Wave 4
        elif row["wave"] == 4:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 60 - row["age"] >= 35:
                    return 60
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 59 - row["age"] >= 35:
                    return 59
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 58 - row["age"] >= 35:
                    return 58
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 57 - row["age"] >= 35:
                    return 57
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 56 - row["age"] >= 35:
                    return 56
                else:
                    return row["age"] + 35 - row["yrscontribution"]
        # Wave 5
        elif row["wave"] == 5:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 61 - row["age"] >= 35:
                    return 61
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 60 - row["age"] >= 35:
                    return 60
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 59 - row["age"] >= 35:
                    return 59
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 58 - row["age"] >= 35:
                    return 58
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 57 - row["age"] >= 35:
                    return 57
                else:
                    return row["age"] + 35 - row["yrscontribution"]
        # Wave 6
        else:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 62 - row["age"] >= 35:
                    return 62
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 61 - row["age"] >= 35:
                    return 61
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 60 - row["age"] >= 35:
                    return 60
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 59 - row["age"] >= 35:
                    return 59
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 58 - row["age"] >= 35:
                    return 58
                else:
                    return row["age"] + 35 - row["yrscontribution"]


def czech_republic_age_early(row):               
    # Male
    if row["gender"] == "Male":
        # Waves 1-2
        if row["wave"] < 4:
            if row["yrscontribution"] + 59 - row["age"] >= 25:
                return 59
            else:
                return row["age"] + 25 - row["yrscontribution"]
        # Waves 4-6
        elif row["wave"] >= 4:
            if row["yrscontribution"] + 60 - row["age"] >= 35:
                return 60
            else:
                return row["age"] + 35 - row["yrscontribution"]

    # Female
    else:
        # Wave 1
        if row["wave"] == 1:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 57 - row["age"] >= 25:
                    return 57
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 56 - row["age"] >= 25:
                    return 56
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 55 - row["age"] >= 25:
                    return 55
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 54 - row["age"] >= 25:
                    return 54
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 53 - row["age"] >= 25:
                    return 53
                else:
                    return row["age"] + 25 - row["yrscontribution"]
        # Wave 2
        elif row["wave"] == 2:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 58 - row["age"] >= 25:
                    return 58
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 57 - row["age"] >= 25:
                    return 57
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 56 - row["age"] >= 25:
                    return 56
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 55 - row["age"] >= 25:
                    return 55
                else:
                    return row["age"] + 25 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 54 - row["age"] >= 25:
                    return 54
                else:
                    return row["age"] + 25 - row["yrscontribution"]
        # Wave 4
        elif row["wave"] == 4:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 58 - row["age"] >= 35:
                    return 58
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 57 - row["age"] >= 35:
                    return 57
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 56 - row["age"] >= 35:
                    return 56
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 55 - row["age"] >= 35:
                    return 55
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 54 - row["age"] >= 35:
                    return 54
                else:
                    return row["age"] + 35 - row["yrscontribution"]
        # Wave 5
        elif row["wave"] == 5:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 59 - row["age"] >= 35:
                    return 59
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 58 - row["age"] >= 35:
                    return 58
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 57 - row["age"] >= 35:
                    return 57
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 56 - row["age"] >= 35:
                    return 56
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 55 - row["age"] >= 35:
                    return 55
                else:
                    return row["age"] + 35 - row["yrscontribution"]
        # Wave 6
        else:
            if row["nb_children"] == 0:
                if row["yrscontribution"] + 60 - row["age"] >= 35:
                    return 60
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 1:
                if row["yrscontribution"] + 59 - row["age"] >= 35:
                    return 59
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 2:
                if row["yrscontribution"] + 58 - row["age"] >= 35:
                    return 58
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            elif row["nb_children"] == 3 or row["nb_children"] == 4:
                if row["yrscontribution"] + 57 - row["age"] >= 35:
                    return 57
                else:
                    return row["age"] + 35 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 56 - row["age"] >= 35:
                    return 56
                else:
                    return row["age"] + 35 - row["yrscontribution"]

