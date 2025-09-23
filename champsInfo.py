import pandas as pd
import databaseBuilder as db
import matplotlib.pyplot as plt
import os
from itertools import combinations
from itertools import permutations
import win32print
import win32api
import PyPDF2

teams = ['ACAC', 'BHSC', 'CITY', 'CGST', 'CBST', 'ELKS', 'FV', 'FCC','FAST', 'FSBC', 'GLEN', 'GHG', 'HM', 'KWC', 'FLST', 'LMST', 'LG']
ages = [6, 8, 10, 12, 14, 18]
gender = ['M', 'W']
strokes = ['sf', 'ba', 'br', 'fl', 'lf', 'im']

def getAgeRange(age):
    ranges = ['6 & Under', '8 & Under', '9-10', '11-12', '13-14', '15-18']
    for r in ranges:
        if str(age) in r:
            return r
    return ''

def getGenderTitle(gender):
    if gender == 'M':
        return 'Boys'
    return 'Girls'

def getTopTwo(database, stroke, age, gender):
    tempDf = database[database['Age'] == age]
    tempDf = tempDf[tempDf['Gender'] == gender]
    tempDf = tempDf[tempDf[stroke] != -1]
    tempSorted = tempDf.sort_values(by = stroke, ascending = True)
    firstRound = tempSorted.groupby('Team', as_index = False).first()
    excludeList = firstRound['Swimmer'].tolist()
    tempDf = tempDf[~tempDf['Swimmer'].isin(excludeList)]
    tempSorted = tempDf.sort_values(by = stroke, ascending = True)
    secondRound = tempSorted.groupby('Team', as_index = False).first()
    outputDf = pd.concat([firstRound, secondRound], ignore_index = True)
    outputDf = outputDf.sort_values(by = stroke, ascending = True)
    outputDf.reset_index(inplace = True)
    outputDf = outputDf[['Swimmer', 'Team', stroke]]
    return outputDf

def getPos(database, swimmer, stroke, age ,gender):
    tempDf = getAgeGroup(database, age, gender)
    sortedDf = tempDf.sort_values(by = stroke, ascending = True)
    sortedDf.reset_index(inplace = True)
    return getIndex(sortedDf, 'Swimmer', swimmer)

def getIndex(sortedDf, colName, specName):
    sortedDf.reset_index(inplace = True)
    mask = sortedDf[colName].apply(lambda x: specName in x)
    foundIndex = sortedDf.index[mask]
    intPos = [sortedDf.index.get_loc(loc) for loc in foundIndex]
    return int(intPos[0])

def getTeamAgeGroup(database, team, age, gender):
    df = getAgeGroup(database, age, gender)
    df = df[df['Team'] == team]
    return df

def getAgeGroup(database, age, gender):
    df = database[database['Age'] == age]
    df = df[df['Gender'] == gender]
    return df

def getRawPosition(database, team, age, gender):
    teamDf = getTeamAgeGroup(database, team, age, gender)
    teamDf.drop(columns = ['Team', 'Age', 'Gender'], inplace = True)
    for index, row in teamDf.iterrows():
        for s in strokes:
            if row[s] != -1:
                teamDf.at[index, s] = getPos(database, row['Swimmer'], s, age, gender)
    for s in strokes:
        teamDf[s] = teamDf[s].astype(int)
    return teamDf

def getScorePosition(database, team, age, gender):
    teamDf = getTeamAgeGroup(database,team,age,gender)
    for index, row in teamDf.iterrows():
        for s in strokes:
            if row[s] != -1:
                topTwo = getTopTwo(database, s, age, gender)
                topTwo = topTwo[topTwo['Team'] != team]
                dict = {
                    'Swimmer': row['Swimmer'],
                    'Team': team,
                    s: row[s]
                }
                topTwo = topTwo._append(dict, ignore_index = True)
                topTwo = topTwo.sort_values(by = s, ascending = True)
                teamDf.at[index, s] = getIndex(topTwo, 'Swimmer', row['Swimmer'])
    for s in strokes:
        teamDf[s] = teamDf[s].astype(int)
    return teamDf

