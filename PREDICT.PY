import pandas as pd

# 1. Load the data sheet
sheet = pd.read_csv("E0.csv")

# 2. Define the two teams playing today
home_team = "Arsenal"
away_team = "Chelsea"

# --- PART A: CALCULATE HOME TEAM FORM ---
# Filter for Arsenal's home games and grab the last 3 rows
home_matches = sheet[sheet["HomeTeam"] == home_team].tail(3)
home_form_points = 0

for index, match in home_matches.iterrows():
    result = match["FTR"]
    if result == "H":  # Home win means Arsenal won!
        home_form_points = home_form_points + 3
    elif result == "D":
        home_form_points = home_form_points + 1

# --- PART B: CALCULATE AWAY TEAM FORM ---
# Filter for Chelsea's away games and grab the last 3 rows
away_matches = sheet[sheet["AwayTeam"] == away_team].tail(3)
away_form_points = 0

for index, match in away_matches.iterrows():
    result = match["FTR"]
    if result == "A":  # Away win means Chelsea won!
        away_form_points = away_form_points + 3
    elif result == "D":
        away_form_points = away_form_points + 1

# --- PART C: COMPARE AND PREDICT ---
print("--- MATCHDAY PREDICTION APP ---")
print(home_team, "Home Form Points:", home_form_points)
print(away_team, "Away Form Points:", away_form_points)
print("--------------------------------")

if home_form_points > away_form_points:
    print("PREDICTION:", home_team, "Straight Win!")
elif away_form_points > home_form_points:
    print("PREDICTION:", away_team, "Straight Win!")
else:
    print("PREDICTION: Draw or Too Close to Call!")
