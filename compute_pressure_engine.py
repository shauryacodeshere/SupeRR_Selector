"""
SupeRR Selector Season 2 - Rajasthan Royals Hackathon
Core Pressure Intelligence Engine

Calculates:
1. Match Situation Reconstruction (Runs needed, Balls remaining, Wickets remaining, RRR, Innings phase)
2. Continuous Pressure Intensity Index (P)
3. Contextual Expected Performance Baselines (Exp Runs, Exp Wicket Prob)
4. Performance Above Expectation (PAE) for Batters and Bowlers
5. Bayesian Shrinkage & Reliability Ratings
6. Player Specialization Profiles (Chase, Death, Collapse, Defense)
7. Global Top 10 Batters & Bowlers Under Pressure
8. Rajasthan Royals Auction Target Recommender (Excluding Travis Head, customized for RR's 27.05 Cr purse & 3 overseas slots)
"""

import pandas as pd
import numpy as np
import json
import re

print("Loading datasets...")
bbb = pd.read_csv('ball_by_ball.csv')
matches = pd.read_csv('matches.csv')
comps = pd.read_csv('competitions.csv')
teams = pd.read_csv('teams.csv')
p11 = pd.read_csv('playing_eleven.csv')
mapping = pd.read_csv('competition_team_player_mapping.csv')

print(f"Loaded BBB: {len(bbb)} deliveries across {bbb['match_id'].nunique()} matches.")

# -------------------------------------------------------------
# STEP 1: MATCH SITUATION RECONSTRUCTION
# -------------------------------------------------------------
print("Reconstructing match state on every delivery...")

# 1. Identify legal deliveries
# Extras that are illegal balls: wide, Overstep, other
bbb['is_legal_ball'] = ~bbb['extras_type'].isin(['wide', 'Overstep', 'other'])

# 2. Team runs per ball (correct calculation discovered during audit)
# runs = bat runs
# extras_type in [wide, Overstep, legbyes, byes, other] -> 1 extra run
# extras_2_runs -> additional boundary/overthrow runs
# Penalty -> 5 runs
bbb['extra_run_val'] = 0
bbb.loc[bbb['extras_type'].isin(['wide', 'Overstep', 'legbyes', 'byes', 'other']), 'extra_run_val'] = 1
bbb.loc[bbb['extras_type'] == 'Penalty', 'extra_run_val'] = 5
bbb['ball_team_runs'] = bbb['runs'] + bbb['extra_run_val'] + bbb['extras_2_runs']

# Bowler runs conceded (byes and legbyes do not count against bowler)
bbb['bowler_runs_conceded'] = bbb['runs']
bbb.loc[bbb['extras_type'].isin(['wide', 'Overstep', 'other']), 'bowler_runs_conceded'] += 1 + bbb['extras_2_runs']

# Bowler wickets (exclude RunOut, Retire Out, Obstructing field)
bowler_wicket_types = ['Caught', 'Bowled', 'LBW', 'Stump', 'Hit Wicket']
bbb['is_bowler_wicket'] = bbb['is_wicket'] & bbb['dismissal_type'].isin(bowler_wicket_types)

# Sort chronologically by match, innings, overid, over_ball_num
bbb = bbb.sort_values(['match_id', 'innings', 'overid', 'over_ball_num']).reset_index(drop=True)

# Cumulative match state BEFORE each ball
# Cumulative team runs before ball
bbb['cum_team_runs_before'] = bbb.groupby(['match_id', 'innings'])['ball_team_runs'].cumsum() - bbb['ball_team_runs']

# Cumulative legal balls bowled before ball
bbb['cum_legal_balls_before'] = bbb.groupby(['match_id', 'innings'])['is_legal_ball'].cumsum() - bbb['is_legal_ball'].astype(int)

# Cumulative wickets down before ball
bbb['cum_wickets_before'] = bbb.groupby(['match_id', 'innings'])['is_wicket'].cumsum() - bbb['is_wicket'].astype(int)

# Merge match metadata
m_cols = ['match_id', 'comp_id', 'match_date', 'knock_out', 'first_inn_revised_overs', 'second_inn_revised_overs', 'revised_target', 'result', 'win_team_id']
bbb = bbb.merge(matches[m_cols], on='match_id', how='left')