def dfToPdf(df, outputName, outputFolder):
    fig, ax = plt.subplots(figsize = (8.27, 11.7))
    ax.axis('tight')
    ax.axis('off')
    ax.set_title(outputName)
    table = ax.table(cellText = df.values, colLabels = df.columns, loc = 'left')
    table.scale(2, 2)
    ax.figure.set_size_inches(8, 11)
    pdf_path = os.path.join(outputFolder, outputName)
    ax.axis('off')
    plt.savefig(pdf_path, format = 'pdf', bbox_inches = 'tight')


def delFolder(folderPath):
    for filename in os.listdir(folderPath):
        filepath = os.path.join(folderPath, filename)
        os.remove(filepath)
    os.rmdir(folderPath)

def createFolders(team, database):
    rawPath = 'Raw Position Folder'
    scorePath = 'Score Position Folder'
    if os.path.exists(rawPath):
        delFolder(rawPath)
    if os.path.exists(scorePath):
        delFolder(scorePath)
    os.makedirs(rawPath, exist_ok = True)
    os.makedirs(scorePath, exist_ok = True)
    for a in ages:
        for g in gender:
            pdfName = ''
            if g == 'M':
                pdfName += 'Boys'
            else:
                pdfName += 'Girls'
            pdfName += ' ' + getAgeRange(a)
            rawData = getRawPosition(database, team, a, g)
            scoreData = getScorePosition(database, team, a, g)
            dfToPdf(rawData, pdfName + ' Raw Position.pdf', rawPath)
            print('Added ' + pdfName + ' to ' + rawPath)
            dfToPdf(scoreData, pdfName + ' Score Position.pdf', scorePath)
            print('Added ' + pdfName + ' to ' + scorePath)

def makeFreeRelay(database, team, age, gender, excludedSwimmers):
    teamDf = getTeamAgeGroup(database, team, age, gender)
    teamDf = teamDf[~teamDf['Swimmer'].isin(excludedSwimmers)]
    teamDf = teamDf[teamDf['sf'] != -1]
    sortedDf = teamDf.sort_values(by = 'sf', ascending = True)
    sortedDf = sortedDf.head(4)
    if len(sortedDf) != 4:
        return None, float('-inf')
    sortedDf = sortedDf.sort_values(by = 'sf', ascending = False)
    bestComb = sortedDf['Swimmer'].tolist()
    totalTime = 0
    for t in sortedDf['sf'].tolist():
        totalTime += t
    return bestComb, totalTime

def calcMedleyTime(swimmers, times):
    totalTime = 0
    strokes = ['fl', 'ba', 'br', 'fr']
    for index, swimmer in enumerate(swimmers):
        strokeTime = times[swimmer][strokes[index]]
        if strokeTime == -1:
            return float('-inf')
        totalTime += strokeTime
    return totalTime

def makeMedleyRelay(database, team, age, gender, excludedSwimmers):
    teamDf = getTeamAgeGroup(database,team,age,gender)
    teamDf = teamDf[~teamDf['Swimmer'].isin(excludedSwimmers)]
    if teamDf.size < 4:
        return None, float('inf')
    swimmers = teamDf['Swimmer'].tolist()
    fl = teamDf['fl'].tolist()
    ba = teamDf['ba'].tolist()
    br = teamDf['br'].tolist()
    fr = teamDf['sf'].tolist()
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

def allRelayScores(database, age, gender, excludedSwimmers, free):
    allTeamsRelays = pd.DataFrame(columns = ['Team', 'Time'])
    for t in teams:
        if not free:
            teamComp, teamTime = makeMedleyRelay(database, t, age, gender, excludedSwimmers)
        else:
            teamComp, teamTime = makeFreeRelay(database, t, age, gender, excludedSwimmers)
        allTeamsRelays = allTeamsRelays._append({'Team': t, 'Time': teamTime}, ignore_index = True)
    sortedRelays = allTeamsRelays.sort_values(by = 'Time', ascending = True)
    return sortedRelays

