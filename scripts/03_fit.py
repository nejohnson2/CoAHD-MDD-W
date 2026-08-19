"""
03_fit.py — fit MDD-W ~ % unable to afford a healthy diet, compute residuals, run robustness checks

Input    data/processed/panel.csv (+ panel_source_priority.csv for one sensitivity row)
Outputs  results/fit_summary.json   headline coefficients, CIs, quadrant counts, named countries
         results/residuals.csv      one row per country: fitted, residual, studentized residual, Cook's D,
                                    95% prediction interval, leave-one-out residual, quadrant, flags
         results/robustness.csv     one row per (model, term)

Headline model
--------------
    mddw = a + b * pua        OLS, HC3 robust SEs, 5 000-draw country bootstrap for slope and R^2

Residual = observed MDD-W minus MDD-W predicted from affordability.
           Read as "higher / lower than predicted" — NOT performance, NOT causal.
Quadrants = PUA split at its median  x  residual sign.
"Notable" = |externally studentized residual| > 1      (which countries get a label in the figure)
"Unusual" = outside the 95% prediction interval         (genuinely atypical, not merely off the line)

Robustness rows
---------------
  fractional-logit GLM                  bounded outcome
  restricted cubic spline in PUA        is a straight line adequate?
  ~ log GDP;  ~ PUA + log GDP           is affordability just income?
  ~ PUA + region fixed effects          within-region benchmark
  ~ PUA + survey-source dummies         Gallup vs DHS vs other
  GDQP-only;  DHS/national-only         platform subsamples
  precision-weighted WLS                1/SE^2 of MDD-W (approximate SEs from 02_build_panel)
  latest-year PUA                       year-matching sensitivity
  drop Cook's D > 4/n                   influence
  exclude flagged surveys               coverage flags from 02_build_panel
  source-priority panel                 DHS/national preferred over Gallup
  leave-one-country-out                 CV R^2; a country does not set its own benchmark
"""
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------------------------------
# Paths, constants, data
# --------------------------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"

SEED, N_BOOT = 42, 5000
rng = np.random.default_rng(SEED)

p = pd.read_csv(ROOT / "data/processed/panel.csv")
p["log_gdp"]  = np.log(p.gdp_pcap_ppp)
p["any_flag"] = p.flag_exclusion | p.flag_phone | p.flag_unverified
n = len(p)


# --------------------------------------------------------------------------------------------------------------
# 1. Headline OLS + country bootstrap
# --------------------------------------------------------------------------------------------------------------
ols = smf.ols("mddw ~ pua", data=p).fit(cov_type="HC3")
log.info("OLS: slope=%.3f (HC3 se %.3f), R2=%.3f, n=%d", ols.params["pua"], ols.bse["pua"], ols.rsquared, n)

# resample countries with replacement; keep slope and R^2 from each draw
boot = np.empty((N_BOOT, 2))
for i in range(N_BOOT):
    sample = p.sample(n, replace=True, random_state=rng.integers(1 << 31))
    f = smf.ols("mddw ~ pua", data=sample).fit()
    boot[i] = f.params["pua"], f.rsquared

slope_ci = np.percentile(boot[:, 0], [2.5, 97.5])
r2_ci    = np.percentile(boot[:, 1], [2.5, 97.5])


# --------------------------------------------------------------------------------------------------------------
# 2. Residuals, influence, prediction intervals, leave-one-out, quadrants
# --------------------------------------------------------------------------------------------------------------
infl = ols.get_influence()
p["fitted"]    = ols.fittedvalues
p["resid"]     = ols.resid
p["std_resid"] = infl.resid_studentized_external
p["cooks_d"]   = infl.cooks_distance[0]

# classical 95% prediction interval for a new observation at each country's PUA
pi = smf.ols("mddw ~ pua", data=p).fit().get_prediction(p).summary_frame(alpha=0.05)
p["pi95_lo"], p["pi95_hi"] = pi.obs_ci_lower, pi.obs_ci_upper
p["outside_pi95"] = (p.mddw < p.pi95_lo) | (p.mddw > p.pi95_hi)

# leave-one-country-out: predict each country from a model that never saw it
p["loo_pred"]  = [smf.ols("mddw ~ pua", data=p.drop(i)).fit().predict(p.loc[[i]]).iloc[0] for i in p.index]
p["loo_resid"] = p.mddw - p.loo_pred
loo_r2 = 1 - (p.loo_resid ** 2).sum() / ((p.mddw - p.mddw.mean()) ** 2).sum()

