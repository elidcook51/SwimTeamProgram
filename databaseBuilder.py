from pypdf import PdfReader
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import cloudscraper
import pytesseract
from pdf2image import convert_from_path
import re
import shutil
from sklearn.cluster import DBSCAN

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

HEADERS = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'),'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8','Accept-Language': 'en-US,en;q=0.9','Accept-Encoding': 'gzip, deflate, br','Cache-Control': 'no-cache','Pragma': 'no-cache','DNT': '1','Upgrade-Insecure-Requests': '1'}

relayNums = ['1P', 1, 2]
for i in range(11,21):
    relayNums.append(i)
for i in range(71,81):
    relayNums.append(i)

eventNums = ['21P', '22P', '41P', '42P']
for j in range(1, 11):
    for i in [0, 10, 20, 30, 40, 50, 60, 70]:
        eventNums.append(i + j)

swimTopiaEventMap = {
    e: 'sf'   for e in range(22, 34)
} | {
    e: 'br' for e in range(34, 44)
} | {
    e: 'ba'   for e in range(44, 56)
} | {
    e: 'fl'    for e in range(56, 66)
} | {
    e: 'lf'    for e in range(66, 76)
} | {
    e: 'im'           for e in range(4, 12)
}

def toSCM(team, time):
    if team in ['BHSC', 'KWC', 'LG']:
        return time * 1.111
    if team in ['ACAC', 'FSBC']:
        return time * 0.971
    else:
        return time

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
    return (firstName + ' ' + lastName).lstrip()

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
        if fileName.endswith('.csv'):
            continue
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

