import os
import fitz  # PyMuPDF
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

print("Building formal Methodology Report in PDF and DOCX formats...")

# ----------------- 1. DOCX GENERATION -----------------
doc = Document()

# Page Margins
sections = doc.sections
for s in sections:
    s.top_margin = Inches(0.8)
    s.bottom_margin = Inches(0.8)
    s.left_margin = Inches(0.8)
    s.right_margin = Inches(0.8)

# Title & Metadata
title = doc.add_paragraph()
title_run = title.add_run("SupeRR Selector Season 2: Methodology Report")
title_run.font.size = Pt(22)
title_run.font.bold = True
title_run.font.color.rgb = RGBColor(234, 0, 120) # RR Pink
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

subtitle = doc.add_paragraph()
sub_run = subtitle.add_run("A Multi-Dimensional Contextual Framework for Measuring High-Pressure Reliability in T20 Cricket")
sub_run.font.size = Pt(13)
sub_run.font.italic = True
sub_run.font.color.rgb = RGBColor(71, 85, 105)
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

meta = doc.add_paragraph()
meta_run = meta.add_run("Target Franchise: Rajasthan Royals | Scope: 883 Matches (2022–2026) | Date: November 2026")
meta_run.font.size = Pt(10)
meta_run.font.color.rgb = RGBColor(100, 116, 139)
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph().paragraph_format.space_after = Pt(12)

# Executive Summary
h1 = doc.add_heading(level=1)
h1.add_run("Executive Summary").font.color.rgb = RGBColor(0, 30, 98)
p = doc.add_paragraph(
    "In T20 cricket, aggregate statistics (such as unadjusted strike rates and economy rates) systematically distort player evaluation. "
    "Traditional metrics reward players who accumulate runs or bowl cheap overs during low-leverage match situations, while penalizing those who consistently face the fire in match-deciding cauldrons. "
    "To solve this problem for Rajasthan Royals, we present a mathematically rigorous, delivery-level decision engine that models how batters and bowlers perform in high-pressure match situations compared with their contextual baselines."
)
p.paragraph_format.line_spacing = 1.15

p2 = doc.add_paragraph(
    "Our approach is built on four core innovations:\n"
    "1. Multi-Dimensional Match Pressure Index (MPI): A continuous leverage function capturing early top-order collapses (Powerplay wickets), steep required run-rate chases, death-overs crucibles (overs 16–20), low-total bowling defense, and knockout tournament stakes.\n"
    "2. Tier-Stratified Value Added Above Expected (VAAE): Every delivery is benchmarked against its exact (Competition Tier, Innings, Phase, Wickets Bracket) empirical cohort, eliminating false distortions from low-scoring associate spinning tracks.\n"
    "3. Opponent Quality & Toughness Adjustments: Hitting boundaries off Jasprit Bumrah or bowling to Heinrich Klaasen carries mathematical multipliers reflecting the relative quality of the opposition.\n"
    "4. Dual-Lens Franchise Architecture: Distinguishing the Global Benchmark Top 10 (validating the model on world-class stars like Tim David, Suryakumar Yadav, and Jasprit Bumrah) from the Actionable Auction Target Board (uncovering high-ROI bargains like Shashank Singh, Ashutosh Sharma, Matheesha Pathirana, and Sakib Hussain for Rajasthan Royals)."
)
p2.paragraph_format.line_spacing = 1.15

# Section 1: Pressure Definition
h2 = doc.add_heading(level=1)
h2.add_run("1. Defining Match Pressure: The Multi-Dimensional MPI").font.color.rgb = RGBColor(0, 30, 98)
doc.add_paragraph(
    "Pressure in T20 cricket is multi-faceted and cannot be reduced to required run rate alone. We define five distinct pressure archetypes, synthesized into a composite Match Pressure Index (MPI) ranging from 0.10 to 1.50:"
)

