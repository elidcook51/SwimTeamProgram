from pypdf import PdfReader
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup


relayNums = ['1P', 1, 2]
for i in range(11,21):
    relayNums.append(i)
for i in range(71,81):
    relayNums.append(i)

eventNums = ['21P', '22P', '41P', '42P']
for j in range(1, 11):
    for i in [0, 10, 20, 30, 40, 50, 60, 70]:
        eventNums.append(i + j)

def convertTimes(list, sort):
    if sort:
        list.sort()
    newList = []
    for i in range(0, len(list)):
        newList.append(timeInMinutes(list[i]))
    return newList

def timeInMinutes(time):
    minutes = 0
    while time >= 60:
        minutes += 1
        time -= 60
    if minutes == 0:
        return str(time)[:5]
    elif time >= 10:
        return str(minutes) + ':' + str(time)[:5]
    else:
        return str(minutes) + ':0' + str(time)[:4]
def appendDict(df, dict):
    tempDf = pd.DataFrame(dict)
    df = df._append(tempDf, ignore_index = True)
    return df


def readEvent(line):
    end = 0
    start = 0
    for i, char in enumerate(line):
        if char.isdigit() and start == 0:
            start = i
        if (not char.isdigit()) and start != 0:
            end = i
            break
    if(line[end] == 'P'):
        return line[start:end+1]
    return int(line[start:end])

def toTeamAbbrv(name):
    keywords = ['atla', 'boar', 'city', 'croz', 'culp', 'elks', 'fair', 'farm', 'fluv', 'fry', 'glen', 'gree', 'holl', 'key', 'fore', 'lake', 'loui']
    team = ['ACAC', 'BHSC', 'CITY', 'CGST', 'CBST', 'ELKS', 'FV', 'FCC','FAST', 'FSBC', 'GLEN', 'GHG', 'HM', 'KWC', 'FLST', 'LMST', 'LG']
    if name in team:
        return name
    name = name.lower()
    for i in range(0, len(keywords)):
        if keywords[i] in name:
            return team[i]
    return ''

def getTeamName(line):
    name = ''
    for i, char in enumerate(line):
        if char.isdigit():
            break
        else:
            name += char
    return toTeamAbbrv(name)

def getSwimmer(line):
    i = line.find(',')
    while i > 0:
        if(line[i].isdigit()):
            break
        if(line[i] == ' '):
            break
        i -= 1
    start = i
    i = line.find(',') + 2
    while i < len(line):
        if line[i] == ' ':
            break
        i += 1
    stop = i
    lastName = line[start+1:line.find(',')]
    lastName = lastName.replace('-','')
    firstName = line[line.find(',') + 1:stop]
    return firstName + ' ' + lastName

def getPoolType(team):
    LCM = ['ACAC', 'FSBC']
    SCY = ['BHSC', 'KWC', 'LG']
    if team in LCM:
        return False, True
    if team in SCY:
        return True, False
    else:
        return False, False

def getSCMTime(time, team):
    yards, long = getPoolType(team)
    if not yards and not long:
        return time
    if yards:
        return time * 1.11
    if long:
        return time * 0.971
def getTime(line, team):
    time = 0
    perIndex = line.find(".")
    if perIndex == -1:
        return -1
    while not line[perIndex - 1].isdigit():
        perIndex = line.find('.', perIndex + 1)
        if perIndex == -1:
            return -1
    if line[perIndex - 3] == ':':
        time += int(line[perIndex - 4]) * 60
    time += float(line[perIndex - 2:perIndex+3])
    time = getSCMTime(time, team)
    return time

def readPage(text, homeTeam, date):
    lines = text.splitlines()
    curEvent = 0
    prevLine = ''
    inEvent = False
    events = []
    teams = []
    swimmers = []
    times = []
    dates = []
    for l in lines:
        if 'Combined Team Scores' in l:
            break
        if 'Event' in l and ('Boys' in l or 'Girls' in l):
            curEvent = readEvent(l)
            inEvent = False
        if 'Age' in prevLine:
            inEvent = True
        if curEvent not in relayNums and inEvent:
            teams.append(getTeamName(l))
            swimmers.append(getSwimmer(l))
            times.append(getTime(l, homeTeam))
            events.append(curEvent)
            dates.append(date)
        prevLine = l
    dict = {
        'Team': teams,
        'Event': events,
        'Swimmer': swimmers,
        'Time': times,
        'Date': dates
    }
    return dict

