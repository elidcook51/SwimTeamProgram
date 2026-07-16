import pandas as pd
import seedingHelp as help
import numpy as np

events = ['sf', 'ba', 'br', 'fl', 'lf', 'im']

def fillEvents(bigDf, max_events, max_event_size):
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

# def fillTo4(bigDf):
#     outputDf = pd.DataFrame()
#     for ageRange in help.getAgeGroups():
#         for gender in help.getGenders():
#             df = bigDf[bigDf['Age'].isin(ageRange)]
#             df = df[df['Gender'] == gender]
#             if 8 in ageRange:
#                 strokes = help.getUnder8Strokes()
#             else:
#                 strokes = help.getStrokes()

#             for stroke in strokes:
#                 in_col = f"in_{stroke}"

#                 while df[in_col].sum() < 4:
#                     candidates = df[df[in_col] == 0].copy()

#                     if candidates.empty:
#                         break

#                     idx = candidates[stroke].idxmin()
#                     df.loc[idx, in_col] = 1

#             changed = True
#             while changed:
#                 changed = False

#                 event_counts = df[[f"in_{s}" for s in strokes]].sum(axis = 1)

#                 for swimmer_idx  in df.index[event_counts > 3]:
#                     entered = [
#                         s for s in strokes
#                         if df.loc[swimmer_idx, f"in_{s}"] == 1
#                     ]

#                     removable = []

#                     for s in entered:
#                         entrants = df[df[f"in_{s}"] == 1]
#                         rank = entrants[s].rank(method = 'first').loc[swimmer_idx]

#                         if rank >= 3:
#                             removable.append(s)
                    
#                     if not removable:
#                         continue

#                     slowest = max(removable, key = lambda s: df.loc[swimmer_idx, s])

#                     df.loc[swimmer_idx, f"in_{slowest}"] = 0 
#                     changed = True
#             outputDf = pd.concat([outputDf, df])
#     return outputDf

def fillTo4(bigDf):
    inevents = ['in_im', 'in_lf', 'in_sf', 'in_ba', 'in_br', 'in_fl', 'in_fr', 'mr_fr', 'mr_ba', 'mr_br', 'mr_fl']
    individuals = ['in_im', 'in_lf', 'in_sf', 'in_ba', 'in_br', 'in_fl']
    outputDf = pd.DataFrame()
    for ageRange in help.getAgeGroups():
        for gender in help.getGenders():
            df = bigDf[bigDf['Age'].isin(ageRange)].copy()
            df = df[df['Gender'] == gender]
            if 8 in ageRange:
                strokes = help.getUnder8Strokes()
            else:
                strokes = help.getStrokes()

            candidates = {}
            strokePos = {}
            for s in strokes:

                candidates[s] = df.loc[df[s] != -1].sort_values(s)['Swimmer'].tolist()

                entered = (
                    df.loc[(df[f"in_{s}"] == 1) & (df[s] != -1)].sort_values(s)
                )

                slowest_entered_name = entered.iloc[-1]['Swimmer']

                strokePos[s] = candidates[s].index(slowest_entered_name)

                while len(candidates[s]) > strokePos[s] + 1 and df[f"in_{s}"].sum() < 4:
                    strokePos[s] += 1
                    newSwimmer = candidates[s][strokePos[s]]

                    df.loc[df['Swimmer'] == newSwimmer, f"in_{s}"] = 1

            changed = True
            while changed:
                changed = False
                
                event_counts = df[[f"in_{s}" for s in strokes]].sum(axis = 1)

                for swimmer_idx  in df.index[event_counts > 3]:
                    entered = [
                        s for s in strokes
                        if df.loc[swimmer_idx, f"in_{s}"] == 1
                    ]

                    removable = []

                    for s in entered:
                        entrants = df[df[f"in_{s}"] == 1]
                        rank = entrants[s].rank(method = 'first').loc[swimmer_idx]
                        if rank >= 3:
                            removable.append(s)

                    slowest = max(removable, key = lambda s: df.loc[swimmer_idx, s])

                    df.loc[swimmer_idx, f"in_{slowest}"] = 0 
                    changed = True
                    strokePos[slowest] += 1
                    if len(candidates[slowest]) > strokePos[slowest] + 1:
                        df.loc[df['Swimmer'] == candidates[slowest][strokePos[slowest]], f"in_{slowest}"] = 1
            for s in strokes:
                changed = True
                if df[f"in_{s}"].sum() < 4:
                    changed = False
                    for candidate in candidates[s]:
                        if changed:
                            continue
                        if df.loc[df["Swimmer"] == candidate, inevents].sum(axis=1).iloc[0] < 4 and df.loc[df["Swimmer"] == candidate, individuals].sum(axis=1).iloc[0] < 3:
                            df.loc[df['Swimmer'] == candidate, f"in_{s}"] = 1
                            changed = True
            outputDf = pd.concat([outputDf, df])
    return outputDf


def fillEventsChamps(bigDf):
    individuals = ['in_im', 'in_lf', 'in_sf', 'in_ba', 'in_br', 'in_fl']
    inevents = ['in_im', 'in_lf', 'in_sf', 'in_ba', 'in_br', 'in_fl', 'in_fr', 'mr_fr', 'mr_ba', 'mr_br', 'mr_fl']
    bigDf = fillTo4(bigDf)
    for index, row in bigDf.iterrows():
        numEvents = np.sum(row[inevents])
        numInd = np.sum(row[individuals])
        if numInd >= 2:
            continue
        if row['in_sf'] != 1:
            bigDf.loc[index, 'in_sf'] = 1
            numInd += 1
            if numInd >= 2:
                continue
        curBest = ""
        curTime = 1
        for s in ['ba', 'br', 'fl']:
            if bigDf.loc[index, s] != -1 and bigDf.loc[index, s] < curTime:
                curBest = s
                curTime = bigDf.loc[index, s]
        if curBest != "":
            bigDf.loc[index, f"in_{curBest}"] = 1
    return bigDf