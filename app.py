import requests
import streamlit as st
import pandas as pd

API_BASE = "https://v3.football.api-sports.io"

key = st.secrets["API_FOOTBALL_KEY"]

response = requests.get(
    f"{API_BASE}/fixtures",
    headers={"x-apisports-key": key},
    params={"live": "all", "timezone": "America/Jamaica"},
    timeout=20,
)

if response.ok:
    payload = response.json()

    if payload.get("errors"):
        st.error(str(payload["errors"]))
    else:
        fixtures = payload.get("response", [])

        if fixtures:
            rows = []
            for match in fixtures:
                teams = match["teams"]
                goals = match["goals"]
                status = match["fixture"]["status"]

                rows.append({
                    "Home Team": teams["home"]["name"],
                    "Home Score": goals["home"],
                    "Away Score": goals["away"],
                    "Away Team": teams["away"]["name"],
                    "Minute": status["elapsed"],
                    "Status": status["short"],
                })

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "No live fixtures are available right now. "
                "Try again during a match."
            )
else:
    st.error(f"API request failed: {response.status_code}")

# Mapping dataset division short-codes to clean display names
competition_map = {
    "E0": "English Premier League (Tier 1)",
    "SP1": "Spanish La Liga (Primera División)",
    "D1": "German Bundesliga (1. Bundesliga)",
    "I1": "Italian Serie A",
    "F1": "French Ligue 1",
    "N1": "Netherlands Eredivisie"
}

# --- SYSTEMATIC DATA LOADING ---
sheet = None
try:
    sheet = pd.read_csv(file_path, on_bad_lines='skip')
    st.success(f"Connected to Local {league_choice} Database!")
except Exception as e:
    st.error(f"CRITICAL ERROR: Could not find '{file_path}' inside your folder. Please ensure it is placed there.")

# --- EXTRACT TEAM ROSTERS ---
available_teams = []
if sheet is not None:
    sheet.columns = [str(col).strip() for col in sheet.columns]
    if "HomeTeam" in sheet.columns:
        available_teams = sorted([str(t).strip() for t in sheet["HomeTeam"].dropna().unique() if str(t).strip() != ""])

if not available_teams:
    available_teams = ["File Empty or Unreadable"]

# --- ADVANCED GLOBAL COMPUTATION ENGINE ---
def calculate_comprehensive_stats(team_name, lookback_games=5):
    all_matches = sheet[(sheet["HomeTeam"] == team_name) | (sheet["AwayTeam"] == team_name)]
    recent_matches = all_matches.tail(lookback_games)
    
    points, goals_scored, goals_conceded, clean_sheets = 0, 0, 0, 0
    corners, yellow_cards, red_cards, halftime_leads = 0, 0, 0, 0
    btts_count, over_25_count = 0, 0
    
    games_played = len(recent_matches)
    if games_played == 0:
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1

    for index, match in recent_matches.iterrows():
        try:
            h_g = int(match["FTHG"])
            a_g = int(match["FTAG"])
            res = match["FTR"]
            ht_res = match["HTR"]
            
            if h_g > 0 and a_g > 0: btts_count += 1
            if (h_g + a_g) > 2.5: over_25_count += 1
            
            if match["HomeTeam"] == team_name:
                goals_scored += h_g
                goals_conceded += a_g
                corners += int(match["HC"])
                yellow_cards += int(match["HY"])
                red_cards += int(match["HR"])
                if a_g == 0: clean_sheets += 1
                if res == "H": points += 3
                elif res == "D": points += 1
                if ht_res == "H": halftime_leads += 1
            else:
                goals_scored += a_g
                goals_conceded += h_g
                corners += int(match["AC"])
                yellow_cards += int(match["AY"])
                red_cards += int(match["AR"])
                if h_g == 0: clean_sheets += 1
                if res == "A": points += 3
                elif res == "D": points += 1
                if ht_res == "A": halftime_leads += 1
        except:
            continue
            
    return points, goals_scored, goals_conceded, clean_sheets, corners, yellow_cards, red_cards, halftime_leads, btts_count, over_25_count, games_played

# --- FETCH RECENT ODDS AND SCHEDULING DETAILS ---
def get_fixture_metadata(h_team, a_team):
    """
    Looks into historical match matrices to pull down the most realistic 
    odds, times, dates, and competition metrics for the chosen pair.
    """
    # Look for the last head-to-head match between these specific teams
    h2h = sheet[(sheet["HomeTeam"] == h_team) & (sheet["AwayTeam"] == a_team)]
    
    # Fallback default configuration values if they haven't faced each other in this sheet yet
    match_date = "Scheduled Matchday"
    match_time = "15:00 GMT"
    comp_code = sheet["Div"].iloc[0] if "Div" in sheet.columns else "E0"
    odd_h, odd_d, odd_a = 2.10, 3.40, 3.20
    
    if not h2h.empty:
        last_match = h2h.iloc[-1]
        if "Date" in sheet.columns: match_date = str(last_match["Date"])
        if "Time" in sheet.columns: match_time = str(last_match["Time"])
        if "Div" in sheet.columns: comp_code = str(last_match["Div"])
        if "B365H" in sheet.columns: odd_h = float(last_match["B365H"])
        if "B365D" in sheet.columns: odd_d = float(last_match["B365D"])
        if "B365A" in sheet.columns: odd_a = float(last_match["B365A"])
        
    comp_name = competition_map.get(comp_code, "Top Flight Football Division")
    return match_date, match_time, comp_name, odd_h, odd_d, odd_a