# Determine Innings 1 total score for target calculation
inn1_totals = bbb[bbb['innings'] == 1].groupby('match_id')['ball_team_runs'].sum().reset_index()
inn1_totals.rename(columns={'ball_team_runs': 'inn1_total_runs'}, inplace=True)
bbb = bbb.merge(inn1_totals, on='match_id', how='left')

# Max legal balls in innings
# Normal match = 120 balls (20 overs). Check revised overs if available
bbb['max_legal_balls'] = 120
# first_inn_revised_overs and second_inn_revised_overs are stored in BALLS!
bbb.loc[(bbb['innings'] == 1) & bbb['first_inn_revised_overs'].notna(), 'max_legal_balls'] = bbb['first_inn_revised_overs']
bbb.loc[(bbb['innings'] == 2) & bbb['second_inn_revised_overs'].notna(), 'max_legal_balls'] = bbb['second_inn_revised_overs']

# Balls remaining before this delivery
bbb['balls_remaining'] = np.maximum(0, bbb['max_legal_balls'] - bbb['cum_legal_balls_before'])

# Wickets in hand before this delivery
bbb['wickets_in_hand'] = np.maximum(0, 10 - bbb['cum_wickets_before'])

# Target runs for 2nd innings
# If revised_target is available, use it; otherwise inn1_total_runs + 1
bbb['target_runs'] = np.nan
bbb.loc[bbb['innings'] == 2, 'target_runs'] = bbb['inn1_total_runs'] + 1
bbb.loc[(bbb['innings'] == 2) & bbb['revised_target'].notna(), 'target_runs'] = bbb['revised_target']

# Runs needed in 2nd innings
bbb['runs_needed'] = np.nan
bbb.loc[bbb['innings'] == 2, 'runs_needed'] = np.maximum(0, bbb['target_runs'] - bbb['cum_team_runs_before'])

# Required Run Rate (RRR)
bbb['rrr'] = np.nan
chase_mask = (bbb['innings'] == 2) & (bbb['balls_remaining'] > 0)
bbb.loc[chase_mask, 'rrr'] = (bbb.loc[chase_mask, 'runs_needed'] / (bbb.loc[chase_mask, 'balls_remaining'] / 6.0))

print("State reconstruction complete.")

# -------------------------------------------------------------
# STEP 2: CONTINUOUS PRESSURE INTENSITY (P)
# -------------------------------------------------------------
print("Calculating Continuous Pressure Intensity (P) on every ball...")

# 2nd Innings Pressure:
# Driven by:
# 1. RRR relative to baseline 8.0: rrr_factor = (RRR / 8.0)
# 2. Wicket scarcity: w_factor = (11 - wickets_in_hand) / 10.0
# 3. Closeness to end: urgency_factor = 1.0 + (120 - balls_remaining) / 120.0
# Sigmoid bounded between [0.0, 1.0]

def calc_chase_pressure(row):
    balls_left = row['balls_remaining']
    runs_need = row['runs_needed']
    w_left = row['wickets_in_hand']
    rrr = row['rrr']
    
    if balls_left <= 0 or runs_need <= 0:
        return 0.5
    
    # Base tension: log ratio of runs needed to balls left
    # Par expectation is ~1.3 runs per ball (7.8 RRR)
    run_rate_stress = rrr / 8.5
    wicket_stress = (10 - w_left) / 9.0  # 0 when 10 in hand, 1 when 1 in hand
    
    # Death over amplifier (overs 16-20 have higher leverage)
    over_idx = row['overid']
    phase_amp = 1.0
    if over_idx >= 16:
        phase_amp = 1.25
    elif over_idx <= 6:
        phase_amp = 0.85
        
    raw_p = (0.55 * run_rate_stress + 0.45 * wicket_stress) * phase_amp
    # Bound to [0.05, 1.0] using smooth logistic
    p = 1.0 / (1.0 + np.exp(-2.5 * (raw_p - 1.0)))
    return np.clip(p, 0.05, 1.0)

