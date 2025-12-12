import algorithms
import relayHelp as relay
import individualScore as ind
import seedingHelp as help
import databaseBuilder as db
import pandas as pd
import numpy as np

# allData = pd.read_csv("C:/Users/ucg8nb/Downloads/2025 Data Transform.csv")

def createAllData(jslWebsiteLink, outputPath):
    db.getFullResults(jslWebsiteLink, 'Current Data')
    curData = db.getFullData('Current Data')
    trans = db.fullDataTransform(curData)
    trans.to_csv(outputPath)

def seedChamps(allData, team):
    ageRanges = help.getAgeRange()
    genders = help.getGenders()
    for a in ageRanges:
        for g in genders:
            tempDf = ind.scoreOneTeam(allData, a, g, team)
            tempDf = ind.dataframePlaceToScore(tempDf)
            relayPos = relay.buildRelayPositions(allData, a, g, team, algorithms.getThreeEventSwimmers(tempDf))
            swimmers = tempDf['Swimmers'].tolist()
            incData = relay.buildInc(relayPos, swimmers)
            x_vals, y_vals, points = algorithms.relayProgram(tempDf, relayPos, incData)
            