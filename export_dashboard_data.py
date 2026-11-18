import pandas as pd
import numpy as np
import json

print("Exporting rich dashboard data with 5-dimension radar scores...")

bbb = pd.read_pickle('processed_deliveries.pkl.gz', compression='gzip')
batters = pd.read_pickle('batters_clutch_scores.pkl.gz', compression='gzip')
bowlers = pd.read_pickle('bowlers_clutch_scores.pkl.gz', compression='gzip')

# Retention & Status sets
retained_set = {
    'Tim David', 'Suryakumar Yadav', 'Shashank Singh', 'Phil Salt', 'Naman Dhir', 
    'Abhishek Sharma', 'Andre Russell', 'Rinku Singh', 'Yashasvi Jaiswal', 
    'Nicholas Pooran', 'Heinrich Klaasen', 'Sanju Samson', 'Rishabh Pant', 
    'Jos Buttler', 'Virat Kohli', 'Rohit Sharma', 'Jasprit Bumrah', 
    'Josh Hazlewood', 'Varun Chakravarthy', 'Arshdeep Singh', 'Jamie Overton', 
    'Rasikh Salam', 'Sunil Narine', 'Rashid Khan', 'Kuldeep Yadav', 
    'Pat Cummins', 'Mitchell Starc', 'Trent Boult', 'Axar Patel', 'Ravindra Jadeja'
}

retired_set = {'Dinesh Karthik'}

def get_player_status(name, is_uncapped):
    if name in retired_set:
        return 'Retired'
    if name in retained_set:
        return 'Retained'
    if is_uncapped:
        return 'Targetable (Uncapped)'
    return 'Targetable (Auction)'

# Define dimension masks
mask_collapse = bbb['p_collapse'] >= 0.5
mask_chase = (bbb['innings'] == 2) & (bbb['p_chase'] >= 0.6)
mask_death = bbb['phase'] == 'Death'
mask_defense = (bbb['innings'] == 2) & ((bbb['p_low_defense'] > 0) | (bbb['runs_needed'] > 0))
mask_knockout = bbb['stakes_mult'] > 1.0

# Stratified expectations for runs & bowler runs
exp_runs_strat = bbb.groupby(['match_tier', 'innings', 'phase', 'wkt_bracket'])['runs'].transform('mean')
exp_bowl_strat = bbb.groupby(['match_tier', 'innings', 'phase', 'wkt_bracket'])['bowler_runs'].transform('mean')

bbb['bat_impact_per_ball'] = (bbb['runs'] - exp_runs_strat) + np.where(bbb['is_four'], 1.5, 0) + np.where(bbb['is_six'], 3.0, 0) - np.where(bbb['is_striker_out'], 8.0, 0)
bbb['bowl_impact_per_ball'] = (exp_bowl_strat - bbb['bowler_runs']) + np.where(bbb['is_dot'], 1.2, 0) + np.where(bbb['is_bowler_wicket'], 10.0, 0)

# Calculate 5-dimension metrics for Batters
def calc_bat_dim(mask):
    sub = bbb[mask & bbb['batter_ball']]
    grp = sub.groupby('striker_id').agg(
        balls=('runs', 'count'),
        runs=('runs', 'sum'),
        impact=('bat_impact_per_ball', 'sum')
    )
    # Rate per 100 balls regularized
    grp['rate'] = (grp['impact'] / (grp['balls'] + 15.0)) * 50.0 + (grp['runs'] / np.maximum(1, grp['balls'])) * 20.0
    return grp['rate']

bat_dim_collapse = calc_bat_dim(mask_collapse)
bat_dim_chase = calc_bat_dim(mask_chase)
bat_dim_death = calc_bat_dim(mask_death)
bat_dim_defense = calc_bat_dim(mask_defense)
bat_dim_knockout = calc_bat_dim(mask_knockout)

# Calculate 5-dimension metrics for Bowlers
def calc_bowl_dim(mask):
    sub = bbb[mask & bbb['is_legal']]
    grp = sub.groupby('bowler_id').agg(
        balls=('bowler_runs', 'count'),
        runs=('bowler_runs', 'sum'),
        wkts=('is_bowler_wicket', 'sum'),
        impact=('bowl_impact_per_ball', 'sum')
    )
    grp['rate'] = (grp['impact'] / (grp['balls'] + 15.0)) * 50.0 + (grp['wkts'] / np.maximum(1, grp['balls'])) * 500.0
    return grp['rate']

bowl_dim_collapse = calc_bowl_dim(mask_collapse)
bowl_dim_chase = calc_bowl_dim(mask_chase)
bowl_dim_death = calc_bowl_dim(mask_death)
bowl_dim_defense = calc_bowl_dim(mask_defense)
bowl_dim_knockout = calc_bowl_dim(mask_knockout)

def normalize_to_100(series):
    s = series.dropna()
    low = s.quantile(0.05)
    high = s.quantile(0.95)
    clipped = np.clip(series, low, high)
    return np.round(20.0 + ((clipped - low) / (high - low)) * 75.0, 1)

