import pandas as pd
import numpy as np
import os
from itertools import permutations
from itertools import combinations
import seedingHelp as help
import swimmerRegression
import champsInfo
from collections import Counter

def findIndexInList(list, num):
    for i in range(len(list)):
        if list[i] > num:
            return i
    else:
        return len(list)

def seedSpecificTeam(teamData, team, age, gender):
    ageGroup = help.AgeGroup(team, age, gender)
    strokeDepth = [2,2,2,2,2,2]
    for index, row in teamData.iterrows():
        times = []
        for s in help.getStrokes():
            times.append(row[s])
        newSwimmer = help.Swimmer(row['Swimmer'], row['Team'], row['Age'], row['Gender'], times)
        ageGroup.addSwimmer(newSwimmer)
    for s in help.getStrokes():
        tempData = teamData.sort_values(by = s, ascending = True)
        tempData = tempData[tempData[s] != -1]
        if len(tempData) > 1:
            ageGroup.enterSwimmer(tempData['Swimmer'].values[0], s)
            if len(tempData) > 2:
                ageGroup.enterSwimmer(tempData['Swimmer'].values[1], s)
    while ageGroup.checkEntries():
        badSwimmer = ageGroup.getSwimmerOver3()
        badStroke = badSwimmer.getSlowestEnteredIn()
        badIndex = help.getIndexOfStroke(badStroke)
        ageGroup.removeSwimmer(badSwimmer.getName(), badStroke)
        strokeDepth[badIndex] += 1
        tempData = teamData.sort_values(by=badStroke, ascending=True)
        tempData = tempData[tempData[badStroke] != -1]
        if len(tempData) > strokeDepth[badIndex]:
            ageGroup.enterSwimmer(tempData['Swimmer'].values[strokeDepth[badIndex]], badStroke)
    return ageGroup.convertToDf()

def seedOtherTeams(allData, ageRange, gender):
    teams = help.getTeams()
    output = pd.DataFrame()
    ageData = allData[allData['Age'].isin(ageRange)]
    ageData = ageData[ageData['Gender'] == gender]
    for t in teams:
        teamData = ageData[ageData['Team'] == t]
        seedTimes = seedSpecificTeam(teamData, t, ageRange, gender)
        if len(seedTimes) > 0:
            for s in help.getStrokes():
                tempSeed = seedTimes[seedTimes[s] != -1]
                if len(tempSeed) > 0:
                    rowOne = {
                        'Stroke': s,
                        'Team': t,
                        'Swimmer': tempSeed['Name'].values[0],
                        'Time': tempSeed[s].values[0]
                    }
                    output = output._append(rowOne, ignore_index = True)
                    if len(tempSeed) > 1:
                        rowTwo = {
                            'Stroke': s,
                            'Team': t,
                            'Swimmer': tempSeed['Name'].values[1],
                            'Time': tempSeed[s].values[1]
                        }
                        output = output._append(rowTwo, ignore_index = True)
    return output

def scoreOneTeam(allData, ageRange, gender, team):
    topTwo = seedOtherTeams(allData, ageRange, gender)
    topTwo = topTwo[topTwo['Team'] != team]
    teamData = allData[allData['Team'] == team]
    teamData = teamData[teamData['Age'].isin(ageRange)]
    teamData = teamData[teamData['Gender'] == gender]
    outputTeamData = pd.DataFrame()
    for index, row in teamData.iterrows():
        swimmer = row['Swimmer']
        gender = row['Gender']
        age = row['Age']
        team = row['Team']
        strokes = []
        for s in help.getStrokes():
            tempTopTwo = topTwo[topTwo['Stroke'] == s]
            times = sorted(tempTopTwo['Time'].tolist())
            strokeTime = row[s]
            if strokeTime == -1:
                strokes.append(-1)
            else:
                strokes.append(findIndexInList(times, strokeTime))
        newRow = {
            'Swimmer': swimmer,
            'Gender': gender,
            'Age': age,
            'Team': team,
            'sf': strokes[0],
            'ba': strokes[1],
            'br': strokes[2],
            'fl': strokes[3],
            'lf': strokes[4],
            'im': strokes[5]
        }
        outputTeamData = outputTeamData._append(newRow, ignore_index = True)
    return outputTeamData

def checkEntries(namesEntered, twoAndTwo = []):
    rawList = []
    for stroke in namesEntered:
        for n in stroke:
            rawList.append(n)
    counts = Counter(rawList)
    uniqueNames = list(set(rawList))
    for name in uniqueNames:
        if counts[name] > 3:
            return name
        if counts[name] > 2 and name in twoAndTwo:
            return name
    else:
        return "All Good!"

