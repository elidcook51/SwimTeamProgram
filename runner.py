import algorithms
import relayHelp as relay
import individualScore as ind
import seedingHelp as help
import databaseBuilder as db
import fillingEvents as fill
import pandas as pd
import numpy as np
import meetplanningsheet as sheet
from copy import deepcopy
from collections import defaultdict
import swimmerRegression
import re

allData = pd.read_csv("C:/Users/ucg8nb/JSL All Results 2021-2025\Transformed Data.csv")

def createAllDataJSL(jslWebsiteLink, outputPath):
    db.getFullResults(jslWebsiteLink, 'Current Data')
    curData = db.getFullData('Current Data')
    trans = db.fullDataTransform(curData)
    trans.to_csv(outputPath)

def createAllDataSwimTopia(jslWebsiteLink, untransformed, transformed):
    db.pullSwimTopiaResults(jslWebsiteLink, '2026 Results')
    curData = db.readSwimTopiaResults('2026 Results')
    curData.to_csv(untransformed)
    trans = db.transformSwimTopiaResults(curData)
    trans.to_csv(transformed)

def resultsToString(x_vals, y_vals, incData, allData):

    x_vals = x_vals.reset_index()
    y_vals = y_vals.reset_index()

    relayTeams = incData[incData['inc'] == 1]

    enteredRelays = y_vals[y_vals['y.val'] >= 0.5]
    swimmersEntered = x_vals[x_vals['x.val'] >= 0.5]

    freeRelay = enteredRelays[enteredRelays['index0'] == 'f']
    freeRelayNumber = freeRelay['index1'].values[0]

    medleyRelay = enteredRelays[enteredRelays['index0'] == 'm']
    medleyRelayNumber = medleyRelay['index1'].values[0]

    freeRelaySwimmers = relayTeams[relayTeams['t'] == freeRelayNumber]['s'].tolist()
    medleyRelaySwimmers = relayTeams[relayTeams['t'] == medleyRelayNumber]['s'].tolist()

    freeRelaySwimmers = list(set(freeRelaySwimmers))
    medleyRelaySwimmers = list(set(medleyRelaySwimmers))
    bestComb = relay.makeBestMedleyRelay(medleyRelaySwimmers, allData)
    if bestComb == None:
        medleyRelaySwimmers = []
    strokes = ['ba', 'br', 'fl', 'fr']

    outputString = ''

    swimmers = swimmersEntered['index0'].unique().tolist()
    swimmers = swimmers  + [s for s in medleyRelaySwimmers if s not in swimmers]
    swimmers = swimmers + [s for s in freeRelaySwimmers if s not in swimmers]

    for s in swimmers:
        tempDf = swimmersEntered[swimmersEntered['index0'] == s]
        events = tempDf['index1'].unique().tolist()
        outputString += f"Swimmer: {s} entered in "
        for e in events:
            outputString += f" {e}, "
        if s in freeRelaySwimmers:
            outputString += f" fr, "
        if s in medleyRelaySwimmers:
            outputString += f" mr ({strokes[list(bestComb).index(s)]}), "
        outputString += '\n'
        
    return outputString

def print_team_scores(team_scores):
    outputString = ""
    count = 1
    for team, points in sorted(team_scores.items(), key = lambda x: x[1], reverse = True):
        outputString += f"{count}. {team} - {points} \n"
        count += 1
    return outputString

def enteredStringToDf(enteredString):
    rows = []
    for line in enteredString.splitlines():
        if not line.startswith("Swimmer:"):
            continue

        m = re.match(r"Swimmer:\s*(.*?)\s*entered in\s*(.*)", line)
        if not m:
            continue

        name = m.group(1).strip().lower()
        events = m.group(2)

        rows.append({
            "Swimmer": name,
            "in_ba": "ba," in events,
            "in_br": "br," in events,
            "in_fl": "fl," in events,
            "in_fr": "fr," in events,
            "in_im": "im," in events,
            "in_lf": "lf," in events,
            "in_sf": "sf," in events,
            "mr_ba": "mr (ba)" in events,
            "mr_br": "mr (br)" in events,
            "mr_fl": "mr (fl)" in events,
            "mr_fr": "mr (fr)" in events,
        })

    strokes_df = pd.DataFrame(rows)

    bool_cols = strokes_df.select_dtypes(include = 'bool').columns
    strokes_df[bool_cols] = strokes_df[bool_cols].astype(int)

    return strokes_df

def seedChamps(allData, team):
    ageRanges = help.getAgeGroups()
    genders = help.getGenders()
    outputString = ''
    totPoints = 0
    team_scores = defaultdict(int)
    for a in ageRanges:
        for g in genders:
            print(f'Seeding ages {a} for gender {g}')
            tempDf, agscores = ind.scoreOneTeam(allData, a, g, team)
            team_scores = help.combine_team_scores(team_scores, agscores)
            tempDf = ind.dataframePlaceToScoreChamps(tempDf)
            relayPos, agrelayscores = relay.buildRelayPositions(allData, a, g, team, algorithms.getThreeEventSwimmers(tempDf))
            team_scores = help.combine_team_scores(team_scores, agrelayscores)
            swimmers = tempDf['Swimmer'].tolist()
            incData = relay.buildInc(relayPos, swimmers)
            x_vals, y_vals, points = algorithms.relayProgram(tempDf, relayPos, incData)
            totPoints += points
            outputString += resultsToString(x_vals,y_vals, incData, allData)
    team_scores['CITY'] = totPoints
    return outputString + f'\n Total Points Scored: {totPoints} \n Final Results: \n {print_team_scores(team_scores)}'

