import pandas as pd
import numpy as np

print("Running full pressure calculation and modeling pipeline...")

# 1. Load data
matches = pd.read_csv('matches.csv')
comp = pd.read_csv('competitions.csv')
teams = pd.read_csv('teams.csv')
mapping = pd.read_csv('competition_team_player_mapping.csv')
bbb = pd.read_csv('ball_by_ball.csv')

print(f"Loaded {len(matches)} matches, {len(bbb)} deliveries.")

# Map competition info
comp_dict = comp.set_index('comp_id')[['comp_name', 'match_format', 'season']].to_dict(orient='index')
matches['comp_name'] = matches['comp_id'].map(lambda cid: comp_dict[cid]['comp_name'] if cid in comp_dict else 'Unknown')
matches['match_format'] = matches['comp_id'].map(lambda cid: comp_dict[cid]['match_format'] if cid in comp_dict else 'Unknown')
matches['season'] = matches['comp_id'].map(lambda cid: comp_dict[cid]['season'] if cid in comp_dict else 'Unknown')

# Identify match tier
tier1_teams = {'India', 'Australia', 'England', 'South Africa', 'New Zealand', 'Pakistan', 'West Indies', 'Sri Lanka'}
ipl_comps = set(comp[comp['comp_name'].str.contains('IPL', na=False)]['comp_id'])

def get_match_tier(row):
    cid = row['comp_id']
    if cid in ipl_comps:
        return 'IPL'
    home = row['home_team']
    away = row['away_team']
    if home in tier1_teams and away in tier1_teams:
        return 'T20I_Tier1'
    elif home in tier1_teams or away in tier1_teams:
        return 'T20I_Tier2'
    else:
        return 'T20I_Other'

matches['match_tier'] = matches.apply(get_match_tier, axis=1)

tier_weight_map = {
    'IPL': 1.15,
    'T20I_Tier1': 1.15,
    'T20I_Tier2': 1.00,
    'T20I_Other': 0.85
}
matches['tier_weight'] = matches['match_tier'].map(tier_weight_map)

# Knockout multiplier
def get_stakes_multiplier(row):
    multiplier = 1.0
    if row['knock_out'] == 1:
        multiplier = 1.25
    stage = str(row['stage']).lower()
    if any(k in stage for k in ['final', 'eliminator', 'qualifier', 'semi']):
        multiplier = max(multiplier, 1.25)
    return multiplier

matches['stakes_mult'] = matches.apply(get_stakes_multiplier, axis=1)

# Basic delivery properties
bbb['is_wide'] = bbb['extras_type'] == 'wide'
bbb['is_noball'] = bbb['extras_type'] == 'Overstep'
bbb['is_legal'] = ~bbb['extras_type'].isin(['wide', 'Overstep'])
bbb['batter_ball'] = ~bbb['is_wide']
bbb['bowler_runs'] = bbb['runs'] + np.where(bbb['is_wide'] | bbb['is_noball'], bbb['extras1_runs'], 0)
bbb['total_ball_runs'] = bbb['runs'] + bbb['extras1_runs'] + bbb['extras_2_runs']

# Bowler wicket (excluding run outs and retirements)
bbb['is_bowler_wicket'] = bbb['is_wicket'] & (~bbb['dismissal_type'].isin(['RunOut', 'Retire Out']))
bbb.loc[bbb['dismissal_type'] == 'Hit Wicket', 'is_bowler_wicket'] = True
bbb['is_dot'] = (bbb['runs'] == 0) & (bbb['extras1_runs'] == 0) & (bbb['extras_2_runs'] == 0) & bbb['is_legal']

# Merge match metadata into ball_by_ball
bbb = bbb.merge(
    matches[['match_id', 'match_date', 'comp_name', 'match_tier', 'tier_weight', 'stakes_mult', 'knock_out', 'stage', 'revised_target', 'win_team_id']], 
    on='match_id', 
    how='left'
)

# Sort balls chronologically by match, innings, overid, over_ball_num
bbb = bbb.sort_values(['match_id', 'innings', 'overid', 'over_ball_num']).reset_index(drop=True)

# Define phase
def get_phase(overid):
    if overid <= 6:
        return 'Powerplay'
    elif overid <= 15:
        return 'Middle'
    else:
        return 'Death'

