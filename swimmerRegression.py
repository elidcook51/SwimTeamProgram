import pandas as pd
import numpy as np
import databaseBuilder as db
from scipy.stats import norm

standardizationDf = pd.read_csv("C:/Users/ucg8nb/Downloads/Swimming Time Standardization.csv")

def ageToAgeRange(age):
    ageRanges = [[5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16, 17, 18]]
    for a in ageRanges:
        if age in a:
            return a
    return []

def createStandardizations():
    fullSwimData = pd.read_csv("C:/Users/ucg8nb/Downloads/Full Swim Data.csv")
    badSwimNums = ['81', '82', '83', '84', '85', '86', '87', '88', '89', '90']
    fullSwimData = fullSwimData[~fullSwimData['Event'].isin(badSwimNums)]

    ageRanges = [[5,6], [7,8], [9,10], [11,12], [13,14], [15,16,17,18]]
    genders = ['M', "W"]
    strokes = ['sf', 'ba', 'br', 'fl', 'lf', 'im']

    agesList = []
    gendersList = []
    strokesList = []
    for index, row in fullSwimData.iterrows():
        age, gender = db.getAgeGender(row['Event'])
        stroke = db.getEventType(row['Event'])
        agesList.append(age)
        gendersList.append(gender)
        strokesList.append(stroke)
    fullSwimData['Age'] = agesList
    fullSwimData['Gender'] = gendersList
    fullSwimData['Stroke'] = strokesList

    outputDf = pd.DataFrame()
    for a in ageRanges:
        for g in genders:
            for s in strokes:
                tempDf = fullSwimData[fullSwimData['Age'].isin(a)]
                tempDf = tempDf[tempDf['Gender'] == g]
                tempDf = tempDf[tempDf['Stroke'] == s]
                tempDf = tempDf[tempDf['Time'] != -1]
                times = tempDf['Time'].tolist()
                newRow = {
                    'Age': np.max(a),
                    'Gender': g,
                    'Stroke': s,
                    'Mean': np.mean(times),
                    'Standard Deviation': np.std(times)
                }
                outputDf = outputDf._append(newRow, ignore_index = True)
    outputDf.to_csv("C:/Users/ucg8nb/Downloads/Swimming Time Standardization.csv")

def standardizeTime(age, gender, stroke, time):
    ageRange = ageToAgeRange(age)
    tempDf = standardizationDf[standardizationDf['Age'] == np.max(ageRange)]
    tempDf = tempDf[tempDf['Gender'] == gender]
    tempDf = tempDf[tempDf['Stroke'] == stroke]
    mean = tempDf['Mean'].values[0]
    std = tempDf['Standard Deviation'].values[0]
    return norm.cdf(time, mean, std)


