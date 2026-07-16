import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
import swimmerRegression
import databaseBuilder as db
import individualScore as ind



# -------------------------------
# Load data
# -------------------------------

#Edit these things every meet
# participants = pd.read_csv("C:/Users/ucg8nb/Downloads/cityswordfishteam_meet_participants_260702103221.csv")
# times = pd.read_csv("C:/Users/ucg8nb/Downloads/best_times.csv")
# allData = pd.read_csv("C:/Users/ucg8nb/Downloads/Transformed 2026.csv")
# oppTeam = 'CGST'
# immeet = False

# timeAllData = deepcopy(allData)

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

def get_events(age_group, immeet, champs = False):
    if age_group in ["5-6", "7-8"]:
        if champs:
            return ["25 Freestyle", "25 Breaststroke","25 Backstroke", "25 Butterfly", '50 Freestyle']
        if not immeet:
            return ["25 Freestyle", "25 Breaststroke","25 Backstroke", "25 Butterfly", '50 Freestyle']
        else:
            return ["25 Freestyle", "25 Breaststroke","25 Backstroke", "25 Butterfly",]
    else:
        if champs:
            return ["50 Freestyle", "50 Breaststroke", "50 Backstroke", "50 Butterfly", "100 Freestyle", '100 Individual Medley']
        if not immeet:
            return ["50 Freestyle", "50 Breaststroke", "50 Backstroke", "50 Butterfly", "100 Freestyle"]
        else:
            return ["50 Freestyle", "50 Breaststroke", "50 Backstroke", "50 Butterfly", "100 Individual Medley"]

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

    # Convert to string for consistent handling
    val_str = str(val).strip().replace("S", "")

    # ✅ If already in mm:ss format → return cleaned
    if ":" in val_str:
        return val_str

    # ✅ Otherwise treat as numeric seconds
    try:
        val_float = round(float(val_str), 4)
    except ValueError:
        return ""

    minutes = int(val_float // 60)
    seconds = val_float % 60
    seconds = round(seconds, 4)

    if minutes != 0:
        if seconds < 10:
            return f"{minutes}:0{seconds:.2f}"
        return f"{minutes}:{seconds:.2f}"

    return f"{seconds:.2f}"

def format_time_with_rank(time_text, rank, styles):
    if pd.isna(time_text) or time_text == "":
        return ""

    if rank is None:
        return str(time_text)

    return Paragraph(
        f"{time_text} <font size='6'>({rank})</font>",
        styles["BodyText"]
    )

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

def normalizeNameKeys(participants, times, rosterdf):
    # Normalize name keys
    name_map = (rosterdf.dropna(subset = ['AthletePreferredName']).set_index(['AthleteFirstName', 'AthleteLastName'])['AthletePreferredName'])
    participants['athlete_first_name'] = (participants.apply(lambda r: name_map.get((r['athlete_first_name'], r['athlete_last_name']), r['athlete_first_name']) if pd.notna(r['athlete_first_name']) else r['athlete_first_name'], axis = 1))
    times['FirstName'] = (times.apply(lambda r: name_map.get((r['FirstName'], r['LastName']), r['FirstName']) if pd.notna(r['FirstName']) else r['FirstName'], axis = 1))
    participants["Name"] = participants["athlete_first_name"].fillna("") + " " + participants["athlete_last_name"]
    times["Name"] = times["FirstName"] + " " + times["LastName"]

    # Keep best (fastest) time per swimmer/event
    times = times.sort_values("ConvertedHundredths").drop_duplicates(["Name", "Event"])

    # Pivot times into columns
    times_pivot = times.pivot(index="Name", columns="Event", values="ConvertedTime")

    # -------------------------------
    # Prepare participants
    # -------------------------------
    participants["AgeGroup"] = participants["athlete_age_group"].apply(get_age_group_label)
    participants["Gender"] = participants["athlete_age_group"].apply(get_gender)

    participants = participants.dropna(subset=["AgeGroup", "Gender"])

    return participants, times_pivot

def cleanAllData(allData, participants):
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
    allData['Swimmer'] = allData['Swimmer'].str.strip().str.lower()
    return allData, cityData

# Map event names to the corresponding CITY time column
event_to_col = {
    "25 Freestyle": "sf",
    "50 Freestyle": "sf",
    "25 Backstroke": "ba",
    "50 Backstroke": "ba",
    "25 Breaststroke": "br",
    "50 Breaststroke": "br",
    "25 Butterfly": "fl",
    "50 Butterfly": "fl",
    "100 Freestyle": "lf",
    "100 Individual Medley": "im"
}

age_groups = ['5-6', '7-8', '9-10', '11-12', '13-14', '15-18']

def getCityRanks(cityData):

    # Store ranks by age/gender/event/swimmer
    city_ranks = {}

    for age in age_groups:
        age_range = age_group_to_range(age)

        for gender in ["W", "M"]:

            subset = cityData[
                (cityData["Gender"] == gender) &
                (cityData["Age"].isin(age_range))
            ]

            for event, col in event_to_col.items():

                valid = subset[subset[col] > 0].copy()

                if len(valid) == 0:
                    continue

                # Fastest time gets rank 1
                valid["Rank"] = valid[col].rank(method="min", ascending=True)

                for _, row in valid.iterrows():
                    city_ranks[(age, gender, event, row["Swimmer"])] = int(row["Rank"])
    return city_ranks

def getRelayString(results, age, gender):
    age = age_group_to_range(age)
    df = results[results['Age'].isin(age)].copy()
    df = df[df['Gender'] == gender]
    try:
        fr_swimmers = (df.loc[df['in_fr'] == 1, ['Swimmer', 'sf']].sort_values('sf', ascending = False))

        fr_text = "\n".join(f"{i}) {name}" for i, name in enumerate(fr_swimmers['Swimmer'], start = 1))

        fr = f"Free Relay: \n {fr_text}"
    except Exception:
        fr = ""

    try:
        ba = df.loc[df['mr_ba'] == 1, 'Swimmer'].iat[0]
        br = df.loc[df['mr_br'] == 1, 'Swimmer'].iat[0]
        fl = df.loc[df['mr_fl'] == 1, 'Swimmer'].iat[0]
        sf = df.loc[df['mr_fr'] == 1, 'Swimmer'].iat[0]
        mr = f"Medley Relay: \n Ba: {ba} \n Br: {br} \n Fly: {fl} \n Fr: {sf}"
    except Exception:
        mr = "SWIM UP!!"

    return fr, mr

def buildPdf(outputPath, participants, times_pivot, city_ranks, results, immeet, oppTeam, timeAllData, champs = False):
    # -------------------------------
    # Build PDF
    # -------------------------------
    doc = SimpleDocTemplate(outputPath, leftMargin = 0, rightMargin = 0)
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

            events = get_events(age, immeet, champs = champs)

            # Table header
            data = [["Name"] + events]

            cell_styles = []

            for row_idx, (_, swimmer_row) in enumerate(group.iterrows(), start = 1):
                name = swimmer_row["Name"]

                swimmer_flags = results[results['Swimmer'] == name.lower()]

                table_row = [name]

                for col_idx, event in enumerate(events, start = 1):
                    val = ""

                    if name in times_pivot.index and event in times_pivot.columns:
                        val = times_pivot.loc[name, event]

                        if pd.isna(val) or val == "":
                            val = ""

                    rank = city_ranks.get(
                        (age, gender, event, name.lower()),
                        None
                    )

                    table_row.append(format_time_with_rank(format_val(val), rank, styles))

                    flag_col = get_event_flag(event,age)

                    if (
                        flag_col
                        and not swimmer_flags.empty
                        and flag_col in swimmer_flags.columns
                        and swimmer_flags.iloc[0][flag_col] == 1
                    ):
                        cell_styles.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.lightgrey))
                    
                data.append(table_row)

            # Create table
            num_cols = len(data[0])

            name_col_width = page_width * 0.25

            other_width = max(50, (page_width - name_col_width) / (num_cols - 1))
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
            if not champs:
                oppTimes = ind.oppTimes(timeAllData, age_group_to_range(age), gender, oppTeam)
                oppTimes = oppTimes.apply(pd.to_numeric, errors = 'coerce')
                oppTimes = oppTimes.apply(lambda col: col.sort_values(ignore_index = True))
                print(oppTimes)
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
                        ("FONTSIZE", (0,0), (-1,-1), 12),
                    ]))

                    elements.append(times_row)
            if champs:
                free_relay, medley_relay = getRelayString(results, age, gender)

                left_para = Paragraph(free_relay.replace("\n", "<br/>"), styles["BodyText"])
                right_para = Paragraph(medley_relay.replace("\n", "<br/>"), styles["BodyText"])

                foot_table = Table([[left_para, right_para]], colWidths=[page_width/2, page_width/ 2])

                foot_table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]))
                elements.append(foot_table)

            elements.append(PageBreak())

    # Build PDF
    doc.build(elements)

    print("PDF created: meet_plan.pdf")