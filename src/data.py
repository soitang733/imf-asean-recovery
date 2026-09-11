from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
import requests

from .config import (
    ASEAN_COUNTRIES,
    CLEAN_PATH,
    COVERAGE_PATH,
    END_YEAR,
    INDICATORS,
    METADATA_PATH,
    RAW_PATH,
    SDMX_BASE,
    START_YEAR,
    WEO_AGENCY,
    WEO_FLOW,
    WEO_VINTAGE,
    WEO_VERSION,
)


def build_sdmx_url() -> str:
    countries = "+".join(ASEAN_COUNTRIES)
    indicators = "+".join(INDICATORS)
    key = f"{countries}.{indicators}.A"
    return (
        f"{SDMX_BASE}/data/{WEO_AGENCY},{WEO_FLOW},{WEO_VERSION}/{key}"
        f"?startPeriod={START_YEAR}&endPeriod={END_YEAR}"
    )


def fetch_raw_sdmx(raw_path: Path = RAW_PATH, force: bool = False) -> Path:
    """Download and retain the exact structure-specific SDMX 2.1 XML response."""
    if raw_path.exists() and not force:
        return raw_path
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        build_sdmx_url(),
        headers={"Accept": "application/vnd.sdmx.structurespecificdata+xml;version=2.1"},
        timeout=180,
    )
    response.raise_for_status()
    if b"StructureSpecificData" not in response.content[:1000]:
        raise ValueError("Unexpected IMF SDMX response; structure-specific XML was not returned.")
    raw_path.write_bytes(response.content)
    return raw_path


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_sdmx_xml(raw_path: Path = RAW_PATH) -> tuple[pd.DataFrame, dict[str, str]]:
    """Parse COUNTRY/INDICATOR/FREQUENCY series and TIME_PERIOD/OBS_VALUE observations."""
    root = ET.parse(raw_path).getroot()
    dataset = next((element for element in root.iter() if _local_name(element.tag) == "DataSet"), None)
    if dataset is None:
        raise ValueError("SDMX XML does not contain a DataSet element.")

    rows: list[dict] = []
    for series in (element for element in dataset if _local_name(element.tag) == "Series"):
        country_code = series.attrib.get("COUNTRY")
        indicator_code = series.attrib.get("INDICATOR")
        frequency = series.attrib.get("FREQ", series.attrib.get("FREQUENCY"))
        if country_code not in ASEAN_COUNTRIES or indicator_code not in INDICATORS:
            continue
        for observation in (element for element in series if _local_name(element.tag) == "Obs"):
            rows.append(
                {
                    "country_code": country_code,
                    "year": pd.to_numeric(observation.attrib.get("TIME_PERIOD"), errors="coerce"),
                    "indicator_code": indicator_code,
                    "value": pd.to_numeric(observation.attrib.get("OBS_VALUE"), errors="coerce"),
                    "frequency": frequency,
                }
            )
    return pd.DataFrame(rows), dict(dataset.attrib)


def clean_sdmx(raw_path: Path = RAW_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str]]:
    parsed, dataset_attributes = parse_sdmx_xml(raw_path)
    if parsed.empty:
        raise ValueError("No matching observations were found in the SDMX XML response.")
    parsed = parsed[parsed["year"].between(START_YEAR, END_YEAR)].copy()
    parsed["year"] = parsed["year"].astype(int)

    duplicates = parsed[parsed.duplicated(["country_code", "year", "indicator_code"], keep=False)].copy()
    if not duplicates.empty:
        conflicts = duplicates.groupby(["country_code", "year", "indicator_code"])["value"].nunique()
        if (conflicts > 1).any():
            raise ValueError("Conflicting duplicate observations found in IMF data.")
        parsed = parsed.drop_duplicates(["country_code", "year", "indicator_code"], keep="first")

    # Reindex to the full country × indicator × year grid. Absent IMF observations remain NA.
    expected = pd.MultiIndex.from_product(
        [ASEAN_COUNTRIES, INDICATORS, range(START_YEAR, END_YEAR + 1)],
        names=["country_code", "indicator_code", "year"],
    ).to_frame(index=False)
    clean = expected.merge(parsed, on=["country_code", "indicator_code", "year"], how="left")
    clean["country"] = clean["country_code"].map(ASEAN_COUNTRIES)
    clean["indicator_name"] = clean["indicator_code"].map(
        {code: details["name"] for code, details in INDICATORS.items()}
    )
    clean["frequency"] = clean["frequency"].fillna("A")
    clean = clean[
        ["country_code", "country", "year", "indicator_code", "indicator_name", "value", "frequency"]
    ].sort_values(["country_code", "indicator_code", "year"])

    missing_values = clean[clean["value"].isna()].copy()
    return clean.reset_index(drop=True), duplicates, missing_values, dataset_attributes


def build_coverage(clean: pd.DataFrame) -> pd.DataFrame:
    expected_years = set(range(START_YEAR, END_YEAR + 1))
    rows = []
    for code, country in ASEAN_COUNTRIES.items():
        for indicator in INDICATORS:
            sub = clean[(clean["country_code"] == code) & (clean["indicator_code"] == indicator)]
            available = set(sub.loc[sub["value"].notna(), "year"].astype(int))
            missing = sorted(expected_years.difference(available))
            rows.append(
                {
                    "country_code": code,
                    "country": country,
                    "indicator_code": indicator,
                    "available_2015_2024": len(available),
                    "coverage_2015_2024": len(available) / len(expected_years),
                    "missing_years": ",".join(map(str, missing)),
                    "serious_gap": len(available) / len(expected_years) < 0.70,
                }
            )
    return pd.DataFrame(rows)


def prepare_data(force_download: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    raw_path = fetch_raw_sdmx(force=force_download)
    clean, duplicates, missing_values, dataset_attributes = clean_sdmx(raw_path)
    coverage = build_coverage(clean)
    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")
    coverage.to_csv(COVERAGE_PATH, index=False, encoding="utf-8-sig")
    metadata = {
        "dataset": "IMF World Economic Outlook",
        "dataset_code": WEO_FLOW,
        "provider": WEO_AGENCY,
        "vintage": WEO_VINTAGE,
        "retrieved_at": date.today().isoformat(),
        "api_family": "IMF SDMX 2.1 API",
        "frequency": "Annual",
        "historical_analysis_period": f"{START_YEAR}-{END_YEAR}",
        "countries_count": len(ASEAN_COUNTRIES),
        "indicators_count": len(INDICATORS),
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = {
        "raw_rows": int(len(clean) - len(missing_values)),
        "clean_rows": int(len(clean)),
        "duplicate_rows": int(len(duplicates)),
        "missing_value_rows": int(len(missing_values)),
        "sdmx_url": build_sdmx_url(),
        "publication_date": dataset_attributes.get("PUBLICATION_DATE"),
        "update_date": dataset_attributes.get("UPDATE_DATE"),
    }
    return clean, coverage, audit