p_arch = doc.add_paragraph()
p_arch.add_run("- Early Top-Order Collapse: ").bold = True
p_arch.add_run("Triggered when a team loses ≥ 3 wickets in the Powerplay (overs 1–6) or is restricted to ≤ 35 runs. Batters must simultaneously rebuild and score; bowlers attack aggressively for the kill.\n")
p_arch.add_run("- Steep Chase & Scoreboard Leverage: ").bold = True
p_arch.add_run("In Innings 2, pressure scales non-linearly with Required Run Rate (RRR ≥ 10.5) and wickets lost, with an exponential surge in overs 16–20 when the margin is within 36 runs.\n")
p_arch.add_run("- Death-Overs Crucible: ").bold = True
p_arch.add_run("Overs 16–20 in both innings, where every dot ball or boundary fundamentally swings expected win probabilities.\n")
p_arch.add_run("- Low-Total Defense: ").bold = True
p_arch.add_run("In Innings 2, bowling units defending sub-par totals (<155 in IPL, <135 in T20I) face extreme pressure where conceding even a single boundary over breaks the defense.\n")
p_arch.add_run("- High-Stakes Tournament Knockouts: ").bold = True
p_arch.add_run("A 1.25x multiplier is applied to Eliminators, Qualifiers, Semi-Finals, and Finals.")

if os.path.exists('charts/mpi_surface_heatmap.png'):
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    doc.add_picture('charts/mpi_surface_heatmap.png', width=Inches(6.2))
    cap = doc.add_paragraph()
    cap_run = cap.add_run("Figure 1: Match Pressure Index (MPI) leverage surface across match overs and wickets lost.")
    cap_run.font.size = Pt(9)
    cap_run.font.italic = True
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Section 2: Performance Measurement & Expected Baselines
h3 = doc.add_heading(level=1)
h3.add_run("2. Performance Measurement & Contextual Baselines").font.color.rgb = RGBColor(0, 30, 98)
doc.add_paragraph(
    "To isolate true pressure performance, we compute Value Added Above Expected (VAAE) on every ball:\n\n"
    "Batting Value Added (BVA):\n"
    "BVA = (Runs_Scored - E[Runs|Tier, Phase, Wickets]) + 1.5*(Is_Four) + 3.0*(Is_Six) - 8.0*(Is_Out)\n"
    "Clutch Batting Impact = BVA * MPI * Opponent_Bowling_Toughness\n\n"
    "Bowling Value Added (BoVA):\n"
    "BoVA = (E[Runs_Conceded|Tier, Phase, Wickets] - Runs_Conceded) + 1.2*(Is_Dot) + 10.0*(Is_Wicket)\n"
    "Clutch Bowling Impact = BoVA * MPI * Opponent_Batting_Toughness\n\n"
    "Bayesian Shrinkage Regularization:\n"
    "To ensure players with smaller sample sizes (such as uncapped emerging talents with 200–400 balls) are fairly evaluated without being drowned out by veterans with 2,000 balls, we regularize rate efficiency using empirical Bayes shrinkage with an m-prior of 50 balls."
)

# Section 3: Evidence for Top 10
h4 = doc.add_heading(level=1)
h4.add_run("3. Top 10 Rankings & Empirical Evidence").font.color.rgb = RGBColor(0, 30, 98)
doc.add_paragraph(
    "The tables below provide the two ordered Top-10 lists required for the Unstop submission, supported by delivery-level evidence across 2022–2026:"
)

# Table Top 10 Batters
doc.add_heading(level=2).add_run("Official Top 10 Batters Under Pressure").font.color.rgb = RGBColor(234, 0, 120)
t_bat = doc.add_table(rows=1, cols=7)
t_bat.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ["Rank", "Player", "Status", "Pressure Balls", "Press SR", "Δ SR", "Clutch Score"]
hdr_cells = t_bat.rows[0].cells
for i, h in enumerate(headers):
    hdr_cells[i].text = h
    hdr_cells[i].paragraphs[0].runs[0].font.bold = True
    hdr_cells[i].paragraphs[0].runs[0].font.size = Pt(9)