bbb['phase'] = bbb['overid'].apply(get_phase)

# 2. Cumulative match state per innings
# Calculate cumulative runs, wickets, and legal balls BEFORE the current ball
print("Computing cumulative state per innings...")
grp = bbb.groupby(['match_id', 'innings'])
bbb['cum_runs'] = grp['total_ball_runs'].cumsum() - bbb['total_ball_runs']
bbb['cum_wickets'] = grp['is_wicket'].cumsum() - bbb['is_wicket']
bbb['legal_balls_bowled'] = grp['is_legal'].cumsum() - bbb['is_legal']

bbb['balls_remaining'] = np.maximum(0, 120 - bbb['legal_balls_bowled'])
bbb['wickets_in_hand'] = np.maximum(0, 10 - bbb['cum_wickets'])
bbb['current_rr'] = np.where(bbb['legal_balls_bowled'] > 0, (bbb['cum_runs'] / bbb['legal_balls_bowled']) * 6.0, 7.5)

# 3. Determine Innings 1 totals and Targets for Innings 2
inn1_totals = bbb[bbb['innings'] == 1].groupby('match_id')['total_ball_runs'].sum().reset_index()
inn1_totals.rename(columns={'total_ball_runs': 'inn1_total'}, inplace=True)

bbb = bbb.merge(inn1_totals, on='match_id', how='left')
bbb['target'] = np.where(bbb['revised_target'].notna() & (bbb['revised_target'] > 0), bbb['revised_target'], bbb['inn1_total'] + 1)

# In innings 2: calculate runs needed and Required Run Rate (RRR)
bbb['runs_needed'] = np.where(bbb['innings'] == 2, np.maximum(0, bbb['target'] - bbb['cum_runs']), np.nan)
bbb['rrr'] = np.where(
    (bbb['innings'] == 2) & (bbb['balls_remaining'] > 0),
    (bbb['runs_needed'] / bbb['balls_remaining']) * 6.0,
    np.where(bbb['innings'] == 2, 36.0, np.nan)
)

print("Cumulative states and chase variables computed.")

# 4. Multi-Dimensional Pressure Modeling (MPI)
print("Calculating Match Pressure Index (MPI)...")

# A. Early Collapse Index (Applies to both Innings 1 and Innings 2)
# Triggered when team is in deep trouble early: e.g. 2+ wickets down in PP, especially 3+ wickets
collapse_pressure = np.zeros(len(bbb))
# Powerplay collapse (overs 1-6)
pp_mask = bbb['overid'] <= 6
collapse_pressure = np.where(pp_mask & (bbb['cum_wickets'] >= 3), 0.85 + 0.05 * (bbb['cum_wickets'] - 3), collapse_pressure)
collapse_pressure = np.where(pp_mask & (bbb['cum_wickets'] == 2), 0.65, collapse_pressure)
collapse_pressure = np.where(pp_mask & (bbb['cum_wickets'] == 1) & (bbb['cum_runs'] < 15) & (bbb['overid'] >= 3), 0.45, collapse_pressure)
# Middle overs collapse (overs 7-12)
mid_mask = (bbb['overid'] > 6) & (bbb['overid'] <= 12)
collapse_pressure = np.where(mid_mask & (bbb['cum_wickets'] >= 5), 0.80, collapse_pressure)
collapse_pressure = np.where(mid_mask & (bbb['cum_wickets'] == 4), 0.65, collapse_pressure)
bbb['p_collapse'] = collapse_pressure

# B. Death Overs Crucible (Overs 16-20)
# In Innings 1: acceleration urgency; in Innings 2: closing out the game
death_pressure = np.zeros(len(bbb))
death_mask = bbb['overid'] >= 16
# Scales from 0.70 at over 16 to 0.95 at over 20
death_pressure = np.where(death_mask, 0.65 + 0.07 * (bbb['overid'] - 15), 0.0)
bbb['p_death'] = death_pressure

# C. Chase / Scoreboard Pressure (Innings 2 only)
# Based on RRR, wickets in hand, and closeness
chase_pressure = np.zeros(len(bbb))
inn2_mask = bbb['innings'] == 2

