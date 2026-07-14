import pandas as pd
import numpy as np
import swimmerRegression
import math
from collections import defaultdict

teams = ['ACAC', 'BHSC', 'CITY', 'CGST', 'CBST', 'FV', 'FCC','FAST', 'FSBC', 'GLEN', 'GHG', 'HM', 'KWC', 'FLST', 'LMST', 'LG']
ages = [6, 8, 10, 12, 14, 18]
gender = ['M', 'W']
strokes = ['sf', 'ba', 'br', 'fl', 'lf', 'im']

def getAgeRange(age):
    ranges = ['6 & Under', '8 & Under', '9-10', '11-12', '13-14', '15-18']
    for r in ranges:
        if str(age) in r:
            return r
    return ''

def getAgeGroups():
    return [[5,6,7,8], [9,10],[11,12],[13,14],[15,16,17,18]]

def getGenderTitle(gender):
    if gender == 'M':
        return 'Boys'
    return 'Girls'

def getIndexOfStroke(stroke):
    for i in range(len(strokes)):
        if stroke == strokes[i]:
            return i

def getTeams():
    return teams

def getAges():
    return ages

def getGenders():
    return gender

def getStrokes():
    return strokes

def getUnder8Strokes():
    return ['sf', 'ba', 'br', 'fl', 'lf']

def getAgeGenderTeam(df, ageRange, gender, team):
    df = df[df['Age'].isin(ageRange)]
    df = df[df['Gender'] == gender]
    df = df[df['Team'] == team]
    return df

def toSCM(team, time):
    if team in ['BHSC', 'KWC', 'LG', 'FSBC']:
        return time * 1.019
    if team in ['ACAC']:
        return time * 0.911
    else:
        return time
    
def combine_team_scores(team_score, agscores):
    combined = defaultdict(int)

    for d in (team_score, agscores):
        for team, score in d.items():
            combined[team] += score

    return combined
    
def checkNan(time):
    return time if isinstance(time, float) and not math.isnan(time) else -1

class Swimmer:

    def __init__(self, name, team, age, gender, times):
        self.name = name
        self.sf = checkNan(times[0])
        self.ba = checkNan(times[1])
        self.br = checkNan(times[2])
        self.fl = checkNan(times[3])
        self.lf = checkNan(times[4])
        self.im = checkNan(times[5])
        self.team = team
        self.age = age
        self.gender = gender
        self.times = [self.sf, self.ba, self.br, self.fl, self.lf, self.im]
        self.entered = [False, False, False, False, False, False]
        self.relays = [False, False]

    def getEntered(self):
        return self.entered, self.relays

    def isEntered(self, stroke):
        return self.entered[getIndexOfStroke(stroke)]

    def getTimes(self):
        return self.times

    def setTimes(self, times):
        self.times = times

    def getTime(self, stroke):
        return self.times[getIndexOfStroke(stroke)]

    def getCountEntered(self):
        return np.sum(self.entered) + np.sum(self.relays)

    def enterStroke(self, stroke):
        self.entered[getIndexOfStroke(stroke)] = True

    def enterStrokes(self, strokes):
        for s in strokes:
            self.enterStroke(s)

    def removeStroke(self, stroke):
        if stroke not in ['sf', 'ba', 'br', 'fl', 'lf', 'im']:
            return
        self.entered[getIndexOfStroke(stroke)] = False

    def getAge(self):
        return self.age

    def getGender(self):
        return self.gender

    def getName(self):
        return self.name

    def getTeam(self):
        return self.team

    def getSlowestEnteredIn(self):
        curSlow = -100
        curStroke = ''
        for i in range(len(self.entered)):
            if self.entered[i]:
                convertTime = swimmerRegression.standardizeTime(self.age, self.gender, strokes[i], self.times[i])
                if convertTime > curSlow:
                    curSlow = convertTime
                    curStroke = strokes[i]
        return curStroke

    def getDictEntries(self):
        enteredTimes = [-1, -1, -1, -1, -1, -1]
        for i in range(len(self.entered)):
            if self.entered[i]:
                enteredTimes[i] = self.times[i]
        return {
            'Name': self.name,
            'Age': self.age,
            'Gender': self.gender,
            'Team': self.team,
            'sf': enteredTimes[0],
            'ba': enteredTimes[1],
            'br': enteredTimes[2],
            'fl': enteredTimes[3],
            'lf': enteredTimes[4],
            'im': enteredTimes[5],
        }
    
    def __str__(self):
        return str(self.getDictEntries())


class AgeGroup:

    def __init__(self, team, ageRange, gender):
        self.team = team
        self.age = ageRange
        self.gender = gender
        self.swimmers = []

    def addSwimmer(self, swimmer):
        self.swimmers.append(swimmer)

    def getSwimmerIndex(self, name):
        for i in range(len(self.swimmers)):
            if self.swimmers[i].getName() == name:
                return i

    def enterSwimmer(self, name, stroke):
        index = self.getSwimmerIndex(name)
        self.swimmers[index].enterStroke(stroke)

    def removeSwimmer(self, name, stroke):
        index = self.getSwimmerIndex(name)
        self.swimmers[index].removeStroke(stroke)

    def checkEntries(self):
        for s in self.swimmers:
            if s.getCountEntered() > 3:
                return True
        return False

    def getSwimmerOver3(self):
        for s in self.swimmers:
            if s.getCountEntered() > 3:
                return s
        return None

    def convertToDf(self):
        output = pd.DataFrame()
        for s in self.swimmers:
            newRow = s.getDictEntries()
            output = output._append(newRow, ignore_index = True)
        return output