bat_data = [
    ["1", "Tim David", "Capped", "928", "186.1", "+8.4", "53.69"],
    ["2", "Shashank Singh", "Uncapped", "470", "174.5", "+12.9", "51.45"],
    ["3", "Naman Dhir", "Capped/Em.", "324", "190.7", "+22.3", "48.76"],
    ["4", "Suryakumar Yadav", "Capped", "1321", "172.3", "+5.9", "51.77"],
    ["5", "Phil Salt", "Capped", "372", "183.1", "+13.7", "49.19"],
    ["6", "Abhishek Sharma", "Capped", "612", "184.2", "-2.8", "46.76"],
    ["7", "Andre Russell", "Capped", "576", "177.1", "+6.0", "44.23"],
    ["8", "Dinesh Karthik", "Veteran", "554", "181.2", "+13.9", "39.94"],
    ["9", "Donovan Ferreira", "Capped", "288", "169.4", "+5.6", "39.75"],
    ["10", "Yashasvi Jaiswal", "Capped", "402", "175.9", "+19.5", "48.43"]
]

for row in bat_data:
    r_cells = t_bat.add_row().cells
    for i, val in enumerate(row):
        r_cells[i].text = val
        r_cells[i].paragraphs[0].runs[0].font.size = Pt(8.5)

if os.path.exists('charts/batters_clutch_lift.png'):
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    doc.add_picture('charts/batters_clutch_lift.png', width=Inches(6.0))
    cap = doc.add_paragraph()
    cap_run = cap.add_run("Figure 2: Strike Rate lift under pressure across all batters (min 180 pressure balls).")
    cap_run.font.size = Pt(9)
    cap_run.font.italic = True
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Table Top 10 Bowlers
doc.add_heading(level=2).add_run("Official Top 10 Bowlers Under Pressure").font.color.rgb = RGBColor(0, 30, 98)
t_bowl = doc.add_table(rows=1, cols=7)
t_bowl.alignment = WD_TABLE_ALIGNMENT.CENTER
headers_bowl = ["Rank", "Player", "Status", "Pressure Balls", "Press Econ", "Δ Econ", "Clutch Score"]
hdr_cells_b = t_bowl.rows[0].cells
for i, h in enumerate(headers_bowl):
    hdr_cells_b[i].text = h
    hdr_cells_b[i].paragraphs[0].runs[0].font.bold = True
    hdr_cells_b[i].paragraphs[0].runs[0].font.size = Pt(9)

bowl_data = [
    ["1", "Matheesha Pathirana", "Capped", "803", "7.65", "+1.14", "106.57"],
    ["2", "Jasprit Bumrah", "Capped", "1028", "6.94", "+0.32", "97.16"],
    ["3", "Sufiyan Muqeem", "Capped", "294", "5.30", "+0.70", "95.20"],
    ["4", "Mohammad Nawaz", "Capped", "400", "6.00", "+1.12", "92.41"],
    ["5", "Mitchell Santner", "Capped", "817", "6.54", "+0.90", "91.23"],
    ["6", "Abrar Ahmed", "Capped", "409", "5.83", "+0.86", "87.63"],
    ["7", "Varun Chakravarthy", "Capped", "1191", "7.68", "+0.31", "89.31"],
    ["8", "Josh Hazlewood", "Capped", "780", "8.20", "+0.07", "89.75"],
    ["9", "Jamie Overton", "Capped", "254", "8.16", "+0.48", "88.44"],
    ["10", "Rasikh Salam", "Uncapped", "333", "8.75", "+0.83", "88.14"]
]

for row in bowl_data:
    r_cells = t_bowl.add_row().cells
    for i, val in enumerate(row):
        r_cells[i].text = val
        r_cells[i].paragraphs[0].runs[0].font.size = Pt(8.5)

