# Women's dietary diversity relative to the affordability of a healthy diet: a cross-country benchmark

*Research letter, draft — 2026-08-19*

## Abstract

Across 66 countries with both indicators, the share of the population unable to afford a healthy diet (FAOSTAT CoAHD) explains about two-thirds of the cross-country variation in the share of women aged 15–49 achieving minimum dietary diversity (MDD-W, SDG 2.2.4). Each additional percentage point of unaffordability is associated with 0.71 fewer points of MDD-W (95 % bootstrap CI −0.82 to −0.60; R² = 0.65; leave-one-country-out R² = 0.63). Affordability is not simply income in disguise: it keeps most of its coefficient when log GDP per capita is added, and the *level* of diet cost in PPP dollars carries no signal at all — only cost relative to income does. The remaining third of the variation — a residual standard deviation of 14 percentage points — is a descriptive benchmark: how much higher or lower a country's MDD-W is than its affordability alone would predict. Only three countries fall outside the 95 % prediction interval (Indonesia and Armenia above; Burkina Faso below). Regional fixed effects absorb part of the residual, so some apparent outliers (notably in Latin America) are regional rather than national features. A methodological caveat conditions all country-level statements: MDD-W estimates from the Gallup-based Global Diet Quality Project and from DHS are not calibrated to each other (Hanley-Cook et al., 2025), and one in three surveys in the panel carries a coverage flag (≥10 % of the population excluded from the frame, a telephone sampling frame, or unverified national coverage). The slope and ranking are robust to all of this; individual country positions are not always.

## 1. Why this comparison

The State of Food Security and Nutrition in the World (SOFI) reports two numbers that are usually discussed separately. One is economic: the cost of the least-expensive diet meeting food-based dietary guidelines, and the share of people whose income falls below it (Herforth et al., 2020). The other is dietary: whether women of reproductive age consumed at least five of ten food groups in the previous day (MDD-W; FAO, 2021), which SOFI 2026 reports under the SDG framework as indicator 2.2.4.

The obvious question is how tightly the two move together. If unaffordability explained dietary diversity almost completely, lowering the cost of a healthy diet would be close to sufficient. If it explained little, cost would be a distraction. The interesting middle case — which is what the data show — is that cost explains a lot but leaves a large, structured remainder. SOFI's own framing acknowledges this: reducing cost is necessary but not sufficient. This note quantifies the "not sufficient", puts country names on it with appropriate caution, and is explicit about where the measurement system cannot yet support country-level claims.

## 2. Data

**Affordability.** FAOSTAT domain CAHD, July 2026 release (the SOFI 2026 vintage): the prevalence of unaffordability (PUA) — the percentage of the population unable to afford a healthy diet — annually for 2017–2025 in 149 countries; and the cost of a healthy diet in PPP dollars per person per day.

**Dietary diversity.** FAOSTAT domain SDGB, indicator 2.2.4, national series: the percentage of non-pregnant women aged 15–49 achieving MDD-W. Seventy-nine countries have at least one value (106 country-years, 2016–2025). FAOSTAT's `Note` field records the source: 67 country-years from the Global Diet Quality Project (GDQP; modules fielded in the Gallup World Poll), 22 from the Demographic and Health Surveys, 17 from one-off national nutrition or food-security surveys. The standalone FAOSTAT "MDD-W" domain contains only ~25 surveys; the SDG 2.2.4 series is the one that matches SOFI 2026.

**Survey coverage metadata.** For every MDD-W observation in the panel we compiled fieldwork dates, sample size, design effect, interview mode and documented geographic exclusions from Gallup's *Country Data Set Details* (DQQ, 2021–2024) and, for DHS and national surveys, from the FAOSTAT note (`reference/mddw_survey_coverage.csv`). Three flags follow: **exclusion** (≥10 % of the national population outside the sampling frame), **telephone frame** (landline/mobile samples, which under-cover non-phone households), and **unverified** (one-off national surveys whose coverage we did not verify).

**Covariates.** World Bank region and income group; GDP per capita at PPP (constant 2021 international dollars).