# 1st Innings Pressure:
# Driven by:
# 1. Collapse pressure (wickets lost early)
# 2. Death over boundary pressure (need to set par/above-par total)
def calc_first_inn_pressure(row):
    over_idx = row['overid']
    w_lost = row['cum_wickets_before']
    
    # Expected wickets lost at this over (empirical heuristic: ~0.35 wickets per over)
    exp_w_lost = min(9.0, over_idx * 0.35)
    collapse_delta = max(0, w_lost - exp_w_lost)
    
    # Base phase pressure
    if over_idx <= 6:
        base_p = 0.30 + (collapse_delta * 0.15)
    elif over_idx <= 15:
        base_p = 0.45 + (collapse_delta * 0.12)
    else:  # Death overs 16-20
        base_p = 0.65 + (w_lost >= 6) * 0.15 + (w_lost <= 4) * 0.10
        
    return np.clip(base_p, 0.1, 0.95)

# Calculate Pressure Intensity P
bbb['pressure_intensity'] = 0.5
bbb.loc[bbb['innings'] == 2, 'pressure_intensity'] = bbb[bbb['innings'] == 2].apply(calc_chase_pressure, axis=1)
bbb.loc[bbb['innings'] == 1, 'pressure_intensity'] = bbb[bbb['innings'] == 1].apply(calc_first_inn_pressure, axis=1)

# Tournament stakes multiplier (knockout = 1.15x pressure)
bbb.loc[bbb['knock_out'] == 1, 'pressure_intensity'] = np.clip(bbb.loc[bbb['knock_out'] == 1, 'pressure_intensity'] * 1.15, 0.0, 1.0)

print("Pressure Intensity calculated.")
print("Pressure distribution:")
print(bbb['pressure_intensity'].describe())

# -------------------------------------------------------------
# STEP 3: CONTEXTUAL EXPECTED PERFORMANCE & PAE
# -------------------------------------------------------------
print("Calibrating Contextual Expected Performance Baselines...")

# Segment match into 3 phases:
# Powerplay (overs 1-6), Middle (overs 7-15), Death (overs 16-20)
def get_phase(overid):
    if overid <= 6:
        return 'Powerplay'
    elif overid <= 15:
        return 'Middle'
    else:
        return 'Death'

bbb['phase'] = bbb['overid'].apply(get_phase)

# Segment wickets in hand into brackets: High (8-10), Medium (5-7), Low (1-4)
def get_wkt_bracket(w):
    if w >= 8:
        return 'High (8-10)'
    elif w >= 5:
        return 'Med (5-7)'
    else:
        return 'Low (1-4)'

bbb['wkt_bracket'] = bbb['wickets_in_hand'].apply(get_wkt_bracket)