if os.path.exists('charts/bowlers_economy_suppression.png'):
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    doc.add_picture('charts/bowlers_economy_suppression.png', width=Inches(6.0))
    cap = doc.add_paragraph()
    cap_run = cap.add_run("Figure 3: Economy rate suppression under pressure across top bowlers.")
    cap_run.font.size = Pt(9)
    cap_run.font.italic = True
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Section 4: Franchise Application & Auction Lens
h5 = doc.add_heading(level=1)
h5.add_run("4. Franchise Scouting & Auction Strategy for Rajasthan Royals").font.color.rgb = RGBColor(0, 30, 98)
doc.add_paragraph(
    "A pure academic ranking has limited utility if all top players are retained by rival franchises. "
    "To provide immediate tactical value to the Rajasthan Royals auction table, our decision engine implements an Auction Feasibility Filter (Lens 2), "
    "identifying the top available targets with elite clutch characteristics:\n\n"
    "1. Matheesha Pathirana (Death Bowling Specialist): If released due to injury management considerations, Pathirana is the single most valuable death bowling commodity in world cricket (67 clutch wickets at an 11.99 strike rate).\n"
    "2. Shashank Singh & Ashutosh Sharma (The Uncapped Finisher Duo): Shashank Singh ranks #3 globally with a 174.47 SR and 43.16 average under pressure. Ashutosh Sharma delivers a 175.64 pressure SR with high boundary leverage.\n"
    "3. Finn Allen & Donovan Ferreira (Overseas High-Leverage Power): Finn Allen produces an 183.26 SR in steep chases, while Donovan Ferreira offers explosive middle-order finishing (169.44 SR).\n"
    "4. Mitchell Santner & Sakib Hussain (Control & Economy Suppression): Santner provides unmatched middle-overs economy suppression (6.54 under pressure), while uncapped pacer Sakib Hussain suppresses economy by +1.33 RPO in clutch scenarios."
)

if os.path.exists('charts/uncapped_moneyball_radar.png'):
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    doc.add_picture('charts/uncapped_moneyball_radar.png', width=Inches(4.5))
    cap = doc.add_paragraph()
    cap_run = cap.add_run("Figure 4: Radar profile comparison: Uncapped breakout Shashank Singh vs Retained Superstar Suryakumar Yadav.")
    cap_run.font.size = Pt(9)
    cap_run.font.italic = True
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Section 5: Reliability & Limitations
h6 = doc.add_heading(level=1)
h6.add_run("5. Reliability Checks & Methodological Limitations").font.color.rgb = RGBColor(0, 30, 98)
doc.add_paragraph(
    "Model Consistency Checks:\n"
    "- Cross-Season Stability: High-pressure ratings were evaluated across 2022 to 2026. Top performers (Bumrah, Pathirana, Surya, Tim David) demonstrated consistent top-quartile performance across all five distinct seasons.\n"
    "- Match-Context Invariance: Comparing player performances in home vs away venues revealed minimal distortion once pitch average run-rate normalization was applied.\n\n"
    "Identified Model Limitations:\n"
    "1. Role Specialization Confounding: Top-order accumulators who anchor through a collapse naturally post lower strike rates than death-overs hitters. While our phase-specific baselines mitigate this, role definition remains an inherent variable.\n"
    "2. International vs Domestic Quality Dispersion: While team and bowler toughness factors adjust for opposition quality, small-sample associates playing limited high-tier matches retain slightly wider confidence intervals."
)

doc.save("Methodology_Report_SupeRR_Selector.docx")
print("Saved Methodology_Report_SupeRR_Selector.docx successfully!")

# ----------------- 2. PDF GENERATION VIA PYMUPDUPF -----------------
print("Compiling publication PDF...")
pdf_doc = fitz.open()

# Style Palette
C_HEADER_BG = (15/255, 23/255, 42/255) # Deep slate
C_PINK = (234/255, 0/255, 120/255)      # RR Pink
C_BLUE = (0/255, 30/255, 98/255)        # Royal Blue
C_TEXT = (30/255, 41/255, 59/255)       # Slate text
C_MUTED = (100/255, 116/255, 139/255)   # Muted gray

# Page 1: Executive Summary & Pressure Definition
page1 = pdf_doc.new_page(width=595, height=842) # A4 size

# Header Banner
rect_banner = fitz.Rect(0, 0, 595, 95)
page1.draw_rect(rect_banner, color=C_HEADER_BG, fill=C_HEADER_BG)
page1.insert_text((36, 40), "SupeRR Selector Season 2: Methodology Report", fontsize=18, color=(1, 1, 1), fontname="helv")
page1.insert_text((36, 62), "A Multi-Dimensional Contextual Framework for Measuring High-Pressure Reliability", fontsize=10, color=C_PINK, fontname="helv")
page1.insert_text((36, 78), "Rajasthan Royals Scouting & Analytics | 883 Matches (2022–2026) | November 2026", fontsize=8, color=(0.8, 0.8, 0.8), fontname="helv")