def findTwoAndTwo(namesEntered):
    rawList = []
    for swimmer in namesEntered:
        if len(namesEntered[swimmer]) == 3:
            rawList.append(swimmer)
    return rawList

def findWorstStroke(scoredData, badSwimmer, namesEntered):
    curLowestDifference = 100
    curStroke = ""
    curReplacementSwimmer = None
    for s in help.getStrokes():
        index = help.getIndexOfStroke(s)
        entries = namesEntered[index]
        if badSwimmer in entries:
            badPlace = scoredData.loc[scoredData['Swimmer'] == badSwimmer, s].values[0]
            tempScored = scoredData[scoredData[s] > badPlace]
            tempScored = tempScored[~tempScored['Swimmer'].isin(entries)]
            if len(tempScored) > 0:
                tempScored = tempScored.sort_values(by = s, ascending = True)
                nextPlace = tempScored[s].values[0]
                difference = nextPlace - badPlace
                if difference < curLowestDifference:
                    curLowestDifference = difference
                    curStroke = s
                    curReplacementSwimmer = tempScored['Swimmer'].values[0]
            elif curReplacementSwimmer is None:
                curStroke = s
    index = help.getIndexOfStroke(curStroke)
    entries = namesEntered[index]
    entries.remove(badSwimmer)
    if curReplacementSwimmer is not None:
        entries.append(curReplacementSwimmer)
    namesEntered[index] = entries
    return namesEntered

def seedBestTeam(scoredData, twoAndTwo = []):
    namesEntered = []
    for s in help.getStrokes():
        tempDf = scoredData[scoredData[s] != -1]
        tempDf = tempDf.sort_values(by = s, ascending = True)
        namesForStroke = []
        if len(tempDf) > 0:
            namesForStroke.append(tempDf['Swimmer'].values[0])
            if len(tempDf) > 1:
                namesForStroke.append(tempDf['Swimmer'].values[1])
        namesEntered.append(namesForStroke)
    while checkEntries(namesEntered, twoAndTwo) != 'All Good!':
        badSwimmer = checkEntries(namesEntered, twoAndTwo)
        namesEntered = findWorstStroke(scoredData, badSwimmer, namesEntered)
    lockedEntries = []
    for l in namesEntered:
        lockedEntries.append(list(l))
    for s in help.getStrokes():
        tempDf = scoredData[scoredData[s] != -1]
        tempDf = tempDf.sort_values(by=s, ascending=True)
        tempDf = tempDf[~tempDf['Swimmer'].isin(lockedEntries[help.getIndexOfStroke(s)])]
        namesForStroke = []
        if len(tempDf) > 0:
            namesForStroke.append(tempDf['Swimmer'].values[0])
            if len(tempDf) > 1:
                namesForStroke.append(tempDf['Swimmer'].values[1])
        for n in namesForStroke:
            namesEntered[help.getIndexOfStroke(s)].append(n)
    while checkEntries(namesEntered, twoAndTwo) != 'All Good!':
        badSwimmer = checkEntries(namesEntered, twoAndTwo)
        curHighscore = -1
        curStroke = ""
        curReplacementSwimmer = None
        for s in help.getStrokes():
            index = help.getIndexOfStroke(s)
            if badSwimmer not in lockedEntries[index]:
                if badSwimmer in namesEntered[index]:
                    badPlace = scoredData.loc[scoredData['Swimmer'] == badSwimmer, s].values[0]
                    if badPlace > curHighscore:
                        curHighscore = badPlace
                        tempDf = scoredData[scoredData[s] != -1]
                        tempDf = tempDf[~tempDf['Swimmer'].isin(namesEntered[help.getIndexOfStroke(s)])]
                        tempDf = tempDf[tempDf[s] > badPlace]
                        tempDf = tempDf.sort_values(by = s, ascending = True)
                        if len(tempDf) > 0:
                            curReplacementSwimmer = tempDf['Swimmer'].values[0]
                        else:
                            curReplacementSwimmer = None
                        curStroke = s
        entries = namesEntered[help.getIndexOfStroke(curStroke)]
        entries.remove(badSwimmer)
        if curReplacementSwimmer is not None:
            entries.append(curReplacementSwimmer)
        namesEntered[help.getIndexOfStroke(curStroke)] = entries
    return namesEntered