**Panel.** Most recent MDD-W survey per country, matched to the CoAHD estimate for the *same calendar year* (±2-year fallback was available but not needed: all 66 matched exactly). Thirteen MDD-W countries have no CoAHD affordability estimate and are dropped (listed in `results/join_log.json`). The sample is 66 countries: 32 Sub-Saharan Africa, 11 Europe & Central Asia, 9 MENA, 6 East Asia–Pacific, 6 Latin America, 2 South Asia; 15 low-income, 27 lower-middle, 21 upper-middle, 3 high-income. Unaffordability runs from 1 % (Switzerland) to 92 % (Malawi); MDD-W from 17 % (DR Congo) to 91 % (Iraq). Twenty-one of the 66 surveys carry at least one coverage flag (5 exclusion, 10 telephone, 6 unverified). A second panel applying a source-priority rule (DHS/national preferred over Gallup where both exist from 2018 on) changes three countries (Côte d'Ivoire, Kyrgyzstan, Sierra Leone).

## 3. Method

The headline model is deliberately simple:

MDD-W<sub>i</sub> = α + β · PUA<sub>i</sub> + ε<sub>i</sub>

by OLS with HC3 standard errors and a 5,000-draw country bootstrap for the slope and R². The residual ε̂<sub>i</sub> is the quantity of interest: MDD-W higher or lower than predicted given estimated unaffordability. We deliberately do not call it "performance": it bundles food availability, preferences, inequality, urbanization, season, conflict, and measurement error in both indicators.

Three guards against over-reading residuals: (i) each country's benchmark is also computed leaving that country out (LOO residuals; LOO-CV R²); (ii) "unusual" means outside the 95 % prediction interval, not merely off the line; (iii) countries are labelled by externally studentized residual, and flagged surveys are marked.

Robustness specifications (Table 1): fractional-logit GLM for the bounded outcome; a restricted cubic spline in PUA; log GDP per capita alone and alongside PUA; region fixed effects (a within-region benchmark); survey-source dummies; GDQP-only and DHS/national-only subsamples; precision-weighted WLS using an approximate binomial SE for each MDD-W estimate (effective women's sample ≈ 0.45·N/deff for Gallup, assumed 10,000 for DHS and 2,000 for other surveys — crude, documented assumptions); latest-year PUA instead of survey-year PUA; dropping high-influence points; excluding all flagged surveys; and the source-priority panel. Everything is reproducible from four scripts; figures read only from saved results.

## 4. Results

### 4.1 Affordability explains about two-thirds

The fitted line is MDD-W = 92.7 − 0.71·PUA. A country where nobody is priced out of a healthy diet is predicted to have about 93 % of women meeting MDD-W; one where everyone is priced out, about 22 %. R² is 0.65 (bootstrap CI 0.50–0.78); leave-one-country-out R² is 0.63, so the fit is not an artefact of any one country. Forty-four of 66 countries lie within one residual SD (14 points) of the line; only three lie outside the 95 % prediction interval.

The slope is stable: −0.71 headline; −0.69 precision-weighted; −0.69 in DHS/national-only (n=20); −0.68 excluding all 21 flagged surveys (n=45); −0.70 on the source-priority panel; −0.71 with latest-year PUA; −0.76 dropping the two most influential points (Indonesia, Malaysia); −0.59 in the GDQP-only subsample (n=46). A natural cubic spline does not improve on the straight line (F-test p = 0.18), and the fractional logit ranks countries identically (ρ = 0.99). Residual rankings correlate at ρ ≥ 0.92 with the headline across every specification except region fixed effects (ρ = 0.79, discussed below).

### 4.2 Affordability is not income, and cost level is not affordability

Log GDP per capita alone explains 62 % of MDD-W variance and correlates with PUA at −0.78. With both in the model, PUA keeps a coefficient of −0.44 (p < 0.0001), log GDP contributes 9.6 points per log unit (p = 0.002), and R² rises only to 0.71. At a given income level, countries where a healthy diet is more affordable have measurably more diverse diets. The headline residual is only weakly related to income (r = 0.26).

Separately, the *cost* of a healthy diet in PPP dollars per day has no relationship with MDD-W (R² = 0.00) and adds nothing next to PUA. The signal is entirely in cost relative to income, which is what the CoAHD affordability indicator was designed to capture.

### 4.3 Regional structure

Adding region fixed effects raises R² to 0.78 and lowers the PUA slope to −0.39 (still p = 0.001). Sub-Saharan Africa's intercept is about 22 points below the reference (East Asia–Pacific) at the same PUA; South Asia's about 18 points below; Europe/Central Asia, Latin America and MENA are indistinguishable from the reference. Part of what the bivariate model attributes to affordability is therefore broad regional structure — food systems, diets and survey platforms differ by region in ways PUA does not capture. The practical consequence is that some countries look unusual against the global line but ordinary against their region: Guatemala (+21 global, +5 within-region), Costa Rica (+16, −1), Peru (+11, −1), Nepal (−21, −6), Côte d'Ivoire (−17, −6). Others keep their position under both benchmarks: Indonesia (+43, +25), Armenia (+31, +14), Kyrgyzstan (+24, +12), Uganda (+19, +22), Iraq (+18, +14); and below, Malaysia (−28, −24), Burkina Faso (−29, −23), Lesotho (−20, −18), Mongolia (−12, −19), Ethiopia (−17, −14). We regard a country as a candidate for case study only if it is far from the line under both benchmarks *and* its survey carries no coverage flag.

### 4.4 The four quadrants (Figure 1)

Splitting at median unaffordability (49.6 %) and at the fitted line gives four descriptive groups. We phrase them as "higher/lower MDD-W than predicted", not as performance.

**Higher unaffordability, MDD-W above prediction (n = 14).** Indonesia is the largest positive deviation in the sample (70 % unable to afford a healthy diet; 86 % of women meet MDD-W; +43, outside the 95 % PI, unflagged survey). Armenia (+31, outside PI, unflagged), Uganda (+19, unflagged), Lao PDR (+21; but Gallup excluded ~14 % of the population, flagged) and Guatemala (+20; regional rather than national once region is controlled) follow.

**Lower unaffordability, MDD-W above prediction (n = 18).** Mostly upper-middle-income countries in Europe, Central Asia and MENA. Kyrgyzstan (+24), Iraq (+18), Algeria (+16; telephone frame, flagged) and Iran (+16; telephone frame, 5-day fieldwork, flagged) are the labelled cases.

**Lower unaffordability, MDD-W below prediction (n = 15).** The quadrant SOFI's caveat is about: healthy diets comparatively affordable, yet diversity falls short of prediction. Malaysia is the sharpest case (2 % priced out; 63 % MDD-W; −28 under both global and regional benchmarks; unflagged Gallup survey). Nepal (−21 global, but −6 within South Asia; DHS) and Jordan (−15; DHS) are the others labelled. Here price is not the binding constraint.

**Higher unaffordability, MDD-W below prediction (n = 19).** Dominated by Sub-Saharan Africa. Burkina Faso is the largest negative deviation (−29, outside PI) **but its MDD-W comes from a 2023 SMART nutrition survey whose national coverage and exclusion of insecure areas we could not verify — it is flagged and should not be quoted without that qualification.** Comoros (−26), Lesotho (−20; DHS), Guinea (−19), Ethiopia (−17; Gallup excluded Tigray, Gambella, Harari — 7 %), Côte d'Ivoire, Liberia, Mali and Tanzania (−15 to −17) complete the group.

### 4.5 Survey platform is a first-order issue

Where a country appears in the SDG 2.2.4 series with both a GDQP estimate and a DHS estimate a year or two apart, the GDQP figure is higher by 32 points in DR Congo, 31 in Mozambique, 25 in Mali, 21 in Malawi, 21 in Kenya, 12 in Senegal. These are not plausible real changes. Hanley-Cook et al. (2025), comparing contemporaneous DHS and Gallup World Poll MDD-W estimates in nine country-year sets, found GWP significantly higher in five, every absolute difference above 5 points (range −17 to +21), sentinel-food lists overlapping by only 21–65 % within the same country, and Gallup fieldwork covering fewer months in fewer languages; they conclude that platforms are not currently calibratable and that mixing them risks misreading change over time. Seasonality compounds this: Gallup rounds typically span a few weeks, DHS several months, and MDD-W is known to swing widely across the agricultural calendar. Gallup's own documentation adds geographic exclusions that are material in several of our countries (Chad 23 %, Cameroon 20 %, Madagascar 17 %, Lao PDR 14 %, Moldova 13 %).

Our rule — most recent survey per country — yields 46 GDQP, 14 DHS and 6 other-survey observations, with DHS concentrated among poorer, higher-unaffordability countries. In a model with source dummies, DHS-sourced points sit 12.8 points below GDQP-sourced points at the same PUA (p = 0.002). Three consequences: the slope attenuates modestly (−0.62) but holds; the residual ranking is robust (ρ = 0.92 with headline; 0.999 for precision-weighted WLS; 0.998 excluding flagged surveys); but individual DHS/national observations move — Jordan's residual goes from −15 to −1, Senegal's from +5 to +14, Kenya's from +11 to +17 once source is adjusted. The positive outliers named above are almost all GDQP-sourced and therefore internally comparable; the negative outliers are mixed-source, and cross-source comparisons among them should be treated as approximate.

## 5. What the residual is, and is not

The residual is descriptive: the part of dietary diversity that a single affordability number does not predict. It bundles everything else — retail density and reach, home production and informal markets, cultural dietary patterns, women's time and intra-household allocation, nutrition information, the season of the survey, conflict — along with measurement error in both indicators. We have not decomposed it; with 66 observations one should not try too hard. Its value is as a targeting device: where "make healthy diets cheaper" is the right first-order message, and where it is not, and which countries merit case study because they remain far from the line under both global and regional benchmarks with an unflagged survey (Indonesia, Armenia, Kyrgyzstan, Uganda, Iraq above; Malaysia, Lesotho, Mongolia below).

Limitations. The analysis is cross-sectional with one observation per country and makes no causal claim. MDD-W measures women 15–49 and is a proxy for micronutrient adequacy, not a general diet-quality index; unaffordability, by contrast, is a total-population measure — the two do not describe the same people. CoAHD is itself a modelled indicator (least-cost diet priced at retail vs. a national income distribution) whose assumptions carry through. The sample is thin at the top of the income distribution (three high-income countries), so "lower unaffordability" means below a median of ~50 %, not "affordable" in an absolute sense. The precision weights rest on assumed effective sample sizes, not published standard errors. And the survey-platform issue described in §4.5 limits every country-level statement.

## 6. Conclusion

Two-thirds of the cross-country variation in women's dietary diversity tracks the affordability of a healthy diet; that relationship is not an artefact of national income, and it is affordability — not the price level — that matters. The other third is large and structured. A handful of countries sit well above or below the affordability benchmark under every specification we tried: that is the empirical content of the claim that reducing cost alone will not be enough, and it tells us where to look for what else is needed. It is also a reminder that the new global MDD-W series is not yet platform-harmonised, and that country-level inferences from it need to carry the survey's provenance alongside the number.

## References

- FAO (2021). *Minimum dietary diversity for women: An updated guide to measurement — from collection to action.* Rome: FAO.
- FAO, IFAD, UNICEF, WFP and WHO (2026). *The State of Food Security and Nutrition in the World 2026.* Rome: FAO.
- Hanley-Cook, G. T., Gie, S. M., Parraguez, J. P. and Holmes, B. A. (2025). Minimum Dietary Diversity for Women: precision of national surveys and accuracy of brief data collection instruments. *BMC Nutrition* 11: 104. doi:10.1186/s40795-025-01065-7.
- Herforth, A., Bai, Y., Venkat, A., Mahrt, K., Ebel, A. and Masters, W. A. (2020). *Cost and affordability of healthy diets across and within countries.* FAO Agricultural Development Economics Technical Study No. 9. Rome: FAO.
- Gallup (2024). *Country Data Set Details — DQQ, Gallup Worldwide Research data collected 2021–2024.* https://www.dietquality.org/DQQ%20data%20collection%20details%20GWP%202021-2024.pdf
- Global Diet Quality Project. *Diet quality data* (Harvard Dataverse, doi:10.7910/DVN/KY3W8A), as cited in FAOSTAT SDG 2.2.4 metadata.
- FAOSTAT (2026). Domains CAHD (July 2026 release) and SDGB (indicator 2.2.4). https://bulks-faostat.fao.org/production/datasets_E.json
- World Bank (2026). World Development Indicators (NY.GDP.PCAP.PP.KD) and country classification API.

---

**Figure 1.** MDD-W against the share of the population unable to afford a healthy diet, 66 countries. OLS fit with ±1 residual-SD band; quadrants split at median unaffordability; countries with |studentized residual| > 1 labelled; hollow markers = survey coverage flag. `figures/fig1_affordability_quality_gap.png`

**Figure 2.** Sorted residuals (observed − predicted MDD-W), coloured by MDD-W survey source; ◦ = coverage flag. `figures/fig2_residual_league_table.png`

**Table 1.** Robustness (`results/robustness.csv`).

| Model | n | PUA coef. | SE | R² | ρ(resid, headline) |
|---|---|---|---|---|---|
| OLS MDD-W ~ PUA (headline) | 66 | −0.71 | 0.06 | 0.65 | — |
| Fractional logit | 66 | −0.033 (logit) | 0.003 | — | 0.99 |
| Natural cubic spline, 4 df | 66 | — (F vs linear p=0.18) | — | 0.67 | 0.96 |
| OLS MDD-W ~ log GDP | 66 | (log GDP: 19.2) | 1.7 | 0.62 | — |
| OLS MDD-W ~ PUA + log GDP | 66 | −0.44 | 0.11 | 0.71 | — |
| OLS + region fixed effects | 66 | −0.39 | 0.12 | 0.78 | 0.79 |
| OLS + survey-source dummies | 66 | −0.62 | 0.06 | 0.70 | 0.92 |
| GDQP-sourced only | 46 | −0.59 | 0.08 | 0.51 | — |
| DHS/national-sourced only | 20 | −0.69 | 0.10 | 0.74 | — |
| WLS, precision-weighted | 66 | −0.69 | 0.09 | 0.76 | 0.999 |
| Latest-year PUA | 66 | −0.71 | 0.05 | 0.68 | 0.98 |
| Drop Cook's D > 4/n (2) | 64 | −0.76 | 0.05 | 0.72 | — |
| Exclude flagged surveys (21) | 45 | −0.68 | 0.08 | 0.60 | 0.998 |
| Source-priority panel | 66 | −0.70 | 0.06 | 0.65 | 0.99 |
| Leave-one-country-out CV | 66 | — | — | 0.63 | 1.00 |
