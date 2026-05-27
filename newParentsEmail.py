import pandas as pd

topiaParents = "C:/Users/ucg8nb/Downloads/cityswordfishteam_parent_information_260526201748.csv"
registeredEmails = "C:/Users/ucg8nb/Downloads/2026 May 26 Swim Team registrations 2.csv"

topiaEmailCol = 'email'
registeredEmailCol = 'Email'

topiaEmailSet = set(pd.read_csv(topiaParents)[topiaEmailCol].tolist())
registeredEmailSet = set(pd.read_csv(registeredEmails)[registeredEmailCol].tolist())

leftOverSet = registeredEmailSet - topiaEmailSet
print(leftOverSet)
print(len(leftOverSet))