def getTopTimes(teamName, fullData):
    fullData = fullData[fullData['Time'] != -1]
    fullData = fullData[fullData['Team'].str.contains(teamName)]
    fullData = fullData.reset_index(drop=True)
    swimmingEvents = []
    for num in eventNums:
        if num not in relayNums:
            swimmingEvents.append(num)
    eventResults = {}
    for e in swimmingEvents:
        eventName = 'Event ' + str(e)
        temp = fullData[fullData['Event'] == str(e)]
        tempSorted = temp.sort_values(by='Time', ascending=True)
        fastestTimes = tempSorted.groupby('Swimmer').first()['Time'].tolist()
        fastestTimes = convertTimes(fastestTimes, True)
        eventResults[eventName] = fastestTimes
    for key, value in eventResults.items():
        print(key + ': [' + ', '.join(value) + ']')

def checkOddTeamCases(line):
    temp = line.lower()
    if temp.find('@') == -1:
        start = temp.find('at')
        start += 3
        return toTeamAbbrv(line[start:start+4])
    else:
        start = temp.find('@')
        return toTeamAbbrv(line[start+1:start+5])

def getFullData(folderPath):
    fullData = pd.DataFrame(columns = ['Team', 'Event', 'Swimmer', 'Time', 'Date'])
    for fileName in os.listdir(folderPath):
        filePath = os.path.join(folderPath, fileName)
        reader = PdfReader(filePath)
        if len(reader.pages[0].extract_text().splitlines()) > 1:
            tempLine = reader.pages[0].extract_text().splitlines()[1]
            team = tempLine[tempLine.find('@') + 2:tempLine.find('@') + 6]
            if team.find(' ') != -1:
                team = team[:team.find(' ')]
            team = toTeamAbbrv(team)
            if team == '':
                team = checkOddTeamCases(tempLine)
            if "/" in tempLine:
                date = tempLine[tempLine.find('-') + 2:tempLine.find('-') + 11]
            else:
                tempLine = reader.pages[0].extract_text().splitlines()[2]
                if "/" in tempLine:
                    date = tempLine[tempLine.find('/')- 1: tempLine.find('/') + 8]
                else:
                    date = tempLine[tempLine.find('_')- 1: tempLine.find('_') + 8]
            date = date.replace("_", "/")
            for page in reader.pages:
                fullData = appendDict(fullData, readPage(page.extract_text(), team, date))
            print(f'{filePath} scraped')
    print('All pdfs scraped')
    return fullData


def getAgeGender(eventNum):
    age = 0
    if 'P' in str(eventNum):
        age = 6
        eventNum = int(eventNum[:-1])
    eventNum = int(eventNum)
    eventNum = eventNum%10
    if eventNum == 0 and age != 6:
        age = 18
    elif eventNum <= 2 and age != 6:
        age = 8
    elif eventNum <= 4 and age != 6:
        age = 10
    elif eventNum <= 6 and age != 6:
        age = 12
    elif eventNum <= 8 and age != 6:
        age = 14
    else:
        if age != 6:
            age = 18
    if eventNum%2 == 0:
        return age, 'W'
    else:
        return age, 'M'

def addSwimmer(name, eventNum, team):
    age, gender = getAgeGender(eventNum)
    dict = {
        'Swimmer': name,
        'Gender': gender,
        'Age': age,
        'Team': team,
        'sf': -1,
        'ba': -1,
        'br': -1,
        'fl': -1,
        'lf': -1,
        'im': -1
    }
    return dict

def getEventType(eventNum):
    if 'P' in str(eventNum):
        eventNum = int(eventNum[:-1])
    eventNum = int(eventNum)
    eventTypes = ['im', '', 'sf', 'br', 'ba', 'fl', 'lf']
    num = int((eventNum -1) / 10)
    return eventTypes[num]

