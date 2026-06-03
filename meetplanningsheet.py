import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER



# -------------------------------
# Load data
# -------------------------------
participants = pd.read_csv("C:/Users/ucg8nb/Downloads/cityswordfishteam_meet_participants_260603130423.csv")
times = pd.read_csv("C:/Users/ucg8nb/Downloads/best_times.csv")

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
        return "Girls"
    if "Boys" in label or "Men" in label:
        return "Boys"
    return None

def get_events(age_group):
    if age_group in ["5-6", "7-8"]:
        return ["25 Freestyle", "25 Backstroke", "25 Breaststroke", "25 Butterfly", "50 Freestyle"]
    else:
        return ["50 Freestyle", "50 Backstroke", "50 Breaststroke", "50 Butterfly", "100 Freestyle", "100 Individual Medley"]

# -------------------------------
# Prepare participants
# -------------------------------
participants["AgeGroup"] = participants["athlete_age_group"].apply(get_age_group_label)
participants["Gender"] = participants["athlete_age_group"].apply(get_gender)

participants = participants.dropna(subset=["AgeGroup", "Gender"])

# -------------------------------
# Build PDF
# -------------------------------
doc = SimpleDocTemplate("C:/Users/ucg8nb/Downloads/meet_plan.pdf")
styles = getSampleStyleSheet()
styles["Heading2"].alignment = TA_CENTER
elements = []

age_groups = ["5-6", "7-8", "9-10", "11-12", "13-14", "15-18"]

for age in age_groups:
    for gender in ["Girls", "Boys"]:
        group = participants[(participants["AgeGroup"] == age) & (participants["Gender"] == gender)]

        if group.empty:
            continue

        events = get_events(age)

        # Table header
        data = [["Name"] + events]

        for _, row in group.iterrows():
            name = row["Name"]

            row_data = [name]

            for event in events:
                val = ""
                if name in times_pivot.index and event in times_pivot.columns:
                    val = times_pivot.loc[name].get(event, "")
                    if pd.isna(val):
                        val = ""
                row_data.append(val)

            data.append(row_data)

        # Create table
        table = Table(data)

        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
        ]))

        title_text = f"{gender} {age}"
        elements.append(Paragraph(title_text, styles['Heading2']))
        elements.append(table)
        elements.append(PageBreak())

# Build PDF
doc.build(elements)

print("PDF created: meet_plan.pdf")