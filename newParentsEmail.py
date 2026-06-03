import pandas as pd

# topiaParents = "C:/Users/ucg8nb/Downloads/cityswordfishteam_parent_information_260526201748.csv"
# registeredEmails = "C:/Users/ucg8nb/Downloads/2026 May 26 Swim Team registrations 2.csv"

# topiaEmailCol = 'email'
# registeredEmailCol = 'Email'

# topiaEmailSet = set(pd.read_csv(topiaParents)[topiaEmailCol].tolist())
# registeredEmailSet = set(pd.read_csv(registeredEmails)[registeredEmailCol].tolist())

# leftOverSet = registeredEmailSet - topiaEmailSet
# print(leftOverSet)
# print(len(leftOverSet))

registration = "C:/Users/ucg8nb/Downloads/2026_registration-details_53681_cityswordfishteam_260529151935.csv"
roster = "C:/Users/ucg8nb/Downloads/cityswordfishteam_athlete_roster_260529151952.csv"

registrationdf = pd.read_csv(registration)
rosterdf = pd.read_csv(roster)


registrationdf['Name List'] = registrationdf['Athlete Names (Age)'].str.replace(r'\s*\(\d+\)', '', regex=True).str.split(r'[\r\n]+')


exploded_df = registrationdf.explode('Name List')
exploded_df['Name List'] = exploded_df['Name List'].str.strip()
exploded_df['Name List'] = exploded_df['Name List'].str.lower()

rosterdf['Name'] = rosterdf['AthletePreferredName'].combine_first(rosterdf['AthleteFirstName']) + " " + rosterdf['AthleteLastName']
rosterdf['Name'] = rosterdf['Name'].str.strip()
rosterdf['Name'] = rosterdf['Name'].str.lower()

rosterNames = set(rosterdf['Name'])
registrationNames = set(exploded_df['Name List'])

print(rosterNames)
print(registrationNames)

print(len(rosterNames - registrationNames))

print(rosterNames - registrationNames)
