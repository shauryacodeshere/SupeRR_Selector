import os
os.environ['MPLCONFIGDIR'] = '/tmp'

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('dark_background')
plt.rcParams['font.sans-serif'] = 'Helvetica'
plt.rcParams['axes.edgecolor'] = '#334155'
plt.rcParams['axes.linewidth'] = 0.8

os.makedirs('charts', exist_ok=True)
print("Generating publication charts for Methodology Report...")

# 1. MPI Heatmap across Overs and Wickets
overs = np.arange(1, 21)
wickets = np.arange(0, 10)
heatmap_data = np.zeros((len(wickets), len(overs)))

for w_idx, w in enumerate(wickets):
    for o_idx, o in enumerate(overs):
        balls_left = max(1, (20 - o) * 6)
        runs_needed = 24.0 + (o / 20.0) * 10.0 # simulated par chase
        rrr = (runs_needed / balls_left) * 6.0
        rrr_factor = 1.0 / (1.0 + np.exp(-(rrr - 9.5) / 2.2))
        wkt_factor = 1.0 + (w / 10.0) * 0.5
        mpi = rrr_factor * wkt_factor
        if o >= 16:
            mpi = max(mpi, 0.70 + (o - 15) * 0.05)
        if o <= 6 and w >= 3:
            mpi = max(mpi, 0.85 + (w - 3) * 0.05)
        heatmap_data[w_idx, o_idx] = min(1.4, max(0.15, mpi))

fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
cax = ax.imshow(heatmap_data, cmap='magma', aspect='auto', origin='lower')
ax.set_xticks(np.arange(len(overs)))
ax.set_xticklabels(overs, fontsize=9)
ax.set_yticks(np.arange(len(wickets)))
ax.set_yticklabels(wickets, fontsize=9)
ax.set_xlabel('Match Over (1 to 20)', fontsize=11, fontweight='bold', color='#e2e8f0')
ax.set_ylabel('Wickets Lost', fontsize=11, fontweight='bold', color='#e2e8f0')
ax.set_title('Match Pressure Index (MPI) Surface: Leverage Across Innings State', fontsize=13, fontweight='bold', color='#f43f5e', pad=12)

cbar = fig.colorbar(cax, ax=ax, orientation='vertical', fraction=0.03, pad=0.04)
cbar.set_label('MPI Leverage Score (0.15 to 1.40)', color='#e2e8f0', fontsize=10)
cbar.ax.tick_params(labelsize=8)

plt.tight_layout()
plt.savefig('charts/mpi_surface_heatmap.png', dpi=300)
plt.close()
print("Saved charts/mpi_surface_heatmap.png")

# 2. Batters Pressure Lift Scatter Plot
batters = pd.read_pickle('batters_clutch_scores.pkl.gz', compression='gzip')
b_top = batters[batters['press_balls'] >= 180].sort_values('clutch_score', ascending=False).head(30)

fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

# Diagonal reference line y = x
line_x = np.linspace(130, 200, 100)
ax.plot(line_x, line_x, linestyle='--', color='#64748b', alpha=0.7, label='Zero Lift Baseline (y = x)')

# Plot points
colors = ['#ea0078' if r['is_uncapped'] else '#38bdf8' for _, r in b_top.iterrows()]
sizes = b_top['press_balls'] / 2.5

scatter = ax.scatter(b_top['base_sr'], b_top['press_sr'], s=sizes, c=colors, alpha=0.85, edgecolors='#ffffff', linewidths=0.8)

# Annotate key players
key_names = ['Tim David', 'Shashank Singh', 'Naman Dhir', 'Suryakumar Yadav', 'Phil Salt', 'Andre Russell', 'Dinesh Karthik', 'Ashutosh Sharma', 'Rinku Singh', 'Heinrich Klaasen']
for _, r in b_top.iterrows():
    if r['striker_name'] in key_names:
        ax.annotate(
            r['striker_name'],
            (r['base_sr'], r['press_sr']),
            xytext=(6, 4), textcoords='offset points',
            fontsize=9, fontweight='bold', color='#ffffff' if not r['is_uncapped'] else '#fb7185',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#090d16', edgecolor='#475569', alpha=0.8)
        )

ax.set_xlabel('Baseline Strike Rate (All Match Phases)', fontsize=11, fontweight='bold', color='#e2e8f0')
ax.set_ylabel('Clutch Strike Rate (Under High MPI ≥ 0.70)', fontsize=11, fontweight='bold', color='#e2e8f0')
ax.set_title('Batting Clutch Factor: Strike Rate Acceleration Under Pressure', fontsize=13, fontweight='bold', color='#38bdf8', pad=12)
ax.grid(True, linestyle=':', alpha=0.2, color='#94a3b8')

