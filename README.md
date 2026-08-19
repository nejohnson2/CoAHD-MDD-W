# The affordability–quality gap: MDD-W vs. the cost of a healthy diet

Quick quantitative note. Across countries with both indicators, how much of women's dietary diversity
(MDD-W) is explained by the share of the population unable to afford a healthy diet (CoAHD), and which
countries deviate most from that relationship? The residual is a proxy for the *non-price* constraint
(markets, culture, retail environment, information) — the thing SOFI 2026 says cost reduction alone won't fix.

## Data

| Input | Source | Notes |
|---|---|---|
| % unable to afford a healthy diet (PUA), cost of a healthy diet | FAOSTAT domain **CAHD**, July 2026 (SOFI) release, bulk zip | 149 countries, 2017–2025 |
| MDD-W (% women 15–49 achieving minimum dietary diversity) | FAOSTAT domain **SDGB**, indicator **2.2.4**, item `24049-F-Y15T49T` (national) | 79 countries, 106 country-years, 2016–2025. Provenance per row is in the FAOSTAT `Note` column: Global Diet Quality Project (Gallup World Poll), DHS, or a national survey |
| Region, income group, GDP per capita PPP | World Bank API | |
| MDD-W survey coverage metadata | `reference/mddw_survey_coverage.csv`, hand-compiled from Gallup *DQQ Country Data Set Details 2021–2024* and FAOSTAT notes | fieldwork dates, N, design effect, mode, % population excluded → flags: exclusion ≥10 %, telephone frame, unverified national coverage |

The standalone FAOSTAT `MDDW` domain has only ~25 surveys; the SDG 2.2.4 series is the SOFI 2026 one.
Bulk URLs are listed at `https://bulks-faostat.fao.org/production/datasets_E.json`.

**Panel: 66 countries** (MDD-W's most recent survey per country, CoAHD matched to the same year; all 66 match
exactly, no ±2-year fallback was needed). 13 MDD-W countries have no CoAHD affordability estimate and are
dropped — every drop is listed in `results/join_log.json`.

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## Reproduce

```bash
.venv/bin/python scripts/01_download.py     # -> data/raw/  (FAOSTAT zips + World Bank JSON)
.venv/bin/python scripts/02_build_panel.py  # -> data/processed/panel.csv, results/join_log.json
.venv/bin/python scripts/03_fit.py          # -> results/fit_summary.json, residuals.csv, robustness.csv
.venv/bin/python scripts/04_figure.py       # -> figures/  (reads results/ only)
```

Notebooks in `notebooks/` are for manual inspection at each stage (raw → panel → results); they are not part
of the pipeline. Seed = 42 for the bootstrap.

## Method

Headline: OLS `MDD-W = a + b·PUA`, HC3 SEs, 5 000-draw country bootstrap for slope and R².
Residual = observed − predicted MDD-W, read as "higher/lower than predicted given unaffordability" — **not** performance.
Quadrants = PUA split at its median (49.6 %) × residual sign. "Notable" = |externally studentized residual| > 1;
"unusual" = outside the 95 % prediction interval. Leave-one-country-out residuals and CV R² are also computed.

Robustness (`results/robustness.csv`): fractional-logit GLM; natural cubic spline; MDD-W ~ log GDP; PUA + log GDP;
PUA + region fixed effects; PUA + survey-source dummies; GDQP-only; DHS/national-only; precision-weighted WLS
(approximate binomial SE of MDD-W); latest-year PUA; drop Cook's D > 4/n; exclude flagged surveys; source-priority
panel (DHS/national preferred over Gallup, `data/processed/panel_source_priority.csv`); LOO-CV.

## Findings (n = 66)

- **Slope −0.71** MDD-W points per point of unaffordability (95 % bootstrap CI −0.82 to −0.60), **R² = 0.65**
  (CI 0.50–0.78), LOO-CV R² = 0.63. Residual SD ≈ 14 points. Only 3 countries outside the 95 % prediction
  interval: Indonesia, Armenia (above), Burkina Faso (below — flagged: SMART survey, coverage unverified).
- **Region fixed effects** raise R² to 0.78 and cut the PUA slope to −0.39; Sub-Saharan Africa sits ~22 pts below
  the reference at the same PUA. Some global outliers are regional (Guatemala, Costa Rica, Peru, Nepal); others hold
  under both benchmarks (Indonesia, Armenia, Kyrgyzstan, Uganda, Iraq above; Malaysia, Lesotho, Mongolia below).
- Affordability is not just income in disguise: with log GDP per capita in the model, PUA keeps a coefficient of
  −0.44 (p < 1e-4) and log GDP adds only 6 pp of R².
- **MDD-W above prediction:** Indonesia (+43), Armenia (+31), Kyrgyzstan (+24), Lao PDR (+21, flagged: 14 % excluded),
  Guatemala (+20), Uganda (+19), Iraq, Algeria (flagged: phone), Costa Rica, Iran (flagged: phone).
- **MDD-W below prediction:** Burkina Faso (−29, flagged), Malaysia (−28), Comoros (−26), Nepal (−21), Lesotho (−20),
  Guinea (−19), Ethiopia, Côte d'Ivoire, Liberia, Mali, Tanzania, Jordan.
- **21 of 66 surveys carry a coverage flag.** Excluding them: slope −0.68, residual ranking ρ = 0.998 with headline.
- **Survey source matters.** Where a country has both, Gallup/GDQP estimates run 20–30 points above DHS —
  consistent with Hanley-Cook et al. (2025, *BMC Nutrition*), who find the two platforms are not calibratable.
  In the pooled model DHS-sourced points sit 12.8 points lower at the same PUA (p = 0.002). The slope survives
  (−0.62; −0.69 in DHS/national-only, n=20) and rankings are stable (ρ = 0.92), but individual DHS/Other countries
  move (Jordan, Senegal, Kenya). Treat cross-source residuals as approximate.

- **Cost level carries no signal; affordability does.** The cost of a healthy diet in PPP$/day has zero correlation with MDD-W (R² = 0.00) and adds nothing next to PUA — it is the price *relative to income* that matters.

Figures: `figures/fig1_affordability_quality_gap.*` (the quadrant plot), `figures/fig2_residual_league_table.*`.

## Caveats

- MDD-W is women 15–49 only (a proxy for micronutrient adequacy); PUA is a total-population measure. Not the same people.
- Precision weights use assumed effective sample sizes (Gallup ≈ 0.45·N/deff; DHS 10k; other 2k), not published SEs.
- Residuals are descriptive benchmarks, not performance or causal effects.
- Cross-sectional, one observation per country, no causal claim.
- CoAHD is a modelled indicator (least-cost healthy diet vs. income distribution); its own assumptions carry through.
- Sample skews to low- and middle-income countries (only 3 high-income), so the "affordable" half is relative
  (below the median PUA of ~50 %).
- Survey-mode heterogeneity in MDD-W (above).

## Layout

```
scripts/     01_download.py  02_build_panel.py  03_fit.py  04_figure.py
reference/   mddw_survey_coverage.csv  (hand-compiled survey metadata; committed)
notebooks/   01_raw_eda  02_panel_eda  03_results_review  04_regression_analysis (all models, one per cell)
data/        raw/ (gitignored) processed/ (gitignored)
results/     fit_summary.json  residuals.csv  robustness.csv  join_log.json
figures/
```