def seedDuelMeet(allData, team1, team2, year):
    allData['Age'] = allData['Age'] + year - 2026
    ageRanges = help.getAgeGroups()
    genders = help.getGenders()
    outputs = []
    for a in ageRanges:
        for g in genders:
            tempDf = ind.scoreOneTeamDuel(allData, a, g, team1, team2)
            tempDf = ind.dataframePlaceToScoreDuel(tempDf)
            x_vals = algorithms.noRelayProgram(tempDf)
            outputs.append(x_vals)
    combined = pd.concat(outputs)
    df = combined.unstack(fill_value=0)
    df = df.reset_index()
    df.columns = [col if isinstance(col, str) else col[-1] for col in df.columns]
    df = df.rename(columns = {'': 'Swimmer', 'sf': 'in_sf', 'ba': 'in_ba', 'br': 'in_br', 'fl': 'in_fl', 'lf': 'in_lf', 'im': 'in_im'})
    df = pd.merge(df, allData, on = 'Swimmer', how  = 'inner')
    df = fill.fillEvents(df, max_events = 2, max_event_size = 12)
    return df

def createDuelMeetPlanningSheet(oppTeam, immeet, participantsPath, bestTimesPath = "C:/Users/ucg8nb/Downloads/best_times.csv", allDataPath = "C:/Users/ucg8nb/Downloads/Transformed 2026.csv", rosterPath = "C:/Users/ucg8nb/Downloads/cityswordfishteam_athlete_roster_260702111202.csv"):
    participants = pd.read_csv(participantsPath)
    times = pd.read_csv(bestTimesPath)
    rosterdf = pd.read_csv(rosterPath)
    allData = pd.read_csv(allDataPath)
    timeAllData = deepcopy(allData)
    participants, times_pivot = sheet.normalizeNameKeys(participants, times, rosterdf)
    allData, cityData = sheet.cleanAllData(allData, participants)
    allData = swimmerRegression.standardizeAllData(allData)
    results = seedDuelMeet(allData, 'CITY', oppTeam, 2026)
    city_ranks = sheet.getCityRanks(cityData)
    sheet.buildPdf("C:/Users/ucg8nb/Downloads/meet_plan.pdf", participants, times_pivot, city_ranks, results, immeet, oppTeam, timeAllData)

def createChampsMeetPlanningSheet(participantsPath, bestTimesPath = "C:/Users/ucg8nb/Downloads/best_times.csv", allDataPath = "C:/Users/ucg8nb/Downloads/Transformed 2026.csv", rosterPath = "C:/Users/ucg8nb/Downloads/cityswordfishteam_athlete_roster_260702111202.csv"):
    participants = pd.read_csv(participantsPath)
    times = pd.read_csv(bestTimesPath)
    rosterdf = pd.read_csv(rosterPath)
    allData = pd.read_csv(allDataPath)
    timeAllData = deepcopy(allData)
    participants, times_pivot = sheet.normalizeNameKeys(participants, times, rosterdf)
    allData, cityData = sheet.cleanAllData(allData, participants)
    allData = swimmerRegression.standardizeAllData(allData)
    cityData = swimmerRegression.standardizeAllData(cityData)
    resultsString = seedChamps(allData, 'CITY')
    print(resultsString)
    entered_df = enteredStringToDf(resultsString)
    cityData['Swimmer'] = cityData['Swimmer'].str.lower()
    entered_df = pd.merge(cityData[['Swimmer','Age','Gender', 'sf', 'ba', 'br', 'fl', 'lf', 'im']], entered_df, on = 'Swimmer', how = 'left')
    entered_df[['in_ba','in_br', 'in_fl', 'in_fr', 'in_im', 'in_lf', 'in_sf', 'mr_ba', 'mr_br','mr_fl', 'mr_fr']] = entered_df[['in_ba','in_br', 'in_fl', 'in_fr', 'in_im', 'in_lf', 'in_sf', 'mr_ba', 'mr_br','mr_fl', 'mr_fr']].fillna(0).astype(int)
    city_ranks = sheet.getCityRanks(cityData)
    print('Filling Events')
    entered_df = fill.fillEventsChamps(entered_df)
    sheet.buildPdf("C:/Users/ucg8nb/Downloads/Champs Meet Sheet.pdf", participants, times_pivot, city_ranks, entered_df, False, '', timeAllData, champs = True)
    


participantSheetPath = "C:/Users/ucg8nb/Downloads/cityswordfishteam_meet_participants_260716004416.csv"
bestTimesPath = "C:/Users/ucg8nb/Downloads/best_times.csv"
allDataPath = "C:/Users/ucg8nb/Downloads/Transformed 2026.csv"
rosterPath = "C:/Users/ucg8nb/Downloads/cityswordfishteam_athlete_roster_260702111202.csv"

# createDuelMeetPlanningSheet('ACAC', False, participantsPath = participantSheetPath)
allData = pd.read_csv(allDataPath)
createChampsMeetPlanningSheet(participantsPath=participantSheetPath)
# print(seedChamps(allData, 'CITY'))