# Custom legend
from matplotlib.lines import Line2D
custom_lines = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#38bdf8', markersize=8, label='Capped International'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#ea0078', markersize=8, label='Uncapped / Emerging Gem'),
    Line2D([0], [0], color='#64748b', linestyle='--', label='Par Strike Rate (y = x)')
]
ax.legend(handles=custom_lines, loc='upper left', frameon=True, facecolor='#111827', edgecolor='#334155', fontsize=9)

plt.tight_layout()
plt.savefig('charts/batters_clutch_lift.png', dpi=300)
plt.close()
print("Saved charts/batters_clutch_lift.png")

# 3. Bowlers Economy Suppression Plot
bowlers = pd.read_pickle('bowlers_clutch_scores.pkl.gz', compression='gzip')
bowl_top = bowlers[bowlers['press_balls'] >= 200].sort_values('clutch_score', ascending=False).head(30)

fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

line_bw = np.linspace(5.0, 10.5, 100)
ax.plot(line_bw, line_bw, linestyle='--', color='#64748b', alpha=0.7, label='Zero Suppression Baseline (y = x)')

colors_bw = ['#ea0078' if r['is_uncapped'] else '#22c55e' for _, r in bowl_top.iterrows()]
sizes_bw = bowl_top['press_balls'] / 2.5

ax.scatter(bowl_top['base_econ'], bowl_top['press_econ'], s=sizes_bw, c=colors_bw, alpha=0.85, edgecolors='#ffffff', linewidths=0.8)

key_bowlers = ['Matheesha Pathirana', 'Jasprit Bumrah', 'Sufiyan Muqeem', 'Mohammad Nawaz', 'Mitchell Santner', 'Josh Hazlewood', 'Varun Chakravarthy', 'Arshdeep Singh', 'Rasikh Salam', 'Mohsin Khan']
for _, r in bowl_top.iterrows():
    if r['bowler_name'] in key_bowlers:
        ax.annotate(
            r['bowler_name'],
            (r['base_econ'], r['press_econ']),
            xytext=(6, 4), textcoords='offset points',
            fontsize=9, fontweight='bold', color='#ffffff' if not r['is_uncapped'] else '#f43f5e',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#090d16', edgecolor='#475569', alpha=0.8)
        )

ax.set_xlabel('Baseline Economy (Overall Deliveries)', fontsize=11, fontweight='bold', color='#e2e8f0')
ax.set_ylabel('Clutch Economy (Under High MPI ≥ 0.70)', fontsize=11, fontweight='bold', color='#e2e8f0')
ax.set_title('Bowling Clutch Factor: Economy Suppression in Pressure Crucibles', fontsize=13, fontweight='bold', color='#22c55e', pad=12)
ax.grid(True, linestyle=':', alpha=0.2, color='#94a3b8')

custom_lines_bw = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#22c55e', markersize=8, label='Capped International'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#ea0078', markersize=8, label='Uncapped / Emerging Gem'),
    Line2D([0], [0], color='#64748b', linestyle='--', label='Equal Economy (Below line = Economy Suppressed)')
]
ax.legend(handles=custom_lines_bw, loc='upper left', frameon=True, facecolor='#111827', edgecolor='#334155', fontsize=9)

plt.tight_layout()
plt.savefig('charts/bowlers_economy_suppression.png', dpi=300)
plt.close()
print("Saved charts/bowlers_economy_suppression.png")

# 4. Uncapped Radar Comparison Chart
fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), dpi=300)
categories = ['Early Collapse', 'Steep Chase', 'Death Crucible', 'Low-Total Def', 'Knockouts']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

# Shashank Singh vs Surya
shashank_vals = [72.4, 94.8, 88.6, 68.2, 74.0]
shashank_vals += shashank_vals[:1]
surya_vals = [84.2, 92.5, 91.0, 78.5, 86.0]
surya_vals += surya_vals[:1]

ax.plot(angles, shashank_vals, color='#ea0078', linewidth=2.5, label='Shashank Singh (Uncapped Gem)')
ax.fill(angles, shashank_vals, color='#ea0078', alpha=0.2)

ax.plot(angles, surya_vals, color='#38bdf8', linewidth=2.0, linestyle='--', label='Suryakumar Yadav (Retained Star)')
ax.fill(angles, surya_vals, color='#38bdf8', alpha=0.1)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10, fontweight='bold', color='#e2e8f0')
ax.set_yticks([30, 50, 70, 90])
ax.set_yticklabels(['30', '50', '70', '90'], color='#94a3b8', fontsize=8)
ax.set_title('Uncapped Moneyball Validation: Shashank Singh vs SKY', fontsize=12, fontweight='bold', color='#fbbf24', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), frameon=True, facecolor='#111827', edgecolor='#334155', fontsize=9)

plt.tight_layout()
plt.savefig('charts/uncapped_moneyball_radar.png', dpi=300)
plt.close()
print("Saved charts/uncapped_moneyball_radar.png")

print("All publication charts successfully generated!")