def getRelayPlace(database, team, age, gender, free, excludedSwimmers):
    relayPlaces = allRelayScores(database, age, gender, excludedSwimmers, free)
    smallRelay = relayPlaces[relayPlaces['Team'] == team]
    if smallRelay['Time'].values[0] == float('-inf'):
        return -1
    relayPlaces = relayPlaces[relayPlaces['Time'] != float('-inf')]
    return getIndex(relayPlaces, 'Team', team)

def makeRelayPdf(team, database):
    relayPath = 'Relay Position Folder'
    if os.path.exists(relayPath):
        delFolder(relayPath)
    os.makedirs(relayPath, exist_ok = True)
    relayPos = pd.DataFrame(columns = ['Age Group', 'Free Position', 'Medley Position'])
    for a in ages[1:]:
        for g in gender:
            ageGroup = getGenderTitle(g) + ' ' + getAgeRange(a)
            dict = {
                'Age Group': ageGroup,
                'Free Position': getRelayPlace(database, team, a, g, True, []),
                'Medley Position': getRelayPlace(database, team, a, g, False, [])
            }
            relayPos = relayPos._append(dict, ignore_index = True)
            print(f"Added {ageGroup} to DataFrame")
            sortedRelaysFree = allRelayScores(database, a, g, [], True)
            sortedRelaysFree.rename(columns = {'Time' : 'Free Time'}, inplace = True)
            sortedRelaysMedley = allRelayScores(database,a ,g, [], False)
            sortedRelaysMedley.rename(columns = {'Time': 'Medley Time'}, inplace = True)
            sortedRelays = pd.merge(sortedRelaysFree, sortedRelaysMedley, on = 'Team')
            pdfName = ''
            if g == 'M':
                pdfName += 'Boys'
            else:
                pdfName += 'Girls'
            pdfName += ' ' + getAgeRange(a) + '.pdf'
            dfToPdf(sortedRelays, pdfName, 'Relay Position Folder')
            print(f'Added {pdfName} to the folder')
    dfToPdf(relayPos, 'Relay Positions.pdf', relayPath)
    return relayPos

def printPdfs(folderName):
    printerName= win32print.GetDefaultPrinter()
    for file in os.listdir(folderName):
        printPdf(os.path.join(folderName, file))


def printPdf(file):
    printerName = win32print.GetDefaultPrinter()
    outputPath = 'scaledPDFToPrint'
    scale_factor = 0.6
    with open(file, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        pdf_writer = PyPDF2.PdfWriter()

        for page in pdf_reader.pages:
            page.scale_by(scale_factor)
            pdf_writer.add_page(page)

        with open(outputPath, 'wb') as output_file:
            pdf_writer.write(output_file)
    try:
        win32api.ShellExecute(0, 'print', file, f'/d:"{printerName}"', '.', 0)
    except Exception as e:
        print(f"Error: {e}")
    os.remove(outputPath)

def makePDFToPrint(folderNames):
    if os.path.exists('printerPDF.pdf'):
        os.remove('printerPDF.pdf')
    pdf_writer = PyPDF2.PdfWriter()
    for folder in folderNames:
        for file in os.listdir(folder):
            fileName = os.path.join(folder, file)
            pdf_reader = PyPDF2.PdfReader(fileName)
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
    pdf_writer.write('printerPDF.pdf')

#db.getFullResults()
#db.updateDatabase()
database = pd.read_csv("C:/Users/ucg8nb/Downloads/2025 Data Transform.csv")
#createFolders('CITY', database)
makeRelayPdf('CITY',database)
# os.remove('printerPDF')
# makePDFToPrint(['Raw Position Folder', 'Score Position Folder', 'Relay Position Folder'])
#printPdfs('Raw Position Folder')