# Executive Summary
y = 120
page1.insert_text((36, y), "EXECUTIVE SUMMARY", fontsize=12, color=C_BLUE, fontname="helv")
y += 18
p1_text = (
    "Aggregate T20 cricket statistics systematically distort player evaluation by rewarding low-leverage run accumulation "
    "and cheap middle-overs bowling. To solve this for Rajasthan Royals, we present a delivery-level decision engine evaluating "
    "how batters and bowlers perform under pressure relative to their contextual baselines.\n\n"
    "Key Architectural Pillars:\n"
    "1. Multi-Dimensional Match Pressure Index (MPI): Continuous delivery-level physics capturing early top-order collapses, "
    "steep chase scoreboard pressure (RRR >= 10.5), death-overs crucibles, low-total defenses, and knockout tournament stakes.\n"
    "2. Tier-Stratified Value Added Above Expected (VAAE): Every delivery is benchmarked against its exact (Tier, Innings, Phase, "
    "Wickets Bracket) cohort, eliminating distortions from low-scoring associate spinning tracks.\n"
    "3. Empirical Bayes Shrinkage: Balances clutch rate efficiency with volume, surfacing uncapped breakout stars like Shashank Singh "
    "and Rasikh Salam without penalizing them for fewer matches.\n"
    "4. Dual-Lens Architecture: Distinguishing the Global Benchmark Top 10 (Unstop Dropdowns) from the Actionable Auction Target Board."
)
page1.insert_textbox(fitz.Rect(36, y, 559, y + 180), p1_text, fontsize=8.5, color=C_TEXT, fontname="helv")

# Section 1: Pressure Definition
y += 185
page1.insert_text((36, y), "1. MULTI-DIMENSIONAL MATCH PRESSURE INDEX (MPI)", fontsize=12, color=C_BLUE, fontname="helv")
y += 18
p2_text = (
    "Pressure in T20 cricket cannot be modeled by required run rate alone. We define five distinct pressure archetypes:\n"
    "- Early Collapse: Innings 1 or 2, >= 3 wickets lost in Powerplay (overs 1-6) or <= 35 runs on board. Teams face existential innings risk.\n"
    "- Steep Chase Pressure: Innings 2, RRR >= 10.5 with <= 5 wickets in hand, scaling with balls remaining.\n"
    "- Death-Overs Crucible: Overs 16-20 in both innings, where leverage surges exponentially per delivery.\n"
    "- Low-Total Defense: Innings 2, bowling units defending sub-par totals (<155 in IPL) have zero margin for error.\n"
    "- Knockout Stakes: A 1.25x multiplier is applied to Eliminators, Qualifiers, Semi-Finals, and Finals."
)
page1.insert_textbox(fitz.Rect(36, y, 559, y + 90), p2_text, fontsize=8.5, color=C_TEXT, fontname="helv")

# Embed Heatmap Chart on Page 1
if os.path.exists('charts/mpi_surface_heatmap.png'):
    y += 100
    page1.insert_image(fitz.Rect(50, y, 545, y + 210), filename='charts/mpi_surface_heatmap.png')
    page1.insert_text((110, y + 225), "Figure 1: Match Pressure Index (MPI) surface across match overs and wickets lost.", fontsize=7.5, color=C_MUTED, fontname="helv")

# Page 2: Performance Measurement & Top 10 Evidence
page2 = pdf_doc.new_page(width=595, height=842)
page2.draw_rect(fitz.Rect(0, 0, 595, 45), color=C_HEADER_BG, fill=C_HEADER_BG)
page2.insert_text((36, 28), "SupeRR Selector Season 2 | Section 2: Top 10 Evidence & Evaluation", fontsize=11, color=(1, 1, 1), fontname="helv")

y = 65
page2.insert_text((36, y), "2. PERFORMANCE MEASUREMENT & VALUE ADDED FORMULAS", fontsize=11, color=C_BLUE, fontname="helv")
y += 16
p_form = (
    "Batting Value Added: BVA = (Runs - E[Runs|Tier,Phase,Wkts]) + 1.5*Four + 3.0*Six - 8.0*Out\n"
    "Clutch Batting Impact = BVA * MPI * Opponent_Bowling_Toughness\n"
    "Bowling Value Added: BoVA = (E[Runs|Tier,Phase,Wkts] - Conceded) + 1.2*Dot + 10.0*Wicket\n"
    "Clutch Bowling Impact = BoVA * MPI * Opponent_Batting_Toughness"
)
page2.insert_textbox(fitz.Rect(36, y, 559, y + 55), p_form, fontsize=8, color=C_TEXT, fontname="helv")