def findBestShortStroke(allData, name):
    tempDf = allData[allData['Swimmer'] == name]
    age = tempDf['Age'].values[0]
    gender = tempDf['Gender'].values[0]
    curStroke = ''
    lowestTime = 1000
    for stroke in ['ba', 'br', 'fl']:
        time = tempDf[stroke].values[0]
        if time != -1:
            standardized = swimmerRegression.standardizeTime(age, gender, stroke, time)
            if standardized < lowestTime:
                lowestTime = standardized
                curStroke = stroke
    if curStroke == "":
        curStroke = 'ba'
    return curStroke

def seedExtraSwimmers(scoredData, allData, namesEntered):
    outputDict = {}
    for s in scoredData['Swimmer'].tolist():
        outputDict[s] = []
    for stroke in help.getStrokes():
        index = help.getIndexOfStroke(stroke)
        entries = namesEntered[index]
        for e in entries:
            if e != '':
                outputDict[e].append(stroke)
    for s in scoredData['Swimmer'].tolist():
        if len(outputDict[s]) < 2:
            if len(outputDict[s]) == 0:
                outputDict[s].append('sf(UNO)')
            if outputDict[s] == ['sf(UNO)']:
                outputDict[s].append(findBestShortStroke(allData, s) + "(UNO)")
            if outputDict[s] == ['sf']:
                outputDict[s].append(findBestShortStroke(allData, s) + "(UNO)")
            if len(outputDict[s]) == 1:
                outputDict[s].append('sf(UNO)')
    return outputDict

def findBestRelays(allData, team, age, gender, namesEntered):
    freePlace = champsInfo.getRelayPlace(allData, team, age, gender, True, [])
    medleyPlace = champsInfo.getRelayPlace(allData, team, age, gender, False, [])
    inThree = findTwoAndTwo(namesEntered)
    if freePlace > medleyPlace:
        freeRelay, freeTime = champsInfo.makeFreeRelay(allData, team, age, gender, [])
        medleyRelay, medleyTime = champsInfo.makeMedleyRelay(allData, team, age, gender, inThree)
    else:
        freeRelay, freeTime = champsInfo.makeFreeRelay(allData, team, age, gender, inThree)
        medleyRelay, medleyTime = champsInfo.makeMedleyRelay(allData, team, age, gender, [])
    return freeRelay, medleyRelay

def findRelayTime(allData, swimmers, free):
    totTime = 0
    if swimmers is None:
        return 0
    if free:
        for s in swimmers:
             totTime += allData.loc[allData['Swimmer'] == s, 'sf'].values[0]
    else:
        strokes = ['ba','br','fl','sf']
        for i in range(len(swimmers)):
            totTime += allData.loc[allData['Swimmer'] == swimmers[i], strokes[i]].values[0]
    return totTime

def findRelayScore(allData, age, gender, team, swimmers, free):
    relayTimes = champsInfo.allRelayScores(allData, age, gender, [], free)
    relayTimes = relayTimes[relayTimes['Team'] != team]
    curRelayTime = findRelayTime(allData, swimmers, free)
    # noinspection PyUnusedLocal
    relayTimes = relayTimes._append({'Team': team, 'Time': curRelayTime}, ignore_index=True)
    relayTimes = relayTimes.sort_values(by = 'Time', ascending = True)
    return champsInfo.getIndex(relayTimes, 'Team', team)

