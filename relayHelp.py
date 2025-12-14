import pandas as pd
import seedingHelp as help
from itertools import combinations
from itertools import permutations
import numpy as np

def placeToScore(place):
    if place == -1:
        return -1
    if place == 1:
        return 19
    else:
        return -0.5 * place + 19

def relayToScore(place):
    return placeToScore(place) + 10

def calcMedleyTime(swimmers, times):
    totalTime = 0
    strokes = ['ba', 'br', 'fl', 'fr']
    for index, swimmer in enumerate(swimmers):
        strokeTime = times[swimmer][strokes[index]]
        if strokeTime == -1:
            return float('inf')
        totalTime += strokeTime
    return totalTime

def makeMedleyRelay(smallData):
    if smallData.size < 4:
        return None, float('inf')
    swimmers = smallData['Swimmer'].tolist()
    fl = smallData['fl'].tolist()
    ba = smallData['ba'].tolist()
    br = smallData['br'].tolist()
    fr = smallData['sf'].tolist()
    times = {swimmers[0]: {'fl':fl[0], 'ba':ba[0], 'br':br[0], 'fr':fr[0]}}
    for i in range(1, len(swimmers)):
        times[swimmers[i]] = {
            'fl':fl[i],
            'ba':ba[i],
            'br':br[i],
            'fr':fr[i]
        }
    bestComb = None
    bestTime = float('-inf')
    for comb in combinations(swimmers, 4):
        for perm in permutations(comb):
            curTime = calcMedleyTime(perm, times)
            if (bestTime == float('-inf') and curTime != float('-inf')) or (curTime < bestTime and curTime != float('-inf')):
                bestTime = curTime
                bestComb = perm
    if bestComb == None:
        return None, bestTime
    return list(bestComb), bestTime

def makeBestMedleyRelay(swimmers, allData):
    swimTimes = allData[allData['Swimmer'].isin(swimmers)]
    fl = swimTimes['fl'].tolist()
    ba = swimTimes['ba'].tolist()
    br = swimTimes['br'].tolist()
    fr = swimTimes['sf'].tolist()
    times = {swimmers[0]: {'fl':fl[0], 'ba':ba[0], 'br':br[0], 'fr':fr[0]}}
    for i in range(1, len(swimmers)):
        times[swimmers[i]] = {
            'fl':fl[i],
            'ba':ba[i],
            'br':br[i],
            'fr':fr[i]
        }
    bestComb = None
    bestTime = float('inf')
    for perm in permutations(swimmers):
        curTime = calcMedleyTime(perm, times)
        if curTime < bestTime:
                bestTime = curTime
                bestComb = perm
    return bestComb

def makeFreeRelay(smallDf):
    smallDf = smallDf[smallDf['sf'] != -1]
    sortedDf = smallDf.sort_values(by = 'sf', ascending = True)
    sortedDf = sortedDf.head(4)
    if len(sortedDf) != 4:
        return None, float('-inf')
    sortedDf = sortedDf.sort_values(by = 'sf', ascending = False)
    bestComb = sortedDf['Swimmer'].tolist()
    totalTime = 0
    for t in sortedDf['sf'].tolist():
        totalTime += t
    return bestComb, totalTime

def allRelayScores(allData, ageRange, gender, free):
    teams = help.getTeams()
    tempDf = allData[allData['Age'].isin(ageRange)]
    tempDf = tempDf[tempDf['Gender'] == gender]
    allRelayTimes = pd.DataFrame()
    for t in teams:
        if not free:
            smallDf = tempDf[tempDf['Team'] == t]
            _, bestTime = makeMedleyRelay(smallDf)
        else:
            smallDf = tempDf[tempDf['Team'] == t]
            _, bestTime = makeFreeRelay(smallDf)
        allRelayTimes = allRelayTimes._append({'Team': t, 'Time': bestTime}, ignore_index = True)
    allRelayTimes = allRelayTimes.sort_values(by = 'Time', ascending = True)
    return allRelayTimes

def getUnecessarySwimmers(fastRunData):
    possibleSwimmers = fastRunData['Swimmer'].tolist()
    for stroke in ['sf', 'ba', 'br', 'fl']:
        tempDf = fastRunData.sort_values(by = stroke, ascending = True).head(4)
        for s in tempDf['Swimmer'].tolist():
            if s in possibleSwimmers:
                possibleSwimmers.remove(s)
    return possibleSwimmers


def buildRelayPositions(allData, ageRange, gender, team, threeEventSwimmers):
    freeRelayScores = allRelayScores(allData, ageRange, gender, True)
    medleyRelayScores = allRelayScores(allData, ageRange, gender, False)
    freeRelayScores = freeRelayScores[freeRelayScores['Team'] != team]
    medleyRelayScores = medleyRelayScores[medleyRelayScores['Team'] != team]
    freeRelayTimes = freeRelayScores['Time'].to_numpy()
    medleyRelayTimes = medleyRelayScores['Time'].to_numpy()

    smallData = help.getAgeGenderTeam(allData, ageRange, gender, team)

    efficiencyHelper = smallData[~smallData['Swimmer'].isin(threeEventSwimmers)]
    remSwimmers = getUnecessarySwimmers(efficiencyHelper)
    smallData = smallData[~smallData['Swimmer'].isin(remSwimmers)]


    swimmers = smallData['Swimmer'].tolist()
    fl = smallData['fl'].tolist()
    ba = smallData['ba'].tolist()
    br = smallData['br'].tolist()
    fr = smallData['sf'].tolist()
    times = {}
    for i in range(0, len(swimmers)):
        times[swimmers[i]] = {
            'fl':fl[i],
            'ba':ba[i],
            'br':br[i],
            'fr':fr[i]
        }

    outputDf = pd.DataFrame()
    count = 0
    for comb in combinations(swimmers, 4):
        medleyTime = float('inf')
        for perm in permutations(comb):
            curTime = calcMedleyTime(perm, times)
            if curTime < medleyTime:
                medleyTime = curTime
        freeTime = 0
        for _, swimmer in enumerate(comb):
            strokeTime = times[swimmer]['fr']
            if strokeTime == -1:
                strokeTime = float('inf')
            freeTime += strokeTime
        freePos = np.searchsorted(freeRelayTimes, freeTime, side = 'left') + 1
        medleyPos = np.searchsorted(medleyRelayTimes, medleyTime, side = 'left') + 1
        swimList = list(comb)
        swimmerDict = {f"s{i + 1}": v for i,v in enumerate(swimList)}
        combinedMedley = {'Team': count, "m": 'm', 'r':relayToScore(medleyPos)}
        combinedMedley.update(swimmerDict)
        combinedFree = {'Team': count, "m": 'f', 'r':relayToScore(freePos)}
        combinedFree.update(swimmerDict)
        outputDf = outputDf._append(combinedMedley, ignore_index = True)
        outputDf = outputDf._append(combinedFree, ignore_index = True)
        count += 1
    return outputDf

def buildInc(relaysDf, swimmers):
    inc_rows = []
    for _, row in relaysDf.iterrows():
        team = str(row['Team'])
        members = [row[f's{i}'] for i in range(1, 5)]
        for s in swimmers:
            inc_rows.append({
                's': s,
                't': team,
                'inc': 1 if s in members else 0
            })
    inc_df = pd.DataFrame(inc_rows)
    return inc_df




