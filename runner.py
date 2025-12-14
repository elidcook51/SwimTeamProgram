import algorithms
import relayHelp as relay
import individualScore as ind
import seedingHelp as help
import databaseBuilder as db
import pandas as pd
import numpy as np

allData = pd.read_csv("C:/Users/ucg8nb/Downloads/2025 Data Transform.csv")

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
    for a in ageRanges:
        for g in genders:
            tempDf = ind.scoreOneTeam(allData, a, g, team)
            tempDf = ind.dataframePlaceToScore(tempDf)
            relayPos = relay.buildRelayPositions(allData, a, g, team, algorithms.getThreeEventSwimmers(tempDf))
            swimmers = tempDf['Swimmer'].tolist()
            incData = relay.buildInc(relayPos, swimmers)
            x_vals, y_vals, points = algorithms.relayProgram(tempDf, relayPos, incData)
            outputString += resultsToString(x_vals,y_vals, incData, allData)
    return outputString

print(seedChamps(allData, 'CITY'))