# quadrants: below/above median unaffordability  x  below/above the fitted line
pua_split = p.pua.median()
p["quadrant"] = np.select(
    [
        (p.pua <= pua_split) & (p.resid >= 0),
        (p.pua >  pua_split) & (p.resid >= 0),
        (p.pua <= pua_split) & (p.resid <  0),
        (p.pua >  pua_split) & (p.resid <  0),
    ],
    [
        "lower unaffordability, higher MDD-W than predicted",
        "higher unaffordability, higher MDD-W than predicted",
        "lower unaffordability, lower MDD-W than predicted",
        "higher unaffordability, lower MDD-W than predicted",
    ],
    default="",
)
p["notable"] = p.std_resid.abs() > 1

p.sort_values("resid", ascending=False).to_csv(RES / "residuals.csv", index=False)


# --------------------------------------------------------------------------------------------------------------
# 3. Robustness table
# --------------------------------------------------------------------------------------------------------------
def row(name, fit, term="pua", note=""):
    """One line of the robustness table for a fitted model and a coefficient name."""
    return {
        "model": name, "n": int(fit.nobs), "term": term,
        "coef": fit.params.get(term, np.nan), "se": fit.bse.get(term, np.nan), "p": fit.pvalues.get(term, np.nan),
        "r2": getattr(fit, "rsquared", np.nan),
        "spearman_resid_vs_headline": np.nan, "note": note,
    }


def spearman(fit, data, scale=1.0):
    """Rank correlation between this model's residuals and the headline residuals (matched on iso3)."""
    r_alt = data.mddw - fit.predict(data) * scale
    return pd.Series(r_alt.values, index=data.iso3).corr(pd.Series(p.resid.values, index=p.iso3), method="spearman")


rob = [row("OLS mddw ~ pua (headline)", ols)]

# -- bounded outcome: fractional logit
frac = smf.glm("I(mddw/100) ~ pua", data=p, family=sm.families.Binomial()).fit(cov_type="HC3")
rob.append(row("Fractional logit mddw/100 ~ pua", frac, note="logit scale")
           | {"spearman_resid_vs_headline": spearman(frac, p, 100)})

# -- nonlinearity: natural cubic spline, 4 df, F-test against the straight line
spl   = smf.ols("mddw ~ cr(pua, df=4)", data=p).fit(cov_type="HC3")
spl_p = sm.stats.anova_lm(smf.ols("mddw ~ pua", data=p).fit(),
                          smf.ols("mddw ~ cr(pua, df=4)", data=p).fit())["Pr(>F)"].iloc[1]
rob.append(row("OLS restricted cubic spline (4 df)", spl, term="", note=f"F-test spline vs linear p={spl_p:.3f}")
           | {"spearman_resid_vs_headline": spearman(spl, p)})

# -- income
rob.append(row("OLS mddw ~ log_gdp", smf.ols("mddw ~ log_gdp", data=p).fit(cov_type="HC3"), term="log_gdp"))
both = smf.ols("mddw ~ pua + log_gdp", data=p).fit(cov_type="HC3")
rob += [row("OLS mddw ~ pua + log_gdp", both), row("OLS mddw ~ pua + log_gdp", both, term="log_gdp")]

# -- region fixed effects
reg = smf.ols("mddw ~ pua + C(region)", data=p).fit(cov_type="HC3")
rob.append(row("OLS mddw ~ pua + region FE", reg, note="within-region benchmark")
           | {"spearman_resid_vs_headline": spearman(reg, p)})

# -- survey platform: dummies, then subsamples
src = smf.ols("mddw ~ pua + C(mddw_source_group, Treatment('GDQP'))", data=p).fit(cov_type="HC3")
rob.append(row("OLS mddw ~ pua + source dummies", src) | {"spearman_resid_vs_headline": spearman(src, p)})
for t in [c for c in src.params.index if "source_group" in c]:
    rob.append(row("OLS mddw ~ pua + source dummies", src, term=t))

gd = p[p.mddw_source_group == "GDQP"]
rob.append(row("OLS, GDQP-sourced only", smf.ols("mddw ~ pua", data=gd).fit(cov_type="HC3")))

