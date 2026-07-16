import pandas as pd
from pypdf import PdfReader
import os
import re

testPath = "C:/Users/ucg8nb/JSL All Champs Results/Test Folder"

def clean_name(name):
    """
    Convert 'Last, First M' -> 'First Last'
    """
    parts = name.split(',')
    if len(parts) == 2:
        last = parts[0].strip()
        first = parts[1].strip().split()[0]  # remove middle initial
        return f"{first} {last}"
    return name.strip()

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

def time_to_seconds(t):
    if isinstance(t, (int, float)):
        return float(t)
    
    if ":" in t:
        minutes, seconds = t.split(':')
        return float(minutes) * 60 + float(seconds)
    else:
        return float(t)

def extract_time(text):
    match = re.search(r'\d+:\d{2}\.\d{2}|\d{2}\.\d{2}', text)
    return match.group(0) if match else None

def parse_result_2025(text):
    output_df = pd.DataFrame(columns = ['Team', 'Event', 'Swimmer', 'Time', 'Year'])
    current_event = None

    for line in text.splitlines():
        line = line.strip()

        event_match = re.match(r"Event\s+(\d+)", line)
        if event_match:
            current_event = int(event_match.group(1))
            continue

        match = re.match(
            r"(.+?)-VA\s+\d+\s+\d*\s*([A-Za-z\-']+,\s*[A-Za-z\s\.']+)\s+(.+)",
            line
        )

        if match and current_event:
            team = toTeamAbbrv(match.group(1).strip())
            raw_name = match.group(2)
            remainder = match.group(3)

            swimmer = clean_name(raw_name)
            time = extract_time(remainder)
            time = time_to_seconds(time)
            time *= 1.0936

            if time:
                new_row = {
                    'Swimmer': swimmer,
                    'Event': current_event,
                    'Team': team,
                    'Time': time,
                }
                output_df = output_df._append(new_row, ignore_index = True)
    return output_df


def read_champs_pdfs(folderPath):
    fullData = pd.DataFrame(columns = ['Team', 'Event', 'Swimmer', 'Time', 'Year'])
    for fileName in os.listdir(folderPath):
        print(fileName)
        curYear = 0
        for year in [2023, 2024, 2025, 2022]:
            if str(year) in fileName:
                curYear = year
        filePath = os.path.join(folderPath, fileName)
        reader = PdfReader(filePath)
        if curYear == 2025:
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            results = parse_result_2025(text)
            results['Year'] = 2025
            fullData = pd.concat([fullData, results])
    return fullData

read_champs_pdfs(testPath).to_csv('C:/Users/ucg8nb/JSL All Champs Results/2025 Champs.csv')
