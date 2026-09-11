from pathlib import Path

import pandas as pd

from src.data import build_coverage, build_sdmx_url, clean_sdmx
from src.features import build_country_features, build_transparent_ranking
from src.clustering import select_cluster_features


def test_sdmx_url_contains_required_dimensions():
    url = build_sdmx_url()
    assert "IMF.RES,WEO,+" in url
    assert ".NGDP_RPCH+PCPIPCH+GGXWDG_NGDP+LUR+BCA_NGDPD.A" in url
    assert "TLS" not in url
    assert "startPeriod=2015&endPeriod=2024" in url


def test_feature_formulas():
    rows = []
    for indicator, values in {
        "NGDP_RPCH": {2015: 4, 2016: 4, 2017: 4, 2018: 4, 2019: 4, 2020: -2, 2021: 5, 2022: 5, 2023: 5, 2024: 5},
        "PCPIPCH": {2015: 2, 2016: 2, 2017: 2, 2018: 2, 2019: 2, 2021: 3, 2022: 3, 2023: 3, 2024: 3},
        "GGXWDG_NGDP": {2019: 40, 2024: 50},
    }.items():
        for year, value in values.items():
            rows.append({"country_code": "BRN", "indicator_code": indicator, "year": year, "value": value})
    result = build_country_features(pd.DataFrame(rows)).set_index("country_code").loc["BRN"]
    assert result["covid_shock"] == -6
    assert result["recovery_gap"] == 1
    assert result["inflation_cost"] == 1
    assert result["debt_cost"] == 10


def test_coverage_keeps_missing_countries():
    clean = pd.DataFrame(
        [{"country_code": "BRN", "indicator_code": "NGDP_RPCH", "year": 2024, "value": 1.0}]
    )
    coverage = build_coverage(clean)
    assert coverage["country_code"].nunique() == 10
    assert len(coverage) == 50


def test_incomplete_optional_feature_is_not_used_for_clustering():
    features = pd.DataFrame(
        {
            "covid_shock": [1.0] * 10,
            "recovery_gap": [1.0] * 10,
            "inflation_cost": [1.0] * 10,
            "debt_cost": [1.0] * 10,
            "growth_volatility_post": [1.0] * 10,
            "unemployment_change": [1.0] * 7 + [float("nan")] * 3,
            "current_account_change": [1.0] * 10,
        }
    )
    selected, coverage = select_cluster_features(features)
    assert coverage["unemployment_change"] == 0.7
    assert "unemployment_change" not in selected
    assert "current_account_change" in selected


def test_tradeoff_profile_names_the_median_rule():
    features = pd.DataFrame(
        {
            "recovery_gap": [-1.0, 1.0],
            "inflation_cost": [0.0, 2.0],
            "debt_cost": [0.0, 2.0],
            "unemployment_change": [0.0, 0.0],
            "current_account_change": [0.0, 0.0],
        }
    )
    ranked = build_transparent_ranking(features)
    assert ranked["tradeoff_profile"].str.contains("median").all()


def test_structure_specific_xml_parser_keeps_explicit_na(tmp_path: Path):
    raw = tmp_path / "sample.xml"
    raw.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
        <message:StructureSpecificData xmlns:message="urn:message">
          <message:DataSet PUBLICATION_DATE="2026-04-14T13:00:00Z">
            <Series COUNTRY="BRN" INDICATOR="NGDP_RPCH" FREQUENCY="A">
              <Obs TIME_PERIOD="2015" OBS_VALUE="1.5"/>
              <Obs TIME_PERIOD="2016"/>
            </Series>
          </message:DataSet>
        </message:StructureSpecificData>""",
        encoding="utf-8",
    )
    clean, duplicates, missing, attributes = clean_sdmx(raw)
    assert list(clean.columns) == [
        "country_code", "country", "year", "indicator_code", "indicator_name", "value", "frequency"
    ]
    assert len(clean) == 500
    assert clean.query("country_code == 'BRN' and indicator_code == 'NGDP_RPCH' and year == 2015")["value"].iloc[0] == 1.5
    assert clean.query("country_code == 'BRN' and indicator_code == 'NGDP_RPCH' and year == 2016")["value"].isna().iloc[0]
    assert duplicates.empty
    assert not missing.empty
    assert attributes["PUBLICATION_DATE"].startswith("2026-04-14")