# Leverage function of RRR and wickets in hand
rrr_clipped = np.clip(bbb['rrr'], 4.0, 20.0)
# Sigmoid-like scaling for RRR: par is ~8.5
rrr_factor = 1.0 / (1.0 + np.exp(-(rrr_clipped - 9.5) / 2.2))  # ranges ~0.08 to ~0.99
# Wicket pressure factor: fewer wickets in hand = much higher leverage
wkt_factor = 1.0 + (bbb['cum_wickets'] / 10.0) * 0.5  # 1.0 to 1.5

raw_chase_p = rrr_factor * wkt_factor

# Closeness bonus in late overs (overs 16-20)
late_chase_mask = inn2_mask & (bbb['overid'] >= 16)
close_game = late_chase_mask & (bbb['runs_needed'] <= 40) & (bbb['runs_needed'] > 0)
raw_chase_p = np.where(close_game, np.maximum(raw_chase_p, 0.85), raw_chase_p)

# Game decided check: if match is virtually over (e.g. 5 runs needed off 30 balls with 8 wickets, or 60 needed off 6 balls)
game_virtually_won = inn2_mask & (bbb['runs_needed'] <= 8) & (bbb['balls_remaining'] >= 24) & (bbb['wickets_in_hand'] >= 6)
game_virtually_lost = inn2_mask & (bbb['runs_needed'] >= 45) & (bbb['balls_remaining'] <= 12) & (bbb['wickets_in_hand'] <= 3)

raw_chase_p = np.where(game_virtually_won, 0.20, raw_chase_p)
raw_chase_p = np.where(game_virtually_lost, 0.35, raw_chase_p)

chase_pressure = np.where(inn2_mask, raw_chase_p, 0.0)
bbb['p_chase'] = chase_pressure

# D. Low Total Defense Pressure (Bowler focus in Innings 2)
# When target is low (<155 in IPL, <135 in T20I), bowling side is under immense pressure
low_target_thresh = np.where(bbb['match_tier'] == 'IPL', 155, 135)
low_target_defense = inn2_mask & (bbb['target'] < low_target_thresh) & (bbb['runs_needed'] > 15)
bbb['p_low_defense'] = np.where(low_target_defense, 0.75, 0.0)

# E. Composite Base Pressure
# In Innings 1: max of collapse and death pressure, plus baseline phase pressure
# In Innings 2: max of chase pressure, collapse pressure, death pressure, and low defense pressure
base_p_inn1 = np.maximum(bbb['p_collapse'], bbb['p_death'])
# Baseline pressure for regular Innings 1 (Powerplay ~0.4, Middle ~0.35)
inn1_baseline = np.where(bbb['overid'] <= 6, 0.40, np.where(bbb['overid'] <= 15, 0.35, 0.70))
base_p_inn1 = np.maximum(base_p_inn1, inn1_baseline)

base_p_inn2 = np.maximum.reduce([bbb['p_chase'], bbb['p_collapse'], bbb['p_death'], bbb['p_low_defense']])

bbb['base_pressure'] = np.where(bbb['innings'] == 1, base_p_inn1, base_p_inn2)

# F. Apply Match Stakes & Tier Multipliers
bbb['mpi'] = np.clip(bbb['base_pressure'] * bbb['stakes_mult'] * bbb['tier_weight'], 0.1, 1.5)

print(f"MPI Summary: min={bbb['mpi'].min():.3f}, median={bbb['mpi'].median():.3f}, mean={bbb['mpi'].mean():.3f}, max={bbb['mpi'].max():.3f}")

# 5. Opponent Toughness Modeling
print("Calculating Opponent Toughness...")
# Compute bowling team economy & dot % relative to competition average
comp_avg_econ = bbb.groupby('match_tier')['bowler_runs'].sum() / (bbb.groupby('match_tier')['is_legal'].sum() / 6.0)
print("Competition average economy by tier:\n", comp_avg_econ)

# Team bowling quality index
team_bowl = bbb.groupby(['match_tier', 'bowling_team_id']).agg(
    balls=('is_legal', 'sum'),
    runs=('bowler_runs', 'sum'),
    dots=('is_dot', 'sum'),
    wkts=('is_bowler_wicket', 'sum')
).reset_index()

team_bowl['econ'] = team_bowl['runs'] / (team_bowl['balls'] / 6.0)
team_bowl['tier_avg_econ'] = team_bowl['match_tier'].map(comp_avg_econ)
# Toughness: lower economy = tougher bowling unit -> factor > 1.0
team_bowl['bowl_toughness'] = np.clip(team_bowl['tier_avg_econ'] / team_bowl['econ'], 0.80, 1.25)