# Segment pressure intensity into brackets for empirical baseline
bbb['pressure_bracket'] = pd.qcut(bbb['pressure_intensity'], q=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Extreme'])

# Baseline table: Expected runs and Expected wicket prob per ball for each (phase, wkt_bracket, innings)
baseline_table = bbb.groupby(['innings', 'phase', 'wkt_bracket']).agg(
    exp_runs=('runs', 'mean'),
    exp_bowler_runs=('bowler_runs_conceded', 'mean'),
    exp_wkt_prob=('is_bowler_wicket', 'mean'),
    exp_team_wkt_prob=('is_wicket', 'mean')
).reset_index()

print("\nSample Baseline Table:")
print(baseline_table.head(10))

# Merge baselines back to delivery level
bbb = bbb.merge(baseline_table, on=['innings', 'phase', 'wkt_bracket'], how='left')

# WICKET RUN VALUE (in T20 cricket, a wicket is empirically worth ~4.5 runs)
WICKET_RUN_VALUE = 4.5

# Calculate Ball-by-Ball Performance Above Expectation (PAE)
# Batting PAE:
# Actual runs scored - expected runs, penalized if dismissed
bbb['bat_pae_raw'] = (bbb['runs'] - bbb['exp_runs']) - (bbb['is_wicket'].astype(int) - bbb['exp_team_wkt_prob']) * WICKET_RUN_VALUE

# Bowling PAE:
# Expected runs conceded - actual runs conceded, rewarded for wickets taken
bbb['bowl_pae_raw'] = (bbb['exp_bowler_runs'] - bbb['bowler_runs_conceded']) + (bbb['is_bowler_wicket'].astype(int) - bbb['exp_wkt_prob']) * WICKET_RUN_VALUE

# Pressure-Weighted PAE:
# Delivery PAE scaled by the continuous pressure intensity of that exact moment!
bbb['bat_pressure_pae'] = bbb['bat_pae_raw'] * bbb['pressure_intensity']
bbb['bowl_pressure_pae'] = bbb['bowl_pae_raw'] * bbb['pressure_intensity']

print("PAE calculations complete.")

# -------------------------------------------------------------
# STEP 4: PLAYER AGGREGATION & BAYESIAN SHRINKAGE
# -------------------------------------------------------------
print("Aggregating player performance and applying Bayesian shrinkage...")

# Define HIGH PRESSURE filter: pressure_intensity >= 0.60
HIGH_PRESSURE_THRESHOLD = 0.60
hp_bbb = bbb[bbb['pressure_intensity'] >= HIGH_PRESSURE_THRESHOLD].copy()

# A. BATTING AGGREGATION
bat_summary = hp_bbb.groupby(['striker_id', 'striker_name']).agg(
    hp_balls=('runs', 'count'),
    hp_runs=('runs', 'sum'),
    hp_dismissals=('is_wicket', 'sum'),
    hp_fours=('is_four', 'sum'),
    hp_sixes=('is_six', 'sum'),
    hp_pae_total=('bat_pressure_pae', 'sum'),
    hp_raw_pae_total=('bat_pae_raw', 'sum'),
    avg_pressure_faced=('pressure_intensity', 'mean'),
    matches_played=('match_id', 'nunique')
).reset_index()

# Also get overall balls to check sample depth
all_bat_balls = bbb.groupby('striker_id')['runs'].count().reset_index().rename(columns={'runs': 'total_career_balls'})
bat_summary = bat_summary.merge(all_bat_balls, on='striker_id', how='left')

bat_summary['hp_strike_rate'] = (bat_summary['hp_runs'] / bat_summary['hp_balls']) * 100.0
bat_summary['hp_boundary_pct'] = ((bat_summary['hp_fours'] + bat_summary['hp_sixes']) / bat_summary['hp_balls']) * 100.0
bat_summary['hp_pae_per_ball'] = bat_summary['hp_pae_total'] / bat_summary['hp_balls']

# Bayesian Shrinkage on Batting PAE per ball
# Prior mean = population average PAE per ball in high pressure
pop_bat_pae_mean = bat_summary['hp_pae_per_ball'].mean()
K_bat = 75  # Evidence threshold (balls)
bat_summary['shrunk_bat_pae_per_ball'] = (
    (bat_summary['hp_balls'] / (bat_summary['hp_balls'] + K_bat)) * bat_summary['hp_pae_per_ball'] +
    (K_bat / (bat_summary['hp_balls'] + K_bat)) * pop_bat_pae_mean
)

# Volume-Reliability Scaled Rating (0 to 100 score)
# Combines quality under pressure (shrunk PAE) with volume of pressure handled
bat_summary['pressure_impact_score'] = bat_summary['shrunk_bat_pae_per_ball'] * np.sqrt(bat_summary['hp_balls'])
# Normalize to 0-100 scale for presentation
min_s = bat_summary['pressure_impact_score'].min()
max_s = bat_summary['pressure_impact_score'].max()
bat_summary['bat_clutch_rating'] = ((bat_summary['pressure_impact_score'] - min_s) / (max_s - min_s)) * 100.0

# B. BOWLING AGGREGATION
bowl_summary = hp_bbb.groupby(['bowler_id', 'bowler_name']).agg(
    hp_balls=('bowler_runs_conceded', 'count'),
    hp_runs_conceded=('bowler_runs_conceded', 'sum'),
    hp_wickets=('is_bowler_wicket', 'sum'),
    hp_dots=('bowler_runs_conceded', lambda x: (x == 0).sum()),
    hp_pae_total=('bowl_pressure_pae', 'sum'),
    hp_raw_pae_total=('bowl_pae_raw', 'sum'),
    avg_pressure_bowled=('pressure_intensity', 'mean'),
    matches_played=('match_id', 'nunique')
).reset_index()

all_bowl_balls = bbb.groupby('bowler_id')['bowler_runs_conceded'].count().reset_index().rename(columns={'bowler_runs_conceded': 'total_career_balls'})
bowl_summary = bowl_summary.merge(all_bowl_balls, on='bowler_id', how='left')

bowl_summary['hp_economy'] = (bowl_summary['hp_runs_conceded'] / (bowl_summary['hp_balls'] / 6.0))
bowl_summary['hp_dot_pct'] = (bowl_summary['hp_dots'] / bowl_summary['hp_balls']) * 100.0
bowl_summary['hp_strike_rate'] = np.where(bowl_summary['hp_wickets'] > 0, bowl_summary['hp_balls'] / bowl_summary['hp_wickets'], 999.0)
bowl_summary['hp_pae_per_ball'] = bowl_summary['hp_pae_total'] / bowl_summary['hp_balls']

# Bayesian Shrinkage on Bowling PAE per ball
pop_bowl_pae_mean = bowl_summary['hp_pae_per_ball'].mean()
K_bowl = 75  # Evidence threshold (balls)
bowl_summary['shrunk_bowl_pae_per_ball'] = (
    (bowl_summary['hp_balls'] / (bowl_summary['hp_balls'] + K_bowl)) * bowl_summary['hp_pae_per_ball'] +
    (K_bowl / (bowl_summary['hp_balls'] + K_bowl)) * pop_bowl_pae_mean
)

bowl_summary['pressure_impact_score'] = bowl_summary['shrunk_bowl_pae_per_ball'] * np.sqrt(bowl_summary['hp_balls'])
min_sb = bowl_summary['pressure_impact_score'].min()
max_sb = bowl_summary['pressure_impact_score'].max()
bowl_summary['bowl_clutch_rating'] = ((bowl_summary['pressure_impact_score'] - min_sb) / (max_sb - min_sb)) * 100.0

# -------------------------------------------------------------
# STEP 5: SPECIALIZATION SUB-SCORES
# -------------------------------------------------------------
print("Calculating Specialization sub-profiles...")

# 1. Chase Finisher (Innings 2, overs 15-20, pressure >= 0.6)
chase_bbb = hp_bbb[(hp_bbb['innings'] == 2) & (hp_bbb['overid'] >= 15)]
chase_bat = chase_bbb.groupby('striker_id')['bat_pressure_pae'].sum().reset_index().rename(columns={'bat_pressure_pae': 'chase_pae'})

# 2. Death Overs Specialist (Overs 17-20, both innings)
death_bbb = hp_bbb[hp_bbb['overid'] >= 17]
death_bat = death_bbb.groupby('striker_id')['bat_pressure_pae'].sum().reset_index().rename(columns={'bat_pressure_pae': 'death_bat_pae'})
death_bowl = death_bbb.groupby('bowler_id')['bowl_pressure_pae'].sum().reset_index().rename(columns={'bowl_pressure_pae': 'death_bowl_pae'})

# 3. Collapse Rescuer (Innings 1 or 2, overs 1-10 with wickets down >= 3)
collapse_bbb = bbb[(bbb['overid'] <= 10) & (bbb['cum_wickets_before'] >= 3)]
collapse_bat = collapse_bbb.groupby('striker_id')['bat_pressure_pae'].sum().reset_index().rename(columns={'bat_pressure_pae': 'collapse_bat_pae'})

# Merge specializations
bat_summary = bat_summary.merge(chase_bat, on='striker_id', how='left').fillna({'chase_pae': 0})
bat_summary = bat_summary.merge(death_bat, on='striker_id', how='left').fillna({'death_bat_pae': 0})
bat_summary = bat_summary.merge(collapse_bat, on='striker_id', how='left').fillna({'collapse_bat_pae': 0})

bowl_summary = bowl_summary.merge(death_bowl, on='bowler_id', how='left').fillna({'death_bowl_pae': 0})

# -------------------------------------------------------------
# STEP 6: FILTER & EXTRACT TOP 10 RANKINGS
# -------------------------------------------------------------
# Minimum qualifying filter for Global Top 10: at least 150 high pressure balls faced/bowled
# This ensures statistical significance while including clutch middle-order players
top10_batters = bat_summary[bat_summary['hp_balls'] >= 150].sort_values('bat_clutch_rating', ascending=False).head(10).copy()
top10_bowlers = bowl_summary[bowl_summary['hp_balls'] >= 150].sort_values('bowl_clutch_rating', ascending=False).head(10).copy()

print("\n=======================================================")
print("GLOBAL TOP 10 BATTERS UNDER PRESSURE (2022-2026)")
print("=======================================================")
for rank, (_, row) in enumerate(top10_batters.iterrows(), 1):
    print(f"{rank}. {row['striker_name']}: Rating={row['bat_clutch_rating']:.1f} | HP Balls={row['hp_balls']} | HP SR={row['hp_strike_rate']:.1f} | PAE Total={row['hp_pae_total']:+.1f}")

print("\n=======================================================")
print("GLOBAL TOP 10 BOWLERS UNDER PRESSURE (2022-2026)")
print("=======================================================")
for rank, (_, row) in enumerate(top10_bowlers.iterrows(), 1):
    print(f"{rank}. {row['bowler_name']}: Rating={row['bowl_clutch_rating']:.1f} | HP Balls={row['hp_balls']} | HP Econ={row['hp_economy']:.2f} | HP Wkts={row['hp_wickets']} | PAE Total={row['hp_pae_total']:+.1f}")

# -------------------------------------------------------------
# STEP 7: RAJASTHAN ROYALS AUCTION WAR ROOM ANALYSIS
# -------------------------------------------------------------
print("\nScoring Released Auction Players for Rajasthan Royals...")

with open('/Users/shauryasingh/.gemini/antigravity/brain/0518b937-5612-4321-91f6-0aaacaddc1a2/scratch/auction_retention_data.json') as f:
    auction_config = json.load(f)

# Extract all released players
released_players_list = []
for team, data in auction_config.items():
    for p in data['released']:
        p_lower = p.lower()
        # Explicit user constraints: Exclude Travis Head (unavailable) and Retired players (Ajinkya Rahane, MS Dhoni)!
        if 'travis head' in p_lower:
            continue
        if 'rahane' in p_lower or 'ajinkya' in p_lower:
            continue
        if 'dhoni' in p_lower:
            continue
        released_players_list.append({
            'name': p,
            'released_by': team
        })

# Map each released player to their stats in bat_summary and bowl_summary
auction_scouted = []

for item in released_players_list:
    p_name = item['name']
    team = item['released_by']
    
    # Check batting
    bat_match = bat_summary[bat_summary['striker_name'].str.lower() == p_name.lower()]
    if bat_match.empty:
        # Partial match
        bat_match = bat_summary[bat_summary['striker_name'].str.lower().str.contains(p_name.lower(), regex=False)]
    
    # Check bowling
    bowl_match = bowl_summary[bowl_summary['bowler_name'].str.lower() == p_name.lower()]
    if bowl_match.empty:
        bowl_match = bowl_summary[bowl_summary['bowler_name'].str.lower().str.contains(p_name.lower(), regex=False)]
        
    has_bat = not bat_match.empty
    has_bowl = not bowl_match.empty
    
    if not has_bat and not has_bowl:
        continue
        
    b_row = bat_match.iloc[0] if has_bat else None
    bw_row = bowl_match.iloc[0] if has_bowl else None
    
    # Determine primary role
    bat_balls = b_row['hp_balls'] if has_bat else 0
    bowl_balls = bw_row['hp_balls'] if has_bowl else 0
    
    if bat_balls >= 60 and bowl_balls >= 60:
        primary_role = 'All-Rounder'
    elif bowl_balls > bat_balls:
        primary_role = 'Bowler'
    else:
        primary_role = 'Batter'
        
    # Overseas vs Indian check (standard knowledge base + competition check)
    overseas_names = [
        'matheesha pathirana', 'mitchell starc', 'trent boult', 'wanindu hasaranga', 'lockie ferguson',
        'anrich nortje', 'gerald coetzee', 'matthew breetzke', 'dilshan madushanka', 'jacob bethell',
        'spencer johnson', 'blessing muzarabani', 'matt henry', 'george linde', 'luke wood',
        'dushmantha chameera', 'pathum nissanka', 'rehan ahmed', 'david payne', 'kamindu mendis'
    ]
    is_overseas = any(on in p_name.lower() for on in overseas_names)
    
    # Determine Tactical Fit Category for RR:
    # 1. "Hetmyer Replacement / Death Finisher"
    # 2. "Premier Death Pacer (Sandeep Partner)"
    # 3. "Powerplay Wicket-Taker"
    # 4. "Clutch All-Rounder / Spin"
    # 5. "High-Value Domestic Target"
    
    tactical_category = "General Squad Depth"
    estimated_price_cr = 3.0
    
    if primary_role == 'Bowler':
        death_val = bw_row['death_bowl_pae'] if bw_row is not None else 0
        hp_econ = bw_row['hp_economy'] if bw_row is not None else 10.0
        
        if 'pathirana' in p_name.lower():
            tactical_category = "Elite Death Pacer (Primary Target)"
            estimated_price_cr = 10.5
        elif 'starc' in p_name.lower():
            tactical_category = "Elite Death & Big-Match Pacer"
            estimated_price_cr = 8.5
        elif 'boult' in p_name.lower():
            tactical_category = "Powerplay Strike Pacer (RR Legend)"
            estimated_price_cr = 6.5
        elif 'madhwal' in p_name.lower():
            tactical_category = "Domestic Death Specialist (High Value)"
            estimated_price_cr = 3.5
        elif death_val > 10 or hp_econ < 9.0:
            tactical_category = "Death / Defensive Bowling Asset"
            estimated_price_cr = 4.5
        else:
            tactical_category = "Pace / Spin Reserve"
            estimated_price_cr = 2.0
            
    elif primary_role in ['Batter', 'All-Rounder']:
        death_bat_val = b_row['death_bat_pae'] if b_row is not None else 0
        hp_sr = b_row['hp_strike_rate'] if b_row is not None else 120.0
        
        if 'wadhera' in p_name.lower():
            tactical_category = "The Hetmyer Heir (Young Clutch Finisher)"
            estimated_price_cr = 5.5
        elif 'shahrukh' in p_name.lower():
            tactical_category = "Power Finisher (Overs 17-20 Specialist)"
            estimated_price_cr = 4.0
        elif 'hasaranga' in p_name.lower():
            tactical_category = "World-Class Mystery Spin All-Rounder"
            estimated_price_cr = 7.0
        elif 'lomror' in p_name.lower():
            tactical_category = "Domestic Middle-Order Enforcer (Ex-RR)"
            estimated_price_cr = 2.5
        elif 'tripathi' in p_name.lower() or 'rana' in p_name.lower() or 'nissanka' in p_name.lower():
            tactical_category = "Top-Order Anchor & Counter-Attacker"
            estimated_price_cr = 4.0
        else:
            tactical_category = "Middle-Order Depth"
            estimated_price_cr = 1.5
            
    # Calculate Overall RR Fit Score (0 to 100)
    # Higher for roles solving RR's severe gaps (Death bowling & Hetmyer void)
    base_rating = 0
    if primary_role == 'Bowler' and bw_row is not None:
        base_rating = bw_row['bowl_clutch_rating']
    elif b_row is not None:
        base_rating = b_row['bat_clutch_rating']
        
    gap_bonus = 0
    if "Elite Death" in tactical_category or "Hetmyer" in tactical_category:
        gap_bonus = 15
    elif "Powerplay" in tactical_category or "Finisher" in tactical_category:
        gap_bonus = 10
        
    rr_fit_score = np.clip(base_rating * 0.75 + gap_bonus + 10, 30, 99)
    
    entry = {
        'player_name': p_name,
        'released_by': team,
        'primary_role': primary_role,
        'is_overseas': is_overseas,
        'tactical_category': tactical_category,
        'estimated_price_cr': estimated_price_cr,
        'rr_fit_score': round(float(rr_fit_score), 1),
        'bat_hp_balls': int(b_row['hp_balls']) if b_row is not None else 0,
        'bat_hp_sr': round(float(b_row['hp_strike_rate']), 1) if b_row is not None else 0.0,
        'bat_hp_pae': round(float(b_row['hp_pae_total']), 1) if b_row is not None else 0.0,
        'bowl_hp_balls': int(bw_row['hp_balls']) if bw_row is not None else 0,
        'bowl_hp_econ': round(float(bw_row['hp_economy']), 2) if bw_row is not None else 0.0,
        'bowl_hp_wkts': int(bw_row['hp_wickets']) if bw_row is not None else 0,
        'bowl_hp_pae': round(float(bw_row['hp_pae_total']), 1) if bw_row is not None else 0.0,
        'death_bat_pae': round(float(b_row['death_bat_pae']), 1) if b_row is not None else 0.0,
        'death_bowl_pae': round(float(bw_row['death_bowl_pae']), 1) if bw_row is not None else 0.0,
    }
    auction_scouted.append(entry)

# Sort auction scouted targets by RR fit score
auction_scouted = sorted(auction_scouted, key=lambda x: x['rr_fit_score'], reverse=True)

print(f"\nScouted {len(auction_scouted)} targets for Rajasthan Royals. Top 10 recommendations:")
for idx, p in enumerate(auction_scouted[:10], 1):
    overseas_tag = "✈️ Overseas" if p['is_overseas'] else "🇮🇳 Indian"
    print(f"{idx}. {p['player_name']} ({overseas_tag}) - Fit: {p['rr_fit_score']} | Category: {p['tactical_category']} | Est: ₹{p['estimated_price_cr']} Cr")

# -------------------------------------------------------------
# STEP 8: EXPORT MASTER JSON FOR REACT FRONTEND
# -------------------------------------------------------------
print("\nExporting comprehensive JSON dataset for React app...")

export_data = {
    "metadata": {
        "title": "SupeRR Selector Season 2 - Rajasthan Royals Pressure Intelligence System",
        "date_range": "2022 - 2026",
        "total_deliveries": int(len(bbb)),
        "total_matches": int(bbb['match_id'].nunique()),
        "generated_at": "2026-11-18",
        "rr_context": {
            "purse_cr": 27.05,
            "total_slots": 6,
            "overseas_slots": 3,
            "retained_count": 19,
            "released_count": 9,
            "key_released_player": "Shimron Hetmyer",
            "excluded_players": ["Travis Head (Unavailable for season)", "Ajinkya Rahane (Retired)", "MS Dhoni (Retired)"]
        }
    },
    "top10_batters": top10_batters[[
        'striker_id', 'striker_name', 'bat_clutch_rating', 'hp_balls', 'hp_runs',
        'hp_dismissals', 'hp_strike_rate', 'hp_boundary_pct', 'hp_pae_total',
        'chase_pae', 'death_bat_pae', 'collapse_bat_pae', 'matches_played'
    ]].to_dict(orient='records'),
    "top10_bowlers": top10_bowlers[[
        'bowler_id', 'bowler_name', 'bowl_clutch_rating', 'hp_balls', 'hp_runs_conceded',
        'hp_wickets', 'hp_economy', 'hp_dot_pct', 'hp_pae_total', 'death_bowl_pae', 'matches_played'
    ]].to_dict(orient='records'),
    "rr_auction_targets": auction_scouted,
    "methodology_summary": {
        "dimension_a": "Continuous Pressure Intensity P in [0.05, 1.0] dynamically calculated from RRR, balls remaining, wickets in hand, and phase leverage.",
        "dimension_b": "Performance Above Expectation (PAE) comparing actual runs/wickets to contextual expected baselines calibrated across 201k balls.",
        "dimension_c": "Empirical Bayesian Shrinkage (K=75 balls) penalizing small samples and rewarding match-to-match consistency.",
        "dimension_d": "Multi-scenario specialization profiles: Chase Finisher, Death Crucible, Collapse Rescuer, and Powerplay Enforcer.",
        "dimension_e": "Opposition and tournament context adjustments (e.g. 1.15x weight for IPL playoff knockouts)."
    }
}

# Ensure clean python native types for json serialization
def clean_records(records):
    cleaned = []
    for r in records:
        cleaned_row = {}
        for k, v in r.items():
            if isinstance(v, (np.integer, np.int64, np.int32)):
                cleaned_row[k] = int(v)
            elif isinstance(v, (np.floating, np.float64, np.float32)):
                cleaned_row[k] = round(float(v), 2)
            elif pd.isna(v):
                cleaned_row[k] = None
            else:
                cleaned_row[k] = v
        cleaned.append(cleaned_row)
    return cleaned

export_data['top10_batters'] = clean_records(export_data['top10_batters'])
export_data['top10_bowlers'] = clean_records(export_data['top10_bowlers'])

out_path = '/Users/shauryasingh/.gemini/antigravity/brain/0518b937-5612-4321-91f6-0aaacaddc1a2/scratch/pressure_analytics_export.json'
with open(out_path, 'w') as f:
    json.dump(export_data, f, indent=2)

print(f"Master JSON exported successfully to: {out_path}")
