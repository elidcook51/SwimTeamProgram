import algorithms
import relayHelp as relay
import individualScore as ind
import seedingHelp as help
import databaseBuilder as db
import pandas as pd
import numpy as np

allData = pd.read_csv("C:/Users/ucg8nb/Downloads/Full Swim Data.csv")

def createAllData(jslWebsiteLink, outputPath):
    db.getFullResults(jslWebsiteLink, 'Current Data')
    curData = db.getFullData('Current Data')
    trans = db.fullDataTransform(curData)
    trans.to_csv(outputPath)

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

def seedChamps(allData, team):
    ageRanges = help.getAgeGroups()
    genders = help.getGenders()
    outputString = ''
    totPoints = 0
    for a in ageRanges:
        for g in genders:
            tempDf = ind.scoreOneTeam(allData, a, g, team)
            tempDf = ind.dataframePlaceToScoreChamps(tempDf)
            relayPos = relay.buildRelayPositions(allData, a, g, team, algorithms.getThreeEventSwimmers(tempDf))
            swimmers = tempDf['Swimmer'].tolist()
            incData = relay.buildInc(relayPos, swimmers)
            x_vals, y_vals, points = algorithms.relayProgram(tempDf, relayPos, incData)
            totPoints += points
            outputString += resultsToString(x_vals,y_vals, incData, allData)
    return outputString + f'\n Total Points Scored: {totPoints}'

def seedDuelMeet(allData, team1, team2):
    ageRanges = help.getAgeGroups()
    genders = help.getGenders()
    outputString = ''
    team1Points = 0
    team2Points = 0
    for a in ageRanges:
        for g in genders:
            tempDf = ind.ScoreOneteamDuel(allData, a, g, team1, team2)
            tempDf = ind.dataframePlaceToScoreDuel(tempDf)
            x_vals = algorithms.noRelayProgram(tempDf)
            print(x_vals)


print(seedDuelMeet(allData, 'CITY', 'LMST'))