nat = p[p.mddw_source_group != "GDQP"]
rob.append(row("OLS, DHS/national-sourced only", smf.ols("mddw ~ pua", data=nat).fit(cov_type="HC3"), note="small n"))

# -- precision weights (approximate MDD-W sampling variance)
wls = smf.wls("mddw ~ pua", data=p, weights=1 / p.mddw_se ** 2).fit(cov_type="HC3")
rob.append(row("WLS, precision-weighted (1/SE^2 of MDD-W)", wls, note="approx. SEs, see 02_build_panel")
           | {"spearman_resid_vs_headline": spearman(wls, p)})

# -- year matching
lat = smf.ols("mddw ~ pua_latest", data=p).fit(cov_type="HC3")
rob.append(row("OLS mddw ~ pua_latest (latest CoAHD year)", lat, term="pua_latest")
           | {"spearman_resid_vs_headline": spearman(lat, p)})

# -- influence
keep = p[p.cooks_d <= 4 / n]
rob.append(row(f"OLS, drop Cook's D > 4/n ({n - len(keep)} dropped)",
               smf.ols("mddw ~ pua", data=keep).fit(cov_type="HC3")))

# -- coverage flags
clean = p[~p.any_flag]
cl = smf.ols("mddw ~ pua", data=clean).fit(cov_type="HC3")
rob.append(row(f"OLS, exclude flagged surveys ({n - len(clean)} dropped)", cl,
               note=">=10% excluded / phone frame / unverified")
           | {"spearman_resid_vs_headline": spearman(cl, clean)})

# -- source-priority panel
pp  = pd.read_csv(ROOT / "data/processed/panel_source_priority.csv")
pri = smf.ols("mddw ~ pua", data=pp).fit(cov_type="HC3")
rob.append(row("OLS, source-priority panel (DHS/national preferred)", pri, note="3 countries change")
           | {"spearman_resid_vs_headline": spearman(pri, pp)})

# -- leave-one-country-out (computed in section 2)
rob.append({
    "model": "Leave-one-country-out CV", "n": n, "term": "",
    "coef": np.nan, "se": np.nan, "p": np.nan, "r2": loo_r2,
    "spearman_resid_vs_headline": p.loo_resid.corr(p.resid, method="spearman"), "note": "CV R^2; LOO residuals",
})

rob = pd.DataFrame(rob)
rob.to_csv(RES / "robustness.csv", index=False)


# --------------------------------------------------------------------------------------------------------------
# 4. Summary JSON  (what the figure script and the write-up read)
# --------------------------------------------------------------------------------------------------------------
cols = ["country", "pua", "mddw", "resid", "std_resid", "mddw_source_group", "any_flag", "outside_pi95"]

summary = {
    "n": n, "seed": SEED, "n_boot": N_BOOT,
    # headline fit
    "intercept": ols.params["Intercept"], "slope": ols.params["pua"], "slope_se_hc3": ols.bse["pua"],
    "slope_ci95_boot": slope_ci.tolist(),
    "r2": ols.rsquared, "r2_ci95_boot": r2_ci.tolist(), "loo_cv_r2": loo_r2,
    "resid_sd": p.resid.std(ddof=2), "pua_split": pua_split,
    # residual structure
    "quadrant_counts": p.quadrant.value_counts().to_dict(),
    "n_outside_pi95": int(p.outside_pi95.sum()), "outside_pi95": p[p.outside_pi95].country.tolist(),
    "n_flagged": int(p.any_flag.sum()),
    "flagged": p[p.any_flag][["country", "flag_exclusion", "flag_phone", "flag_unverified", "excluded_pct"]].to_dict("records"),
    "top_positive": p.nlargest(10, "resid")[cols].round(1).to_dict("records"),
    "top_negative": p.nsmallest(10, "resid")[cols].round(1).to_dict("records"),
    # key robustness numbers
    "pua_plus_loggdp": {"pua_coef": both.params["pua"], "pua_p": both.pvalues["pua"],
                        "log_gdp_coef": both.params["log_gdp"], "log_gdp_p": both.pvalues["log_gdp"], "r2": both.rsquared},
    "region_fe": {"pua_coef": reg.params["pua"], "r2": reg.rsquared},
}
json.dump(summary, open(RES / "fit_summary.json", "w"), indent=2,
          default=lambda o: o.item() if hasattr(o, "item") else str(o))

log.info("wrote %s", RES)
print(rob.round(3).to_string())
