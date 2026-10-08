"""
04_figure.py — publication figures. Reads ONLY from results/ (no analysis happens here).

Input    results/residuals.csv, results/fit_summary.json
Outputs  figures/fig1_affordability_quality_gap.{png,pdf,svg}
             MDD-W vs % unable to afford a healthy diet; OLS line; +/-1 residual-SD band; four labelled quadrants;
             notable countries named; colour = income group (3 bins); hollow marker = survey coverage flag.
         figures/fig1b_affordability_quality_gap_by_source.{png,pdf,svg}
             identical, but colour = MDD-W survey platform (Gallup / DHS / other).
         figures/fig2_residual_league_table.{png,pdf}
             sorted residuals (observed - predicted MDD-W); colour = MDD-W survey platform; small circle = flag.

Colours: the validated 3-slot categorical palette from the dataviz reference (a scatter compares every pair of
colours, so the palette is capped at three hues); text and lines use ink/muted greys, never a series colour.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from adjustText import adjust_text
from matplotlib.patches import Patch

# --------------------------------------------------------------------------------------------------------------
# Paths, inputs, styling
# --------------------------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RES, FIG = ROOT / "results", ROOT / "figures"
FIG.mkdir(exist_ok=True)

r = pd.read_csv(RES / "residuals.csv")          # one row per country
s = json.load(open(RES / "fit_summary.json"))   # headline numbers for the subtitle and the fitted line

# short display names for long official names
SHORT = {
    "Lao People's Democratic Republic": "Lao PDR", "United Republic of Tanzania": "Tanzania",
    "Iran (Islamic Republic of)": "Iran", "Bolivia (Plurinational State of)": "Bolivia",
    "Democratic Republic of the Congo": "DR Congo", "Republic of Moldova": "Moldova",
    "Viet Nam": "Vietnam", "China, mainland": "China",
}
r["label"] = r.country.replace(SHORT)
r["any_flag"] = r.flag_exclusion | r.flag_phone | r.flag_unverified

C = ["#2a78d6", "#eb6834", "#1baf7a"]            # categorical slots 1-3 (blue, orange, aqua)
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
})


# ==============================================================================================================
# Figure 1 — the scatter with quadrants  (two colourings: income group, survey platform)
# ==============================================================================================================
# income: fold the 3 high-income countries into upper-middle so the scatter uses only 3 colours
r["income3"] = r.income.replace({"High income": "Upper-middle & high income",
                                 "Upper middle income": "Upper-middle & high income"})

SRC_LABEL = {"GDQP": "Global Diet Quality Project (Gallup)", "DHS": "DHS", "Other": "Other national survey"}


def scatter_figure(color_col, order, legend_title, fname, legend_labels=None):
    """
    Draw the MDD-W vs PUA scatter. Everything is identical across calls except which column colours the points.
      color_col      column of r holding the 3-level grouping
      order          the 3 levels, in palette order
      legend_title   legend heading
      fname          output stem in figures/
      legend_labels  optional {level: display label}
    """
    legend_labels = legend_labels or {}
    fig, ax = plt.subplots(figsize=(9, 7))

    # -- fitted line, +/-1 residual-SD band, median-PUA split
    xs = np.linspace(0, 100, 200)
    ax.plot(xs, s["intercept"] + s["slope"] * xs, color=INK, lw=1.5, zorder=2)
    ax.fill_between(xs,
                    s["intercept"] + s["slope"] * xs - s["resid_sd"],
                    s["intercept"] + s["slope"] * xs + s["resid_sd"],
                    color=INK, alpha=.06, lw=0, zorder=1)
    ax.axvline(s["pua_split"], color=GRID, lw=1, zorder=0)

    # -- points: filled by group; hollow if the MDD-W survey carries a coverage flag
    for c, g in zip(C, order):
        sub = r[r[color_col] == g]
        ok, fl = sub[~sub.any_flag], sub[sub.any_flag]
        lab = f"{legend_labels.get(g, g)} (n={len(sub)})"
        ax.scatter(ok.pua, ok.mddw, s=38, color=c, edgecolor="white", lw=.8, label=lab, zorder=3)
        ax.scatter(fl.pua, fl.mddw, s=38, facecolor="white", edgecolor=c, lw=1.4, zorder=3)
    ax.scatter([], [], s=38, facecolor="white", edgecolor=MUTED, lw=1.4, label=f"Survey coverage flag (MDD-W survey with ≥10% \nof population excluded, telephone frame, or unverified \nnational coverage)")  # legend entry

    # -- country labels: notable residuals (|t| > 1) plus the two extreme-PUA countries at each end
    name = r[r.notable | r.index.isin(r.nlargest(2, "pua").index) | r.index.isin(r.nsmallest(2, "pua").index)]
    texts = [ax.text(x, y, t, fontsize=7.5, color=INK) for x, y, t in zip(name.pua, name.mddw, name.label)]
    adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color=MUTED, lw=.5), expand=(1.15, 1.3))

    # -- quadrant captions with counts (descriptive wording, not evaluative)
    q = s["quadrant_counts"]
    kw = dict(fontsize=8.5, color=MUTED, style="italic", ha="center")
    
    # ax.text(s["pua_split"] / 2,         97, f"lower unaffordability\nMDD-W above prediction (n={q['lower unaffordability, higher MDD-W than predicted']})", **kw)
    # ax.text((100 + s["pua_split"]) / 2, 97, f"higher unaffordability\nMDD-W above prediction (n={q['higher unaffordability, higher MDD-W than predicted']})", **kw)
    # ax.text(s["pua_split"] * .78,       12, f"lower unaffordability\nMDD-W below prediction (n={q['lower unaffordability, lower MDD-W than predicted']})", **kw)
    # ax.text((100 + s["pua_split"]) / 2,  3, f"higher unaffordability\nMDD-W below prediction (n={q['higher unaffordability, lower MDD-W than predicted']})", **kw)

    # -- axes, title, subtitle, legend, footer
    ax.set(xlim=(-2, 100), ylim=(0, 104),
           xlabel="Share of population unable to afford a healthy diet (PUA, %)",
           ylabel="Women 15–49 achieving minimum dietary diversity (%, MDD-W)")
    ax.set_title("Women's dietary diversity relative to healthy-diet affordability", loc="left", fontsize=13, color=INK, pad=28)
    # ax.text(0, 1.015,
    #             f"n = {s['n']} countries · OLS slope {s['slope']:.2f} (95% bootstrap CI {s['slope_ci95_boot'][0]:.2f} to {s['slope_ci95_boot'][1]:.2f}) · R² = {s['r2']:.2f}\n"
    #             f"shaded band = ±1 residual SD ({s['resid_sd']:.0f} pts) · vertical line = median unaffordability ({s['pua_split']:.0f}%) · labels: |studentized residual| > 1 · LOO-CV R² = {s['loo_cv_r2']:.2f}\n"
    #             f"hollow markers: MDD-W survey with ≥10% of population excluded, telephone frame, or unverified national coverage",
    #             transform=ax.transAxes, fontsize=8, color=MUTED)
    ax.text(0, 1.0,
            f"n = {s['n']} countries; OLS slope {s['slope']:.2f} (95% bootstrap CI {s['slope_ci95_boot'][0]:.2f} - {s['slope_ci95_boot'][1]:.2f}); R² = {s['r2']:.2f}; shaded band = ±1 residual SD ({s['resid_sd']:.0f} pts)\n",
            # f"shaded band = ±1 residual SD ({s['resid_sd']:.0f} pts) · vertical line = median unaffordability ({s['pua_split']:.0f}%) · labels: |studentized residual| > 1 · LOO-CV R² = {s['loo_cv_r2']:.2f}\n"
            # f"hollow markers: MDD-W survey with ≥10% of population excluded, telephone frame, or unverified national coverage",
            transform=ax.transAxes, fontsize=8, color=MUTED)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, .0), fontsize=7.5,
              title=legend_title, title_fontsize=8, alignment='left')
    ax.grid(axis="both", color=GRID, lw=.6, zorder=0)
    fig.text(0.01, 0.005,
             "Sources: FAOSTAT CAHD (July 2026); FAOSTAT SDG 2.2.4 (MDD-W; Global Diet Quality Project, DHS, national surveys); World Bank.",
             fontsize=7, color=MUTED)
    fig.tight_layout()

    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIG / f"{fname}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


# 1a — coloured by World Bank income group (3 bins)
scatter_figure("income3", ["Low income", "Lower middle income", "Upper-middle & high income"],
               "World Bank income group", "fig1_affordability_quality_gap")

# 1b — same figure, coloured by MDD-W survey platform
scatter_figure("mddw_source_group", ["GDQP", "DHS", "Other"],
               "MDD-W survey platform", "fig1b_affordability_quality_gap_by_source", legend_labels=SRC_LABEL)


# ==============================================================================================================
# Figure 2 — residual league table
# ==============================================================================================================
src_order = ["GDQP", "DHS", "Other"]
rr = r.sort_values("resid")

fig, ax = plt.subplots(figsize=(7, 12))

# -- bars coloured by survey platform; small hollow circle just past the bar end marks a coverage flag
colors = rr.mddw_source_group.map(dict(zip(src_order, C)))
ax.barh(rr.label, rr.resid, color=colors, height=.72)
fl = rr[rr.flag_exclusion | rr.flag_phone | rr.flag_unverified]
ax.scatter(fl.resid + np.sign(fl.resid) * 1.2, fl.label, s=18, facecolor="white", edgecolor=INK, lw=.8, zorder=3)

# -- reference lines: zero and +/-1 residual SD
ax.axvline(0, color=INK, lw=1)
for v in (-s["resid_sd"], s["resid_sd"]):
    ax.axvline(v, color=GRID, lw=1, ls="--")

# -- labels, legend, grid
ax.set_xlabel("Observed − predicted MDD-W (percentage points); dashed = ±1 residual SD; ◦ = survey coverage flag")
ax.set_title("MDD-W relative to the level predicted by healthy-diet unaffordability", loc="left", fontsize=11, color=INK)
ax.tick_params(axis="y", labelsize=7.5)
handles = [Patch(color=c, label=lab) for c, lab in
           zip(C, ["Global Diet Quality Project (Gallup)", "DHS", "Other national survey"])]
ax.legend(handles=handles, frameon=False, loc="lower right", fontsize=8, title="MDD-W source", title_fontsize=8)
ax.grid(axis="x", color=GRID, lw=.6, zorder=0)
ax.set_axisbelow(True)
fig.tight_layout()

for ext in ("png", "pdf"):
    fig.savefig(FIG / f"fig2_residual_league_table.{ext}", dpi=200, bbox_inches="tight")

print("figures written to", FIG)
