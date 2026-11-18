# 🏏 SupeRR Selector Season 2 — Rajasthan Royals Analytics Hackathon
### Context-Aware Player Pressure Intelligence & Franchise Auction War Room System

[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61DAFB?logo=react&logoColor=black)](https://reactjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Python](https://img.shields.io/badge/Engine-Python_3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Deliverables](https://img.shields.io/badge/Official_Report-PDF_%2B_DOCX-EA1A7F)](./Methodology_Report_SupeRR_Selector.pdf)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Official Competition Deliverables:**
> * 📄 **PDF Methodology Report:** [`Methodology_Report_SupeRR_Selector.pdf`](./Methodology_Report_SupeRR_Selector.pdf) (7-page publication document)
> * 📝 **DOCX Methodology Report:** [`Methodology_Report_SupeRR_Selector.docx`](./Methodology_Report_SupeRR_Selector.docx) (Editable Word document)
> * 📑 **Markdown Specification:** [`METHODOLOGY_REPORT.md`](./METHODOLOGY_REPORT.md)
> * 💻 **Interactive React Dashboard:** [`rr-selector-ui`](./rr-selector-ui)

---

## 📌 Executive Summary & Philosophy

Traditional T20 cricket metrics like unadjusted Strike Rate (SR) and Economy Rate (ER) treat a boundary in a blowout game identically to a boundary required at 12.0 RRR in the final over of an IPL playoff. 

Built for the **Rajasthan Royals SupeRR Selector Season 2 Hackathon**, this project introduces a **Five-Dimensional Pressure Intelligence System**. It evaluates **what a player achieved, how difficult the situation was, what was expected of them, and how consistently they delivered** across **200,999 deliveries** and **867 matches** (2022–2026).

Furthermore, we connect this model directly to Rajasthan Royals' live franchise reality: evaluating the **latest Retention & Release roster**, addressing the tactical void left by releasing **Shimron Hetmyer** and key seamers, respecting the **₹27.05 Cr purse** and **3 overseas slots**, and identifying target recruits from rival team releases (with Travis Head excluded due to season unavailability).

---

## 🔬 The Five-Dimensional Mathematical Framework

1. **Dimension A: Continuous Pressure Intensity ($P \in [0.05, 1.0]$)**  
   Replaces arbitrary death-over filters with a real-time sigmoid leverage function driven by Required Run Rate (RRR), balls left, wickets in hand, collapse stress, and a 1.15x playoff knockout multiplier.

2. **Dimension B: Performance Above Expectation (PAE)**  
   Measures actual runs and dismissals relative to contextual expected baselines conditioned on $(Phase, WicketsInHand, PressureBracket)$ calibrated across 200k+ balls. Wickets carry an empirical penalty/reward of $\lambda_w = 4.5$ runs.

3. **Dimension C: Empirical Bayesian Shrinkage ($K=75$ balls)**  
   Protects against small-sample flukes by regularizing clutch efficiency toward the population mean, rewarding sustained match-winning reliability over isolated heroic cameos.

4. **Dimension D: Multi-Scenario Specialization Profiles**  
   Dissects player reliability across 4 tactical roles: Chase Finishers, Death Overs Specialists, Collapse Rescuers, and Defensive Anchors.

5. **Dimension E: Opposition & Tournament Context**  
   Adjusts delivery impact based on bowler and batter quality ratings and competition tiers (IPL vs T20I).

---

## 🏆 Global Top 10 Leaderboards (2022–2026)

### Top 10 Batters Under Pressure
| Rank | Player Name | Clutch Rating | HP Balls | HP Strike Rate | Boundary % | Total Pressure PAE |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **1** | **Tim David** | **100.0** | 621 | 181.0 | 25.1% | **+239.2** |
| **2** | **Rinku Singh** | **92.6** | 610 | 174.3 | 24.4% | **+205.4** |
| **3** | **Tilak Varma** | **87.2** | 539 | 183.1 | 26.2% | **+174.0** |
| **4** | **Tristan Stubbs** | **86.6** | 429 | 185.8 | 26.8% | **+159.8** |
| **5** | **Suryakumar Yadav** | **82.4** | 319 | 215.0 | 32.6% | **+132.7** |
| **6** | **Rovman Powell** *(RR Retained)* | **81.1** | 565 | 172.0 | 23.9% | **+151.1** |
| **7** | **Romario Shepherd** | **77.9** | 552 | 156.2 | 21.0% | **+136.3** |
| **8** | **Heinrich Klaasen** | **76.2** | 436 | 187.4 | 28.0% | **+120.3** |
| **9** | **Naman Dhir** *(Uncapped Gem)* | **73.4** | 204 | 200.0 | 29.4% | **+92.5** |
| **10** | **Shashank Singh** *(Uncapped Gem)* | **71.7** | 282 | 168.8 | 23.8% | **+92.8** |

### Top 10 Bowlers Under Pressure
| Rank | Player Name | Clutch Rating | HP Balls | HP Economy | Clutch Wickets | Dot Ball % |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **1** | **Jasprit Bumrah** | **100.0** | 546 | **7.02** | 40 | 39.2% |
| **2** | **Matheesha Pathirana** *(Auction Target)* | **92.0** | 586 | **7.52** | 48 | 38.6% |
| **3** | **Sunil Narine** | **86.4** | 280 | **6.24** | 21 | 42.1% |
| **4** | **Kuldeep Yadav** | **85.0** | 328 | **7.37** | 31 | 37.8% |
| **5** | **Wanindu Hasaranga** | **78.5** | 323 | **7.93** | 36 | 36.5% |
| **6** | **Rashid Khan** | **74.3** | 578 | **8.09** | 54 | 34.4% |
| **7** | **Abrar Ahmed** | **74.1** | 181 | **5.10** | 12 | 47.0% |
| **8** | **Noor Ahmad** | **72.9** | 267 | **7.21** | 22 | 36.7% |
| **9** | **Shaheen Afridi** | **69.7** | 267 | **7.39** | 24 | 37.5% |
| **10** | **Mustafizur Rahman** | **67.1** | 631 | **8.09** | 38 | 35.0% |

> *Note on Nationality & Franchise Eligibility:* Pakistani players (e.g., Sufiyan Muqeem, Shaheen Afridi, Abrar Ahmed) appear in analytical benchmarks due to international T20I fixtures, but are ineligible for IPL auctions. For franchise recruitment, eligible targets such as **Wanindu Hasaranga** (LSG Release) and **Mitchell Santner** are prioritized on the Rajasthan Royals Auction Board.

---

## 🎯 Rajasthan Royals Auction Strategy ("SupeRR Selector War Room")

* **Purse Remaining:** **₹27.05 Cr** | **Slots Open:** **6 (Max 3 Overseas)**
* **Tactical Gaps:** Replaced Shimron Hetmyer (death finisher) and built death bowling depth alongside Sandeep Sharma.
* **Constraints Enforced:** Travis Head (unavailable), Ajinkya Rahane & MS Dhoni (retired), Pakistani players (ineligible).

### Recommended Auction Target Basket (₹27.00 Cr Spent)
1. **Matheesha Pathirana (✈️ Overseas) — ₹10.50 Cr:** #2 in the world under pressure; premier death pacer to partner Sandeep Sharma.
2. **Nehal Wadhera (🇮🇳 Indian) — ₹5.50 Cr:** Young clutch left-hand finisher; direct Hetmyer replacement under steep RRR.
3. **M Shahrukh Khan (🇮🇳 Indian) — ₹4.00 Cr:** Overs 17–20 power accelerator against high pace.
4. **Akash Madhwal (🇮🇳 Indian) — ₹3.50 Cr:** Proven playoff death yorker weapon.
5. **Blessing Muzarabani (✈️ Overseas) — ₹2.50 Cr:** Tall hit-the-deck pacer; high dot-ball suppression.
6. **Mahipal Lomror (🇮🇳 Indian) — ₹1.00 Cr:** Ex-RR middle-order spin basher.

---

## 🚀 Quickstart & Setup

### 1. Run the Analytics Engine
```bash
python3 scratch/compute_pressure_engine.py
```
*Processes ball-by-ball deliveries, computes PAE & Bayesian regularizations, and exports `pressure_analytics.json`.*

### 2. Launch the React Web Dashboard
```bash
cd rr-selector-ui
npm install
npm run dev
```
*Open `http://localhost:3000` to interact with the live Auction War Room simulator, leaderboards, and head-to-head matchup comparisons.*

### 3. Generate Methodology Reports
```bash
python3 build_masterpiece_report.py   # Compiles publication PDF with text wrapping
python3 generate_docx_report.py       # Compiles editable Word DOCX
```

---

## 📄 Repository Structure
```
├── README.md                         # Main repository guide
├── METHODOLOGY_REPORT.md             # Comprehensive hackathon methodology report
├── Methodology_Report_SupeRR_Selector.pdf # Publication-grade 7-page PDF report (1.2 MB)
├── Methodology_Report_SupeRR_Selector.docx # Synchronized Word document
├── build_masterpiece_report.py       # PyMuPDF reporting engine with text wrapping
├── generate_docx_report.py           # Python-docx reporting pipeline
├── charts/                           # High-resolution visual analytics charts
└── rr-selector-ui/                   # React 18 + Vite + Tailwind CSS frontend
    ├── src/
    │   ├── App.jsx                   # Interactive auction simulator & dashboards
    │   └── data/pressure_analytics.json # Precomputed data payload
    └── dist/                         # Production static build ready for deployment
```

---

## 👥 Authors
* **Rajasthan Royals SupeRR Selector Season 2 Hackathon Team**