def addSwimmer(name, eventNum, team, date, curYear):
    timeDiff = curYear - date.year
    age, gender = getAgeGender(eventNum)
    dict = {
        'Swimmer': name,
        'Gender': gender,
        'Age': age + timeDiff,
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
    if eventNum > 100:
        eventNum = eventNum / 10
    eventTypes = ['im', '', 'sf', 'br', 'ba', 'fl', 'lf']
    num = int((eventNum -1) / 10)
    return eventTypes[num]

def check25Event(eventNum):
    if "P" in str(eventNum):
        return True
    eventNum = int(eventNum)
    if eventNum > 99:
        return True
    if (eventNum - 1) % 10 < 2:
        return True
    return False

def fullDataTransform(fullData):
    fullData['Date'] = pd.to_datetime(fullData['Date'], format = 'mixed', errors = 'coerce')
    fullData = fullData.dropna(subset = ['Swimmer', 'Team'])
    # curYear = fullData['Date'].dt.year.max()
    curYear = 2026
    dataBase = pd.DataFrame(columns = ['Swimmer', 'Gender', 'Age', 'Team', 'sf', 'ba', 'br', 'fl', 'lf', 'im'])
    for index, row in fullData.iterrows():
        if row['Time'] == -1:
            continue
        if row['Event'] in ['81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '100']:
            continue
        name = row['Swimmer']
        if pd.isna(row['Swimmer']) or 'nan' in name or name.strip() == '' or 'Event' in name or 'AgeName' in name:
            continue
        if not ((dataBase['Swimmer'] == name) & (dataBase['Team'] == row['Team'])).any():
            dataBase = dataBase._append(addSwimmer(name, row['Event'], row['Team'], row['Date'], curYear), ignore_index = True)
        event = getEventType(row['Event'])
        if check25Event(row['Event']) and dataBase.loc[(dataBase['Swimmer'] == name) & (dataBase['Team'] == row['Team']), 'Age'].iloc[0] > 8:
            if not isinstance(row['Event'], (int, float)):
                if "P" not in row['Event']:
                    if int(int(row['Event']) / 10) == 6:
                        event = 'sf'
                    else:
                        continue
                else:
                    continue
        if dataBase.loc[(dataBase['Swimmer'] == name) & (dataBase['Team'] == row['Team']), event].iloc[0] == -1:
            dataBase.loc[(dataBase['Swimmer'] == name) & (dataBase['Team'] == row['Team']), event] = row['Time']
        elif dataBase.loc[(dataBase['Swimmer'] == name) & (dataBase['Team'] == row['Team']), event].iloc[0] >= row['Time']:
            dataBase.loc[(dataBase['Swimmer'] == name) & (dataBase['Team'] == row['Team']),event] = row['Time']
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

def pullSwimTopiaResults(url, outputFolder):
    if os.path.isdir(outputFolder):
        shutil.rmtree(outputFolder)

    scraper = cloudscraper.create_scraper()

    html = scraper.get(url).text
    
    os.makedirs(outputFolder, exist_ok = True)
    soup = BeautifulSoup(html, 'html.parser')


    for link in soup.find_all('a', href = True):
        href = link['href']

        print(href)

        if "s3_files" in href:
            file_url = urljoin(url, href)

            name = link.get_text(strip = True)
            invalid_chars = r'<>:"/\|?*'
            for ch in invalid_chars:
                name = name.replace(ch, "")

            filename = os.path.join(outputFolder, f"{name}.pdf")

            print(f"Downloading: {file_url}")

            
            response = scraper.get(file_url, headers=HEADERS, stream=True)

            # DEBUG: check what you're actually getting
            print(response.headers.get("Content-Type"))

            if "application/pdf" not in response.headers.get("Content-Type", ""):
                print("Not a PDF! Skipping:", file_url)
                continue

            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)


    print('Done!')

def parseSwimTopiaText(text):
    # Extract date
    date_match = re.search(r'([A-Za-z]{3,9})\s+(\d{1,2}),?\s*(\d{4})', text)
    meet_date = date_match.group(1) if date_match else None

    # Clean weird header corruption
    text = re.sub(r'#\s+(\d+)', r'#\1', text)

    # Split into events FIRST (preserve structure)
    event_splits = re.split(r'(#\d+)', text)

    rows = []

    for i in range(1, len(event_splits), 2):
        event_num = int(event_splits[i][1:])
        chunk = event_splits[i + 1]

        if "Relay" in chunk:
            continue

        # Flatten ONLY inside this event
        chunk = chunk.replace('\n', ' ')
        chunk = re.sub(r'\s+', ' ', chunk)

        # Remove EXH / DQ / NS
        chunk = re.sub(r'\b(EXH|DQ|NS|SCR)\b', '', chunk)
        chunk = re.sub(r'[=~•*©§\|\\]+', '', chunk)

        # --- MAIN PATTERN ---
        pattern = re.compile(
            r'(?:^|\s)'
            r'(?:\d+\s*[\.\)]?\s*)?'  # optional placing
            
            # --- NAME ---
            r'([A-Za-z\'\-]+),\s*([A-Za-z\.]+(?:\s+[A-Za-z\.]+)*)\s+'

            # Optional stray numbers (place column leaks)
            r'(?:\d+\s+)?'

            # --- AGE ---
            r'(\d{1,2})\s+'

            # --- TEAM ---
            r'([A-Z]{2,5})\s+'

            # Optional NT / seed time(s)
            r'(?:NT\s+)?'
            r'(?:[\d:]+\.\d+\s+)*'

            # --- FINAL TIME ---
            r'((?:\d{1,2}:)?\d{1,2}\.\d{2})'

            # Optional trailing junk (points, etc.)25    
            r'(?:\s+\d+)?'
        )

        for m in pattern.finditer(chunk):
            last, first, age, team, time_str = m.groups()

            last = re.sub(r'^[^A-Za-z]+', '', last).strip()
            first = re.sub(r'^[^A-Za-z]+', '', first).strip()

            last = last.lower()
            first = first.lower()

            # Convert time
            if ':' in time_str:
                mins, secs = time_str.split(':')
                time = int(mins) * 60 + float(secs)
            else:
                time = float(time_str)

            rows.append({
                "Team": team,
                "Event": event_num,
                "Swimmer": f"{first.strip()} {last.strip()}",
                "Time": time,
                "Age": int(age),
                "Date": meet_date
            })

    df = pd.DataFrame(rows)

    # Final cleanup
    df = df[df["Swimmer"].str.len() > 4]

    return df

def group_lines(df):
    y_positions = df['top'].values.reshape(-1,1)

    clustering = DBSCAN(eps = 8, min_samples = 1).fit(y_positions)

    df['line_id'] = clustering.labels_
    grouped = df.groupby('line_id')

    lines = []
    for _, group in grouped:
        line = " ".join(group.sort_values('left')['text'])
        lines.append((group['top'].mean(), line))
    
    return pd.DataFrame(lines, columns = ['top', 'line'])

def readSwimTopiaResults(folderPath):
    fullData = pd.DataFrame(columns=['Team', 'Event', 'Swimmer', 'Time', "Age", 'Date'])
    for fileName in os.listdir(folderPath):
        print("Processing:", fileName)

        home = fileName.split('@')[-1].strip()
        home = home.replace(".pdf", "")

        filePath = os.path.join(folderPath, fileName)

        # Convert PDF to images
        pages = convert_from_path(filePath)

        full_text = []

        for page in pages:
            data = pytesseract.image_to_data(page, config = '--psm 6', output_type = pytesseract.Output.DATAFRAME)

            data = data.dropna(subset = ['text'])
            data = data[data['text'].str.strip() != ""]

            page_width = page.width  # or image width2split_x = page_width * 0.5  # tweak this (0.45–0.6 usually)
            split_x = page_width * 0.5

            left_col = data[data['left'] < split_x].sort_values(by = ['top', 'left'])
            right_col = data[data['left'] >= split_x].sort_values(by = ['top','left'])

            left_lines = group_lines(left_col).sort_values('top')
            right_lines = group_lines(right_col).sort_values('top')

            page_text = " ".join(left_lines['line']) + " " + " ".join(right_lines['line'])
            full_text.append(page_text)
        
        text = "\n".join(full_text)
        with open("C:/Users/ucg8nb/Downloads/meet_results.txt", 'a') as f:
            f.write(text)

        meetDf = parseSwimTopiaText(text)
        meetDf['Time'] = meetDf['Time'].apply(lambda t: toSCM(home, t))

        fullData = pd.concat([fullData, meetDf], ignore_index = True)

    return fullData

def gender_from_swimtopia_event(num):
    if num % 2 == 0:
        return "M"
    else:
        return "W"

def transformSwimTopiaResults(df):
    df = df.copy()

    df['stroke'] = df['Event'].map(swimTopiaEventMap)
    df['Gender'] = df['Event'].map(gender_from_swimtopia_event)

    df = df.dropna(subset = ['stroke'])

    fastest = (df.groupby(['Swimmer', 'stroke'], as_index = False)['Time'].min())

    wide = fastest.pivot(index = 'Swimmer', columns = 'stroke', values = 'Time')

    expected_cols = [
        'sf',
        'ba',
        'br',
        'fl',
        'lf',
        'im'
    ]

    for col in expected_cols:
        if col not in wide.columns:
            wide[col] = pd.NA

    meta = (
        df.sort_values('Time').groupby('Swimmer').first()[['Age', 'Team', 'Gender']].reset_index()
    )

    result = meta.merge(wide, on = 'Swimmer', how = 'left')

    return result

# swimtopiaResults = 'https://jsl.swimtopia.com/full-results'
# swimTopiaResultsFolder = "C:/Users/ucg8nb/Downloads/2026 Results"
# pullSwimTopiaResults(swimtopiaResults, swimTopiaResultsFolder)

# df = readSwimTopiaResults(swimTopiaResultsFolder)
# df.to_csv("C:/Users/ucg8nb/Downloads/Untransformed 2026.csv")

# df = pd.read_csv("C:/Users/ucg8nb/Downloads/Untransformed 2026.csv")
# transformeddf = transformSwimTopiaResults(df)
# transformeddf.to_csv("C:/Users/ucg8nb/Downloads/Transformed 2026.csv")

# jslPath = "C:/Users/ucg8nb/JSL All Results 2021-2025"
# fullData = getFullData(jslPath)
# fullData.to_csv(f"{jslPath}/Untransformed Data.csv")
# fullData = pd.read_csv(f"{jslPath}/Untransformed Data.csv")
# second_full_data = pd.read_csv('C:/Users/ucg8nb/JSL All Champs Results/2025 Champs.csv')
# fullData = pd.concat([fullData, second_full_data])
# transData = fullDataTransform(fullData)
# transData.to_csv(f"{jslPath}/Transformed Data.csv")


