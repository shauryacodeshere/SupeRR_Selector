import pandas as pd
import numpy as np
import os
import sys

print("Starting data pipeline execution...")

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

# Match tier weights
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
    if 'final' in stage or 'eliminator' in stage or 'qualifier' in stage or 'semi' in stage:
        multiplier = max(multiplier, 1.25)
    return multiplier

matches['stakes_mult'] = matches.apply(get_stakes_multiplier, axis=1)

# Delivery properties
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

print("Computed basic delivery flags and merged match metadata.")