def findJustification(swimmer, ageGroupOutput, twoAndTwoOutput, relaysOld, relaysNew, scoredData, allData):
    oldEvents = ageGroupOutput[swimmer]
    newEvents = twoAndTwoOutput[swimmer]
    runningJustification = ""
    newSwimmer = ""
    removedEvent = ""
    age = np.max(scoredData['Age'])
    gender = scoredData['Gender'].values[0]
    team = scoredData['Team'].values[0]
    for event in oldEvents:
        if event not in newEvents:
            removedEvent = event
    oldEntries = []
    newEntries = []
    for s in ageGroupOutput:
        if removedEvent in ageGroupOutput[s]:
            oldEntries.append(s)
        if removedEvent in twoAndTwoOutput[s]:
            newEntries.append(s)
    oldScored = scoredData[scoredData['Swimmer'].isin(oldEntries)]
    oldScored = oldScored.sort_values(by = removedEvent, ascending = True)
    newScored = scoredData[scoredData['Swimmer'].isin(newEntries)]
    newScored = newScored.sort_values(by = removedEvent, ascending = True)
    oldScoring = []
    newScoring = []
    if len(oldScored) > 0:
        oldScoring.append(oldScored['Swimmer'].values[0])
        if len(oldScored) > 1:
            oldScoring.append(oldScored['Swimmer'].values[1])
    if swimmer not in oldScoring:
        runningJustification += f'Removed {swimmer} from {removedEvent} due to not scoring'
    else:
        if len(newScored) > 0:
            newScoring.append(newScored['Swimmer'].values[0])
            if len(newScored) > 1:
                newScoring.append(newScored['Swimmer'].values[1])
        swimmerTime = allData.loc[allData['Swimmer'] == swimmer, removedEvent].values[0]
        for s in newScored:
            if s not in oldScored:
                newSwimmer = s
        if newSwimmer != "":
            newSwimmerTime = allData.loc[allData['Swimmer'] == newSwimmer, removedEvent].values[0]
            swimmerScore = placeToScore(scoredData.loc[scoredData['Swimmer'] == swimmer, removedEvent].values[0])
            newSwimmerScore = placeToScore(scoredData.loc[scoredData['Swimmer'] == newSwimmer, removedEvent].values[0])
            runningJustification += f'Removed {swimmer} from {removedEvent} with time {swimmerTime} and replaced with {newSwimmer} with time {newSwimmerTime} scoring {swimmerScore - newSwimmerScore} less'
        else:
            runningJustification += f'Removed {swimmer} from {removedEvent} with time {swimmerTime} with no replacement'
    relayDifference = 0
    medleyOrFree = ""
    if relaysOld[0] != relaysNew[0]:
        oldFree = findRelayTime(allData, relaysOld[0], True)
        newFree = findRelayTime(allData, relaysNew[0], True)
        relayDifference = oldFree - newFree
        medleyOrFree = "free"
    elif relaysOld[1] != relaysNew[1]:
        oldMedley = findRelayTime(allData, relaysOld[1], False)
        newMedley = findRelayTime(allData, relaysNew[1], False)
        relayDifference = oldMedley - newMedley
        medleyOrFree = 'medley'
    oldRelayScore = findRelayScore(allData, age, gender, team, relaysOld[0], True) + findRelayScore(allData, age, gender, team, relaysOld[1],False)
    newRelayScore = findRelayScore(allData, age, gender, team, relaysNew[0], True) + findRelayScore(allData, age, gender, team,relaysNew[1], False)
    runningJustification += f'| Relays improved {newRelayScore - oldRelayScore} points due to adding {swimmer} to {medleyOrFree} relay resulting in {relayDifference} time'
    return runningJustification


def seedEntireTeam(allData, team, optOutList = [], doTwos = True):
    allData = allData[~allData['Swimmer'].isin(optOutList)]
    outputDict = {}
    originalEntriesDict = {}
    twoAndTwoDf = pd.DataFrame()
    outputRelays = []
    originalOutputRelays = []
    ageRanges = [[5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16, 17, 18]]
    genders = ['M', 'W']
    justifications = ""
    for ageRange in ageRanges:
        for gender in genders:
            scoredData = scoreOneTeam(allData, ageRange, gender, team)
            namesEntered = seedBestTeam(scoredData)
            ageGroupOutput = seedExtraSwimmers(scoredData, allData, namesEntered)
            freeRelay, medleyRelay = findBestRelays(allData, team, np.max(ageRange), gender, ageGroupOutput)
            relays = [freeRelay, medleyRelay]
            originalOutputRelays.append(relays)
            originalEntriesDict.update(ageGroupOutput)
            bestScore = scoreAgeGroup(scoredData, allData, ageGroupOutput, relays)
            curBestScore = bestScore
            curBestOutput = ageGroupOutput
            curBestRelays = relays
            curJustification = ""
            if doTwos:
                twoAndTwoSwimmers = findTwoAndTwo(ageGroupOutput)
                for r in range(1, len(twoAndTwoSwimmers) + 1):
                    for combo in combinations(twoAndTwoSwimmers, r):
                        twoAndTwos = list(combo)
                        key = ''
                        for t in twoAndTwos:
                            key += t + ', '
                        namesEnteredTwo = seedBestTeam(scoredData, twoAndTwos)
                        ageGroupOutputTwo = seedExtraSwimmers(scoredData, allData, namesEnteredTwo)
                        freeRelayTwo, medleyRelayTwo = findBestRelays(allData, team, np.max(ageRange), gender, ageGroupOutputTwo)
                        relaysTwo = [freeRelayTwo, medleyRelayTwo]
                        twoAndTwoScore = scoreAgeGroup(scoredData, allData, ageGroupOutputTwo, relaysTwo)
                        scoreDifference = bestScore - twoAndTwoScore
                        newRow = {
                            'Names': twoAndTwos,
                            'Age': ageRange,
                            'Gender': gender,
                            'Score Difference': scoreDifference,
                        }
                        twoAndTwoDf = twoAndTwoDf._append(newRow, ignore_index = True)
                        if curBestScore < twoAndTwoScore:
                            curBestScore = twoAndTwoScore
                            curBestOutput = ageGroupOutputTwo
                            tempJustification = ""
                            for s in twoAndTwos:
                                tempJustification += findJustification(s, ageGroupOutput, ageGroupOutputTwo, relays, relaysTwo, scoredData, allData) + '\n'
                            curJustification = tempJustification
                            curBestRelays = relaysTwo
            outputDict.update(curBestOutput)
            outputRelays.append(curBestRelays)
            justifications += curJustification
            print(f'Seeded {ageRange} and {gender}')
    for relays in outputRelays:
        freeRelay = relays[0]
        medleyRelay = relays[1]
        if freeRelay != None:
            for s in freeRelay:
                outputDict[s].append('fr')
        strokes = ['ba', 'br', 'fl', 'sf']
        if medleyRelay != None:
            for i in range(len(medleyRelay)):
                outputDict[medleyRelay[i]].append(f"mr({strokes[i]})")
    return outputDict, originalEntriesDict, justifications, outputRelays, originalOutputRelays, twoAndTwoDf

