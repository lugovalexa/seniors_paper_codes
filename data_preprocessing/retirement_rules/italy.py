"""
Retirement-age rules for Italy used to construct statutory old and early retirement ages in SHARE.

These functions implement an approximation to old and early retirement eligibility based on:
- age
- gender
- SHARE wave (policy timing proxy)
- years of contributions (minimum contribution requirement)
- job status (private sector employee / public sector employee / self-employed)

The eligibility rules are mainly derived from Mutual Information System on Social Protection (MISSOC), 
complemented by additional details from previous literature on pension reforms. 

Inputs:
- row: pandas Series with fields: gender, wave, age, yrscontribution, job_status

Returns:
- retirement age (float/int).

"""

def italy_age(row):
    # Male
    if row["gender"] == "Male":
        # Waves 1-2
        if row["wave"] < 4:
            if row["yrscontribution"] + 65 - row["age"] >= 20:
                return 65
            else:
                return row["age"] + 20 - row["yrscontribution"]
        # Waves 4-6
        if row["wave"] >= 4:
            if row["yrscontribution"] + 66 - row["age"] >= 20:
                return 66
            else:
                return row["age"] + 20 - row["yrscontribution"]
    # Female
    else:
        # Waves 1-2
        if row["wave"] < 4:
            if row["yrscontribution"] + 60 - row["age"] >= 20:
                return 60
            else:
                return row["age"] + 20 - row["yrscontribution"]
        # Wave 4
        elif row["wave"] == 4:
            if (row["job_status"] == "Public sector employee") or (row["job_status"] == "Civil servant"):
                if row["yrscontribution"] + 61 - row["age"] >= 20:
                    return 61
                else:
                    return row["age"] + 20 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 60 - row["age"] >= 20:
                    return 60
                else:
                    return row["age"] + 20 - row["yrscontribution"]
        # Wave 5
        elif row["wave"] == 5:
            if row["job_status"] == "Self-employed":
                if row["yrscontribution"] + 64 - row["age"] >= 20:
                    return 64
                else:
                    return row["age"] + 20 - row["yrscontribution"]
            elif (row["job_status"] == "Public sector employee") or (row["job_status"] == "Civil servant"):
                if row["yrscontribution"] + 66 - row["age"] >= 20:
                    return 66
                else:
                    return row["age"] + 20 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 62 - row["age"] >= 20:
                    return 62
                else:
                    return row["age"] + 20 - row["yrscontribution"]    
        # Wave 6
        else:
            if row["job_status"] == "Self-employed":
                if row["yrscontribution"] + 65 - row["age"] >= 20:
                    return 65
                else:
                    return row["age"] + 20 - row["yrscontribution"]
            elif (row["job_status"] == "Public sector employee") or (row["job_status"] == "Civil servant"):
                if row["yrscontribution"] + 66 - row["age"] >= 20:
                    return 66
                else:
                    return row["age"] + 20 - row["yrscontribution"]
            else:
                if row["yrscontribution"] + 64 - row["age"] >= 20:
                    return 64
                else:
                    return row["age"] + 20 - row["yrscontribution"] 

def italy_age_early(row):
    # Wave 1
    if row["wave"] == 1:
        if row["job_status"] == "Self-employed":
            if row["age"] + 39 - row["yrscontribution"] < 58:
                return row["age"] + 39 - row["yrscontribution"]
            elif row["yrscontribution"] + 58 - row["age"] >= 35:
                return 58
            else:
                return row["age"] + 35 - row["yrscontribution"]
        else:
            if row["age"] + 38 - row["yrscontribution"] < 57:
                return row["age"] + 38 - row["yrscontribution"]
            elif row["yrscontribution"] + 57 - row["age"] >= 35:
                return 57
            else:
                return row["age"] + 35 - row["yrscontribution"]
    # Wave 2
    elif row["wave"] == 2:
        if row["job_status"] == "Self-employed":
            if row["age"] + 40 - row["yrscontribution"] < 58:
                return row["age"] + 40 - row["yrscontribution"]
            elif row["yrscontribution"] + 58 - row["age"] >= 35:
                return 58
            else:
                return row["age"] + 35 - row["yrscontribution"]
        else:
            if row["age"] + 39 - row["yrscontribution"] < 57:
                return row["age"] + 39 - row["yrscontribution"]
            elif row["yrscontribution"] + 57 - row["age"] >= 35:
                return 57
            else:
                return row["age"] + 35 - row["yrscontribution"]
    # Wave 4
    elif row["wave"] == 4:
        if row["job_status"] == "Self-employed":
            if row["age"] + 40 - row["yrscontribution"] < 61:
                return row["age"] + 40 - row["yrscontribution"]
            elif row["yrscontribution"] + 61 - row["age"] >= 35:
                return 61
            else:
                return row["age"] + 35 - row["yrscontribution"]
        else:
            if row["age"] + 40 - row["yrscontribution"] < 60:
                return row["age"] + 40 - row["yrscontribution"]
            elif row["yrscontribution"] + 60 - row["age"] >= 35:
                return 60
            else:
                return row["age"] + 35 - row["yrscontribution"]        
    # Waves 5 and 6
    else:
        # Male
        if row["gender"] == "Male":
            return row["age"] + 43 - row["yrscontribution"]
        # Female
        else:
            return row["age"] + 42 - row["yrscontribution"]
