import pandas as pd

def addNameEmail(name,email, curYear):
    temp = pd.DataFrame(columns = ['Name', 'email'])
    for i in range(0, len(name)):
        curName = name[i]
        curEmail = email[i]
        nameExists = curName in curYear['Name'].values
        emailExists = curEmail in curYear['email'].values
        if not (nameExists or emailExists) and (curName != -1 and curEmail != -1):
            newPerson = {'Name' : curName, 'email': curEmail}
            temp = temp._append(newPerson, ignore_index = True)
    return temp

def in1ButNot2(one, two, emails):
    if emails:
        cleanOne = cleanEmails(one)
        cleanTwo = cleanEmails(two)
    else:
        cleanOne = one
        cleanTwo = two
    nums = []
    temp = []
    for i in range(0, len(one)):
        if cleanOne[i] not in cleanTwo:
            nums.append(i)
            temp.append(cleanOne[i])
    return temp, nums

def cleanEmails(email):
    temp = []
    for e in email:
        e = e.replace('.','')
        e = e.replace(',','')
        temp.append(e.lower())
    return temp

teamSnap = pd.read_csv("C:/Users/ucg8nb/Downloads/City Swordfish members export (2).csv", usecols = [0,1,9,12,14,16,18])

newYear = pd.read_csv("C:/Users/ucg8nb/Downloads/tmathemaillist.csv", usecols = [14,21,22,24,25], header = None)
newYear.columns = ['Swimmer', 'Parent 1', 'Email 1', 'Parent 2', 'Email 2']
newYear = newYear.fillna("")
email1List = newYear['Email 1'].tolist()
cleanedEmail1 = cleanEmails(email1List)
newYear['Cleaned Email 1'] = cleanedEmail1
email2List = newYear['Email 2'].tolist()
cleanedEmail2 = cleanEmails(email2List)
newYear['Cleaned Email 2'] = cleanedEmail2
teamSnap['First']= teamSnap['First'].fillna('')
teamSnap['Last']= teamSnap['Last'].fillna('')
teamSnap = teamSnap.fillna(-1)
teamSnap['Name'] = teamSnap['First'] + ' ' + teamSnap['Last']
teamSnap.drop(columns = ['First', 'Last'], inplace = True)
curYear = pd.DataFrame(columns = ['Name', 'email'])

curYear = curYear._append(addNameEmail(teamSnap['Name'].to_list(),teamSnap['Email'].to_list(), curYear), ignore_index = True)
curYear = curYear._append(addNameEmail(teamSnap['Contact 1 Name'].to_list(),teamSnap['Contact 1 Email'].to_list(), curYear), ignore_index = True)
curYear = curYear._append(addNameEmail(teamSnap['Contact 2 Name'].to_list(),teamSnap['Contact 2 Email'].to_list(), curYear), ignore_index = True)

newParents = newYear['Parent 1'].to_list() + newYear['Parent 2'].to_list()
newEmails = newYear['Email 1'].to_list() + newYear['Email 2'].to_list()

for i in reversed(range(0, len(newParents))):
    if(i >= len(newParents)):
        break
    if(newParents[i] == -1 or newEmails[i] == -1):
        del newParents[i]
        del newEmails[i]


oldParents = curYear['Name'].to_list()
oldEmails = curYear['email'].to_list()


newButNotOld, newNums = in1ButNot2(newEmails, oldEmails, True)
oldButNotNew, oldNums = in1ButNot2(oldEmails, newEmails, True)

needToAdd = pd.DataFrame(columns = ['Name', 'Email'])
for i in newNums:
    newPerson = {'Name': newParents[i], 'Email': newEmails[i]}
    needToAdd = needToAdd._append(newPerson, ignore_index = True)
needToAdd.to_csv('needToAdd.csv', index = False)

needToRemove = pd.DataFrame(columns = ['Name', 'Email'])
for i in oldNums:
    newPerson = {'Name': oldParents[i], 'Email': oldEmails[i]}
    needToRemove = needToRemove._append(newPerson, ignore_index = True)
needToRemove.to_csv('needToRemove.csv', index = False)
print(newButNotOld)
print(oldButNotNew)

uniqueNewButNotOld = list(set(newButNotOld))
print(uniqueNewButNotOld)

outputDf = pd.DataFrame()
for email in uniqueNewButNotOld:
    fullName = ""
    fullEmail = ""
    if email in newYear['Cleaned Email 1'].tolist():
        fullName = newYear.loc[newYear['Cleaned Email 1'] == email, 'Parent 1'].values[0]
        fullEmail = newYear.loc[newYear['Cleaned Email 1'] == email, 'Email 1'].values[0]
    if email in newYear['Cleaned Email 2'].tolist():
        fullName = newYear.loc[newYear['Cleaned Email 2'] == email, 'Parent 2'].values[0]
        fullEmail = newYear.loc[newYear['Cleaned Email 2'] == email, 'Email 2'].values[0]
    if fullName != "" and fullEmail != "":
        a = fullName.split()
        firstName = a[0]
        lastName = a[1]
        newRow = {'First Name': firstName, "Last Name": lastName, 'Email Address 1': fullEmail}
        outputDf = outputDf._append(newRow, ignore_index = True)
outputDf.to_csv("C:/Users/ucg8nb/Downloads/New Parents Add 06-30-25.csv")