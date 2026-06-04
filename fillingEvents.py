import pandas as pd
import seedingHelp as help

events = ['sf', 'ba', 'br', 'fl', 'lf', 'im']

def fillEvents(bigDf):
    ageRanges = help.getAgeGroups()
    genders = help.getGenders()
    outputDf = pd.DataFrame()
    for a in ageRanges:
        for g in genders:
            tempDf = bigDf[bigDf['Age'].isin(a)]
            tempDf = tempDf[tempDf['Gender'] == g]
            tempDf = assign(tempDf)
            outputDf = outputDf._append(tempDf, ignore_index = True)
    
    return outputDf


def assign(df, max_events = 3, max_event_size = 12):
    #Put all people with no times in sf and ba
    no_times = (df[events] == -1).all(axis = 1)
    df.loc[no_times, ['in_sf', 'in_ba']] = 1

    for i, row in df.iterrows():
        entered = [e for e in events if row[f"in_{e}"] == 1]
        if len(entered) < max_events:
            valid = [e for e in events if row[e] != -1]
            fastest = sorted(valid, key = lambda e: row [e])
            for e in fastest:
                if f"in_{e}" not in [f"in_{x}" for x in entered]:
                    df.at[i, f"in_{e}"] = 1
                    entered.append(e)
                    if len(entered) >= max_events:
                        break
    
    for e in events:
        while df[f"in_{e}"].sum() > max_event_size:
            swimmers = df[df[f"in_{e}"] == 1]
            slowest_idx = swimmers[e].idxmax()

            row = df.loc[slowest_idx]

            choices = [ev for ev in events if ev != e and row[ev] != -1 and df[f"in_{ev}"].sum() < max_event_size]

            if not choices:
                break

            best = min(choices, key = lambda ev: row[ev])
            df.loc[slowest_idx, f"in_{e}"] = 0
            df.loc[slowest_idx, f"in_{best}"] = 1
    
    return df