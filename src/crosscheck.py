from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
import requests

from .config import (
    ASEAN_COUNTRIES,
    CLEAN_PATH,
    END_YEAR,
    START_YEAR,
    WB_COMPARISON_PATH,
    WB_RAW_PATH,
    WB_SUMMARY_PATH,
)


WB_INDICATOR = "NY.GDP.MKTP.KD.ZG"
WB_API_BASE = "https://api.worldbank.org/v2"


def build_world_bank_url(country_code: str) -> str:
    return f"{WB_API_BASE}/country/{country_code}/indicator/{WB_INDICATOR}"


def fetch_world_bank_raw(force: bool = False) -> dict:
    """Retrieve World Bank GDP growth for validation only and retain raw JSON."""
    if WB_RAW_PATH.exists() and not force:
        return json.loads(WB_RAW_PATH.read_text(encoding="utf-8-sig"))

    session = requests.Session()
    session.headers.update({"User-Agent": "IMF-WEO-ASEAN-Crosscheck/1.0"})
    responses: dict[str, list] = {}
    for country_code in ASEAN_COUNTRIES:
        response = session.get(
            build_world_bank_url(country_code),
            params={
                "date": f"{START_YEAR}:{END_YEAR}",
                "format": "json",
                "per_page": 100,
            },
            timeout=60,
        )
        response.raise_for_status()
        responses[country_code] = response.json()

    raw = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "World Bank Indicators API v2",
        "indicator": WB_INDICATOR,
        "period": f"{START_YEAR}-{END_YEAR}",
        "responses": responses,
    }
    WB_RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    WB_RAW_PATH.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return raw


def parse_world_bank_raw(raw: dict) -> pd.DataFrame:
    rows = []
    for country_code, payload in raw.get("responses", {}).items():
        observations = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        for observation in observations or []:
            year = pd.to_numeric(observation.get("date"), errors="coerce")
            value = pd.to_numeric(observation.get("value"), errors="coerce")
            if pd.isna(year) or not START_YEAR <= int(year) <= END_YEAR:
                continue
            rows.append(
                {
                    "country_code": country_code,
                    "year": int(year),
                    "world_bank_gdp_growth": float(value) if pd.notna(value) else pd.NA,
                }
            )
    return pd.DataFrame(
        rows,
        columns=["country_code", "year", "world_bank_gdp_growth"],
    )


def build_gdp_crosscheck(imf_clean: pd.DataFrame, world_bank: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create a complete comparison grid without replacing either source's values."""
    expected = pd.MultiIndex.from_product(
        [ASEAN_COUNTRIES, range(START_YEAR, END_YEAR + 1)],
        names=["country_code", "year"],
    ).to_frame(index=False)
    expected["country"] = expected["country_code"].map(ASEAN_COUNTRIES)

    imf = imf_clean[imf_clean["indicator_code"] == "NGDP_RPCH"][
        ["country_code", "year", "value"]
    ].rename(columns={"value": "imf_gdp_growth"})
    comparison = expected.merge(imf, on=["country_code", "year"], how="left")
    comparison = comparison.merge(world_bank, on=["country_code", "year"], how="left")
    comparison["difference_pp"] = (
        comparison["imf_gdp_growth"] - comparison["world_bank_gdp_growth"]
    )
    comparison["absolute_difference_pp"] = comparison["difference_pp"].abs()
    comparison = comparison[
        [
            "country_code",
            "country",
            "year",
            "imf_gdp_growth",
            "world_bank_gdp_growth",
            "difference_pp",
            "absolute_difference_pp",
        ]
    ].sort_values(["country_code", "year"])

    summaries = []
    for country_code, country in ASEAN_COUNTRIES.items():
        group = comparison[comparison["country_code"] == country_code]
        paired = group.dropna(subset=["imf_gdp_growth", "world_bank_gdp_growth"])
        missing_years = group.loc[group["world_bank_gdp_growth"].isna(), "year"].astype(int).tolist()
        summaries.append(
            {
                "country_code": country_code,
                "country": country,
                "paired_observations": len(paired),
                "world_bank_missing_years": ",".join(map(str, missing_years)),
                "mean_difference_pp": paired["difference_pp"].mean(),
                "mean_absolute_difference_pp": paired["absolute_difference_pp"].mean(),
                "max_absolute_difference_pp": paired["absolute_difference_pp"].max(),
            }
        )
    return comparison.reset_index(drop=True), pd.DataFrame(summaries)


def run_world_bank_crosscheck(force_download: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = fetch_world_bank_raw(force=force_download)
    world_bank = parse_world_bank_raw(raw)
    imf_clean = pd.read_csv(CLEAN_PATH)
    comparison, summary = build_gdp_crosscheck(imf_clean, world_bank)
    WB_COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(WB_COMPARISON_PATH, index=False, encoding="utf-8-sig")
    summary.to_csv(WB_SUMMARY_PATH, index=False, encoding="utf-8-sig")
    return comparison, summary
