import pandas as pd
import numpy as np

print("Aggregating player clutch performances...")

# Load processed deliveries
bbb = pd.read_pickle('processed_deliveries.pkl.gz', compression='gzip')
comp = pd.read_csv('competitions.csv')
mapping = pd.read_csv('competition_team_player_mapping.csv')
p11 = pd.read_csv('playing_eleven.csv')

# Identify capped players (who played in any T20I match in dataset)
t20i_comp_ids = set(comp[comp['match_format'] == 'T20I']['comp_id'])
t20i_player_ids = set(mapping[mapping['comp_id'].isin(t20i_comp_ids)]['player_id'])

# Also flag international veterans who may not have played T20Is in 2022-2026 but are internationally capped:
# e.g., Dhoni, Faf du Plessis, Rahane, Dhawan, Narine, Bravo, Saha, Rayudu, Ishant Sharma, Mohit Sharma, Piyush Chawla, Manish Pandey, Krunal Pandya, Vijay Shankar, Mayank Agarwal, Jaydev Unadkat, Amit Mishra
known_intl_veterans = {
    8, 88, 167, 142, 781, 109, 535, 28, 2878, 23, 198, 4219, 2877, 992, 1071, 128, 2411, 4265
}

def is_uncapped_emerging(player_id):
    if player_id in t20i_player_ids:
        return False
    if player_id in known_intl_veterans:
        return False
    return True

# ----------------- BATTER AGGREGATION -----------------
print("Computing Batter Clutch Scores...")

# Overall baseline
bat_all = bbb.groupby(['striker_id', 'striker_name']).agg(
    total_balls=('batter_ball', 'sum'),
    total_runs=('runs', 'sum'),
    total_outs=('is_striker_out', 'sum'),
    total_fours=('is_four', 'sum'),
    total_sixes=('is_six', 'sum'),
    total_matches=('match_id', 'nunique')
).reset_index()

bat_all['base_sr'] = np.where(bat_all['total_balls'] > 0, 100.0 * bat_all['total_runs'] / bat_all['total_balls'], 0)
bat_all['base_avg'] = np.where(bat_all['total_outs'] > 0, bat_all['total_runs'] / bat_all['total_outs'], bat_all['total_runs'])
bat_all['base_boundary_pct'] = (bat_all['total_fours'] + bat_all['total_sixes']) / bat_all['total_balls']

# Under high pressure (MPI >= 0.70)
bat_press = bbb[bbb['is_high_pressure']].groupby('striker_id').agg(
    press_balls=('batter_ball', 'sum'),
    press_runs=('runs', 'sum'),
    press_outs=('is_striker_out', 'sum'),
    press_fours=('is_four', 'sum'),
    press_sixes=('is_six', 'sum'),
    press_clutch_impact=('bat_clutch_impact', 'sum')
).reset_index()

bat_press['press_sr'] = np.where(bat_press['press_balls'] > 0, 100.0 * bat_press['press_runs'] / bat_press['press_balls'], 0)
bat_press['press_avg'] = np.where(bat_press['press_outs'] > 0, bat_press['press_runs'] / bat_press['press_outs'], bat_press['press_runs'])
bat_press['press_boundary_pct'] = (bat_press['press_fours'] + bat_press['press_sixes']) / bat_press['press_balls']

# Merge
batters = bat_all.merge(bat_press, on='striker_id', how='left').fillna(0)

# Deltas
batters['delta_sr'] = batters['press_sr'] - batters['base_sr']
batters['delta_avg'] = batters['press_avg'] - batters['base_avg']
batters['delta_boundary_pct'] = batters['press_boundary_pct'] - batters['base_boundary_pct']

# Uncapped flag
batters['is_uncapped'] = batters['striker_id'].apply(is_uncapped_emerging)

# Bayesian Shrinkage & Clutch Score Formula
# Clutch Efficiency per ball: press_clutch_impact / press_balls
# We regularize by adding prior pseudo-balls (m = 50 balls of average impact 0.0)
m_prior = 50.0
batters['shrink_clutch_per_ball'] = batters['press_clutch_impact'] / (batters['press_balls'] + m_prior)

