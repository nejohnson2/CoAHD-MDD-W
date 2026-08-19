"""
02_build_panel.py — one row per country: MDD-W + matched CoAHD unaffordability + covariates + survey metadata

Inputs   data/raw/  (from 01_download.py)   and   reference/mddw_survey_coverage.csv (hand-compiled)
Outputs  data/processed/panel.csv                 headline panel (most recent MDD-W survey per country)
         data/processed/panel_source_priority.csv sensitivity panel (DHS/national preferred over Gallup)
         data/processed/mddw_all_surveys.csv      every MDD-W country-year FAOSTAT has (for notebooks)
         results/join_log.json                    every drop, every flag count, what the priority rule changed

Rules
-----
MDD-W      SDG 2.2.4 national series (item 24049-F-Y15T49T). Headline: most recent survey per country.
CoAHD PUA  item 7005 (% unable to afford a healthy diet). Matched to the MDD-W survey year; if that year is missing,
           nearest year within +/- MAX_GAP. We also keep the latest available PUA for a sensitivity check.
GDP        World Bank GDP per capita PPP, same nearest-year rule.
Join key   ISO3. FAOSTAT ships M49 numeric codes; pycountry converts M49 -> ISO3.
Coverage   reference/mddw_survey_coverage.csv is merged on (iso3, year, source_group) and yields three flags plus an
           approximate precision (n_eff_women, mddw_se) used only for a weighted sensitivity fit.
"""
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pycountry

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------------------------------
# Paths and constants
# --------------------------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW  = ROOT / "data/raw"
PROC = ROOT / "data/processed"
RES  = ROOT / "results"
PROC.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)

MAX_GAP = 2  # years: how far CoAHD / GDP may be from the MDD-W survey year


# --------------------------------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------------------------------
def m49_to_iso3(m49: str) -> str | None:
    """FAOSTAT stores M49 as e.g. "'008" (leading apostrophe); pycountry wants "008"."""
    code = m49.strip("'").zfill(3)
    c = pycountry.countries.get(numeric=code)
    return c.alpha_3 if c else None


def nearest_year(df: pd.DataFrame, iso3: str, year: int, col: str) -> tuple[float, int] | tuple[None, None]:
    """Value of `col` for `iso3` in `year`; else the nearest year within MAX_GAP (ties -> earlier year); else None."""
    sub = df[df.iso3 == iso3].dropna(subset=[col])
    if sub.empty:
        return None, None
    sub = sub.assign(gap=(sub.year - year).abs()).sort_values(["gap", "year"])
    best = sub.iloc[0]
    return (best[col], int(best.year)) if best.gap <= MAX_GAP else (None, None)


