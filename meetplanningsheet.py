import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
import swimmerRegression
import runner
import databaseBuilder as db
import individualScore as ind
from copy import deepcopy



# -------------------------------
# Load data
# -------------------------------
participants = pd.read_csv("C:/Users/ucg8nb/Downloads/cityswordfishteam_meet_participants_260604093334.csv")
times = pd.read_csv("C:/Users/ucg8nb/Downloads/best_times.csv")
allData = pd.read_csv("C:/Users/ucg8nb/JSL All Results 2021-2025/Transformed Data.csv")
timeAllData = deepcopy(allData)

# Normalize name keys
participants["Name"] = participants["athlete_first_name"].fillna("") + " " + participants["athlete_last_name"]
times["Name"] = times["FirstName"] + " " + times["LastName"]

# Keep best (fastest) time per swimmer/event
times = times.sort_values("ConvertedHundredths").drop_duplicates(["Name", "Event"])

# Pivot times into columns
times_pivot = times.pivot(index="Name", columns="Event", values="ConvertedTime")



# -------------------------------
# Helpers
# -------------------------------
def get_age_group_label(label):
    # Extract "7-8" etc
    for grp in ["6 & Under", "7-8", "9-10", "11-12", "13-14", "15-18"]:
        if grp in label:
            return grp.replace("6 & Under", "5-6")
    return None

def get_gender(label):
    if "Girls" in label or "Women" in label:
        return "W"
    if "Boys" in label or "Men" in label:
        return "M"
    return None

def get_events(age_group):
    if age_group in ["5-6", "7-8"]:
        return ["25 Freestyle", "25 Backstroke", "25 Breaststroke", "25 Butterfly", "50 Freestyle"]
    else:
        return ["50 Freestyle", "50 Backstroke", "50 Breaststroke", "50 Butterfly", "100 Freestyle", "100 Individual Medley"]


def get_event_flag(event, age):
    # 8 & under (25s + 50 free)
    if age in ["5-6", "7-8"]:
        mapping = {
            "25 Freestyle": "in_sf",
            "50 Freestyle": "in_lf",
            "25 Backstroke": "in_ba",
            "25 Breaststroke": "in_br",
            "25 Butterfly": "in_fl",
        }
    else:
        # 9 & up (50s + 100s)
        mapping = {
            "50 Freestyle": "in_sf",
            "100 Freestyle": "in_lf",
            "50 Backstroke": "in_ba",
            "50 Breaststroke": "in_br",
            "50 Butterfly": "in_fl",
            "100 Individual Medley": "in_im"
        }

    return mapping.get(event)

def get_event_flag_time(event, age):
    # 8 & under (25s + 50 free)
    if age in ["5-6", "7-8"]:
        mapping = {
            "25 Freestyle": "sf",
            "50 Freestyle": "lf",
            "25 Backstroke": "ba",
            "25 Breaststroke": "br",
            "25 Butterfly": "fl",
        }
    else:
        # 9 & up (50s + 100s)
        mapping = {
            "50 Freestyle": "sf",
            "100 Freestyle": "lf",
            "50 Backstroke": "ba",
            "50 Breaststroke": "br",
            "50 Butterfly": "fl",
            "100 Individual Medley": "im"
        }

    return mapping.get(event)

