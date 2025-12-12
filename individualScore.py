import pandas as pd
import numpy as np
import os
from itertools import combinations
import seedingHelp as help
import swimmerRegression
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

def placeToScore(place):
    if place == -1:
        return -1
    if place == 1:
        return 19
    else:
        return -0.5 * place + 19

def dataframePlaceToScore(df):
    for stroke in help.getStrokes():
        df[stroke] = df[stroke].apply(placeToScore)
    return df