def getTwoAndTwoEntries(allData, ageRange, gender, team, twoAndTwoList):
    scoredData = scoreOneTeam(allData, ageRange, gender, team)
    namesEntered = seedBestTeam(scoredData, twoAndTwoList)
    ageGroupOutput = seedExtraSwimmers(scoredData, allData, namesEntered)
    return ageGroupOutput

def transformOutputDict(outputDict):
    outputString = ''
    for s in outputDict:
        outputString += str(s) + ': ' + str(outputDict[s]) + '\n'
    return outputString

def placeToScore(place):
    if place == -1:
        return -1
    if place == 1:
        return 19
    else:
        return -0.5 * place + 19

def relayToScore(place):
    return placeToScore(place) + 10

def dataframePlaceToScore(df):
    for stroke in help.getStrokes():
        df[stroke] = df[stroke].apply(placeToScore)
    return df

def getAllRelayTeams(testData):
    swimmers = testData['Swimmer'].tolist()
    

def scoreAgeGroup(scoredData, allData, entriesDict, relays):
    totalScore = 0
    age = np.max(scoredData['Age'])
    gender = scoredData['Gender'].values[0]
    team = scoredData['Team'].values[0]
    swimmers = scoredData['Swimmer'].tolist()
    for s in help.getStrokes():
        entered = []
        for swimmer in swimmers:
            if s in entriesDict[swimmer]:
                entered.append(swimmer)
        tempDf = scoredData[scoredData['Swimmer'].isin(entered)]
        tempDf = tempDf.sort_values(by=s, ascending=True)
        if len(tempDf) > 0:
            totalScore += placeToScore(tempDf[s].values[0])
            if len(tempDf) > 1:
                totalScore += placeToScore(tempDf[s].values[1])

    if relays[0] != None and relays[1] != None:
        totalScore += findRelayScore(allData, age, gender, team, relays[0], True) + findRelayScore(allData, age, gender, team, relays[1], False)
    elif relays[0] != None:
        totalScore += findRelayScore(allData, age, gender, team, relays[0], True)
    elif relays[1] != None:
        findRelayScore(allData, age, gender, team, relays[1], False)
    return totalScore

# allData = pd.read_csv("C:/Users/ucg8nb/Downloads/2025 Data Transform.csv")
# optOutList = pd.read_csv("C:/Users/ucg8nb/Downloads/OptOutList.csv")
# optOutList['Name'] = ' ' + optOutList['Name']
# optOuts = optOutList['Name'].tolist()
# print(optOuts)
# outputDict, originalEntriesDict, justification, outputRelays, originalOutputRelays, twoAndTwoDf = seedEntireTeam(allData, 'CITY', doTwos = True, optOutList = optOuts)
# print(transformOutputDict(outputDict))
# # print(outputRelays)
# print(justification)
# twoAndTwoDf.to_csv("C:/Users/ucg8nb/Downloads/Two And Two.csv")