def fullDataTransform(fullData):
    dataBase = pd.DataFrame(columns = ['Swimmer', 'Gender', 'Age', 'Team', 'sf', 'ba', 'br', 'fl', 'lf', 'im'])
    for index, row in fullData.iterrows():
        name = row['Swimmer']
        if name not in dataBase['Swimmer'].values:
            dataBase = dataBase._append(addSwimmer(name, row['Event'], row['Team']), ignore_index = True)
        event = getEventType(row['Event'])
        dataBase.set_index('Swimmer', inplace = True)
        if dataBase.loc[name, event] == -1:
            dataBase.loc[name, event] = row['Time']
        elif dataBase.loc[name, event] >= row['Time']:
            dataBase.loc[name,event] = row['Time']
        dataBase.reset_index(drop = False, inplace = True)
    print('dataBase transformed')
    return dataBase

def getDatabase(folderName):
    return fullDataTransform(getFullData(folderName))

def updateDatabase():
    filepath = 'database.csv'
    if os.path.exists(filepath):
        os.remove(filepath)
    dataBase = getDatabase('All Results')
    dataBase.to_csv(filepath)

def getFullResults(url, outputFolder):
    if os.path.exists(outputFolder):
        for filename in os.listdir(outputFolder):
            filePath = os.path.join(outputFolder, filename)
            os.remove(filePath)
        os.rmdir(outputFolder)
    os.makedirs(outputFolder, exist_ok=True)

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    a_tags = soup.find_all('a')
    # a_tags = [f for f in a_tags if ".pdf" in f]
    brokenUrls = []
    for a_tag in a_tags:
        url = a_tag.get('href', None)
        if ".pdf" in url:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    filename = os.path.basename(url)
                    outputPath = os.path.join(outputFolder, filename)
                    with open(outputPath, 'wb') as f:
                        f.write(response.content)
                    print(f'Saved {filename} to {outputFolder}')
                else:
                    print(f'Failed to download {url} (status code: {response.status_code})')
            except Exception as e:
                brokenUrls.append(url)
                print(f'Error downloading {url}: {e}')
    for url in brokenUrls:
        saveSpecificUrl(url, outputFolder)
    print(f'All PDFs downloaded and saved to {outputFolder}')
    return brokenUrls

def saveSpecificUrl(url, outputFolder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.basename(url)
            outputPath = os.path.join(outputFolder, filename)
            with open(outputPath, 'wb') as f:
                f.write(response.content)
            print(f'Saved {filename} to {outputFolder}')
        else:
            print(f'Failed to download {url} (status code: {response.status_code})')
    except Exception as e:
        print('retry program, big oopsie')

def getChampsResults(champsFolder):
    champsData = pd.DataFrame(columns=['Team', 'Event', 'Swimmer', 'Time', 'Date'])
    for file in os.listdir(champsFolder):
        filePath = os.path.join(champsFolder, file)
        reader = PdfReader(filePath)
        tempLine = reader.pages[0].extract_text().splitlines()[1]
        year = tempLine[-4:]
        readType = 1
        for page in reader.pages:
            text = page.extract_text()



# getChampsResults("C:/Users/ucg8nb/Downloads/Champs Results")

# fullData = getFullData('All Results')
# fullData.to_csv("C:/Users/ucg8nb/Downloads/Full Swim Data.csv")
#getTopTimes('LMST')

# print(getFullResults('https://www.jsl.org/meet-results2020.php?section=results', '2025 Data'))
# #
# curData = getFullData('2025 Data')
# curData.to_csv("C:/Users/ucg8nb/Downloads/2025 Data.csv")
# #
# fullData = pd.read_csv("C:/Users/ucg8nb/Downloads/2025 Data.csv")
# getTopTimes('FV', fullData)
# trans2025 = fullDataTransform(fullData)
# trans2025.to_csv("C:/Users/ucg8nb/Downloads/2025 Data Transform.csv")