# Attach to batters
batters['dim_collapse'] = normalize_to_100(batters['striker_id'].map(bat_dim_collapse)).fillna(45.0)
batters['dim_chase'] = normalize_to_100(batters['striker_id'].map(bat_dim_chase)).fillna(45.0)
batters['dim_death'] = normalize_to_100(batters['striker_id'].map(bat_dim_death)).fillna(45.0)
batters['dim_defense'] = normalize_to_100(batters['striker_id'].map(bat_dim_defense)).fillna(45.0)
batters['dim_knockout'] = normalize_to_100(batters['striker_id'].map(bat_dim_knockout)).fillna(45.0)

batters['status'] = batters.apply(lambda r: get_player_status(r['striker_name'], r['is_uncapped']), axis=1)

# Attach to bowlers
bowlers['dim_collapse'] = normalize_to_100(bowlers['bowler_id'].map(bowl_dim_collapse)).fillna(45.0)
bowlers['dim_chase'] = normalize_to_100(bowlers['bowler_id'].map(bowl_dim_chase)).fillna(45.0)
bowlers['dim_death'] = normalize_to_100(bowlers['bowler_id'].map(bowl_dim_death)).fillna(45.0)
bowlers['dim_defense'] = normalize_to_100(bowlers['bowler_id'].map(bowl_dim_defense)).fillna(45.0)
bowlers['dim_knockout'] = normalize_to_100(bowlers['bowler_id'].map(bowl_dim_knockout)).fillna(45.0)

bowlers['status'] = bowlers.apply(lambda r: get_player_status(r['bowler_name'], r['is_uncapped']), axis=1)

# Filter top batters: min 200 pressure balls for established benchmark, plus uncapped gems with 80+ balls
top_bat_main = batters[batters['press_balls'] >= 200].sort_values('clutch_score', ascending=False)
top_bat_uncapped = batters[(batters['press_balls'] >= 80) & (batters['is_uncapped']) & (~batters['striker_id'].isin(top_bat_main['striker_id']))].sort_values('clutch_score', ascending=False)
top_bat = pd.concat([top_bat_main, top_bat_uncapped]).drop_duplicates(subset=['striker_id'])

# Filter top bowlers: min 200 pressure balls for established benchmark, plus uncapped gems with 80+ balls
top_bowl_main = bowlers[bowlers['press_balls'] >= 200].sort_values('clutch_score', ascending=False)
top_bowl_uncapped = bowlers[(bowlers['press_balls'] >= 80) & (bowlers['is_uncapped']) & (~bowlers['bowler_id'].isin(top_bowl_main['bowler_id']))].sort_values('clutch_score', ascending=False)
top_bowl = pd.concat([top_bowl_main, top_bowl_uncapped]).drop_duplicates(subset=['bowler_id'])

# Prepare JSON structures
batters_list = []
for idx, r in top_bat.head(50).reset_index(drop=True).iterrows():
    batters_list.append({
        'rank': idx + 1,
        'id': int(r['striker_id']),
        'name': r['striker_name'],
        'status': r['status'],
        'is_uncapped': bool(r['is_uncapped']),
        'press_balls': int(r['press_balls']),
        'total_balls': int(r['total_balls']),
        'press_sr': round(float(r['press_sr']), 1),
        'base_sr': round(float(r['base_sr']), 1),
        'delta_sr': round(float(r['delta_sr']), 1),
        'press_avg': round(float(r['press_avg']), 1),
        'press_boundary_pct': round(float(r['press_boundary_pct']) * 100, 1),
        'clutch_score': round(float(r['clutch_score']), 1),
        'radar': {
            'collapse': float(r['dim_collapse']),
            'chase': float(r['dim_chase']),
            'death': float(r['dim_death']),
            'defense': float(r['dim_defense']),
            'knockout': float(r['dim_knockout'])
        }
    })

bowlers_list = []
for idx, r in top_bowl.head(50).reset_index(drop=True).iterrows():
    bowlers_list.append({
        'rank': idx + 1,
        'id': int(r['bowler_id']),
        'name': r['bowler_name'],
        'status': r['status'],
        'is_uncapped': bool(r['is_uncapped']),
        'press_balls': int(r['press_balls']),
        'total_balls': int(r['total_balls']),
        'press_econ': round(float(r['press_econ']), 2),
        'base_econ': round(float(r['base_econ']), 2),
        'delta_econ': round(float(r['delta_econ']), 2),
        'press_wkts': int(r['press_wkts']),
        'press_dot_pct': round(float(r['press_dot_pct']) * 100, 1),
        'press_sr': round(float(r['press_sr']), 1),
        'clutch_score': round(float(r['clutch_score']), 1),
        'radar': {
            'collapse': float(r['dim_collapse']),
            'chase': float(r['dim_chase']),
            'death': float(r['dim_death']),
            'defense': float(r['dim_defense']),
            'knockout': float(r['dim_knockout'])
        }
    })

dashboard_data = {
    'metadata': {
        'total_matches': 883,
        'total_deliveries': 200999,
        'high_pressure_deliveries': 93264,
        'unique_players': 1217,
        'seasons': '2022-2026',
        'generated_date': '2026-11-15'
    },
    'batters': batters_list,
    'bowlers': bowlers_list
}

with open('dashboard_data.json', 'w') as f:
    json.dump(dashboard_data, f, indent=2)

print("Saved dashboard_data.json with", len(batters_list), "batters and", len(bowlers_list), "bowlers.")
