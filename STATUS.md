# STATUS — 2026-08-19

## State
Pipeline complete and re-run end to end after the measurement-robustness pass: download → panel (66 countries, +
source-priority variant, + survey coverage flags) → OLS fit with 16 robustness rows → 2 figures. Four executed
notebooks (raw EDA, panel EDA, results review, regression analysis). writeup.md revised (restrained wording,
region FE, flags, Hanley-Cook 2025 citation).

## Key facts
- MDD-W for SOFI 2026 is FAOSTAT SDGB indicator 2.2.4 (item `24049-F-Y15T49T`), not the small `MDDW` domain.
- N = 66 (79 MDD-W countries, 13 lack CoAHD). All matched CoAHD in the exact survey year.
- Headline slope −0.71, R² 0.65, LOO-CV R² 0.63. PUA survives log-GDP; cost *level* has R² 0.00.
- Region FE: R² 0.78, slope −0.39 — some global outliers are regional (LatAm, Nepal).
- Only Indonesia, Armenia, Burkina Faso outside 95% PI. Burkina Faso = SMART survey, unverified coverage → flagged.
- 21/66 surveys flagged (5 ≥10% excluded, 10 phone frame, 6 unverified). Slope/ranking robust to dropping them.
- GDQP vs DHS not calibrated (Hanley-Cook et al. 2025 BMC Nutr 11:104 — verified via PubMed abstract).

## Left to do
- Verify in Hanley-Cook full text: "11.6 pp mean abs diff", "3.5× less precise", "source hierarchy" (not in abstract).
- Burkina Faso 2023 SMART: check report for national coverage / excluded zones; update coverage CSV.
- DHS rows in coverage CSV are generic; fill fieldwork dates and women-sample sizes from final reports if weights matter.
- Venue decision (see earlier discussion: arXiv + blog now; Curr Dev Nutr / PHN letter; Nature Food correspondence on platform issue).
- Confirm OK to commit `results/residuals.csv` and `reference/mddw_survey_coverage.csv` (derived/public metadata).

## Known issues
- Notebook 03 quadrant loop uses the new quadrant names automatically; README/writeup wording updated.
- adjustText label placement may shift slightly across matplotlib versions.
- pandas 3.x: SDG `Value` reads as text (censored "<2.5") — handled.