# Map back to ball_by_ball
bbb = bbb.merge(
    team_bowl[['match_tier', 'bowling_team_id', 'bowl_toughness']], 
    on=['match_tier', 'bowling_team_id'], 
    how='left'
)
bbb['bowl_toughness'] = bbb['bowl_toughness'].fillna(1.0)

# Team batting quality index (toughness for bowlers)
comp_avg_bat_sr = bbb.groupby('match_tier')['runs'].sum() / bbb.groupby('match_tier')['batter_ball'].sum()
team_bat = bbb.groupby(['match_tier', 'batting_team_id']).agg(
    balls=('batter_ball', 'sum'),
    runs=('runs', 'sum')
).reset_index()
team_bat['sr'] = team_bat['runs'] / team_bat['balls']
team_bat['tier_avg_sr'] = team_bat['match_tier'].map(comp_avg_bat_sr)
team_bat['bat_toughness'] = np.clip(team_bat['sr'] / team_bat['tier_avg_sr'], 0.80, 1.25)

bbb = bbb.merge(
    team_bat[['match_tier', 'batting_team_id', 'bat_toughness']], 
    on=['match_tier', 'batting_team_id'], 
    how='left'
)
bbb['bat_toughness'] = bbb['bat_toughness'].fillna(1.0)

# 6. Context Expectation Baseline (Value Added Above Expected)
print("Computing Context Baseline expectations...")
# Expected runs and wicket hazard by phase, wickets bracket, and innings
def get_wkt_bracket(w):
    if w <= 1:
        return '0-1'
    elif w <= 3:
        return '2-3'
    elif w <= 5:
        return '4-5'
    else:
        return '6+'

bbb['wkt_bracket'] = bbb['cum_wickets'].apply(get_wkt_bracket)

baseline_exp = bbb.groupby(['innings', 'phase', 'wkt_bracket']).agg(
    exp_runs=('runs', 'mean'),
    exp_bowler_runs=('bowler_runs', 'mean'),
    exp_wicket=('is_bowler_wicket', 'mean'),
    exp_dot=('is_dot', 'mean')
).reset_index()

bbb = bbb.merge(baseline_exp, on=['innings', 'phase', 'wkt_bracket'], how='left')

# 7. Batting Impact Calculation
# Runs Above Expected (RAE), Boundary bonus, Striker Out penalty
# Striker dismissed check:
bbb['is_striker_out'] = bbb['is_wicket'] & (bbb['dismissed_player_id'] == bbb['striker_id'])
# Batting ball value
bbb['bat_val_added'] = (bbb['runs'] - bbb['exp_runs']) + \
                       np.where(bbb['is_four'], 1.5, 0.0) + \
                       np.where(bbb['is_six'], 3.0, 0.0) - \
                       np.where(bbb['is_striker_out'], 8.0, 0.0)

# Batter Weighted Clutch Impact
bbb['bat_clutch_impact'] = bbb['bat_val_added'] * bbb['mpi'] * bbb['bowl_toughness']

# 8. Bowling Impact Calculation
# Runs Saved Below Expected (RSBE), Dot ball value, Wicket value
bbb['bowl_val_added'] = (bbb['exp_bowler_runs'] - bbb['bowler_runs']) + \
                        np.where(bbb['is_dot'], 1.2, 0.0) + \
                        np.where(bbb['is_bowler_wicket'], 10.0, 0.0)

# Bowler Weighted Clutch Impact
bbb['bowl_clutch_impact'] = bbb['bowl_val_added'] * bbb['mpi'] * bbb['bat_toughness']

# High Pressure Deliveries Definition (Top ~35% of pressure distribution: MPI >= 0.70)
bbb['is_high_pressure'] = bbb['mpi'] >= 0.70

print(f"High Pressure Deliveries: {bbb['is_high_pressure'].sum()} / {len(bbb)} ({bbb['is_high_pressure'].mean()*100:.1f}%)")

# Save processed ball-by-ball summary or metrics
bbb.to_pickle('processed_deliveries.pkl.gz', compression='gzip')
print("Saved processed_deliveries.pkl.gz successfully!")
