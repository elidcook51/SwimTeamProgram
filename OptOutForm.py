import pandas as pd
import numpy as np

fullForm = pd.read_csv("C:/Users/ucg8nb/Downloads/Swim Meet Opt Out Form (Responses) - Form Responses 1.csv")

def createCleanedOptOuts(fullForm):
    oldCols = ['Timestamp', "Swimmer's Full Name", 'What meets will they not be attending?', "Swimmer's Age"]
    fullForm = fullForm[oldCols]
    fullForm = fullForm.dropna()
    meets = ['June 11', 'June 18', 'June 25', 'July 2', 'July 9', 'July 16']
    newCols = ['Name', 'Age']
    for m in meets:
        newCols.append(m + " Opt Out")
        newCols.append(m + ' Time')
    outputFrame = pd.DataFrame(columns = newCols)
    for index, row in fullForm.iterrows():
        newDict = {}
        for col in newCols:
            newDict[col] = 0
        newDict['Name'] = row["Swimmer's Full Name"]
        newDict['Age'] = row["Swimmer's Age"]
        for m in meets:
            if m in row['What meets will they not be attending?']:
                newDict[m + ' Opt Out'] = 1
                newDict[m + ' Time'] = row['Timestamp']
        outputFrame = outputFrame._append(newDict, ignore_index = True)
    return outputFrame

def checkScratches(meetEntriesPath, meetResultsPath):
    entries = pd.read_csv(meetEntriesPath, usecols = [14], header = None)
    results = pd.read_csv(meetResultsPath, usecols = [10], header = None)
    entries.columns = ['Name']
    results.columns = ['Name']
    results = results['Name'].tolist()
    entries = entries['Name'].tolist()
    for i in range(0, len(results)):
        tempResult = results[i]
        tempResult = tempResult[:tempResult.find('(')-1] + tempResult[tempResult.find('('):tempResult.find(')') + 1]
        results[i] = tempResult
    outputList = []
    for e in entries:
        if e not in results:
            outputList.append(e)
    return sorted(list(set(outputList)))

# createCleanedOptOuts(fullForm).to_csv("C:/Users/ucg8nb/Downloads/Cleaned Opt Outs.csv")
# optOuts = pd.read_csv("C:/Users/ucg8nb/Downloads/Cleaned Opt Outs.csv")
# meetEntries = "C:/Users/ucg8nb/Downloads/check entries july 2.csv"
# meetResults= "C:/Users/ucg8nb/Downloads/check scratches july 2.csv"
# scratches = checkScratches(meetEntries, meetResults)
# # july2 = optOuts[optOuts["July 2 Opt Out"] == 1]
# # july2 = july2[['Name', 'Age', 'July 2 Opt Out', 'July 2 Time']]
# # july2.to_csv("C:/Users/ucg8nb/Downloads/July 2 opt outs.csv")
# july9 = optOuts[optOuts["July 9 Opt Out"] == 1]
# july9[['firstName', 'lastName']] = july9['Name'].str.split(n = 1, expand = True)
# july9 = july9.sort_values(by = ['lastName', 'firstName'])
# july9 = july9[['Name', 'Age', 'July 9 Opt Out', 'July 9 Time']]
# july9.to_csv("C:/Users/ucg8nb/Downloads/July 9 opt outs.csv")