def format_val(val):
    if pd.isna(val) or val == "":
        return ""
    
    val = round(float(val), 4)

    minutes = int(val // 60)
    seconds = val % 60

    seconds = round(seconds,4)

    if minutes != 0:
        if seconds < 10:
            return f"{minutes}:0{seconds:.2f}"
        return f"{minutes}:{seconds:.2f}"

    return f"{seconds:.2f}"

def age_group_to_range(ageGroup):
    if ageGroup == '5-6':
        return [5,6]
    if ageGroup == '7-8':
        return [7,8]
    if ageGroup == '9-10':
        return [9,10]
    if ageGroup == '11-12':
        return [11,12]
    if ageGroup == '13-14':
        return [13,14]
    if ageGroup == '15-18':
        return [15,16,17,18]


#Clean allData
cityData = allData[allData['Team'] == 'CITY']
allData = allData[allData['Team'] != 'CITY']
allData = allData.dropna()
participants['lowerName'] = participants['Name'].str.strip().str.lower()
cityData['lowerName'] = cityData['Swimmer'].str.strip().str.lower()

cityData = participants[['lowerName', 'Name', 'athlete_age', 'athlete_age_group']].merge(cityData[['lowerName', 'sf', 'ba', 'br', 'fl', 'lf', 'im']], on = 'lowerName', how = 'left').fillna(-1)
cityData['Gender'] = cityData['athlete_age_group'].apply(get_gender)
cityData['Team'] = "CITY"
cityData = cityData.rename(columns = {'athlete_age': 'Age', 'Name': "Swimmer"})
cityData = cityData.drop(columns = ['lowerName', 'athlete_age_group'])
allData = pd.concat([allData, cityData])
allData = swimmerRegression.standardizeAllData(allData)
results = runner.seedDuelMeet(allData, 'CITY', 'LMST', 2026)

# -------------------------------
# Prepare participants
# -------------------------------
participants["AgeGroup"] = participants["athlete_age_group"].apply(get_age_group_label)
participants["Gender"] = participants["athlete_age_group"].apply(get_gender)

participants = participants.dropna(subset=["AgeGroup", "Gender"])

# -------------------------------
# Build PDF
# -------------------------------
doc = SimpleDocTemplate("C:/Users/ucg8nb/Downloads/meet_plan.pdf", leftMargin = 0, rightMargin = 0)
styles = getSampleStyleSheet()
styles["Heading2"].alignment = TA_CENTER
elements = []

age_groups = ["5-6", "7-8", "9-10", "11-12", "13-14", "15-18"]

page_width = doc.width

for age in age_groups:
    for gender in ["W", "M"]:
        group = participants[(participants["AgeGroup"] == age) & (participants["Gender"] == gender)]

        if group.empty:
            continue

        events = get_events(age)

        # Table header
        data = [["Name"] + events]

        cell_styles = []

        for row_idx, (_, swimmer_row) in enumerate(group.iterrows(), start = 1):
            name = swimmer_row["Name"]

            row_name = f"{name} ({swimmer_row['athlete_age']})"

            row_data = [row_name]

            swimmer_flags = results[results['Swimmer'] == name]

            for col_idx, event in enumerate(events, start = 1):
                val = ""

                cur_row = timeAllData[timeAllData["Swimmer"].str.strip().str.lower() == name.strip().lower()]
                cur_row = cur_row[cur_row['Team'] == 'CITY']

                flag_col = get_event_flag_time(event, age)

                val = ""

                if (
                    not cur_row.empty
                    and flag_col in cur_row.columns
                ):
                    val = cur_row.iloc[0][flag_col]

                    # Clean missing values
                    if pd.isna(val) or val <= 0:
                        val = ""

                row_data.append(format_val(val))

                flag_col = get_event_flag(event,age)

                if (
                    flag_col
                    and not swimmer_flags.empty
                    and flag_col in swimmer_flags.columns
                    and swimmer_flags.iloc[0][flag_col] == 1
                ):
                    cell_styles.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.lightgrey))
                
            data.append(row_data)

        # Create table
        num_cols = len(data[0])

        name_col_width = page_width * 0.25

        other_width = (page_width - name_col_width) / (num_cols - 1)
        col_widths = [name_col_width] + [other_width] * (num_cols - 1)

        table = Table(data, colWidths=col_widths)
        table.hAlign = 'LEFT'

        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
        ] + cell_styles))

        title_text = f"{'Boys' if gender == 'M' else "Girls"} {age}"
        elements.append(Paragraph(title_text, styles['Heading2']))
        elements.append(table)

        oppTimes = ind.oppTimes(timeAllData, age_group_to_range(age), gender, 'LMST')
        for index, row in oppTimes.iterrows():

            if age == '5-6' or age == '7-8':
                extra_times = ["", format_val(row['sf']), format_val(row['ba']), format_val(row['br']), format_val(row['fl']), format_val(row['lf'])]
            else:
                extra_times = ["", format_val(row['sf']), format_val(row['ba']), format_val(row['br']), format_val(row['fl']), format_val(row['lf']), format_val(row['im'])]

            times_row = Table([extra_times], colWidths=col_widths)
            times_row.hAlign = 'LEFT'

            times_row.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]))

            elements.append(times_row)

        elements.append(PageBreak())

# Build PDF
doc.build(elements)

print("PDF created: meet_plan.pdf")