# Volume component (log-scaled so 2000 balls doesn't drown 400 balls)
batters['vol_weight'] = np.log1p(batters['press_balls']) / np.log1p(1000)

# Final Batter Clutch Composite Score
# Balance rate efficiency (ability to lift scoring/average above par against tough attacks) with volume
batters['clutch_score'] = (
    batters['shrink_clutch_per_ball'] * 60.0 + 
    np.maximum(0, batters['delta_sr']) * 0.15 + 
    (batters['press_boundary_pct'] * 100.0) * 0.20 + 
    np.log1p(np.maximum(0, batters['press_clutch_impact'])) * 4.0
)

# ----------------- BOWLER AGGREGATION -----------------
print("Computing Bowler Clutch Scores...")

# Overall baseline
bowl_all = bbb.groupby(['bowler_id', 'bowler_name']).agg(
    total_balls=('is_legal', 'sum'),
    total_runs=('bowler_runs', 'sum'),
    total_wkts=('is_bowler_wicket', 'sum'),
    total_dots=('is_dot', 'sum'),
    total_matches=('match_id', 'nunique')
).reset_index()

bowl_all['base_econ'] = bowl_all['total_runs'] / (bowl_all['total_balls'] / 6.0)
bowl_all['base_sr'] = np.where(bowl_all['total_wkts'] > 0, bowl_all['total_balls'] / bowl_all['total_wkts'], 999.0)
bowl_all['base_dot_pct'] = bowl_all['total_dots'] / bowl_all['total_balls']

# Under high pressure (MPI >= 0.70)
bowl_press = bbb[bbb['is_high_pressure']].groupby('bowler_id').agg(
    press_balls=('is_legal', 'sum'),
    press_runs=('bowler_runs', 'sum'),
    press_wkts=('is_bowler_wicket', 'sum'),
    press_dots=('is_dot', 'sum'),
    press_clutch_impact=('bowl_clutch_impact', 'sum')
).reset_index()

bowl_press['press_econ'] = bowl_press['press_runs'] / (bowl_press['press_balls'] / 6.0)
bowl_press['press_sr'] = np.where(bowl_press['press_wkts'] > 0, bowl_press['press_balls'] / bowl_press['press_wkts'], 999.0)
bowl_press['press_dot_pct'] = bowl_press['press_dots'] / bowl_press['press_balls']

# Merge
bowlers = bowl_all.merge(bowl_press, on='bowler_id', how='left').fillna(0)

# Deltas
bowlers['delta_econ'] = bowlers['base_econ'] - bowlers['press_econ'] # positive = suppressed economy under pressure!
bowlers['delta_dot_pct'] = bowlers['press_dot_pct'] - bowlers['base_dot_pct']

# Uncapped flag
bowlers['is_uncapped'] = bowlers['bowler_id'].apply(is_uncapped_emerging)

# Bayesian Shrinkage & Bowler Clutch Score Formula
bowlers['shrink_clutch_per_ball'] = bowlers['press_clutch_impact'] / (bowlers['press_balls'] + m_prior)
bowlers['vol_weight'] = np.log1p(bowlers['press_balls']) / np.log1p(1000)

bowlers['clutch_score'] = (
    bowlers['shrink_clutch_per_ball'] * 50.0 + 
    np.maximum(0, bowlers['delta_econ']) * 2.0 + 
    (bowlers['press_dot_pct'] * 100.0) * 0.25 + 
    np.log1p(np.maximum(0, bowlers['press_clutch_impact'])) * 4.0
)

# Save results
batters.to_pickle('batters_clutch_scores.pkl.gz', compression='gzip')
bowlers.to_pickle('bowlers_clutch_scores.pkl.gz', compression='gzip')

print("Saved batters_clutch_scores.pkl.gz and bowlers_clutch_scores.pkl.gz.")