def pick_survey(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """
    Reduce the MDD-W country-year table to one row per country.

    rule = "latest"    most recent survey (headline)
    rule = "priority"  prefer a DHS / national survey over Gallup (GDQP) when one exists from 2018 on
                       (CoAHD coverage starts 2017); otherwise fall back to the latest survey.
                       Motivation: Hanley-Cook et al. (2025) — the two platforms are not calibrated.
    """
    df = df.sort_values("year")
    if rule == "latest":
        return df.groupby("iso3", as_index=False).last()

    nat  = df[(df.source_group != "GDQP") & (df.year >= 2018)].groupby("iso3", as_index=False).last()
    rest = df[~df.iso3.isin(nat.iso3)].groupby("iso3", as_index=False).last()
    return pd.concat([nat, rest], ignore_index=True)


# --------------------------------------------------------------------------------------------------------------
# 1. MDD-W  (FAOSTAT SDGB, indicator 2.2.4)
# --------------------------------------------------------------------------------------------------------------
sdg = pd.read_csv(RAW / "SDGB/SDG_BulkDownloads_E_All_Data_(Normalized).csv", encoding="utf-8", low_memory=False)

mdd = sdg[(sdg["Item Code"] == "24049-F-Y15T49T") & (sdg["Area Code"] < 5000)].copy()   # Area Code < 5000 = countries
mdd["Value"] = pd.to_numeric(mdd["Value"], errors="coerce")   # text column: other SDG items are censored ("<2.5")
mdd = mdd.dropna(subset=["Value"])

mdd["iso3"] = mdd["Area Code (M49)"].map(m49_to_iso3)

# Provenance lives in the Note column, e.g. "Global monitoring data | DHS Program: https://..."
mdd["source"] = mdd["Note"].str.split("|").str[1].str.split(":").str[0].str.strip()
mdd["source_group"] = mdd["source"].map(
    lambda s: "GDQP" if "Global Diet Quality" in str(s) else "DHS" if "DHS" in str(s) else "Other"
)

mdd = mdd[mdd.iso3.notna()]   # drops a 'Sub-Saharan Africa' aggregate that happens to sit below code 5000
mdd = mdd.rename(columns={"Area": "country", "Year": "year", "Value": "mddw"})
mdd = mdd[["iso3", "country", "year", "mddw", "source", "source_group", "Flag"]]

mdd.to_csv(PROC / "mddw_all_surveys.csv", index=False)
log.info("MDD-W: %d country-years, %d countries", len(mdd), mdd.iso3.nunique())


# --------------------------------------------------------------------------------------------------------------
# 2. Survey coverage / precision metadata  (reference/mddw_survey_coverage.csv)
# --------------------------------------------------------------------------------------------------------------
cov = pd.read_csv(ROOT / "reference/mddw_survey_coverage.csv")

# Approximate effective sample of women 15-49 behind each estimate. ASSUMPTIONS, used only for precision weights:
#   GDQP  ~45% of ~1000 adult interviews are women 15-49, deflated by the design effect (Hanley-Cook 2025: 416-595)
#   DHS   10 000 (conservative; actual women's samples are 11k-42k)
#   Other  2 000 (unknown; conservative)
cov["n_eff_women"] = np.where(
    cov.source_group == "GDQP", 0.45 * cov.n_interviews / cov.design_effect,
    np.where(cov.source_group == "DHS", 10_000, 2_000),
)

# Three coverage flags (any one of them -> hollow marker in the figures, dropped in one robustness fit)
cov["flag_exclusion"]  = cov.excluded_pct.fillna(0) >= 10              # >=10% of population outside sampling frame
cov["flag_phone"]      = cov["mode"].str.contains("elephone", na=False)  # telephone frame under-covers non-phone households
cov["flag_unverified"] = cov.source_group == "Other"                    # one-off national survey, coverage not verified

cov = cov.drop(columns=["reference"])


# --------------------------------------------------------------------------------------------------------------
# 3. CoAHD  (FAOSTAT CAHD)
# --------------------------------------------------------------------------------------------------------------
cahd = pd.read_csv(RAW / "CAHD/Cost_Affordability_Healthy_Diet_(CoAHD)_E_All_Data_(Normalized).csv", encoding="utf-8")
cahd = cahd[cahd["Area Code"] < 5000].copy()
cahd["iso3"] = cahd["Area Code (M49)"].map(m49_to_iso3)
cahd = cahd.rename(columns={"Year": "year", "Value": "value"})

pua  = cahd[cahd["Item Code"] == 7005][["iso3", "year", "value"]].rename(columns={"value": "pua"})    # % unable to afford
cohd = cahd[cahd["Item Code"] == 70040][["iso3", "year", "value"]].rename(columns={"value": "cohd"})  # PPP$/person/day
log.info("CoAHD PUA: %d countries", pua.iso3.nunique())


# --------------------------------------------------------------------------------------------------------------
# 4. World Bank  (region, income group, GDP per capita PPP)
# --------------------------------------------------------------------------------------------------------------
wb = pd.DataFrame(json.load(open(RAW / "wb_countries.json"))[1])
wb = wb[wb["region"].apply(lambda r: r["id"]) != "NA"]   # region id "NA" marks aggregates, not countries
wb = pd.DataFrame({
    "iso3":   wb["id"],
    "region": wb["region"].apply(lambda r: r["value"].strip()),
    "income": wb["incomeLevel"].apply(lambda r: r["value"]),
})

gdp = pd.DataFrame(json.load(open(RAW / "wb_gdp_pcap_ppp.json"))[1])
gdp = pd.DataFrame({
    "iso3":         gdp["countryiso3code"],
    "year":         gdp["date"].astype(int),
    "gdp_pcap_ppp": gdp["value"],
})


# --------------------------------------------------------------------------------------------------------------
# 5. Join  -> one row per country
# --------------------------------------------------------------------------------------------------------------
def build(mdd_sel: pd.DataFrame):
    """Join one selected MDD-W row per country to CoAHD, GDP, WB metadata and coverage metadata."""
    rows, dropped = [], []

    for _, r in mdd_sel.iterrows():
        # CoAHD in the survey year (or nearest within MAX_GAP); drop the country if none
        pua_val, pua_year = nearest_year(pua, r.iso3, r.year, "pua")
        if pua_val is None:
            reason = "no CoAHD data" if pua[pua.iso3 == r.iso3].empty else f"no CoAHD within +/-{MAX_GAP}y of {r.year}"
            dropped.append({"country": r.country, "iso3": r.iso3, "reason": reason})
            continue

        cohd_val, _       = nearest_year(cohd, r.iso3, r.year, "cohd")
        gdp_val, gdp_year = nearest_year(gdp, r.iso3, r.year, "gdp_pcap_ppp")
        latest = pua[(pua.iso3 == r.iso3)].dropna(subset=["pua"]).sort_values("year").iloc[-1]   # for sensitivity

        rows.append({
            "iso3": r.iso3, "country": r.country,
            "mddw": r.mddw, "mddw_year": r.year, "mddw_source": r.source, "mddw_source_group": r.source_group,
            "pua": pua_val, "pua_year": pua_year, "cohd": cohd_val,
            "pua_latest": latest.pua, "pua_latest_year": int(latest.year),
            "gdp_pcap_ppp": gdp_val, "gdp_year": gdp_year,
        })

    panel = pd.DataFrame(rows).merge(wb, on="iso3", how="left")

    # coverage metadata keyed on the specific survey used
    panel = panel.merge(cov, left_on=["iso3", "mddw_year", "mddw_source_group"],
                        right_on=["iso3", "year", "source_group"], how="left")
    panel = panel.drop(columns=["year", "source_group"])

    # binomial SE of the MDD-W estimate (percentage points) from the approximate effective sample
    panel["mddw_se"] = np.sqrt(panel.mddw / 100 * (1 - panel.mddw / 100) / panel.n_eff_women) * 100
    return panel, dropped


# headline panel
panel, dropped = build(pick_survey(mdd, "latest"))
panel.to_csv(PROC / "panel.csv", index=False)

# sensitivity panel: DHS / national preferred over Gallup
panel_pri, dropped_pri = build(pick_survey(mdd, "priority"))
panel_pri.to_csv(PROC / "panel_source_priority.csv", index=False)

changed = panel.merge(panel_pri, on="iso3", suffixes=("", "_pri")).query("mddw != mddw_pri")
log.info("source-priority rule changes %d countries: %s", len(changed), changed.country.tolist())


# --------------------------------------------------------------------------------------------------------------
# 6. Join log  (auditable record of every drop and flag)
# --------------------------------------------------------------------------------------------------------------
join_log = {
    "n_mddw_countries": mdd.iso3.nunique(),
    "n_panel": len(panel),
    "max_gap_years": MAX_GAP,
    "dropped": dropped,
    "missing_gdp":           panel[panel.gdp_pcap_ppp.isna()].country.tolist(),
    "missing_wb_meta":       panel[panel.region.isna()].country.tolist(),
    "missing_coverage_meta": panel[panel.n_eff_women.isna()].country.tolist(),
    "year_gap_counts": (panel.pua_year - panel.mddw_year).value_counts().sort_index().to_dict(),
    "flag_counts": {f: int(panel[f].sum()) for f in ["flag_exclusion", "flag_phone", "flag_unverified"]},
    "source_priority": {
        "n_panel": len(panel_pri),
        "dropped": dropped_pri,
        "changed": changed[["country", "mddw", "mddw_source_group", "mddw_year",
                            "mddw_pri", "mddw_source_group_pri", "mddw_year_pri"]].to_dict("records"),
    },
}
json.dump(join_log, open(RES / "join_log.json", "w"), indent=2, default=str)
log.info("panel: %d countries; dropped %d -> %s", len(panel), len(dropped), RES / "join_log.json")