# --- USER SELECTION INTERFACE ---
st.subheader("Matchday Lineup Selector")
col1, col2 = st.columns(2)
with col1:
    home_selection = st.selectbox("Home Team Selection", available_teams, key="h_sl")
with col2:
    away_selection = st.selectbox("Away Team Selection", available_teams, key="a_sl")

# --- MODEL TRIGGER ---
if st.button("Run Multi-Market Predictive Analytics", type="primary"):
    if home_selection == "File Empty or Unreadable":
        st.error("Engine execution locked: Local dataset files missing.")
    elif home_selection == away_selection:
        st.warning("Prediction models require two separate opponent selections.")
    else:
        # Fetch metadata arrays
        m_date, m_time, m_comp, o_h, o_d, o_a = get_fixture_metadata(home_selection, away_selection)
        
        # Calculate calculation layers
        h_pts, h_gs, h_gc, h_cs, h_cr, h_yc, h_rc, h_ht, h_btts, h_ovr, h_gp = calculate_comprehensive_stats(home_selection)
        a_pts, a_gs, a_gc, a_cs, a_cr, a_yc, a_rc, a_ht, a_btts, a_ovr, a_gp = calculate_comprehensive_stats(away_selection)
        
        # --- TOP HEADER SUMMARY: FIXTURE INFO & ODDS ---
        st.write("---")
        info_col1, info_col2 = st.columns([2, 1])
        
        with info_col1:
            st.markdown(f"## 🏟️ {home_selection} vs {away_selection}")
            st.markdown(f"**Competition:** {m_comp} | **📅 Date:** {m_date} | **⏰ Kickoff:** {m_time}")
            
        with info_col2:
            st.markdown("### 🎲 Bet365 Closing Odds")
            odds_c1, odds_c2, odds_c3 = st.columns(3)
            odds_c1.metric(f"{home_selection} Win (1)", f"{o_h:.2f}")
            odds_c2.metric("Draw (X)", f"{o_d:.2f}")
            odds_c3.metric(f"{away_selection} Win (2)", f"{o_a:.2f}")
            
        st.write("---")
        st.subheader("📋 Comprehensive Analytical Dashboard Breakdown")
        
        # --- THE MAIN ADVANCED TABS MATRIX ---
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🏆 Straight Wins & Form", "⚽ Goals Profile", "🎯 BTTS Market", 
            "📐 Corners Stats", "⏱️ Halftime Metrics", "🟨 Bookings & Discipline", "👤 Player Analytics Hub"
        ])
        
        # TAB 1: STRAIGHT WINS
        with tab1:
            st.markdown("### 🏆 Form Standing & Straight Win Analysis")
            c1, c2 = st.columns(2)
            with c1: st.metric(f"{home_selection} Form Points (Last 5)", h_pts)
            with c2: st.metric(f"{away_selection} Form Points (Last 5)", a_pts)
            st.write("---")
            if h_pts > a_pts:
                st.success(f"**Algorithmic Winner Outlook:** {home_selection} straight win favored due to point velocity superiority.")
            elif a_pts > h_pts:
                st.success(f"**Algorithmic Winner Outlook:** {away_selection} straight win favored due to point velocity superiority.")
            else:
                st.info("**Algorithmic Winner Outlook:** High probability of a hard-fought Draw outcome.")
                
        # TAB 2: GOALS
        with tab2:
            st.markdown("### ⚽ Offensive & Defensive Goal Profiles")
            c1, c2 = st.columns(2)
            with c1:
                st.metric(f"{home_selection} Goals Scored", h_gs)
                st.metric(f"{home_selection} Goals Conceded", h_gc)
            with c2:
                st.metric(f"{away_selection} Goals Scored", a_gs)
                st.metric(f"{away_selection} Goals Conceded", a_gc)
                
        # TAB 3: BTTS & OVER/UNDER
        with tab3:
            st.markdown("### 🎯 Alternative Betting Markets Probability")
            combined_btts = ((h_btts / h_gp) + (a_btts / a_gp)) * 50
            combined_over = ((h_ovr / h_gp) + (a_ovr / a_gp)) * 50
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Both Teams to Score Trend Rate", f"{combined_btts:.1f}%")
                if combined_btts >= 60.0: st.success("Market Tip: **YES (Both Teams to Score)**")
                else: st.error("Market Tip: **NO (Low Scoring Tendencies)**")
            with c2:
                st.metric("Over 2.5 Match Goals Probability", f"{combined_over:.1f}%")
                if combined_over >= 60.0: st.success("Market Tip: **OVER 2.5 Match Goals**")
                else: st.error("Market Tip: **UNDER 2.5 Match Goals**")
                
        # TAB 4: CORNERS
        with tab4:
            st.markdown("### 📐 Set Piece Corner Averages")
            c1, c2 = st.columns(2)
            with c1: st.metric(f"{home_selection} Avg Corners", f"{(h_cr/h_gp):.1f}")
            with c2: st.metric(f"{away_selection} Avg Corners", f"{(a_cr/a_gp):.1f}")