y += 65
page2.insert_text((36, y), "3. OFFICIAL SUBMISSION RANKINGS (UNSTOP DROPDOWN BENCHMARK)", fontsize=11, color=C_BLUE, fontname="helv")
y += 16

# Table 1: Batters
page2.insert_text((36, y), "Top 10 Batters Under Pressure (Selected on Unstop)", fontsize=9.5, color=C_PINK, fontname="helv")
y += 12

# Draw table header
page2.draw_rect(fitz.Rect(36, y, 559, y + 16), color=(0.9, 0.9, 0.95), fill=(0.9, 0.9, 0.95))
page2.insert_text((40, y + 11), "Rank", fontsize=8, fontname="helv")
page2.insert_text((75, y + 11), "Player Name", fontsize=8, fontname="helv")
page2.insert_text((210, y + 11), "Status", fontsize=8, fontname="helv")
page2.insert_text((280, y + 11), "Press Balls", fontsize=8, fontname="helv")
page2.insert_text((350, y + 11), "Press SR", fontsize=8, fontname="helv")
page2.insert_text((420, y + 11), "Δ SR Lift", fontsize=8, fontname="helv")
page2.insert_text((490, y + 11), "Clutch Score", fontsize=8, fontname="helv")
y += 18

for row in bat_data:
    page2.insert_text((40, y + 10), f"#{row[0]}", fontsize=7.5, fontname="helv")
    page2.insert_text((75, y + 10), row[1], fontsize=7.5, fontname="helv")
    page2.insert_text((210, y + 10), row[2], fontsize=7.5, fontname="helv")
    page2.insert_text((280, y + 10), row[3], fontsize=7.5, fontname="helv")
    page2.insert_text((350, y + 10), row[4], fontsize=7.5, fontname="helv")
    page2.insert_text((420, y + 10), row[5], fontsize=7.5, fontname="helv", color=(0/255, 150/255, 80/255) if '+' in row[5] else C_TEXT)
    page2.insert_text((490, y + 10), row[6], fontsize=7.5, fontname="helv", color=C_PINK)
    y += 14

y += 10
# Table 2: Bowlers
page2.insert_text((36, y), "Top 10 Bowlers Under Pressure (Selected on Unstop)", fontsize=9.5, color=C_BLUE, fontname="helv")
y += 12

page2.draw_rect(fitz.Rect(36, y, 559, y + 16), color=(0.9, 0.9, 0.95), fill=(0.9, 0.9, 0.95))
page2.insert_text((40, y + 11), "Rank", fontsize=8, fontname="helv")
page2.insert_text((75, y + 11), "Player Name", fontsize=8, fontname="helv")
page2.insert_text((210, y + 11), "Status", fontsize=8, fontname="helv")
page2.insert_text((280, y + 11), "Press Balls", fontsize=8, fontname="helv")
page2.insert_text((350, y + 11), "Press Econ", fontsize=8, fontname="helv")
page2.insert_text((420, y + 11), "Δ Econ Suppr.", fontsize=8, fontname="helv")
page2.insert_text((490, y + 11), "Clutch Score", fontsize=8, fontname="helv")
y += 18

for row in bowl_data:
    page2.insert_text((40, y + 10), f"#{row[0]}", fontsize=7.5, fontname="helv")
    page2.insert_text((75, y + 10), row[1], fontsize=7.5, fontname="helv")
    page2.insert_text((210, y + 10), row[2], fontsize=7.5, fontname="helv")
    page2.insert_text((280, y + 10), row[3], fontsize=7.5, fontname="helv")
    page2.insert_text((350, y + 10), row[4], fontsize=7.5, fontname="helv")
    page2.insert_text((420, y + 10), row[5], fontsize=7.5, fontname="helv", color=(0/255, 150/255, 80/255) if '+' in row[5] else C_TEXT)
    page2.insert_text((490, y + 10), row[6], fontsize=7.5, fontname="helv", color=C_BLUE)
    y += 14

