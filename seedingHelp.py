import pandas as pd
import numpy as np
import swimmerRegression

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

def getAgeGenderTeam(df, ageRange, gender, team):
    df = df[df['Age'].isin(ageRange)]
    df = df[df['Gender'] == gender]
    df = df[df['Team'] == team]
    return df

class Swimmer:

    def __init__(self, name, team, age, gender, times):
        self.name = name
        self.sf = times[0]
        self.ba = times[1]
        self.br = times[2]
        self.fl = times[3]
        self.lf = times[4]
        self.im = times[5]
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



