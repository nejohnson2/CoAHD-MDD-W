"""
01_download.py — fetch raw inputs into data/raw/

Run first. Files already on disk are skipped, so re-running is cheap.

Sources
-------
FAOSTAT CAHD   Cost and Affordability of a Healthy Diet.
               Item 7005 = % of population unable to afford a healthy diet (PUA); item 70040 = cost in PPP$/day.
FAOSTAT SDGB   SDG indicators. Item 24049-F-Y15T49T = SDG 2.2.4 MDD-W, national, no urban/rural split.
               (FAOSTAT's standalone "MDDW" domain has only ~25 surveys; SDGB is the SOFI 2026 series.)
World Bank     Country metadata (region, income group) and GDP per capita PPP (NY.GDP.PCAP.PP.KD).

Bulk-zip URLs come from https://bulks-faostat.fao.org/production/datasets_E.json
"""
import logging
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------------------------------
# Paths and URLs
# --------------------------------------------------------------------------------------------------------------
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

FAOSTAT = {
    "CAHD": "https://bulks-faostat.fao.org/production/Cost_Affordability_Healthy_Diet_(CoAHD)_E_All_Data_(Normalized).zip",
    "SDGB": "https://bulks-faostat.fao.org/production/SDG_BulkDownloads_E_All_Data_(Normalized).zip",
}

WORLD_BANK = {
    # region + income group for every economy
    "wb_countries.json": "https://api.worldbank.org/v2/country?format=json&per_page=400",
    # GDP per capita, PPP, constant 2021 int$; one page is enough (≈2 900 rows for 2015-2025)
    "wb_gdp_pcap_ppp.json": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.PP.KD"
                            "?format=json&per_page=5000&date=2015:2025",
}


# --------------------------------------------------------------------------------------------------------------
# Helper
# --------------------------------------------------------------------------------------------------------------
def fetch(url: str, dest: Path) -> None:
    """Stream a URL to disk with a progress bar. Skips the download if `dest` already exists."""
    if dest.exists():
        log.info("exists, skipping: %s", dest.name)
        return

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as bar:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
                bar.update(len(chunk))


# --------------------------------------------------------------------------------------------------------------
# 1. FAOSTAT bulk zips -> data/raw/<CODE>/*.csv
# --------------------------------------------------------------------------------------------------------------
for code, url in FAOSTAT.items():
    zpath = RAW / f"{code}.zip"
    fetch(url, zpath)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(RAW / code)
        log.info("%s -> %s", code, z.namelist())

# --------------------------------------------------------------------------------------------------------------
# 2. World Bank JSON
# --------------------------------------------------------------------------------------------------------------
for name, url in WORLD_BANK.items():
    fetch(url, RAW / name)

log.info("done")