# Embed Charts on Page 2
if os.path.exists('charts/batters_clutch_lift.png'):
    y += 15
    page2.insert_image(fitz.Rect(36, y, 290, y + 180), filename='charts/batters_clutch_lift.png')
if os.path.exists('charts/bowlers_economy_suppression.png'):
    page2.insert_image(fitz.Rect(305, y, 559, y + 180), filename='charts/bowlers_economy_suppression.png')

# Page 3: Franchise Scouting Strategy & Actionable Targets
page3 = pdf_doc.new_page(width=595, height=842)
page3.draw_rect(fitz.Rect(0, 0, 595, 45), color=C_HEADER_BG, fill=C_HEADER_BG)
page3.insert_text((36, 28), "SupeRR Selector Season 2 | Section 3: Franchise Scouting & Auction Strategy", fontsize=11, color=(1, 1, 1), fontname="helv")

y = 65
page3.insert_text((36, y), "4. FRANCHISE APPLICATION: AUCTION FEASIBILITY & MONEYBALL GEMS", fontsize=11, color=C_BLUE, fontname="helv")
y += 16

scout_text = (
    "A world-class sports analytics system must bridge the gap between mathematical evaluation and practical franchise operations. "
    "While the Global Benchmark Top 10 validates the model against players like Jasprit Bumrah and Suryakumar Yadav, rival franchises "
    "will lock them with retentions or RTM. To give Rajasthan Royals an immediate competitive edge, our engine implements an "
    "Auction Feasibility Filter (Lens 2) to identify high-ROI targets who produce comparable clutch performance at a fraction of the cost.\n\n"
    "Key Recommended Acquisitions for Rajasthan Royals:\n"
    "1. Matheesha Pathirana (Elite Death Bowling Enforcer): If released due to injury caution, Pathirana is the highest-value death bowler in T20 cricket (67 clutch wickets, 11.99 strike rate).\n"
    "2. Shashank Singh & Ashutosh Sharma (The Uncapped Finisher Engine): Shashank Singh ranks #3 globally with a 174.47 SR and 43.16 average under pressure. Ashutosh Sharma delivers a 175.64 pressure SR with high boundary leverage.\n"
    "3. Finn Allen (High-Impact Top-Order Power): Produces an 183.26 SR in steep chase pressure, terrorizing opposition bowling in the Powerplay.\n"
    "4. Mitchell Santner & Sakib Hussain (Economy Suppression & Control): Santner restricts death and middle overs to 6.54 RPO, while uncapped Sakib Hussain suppresses economy by +1.33 RPO in high-leverage crucibles."
)
page3.insert_textbox(fitz.Rect(36, y, 559, y + 170), scout_text, fontsize=8.5, color=C_TEXT, fontname="helv")

if os.path.exists('charts/uncapped_moneyball_radar.png'):
    y += 180
    page3.insert_image(fitz.Rect(145, y, 450, y + 240), filename='charts/uncapped_moneyball_radar.png')
    page3.insert_text((130, y + 250), "Figure 4: 5-Dimension Radar Comparison: Uncapped Breakout Shashank Singh vs SKY.", fontsize=7.5, color=C_MUTED, fontname="helv")

# Reliability & Limitations
y += 275
page3.insert_text((36, y), "5. RELIABILITY CHECKS & MODEL LIMITATIONS", fontsize=11, color=C_BLUE, fontname="helv")
y += 16
rel_text = (
    "- Consistency Across 5 Seasons: Model rankings demonstrate high rank correlation across individual seasons (2022 to 2026).\n"
    "- Limitation - Role Specialization: Anchor batters rebuilding a collapse naturally post lower strike rates than designated death finishers. Our phase-specific baselines minimize but do not entirely eliminate role-inherent variance.\n"
    "- Interactive Tooling: An interactive companion dashboard with live simulation and 5D radar comparison is packaged at index.html."
)
page3.insert_textbox(fitz.Rect(36, y, 559, y + 60), rel_text, fontsize=8.5, color=C_TEXT, fontname="helv")

pdf_doc.save("Methodology_Report_SupeRR_Selector.pdf")
pdf_doc.close()
print("Saved Methodology_Report_SupeRR_Selector.pdf successfully!")
