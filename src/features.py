from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ASEAN_COUNTRIES, COVID_YEAR, FEATURE_PATH, PRE_YEARS, RECOVERY_YEARS


def _series(df: pd.DataFrame, country_code: str, indicator: str) -> pd.Series:
    sub = df[(df["country_code"] == country_code) & (df["indicator_code"] == indicator)]
    return sub.set_index("year")["value"].sort_index()


def _mean(series: pd.Series, years: list[int]) -> float:
    return float(series.reindex(years).mean()) if not series.empty else np.nan


def _std(series: pd.Series, years: list[int]) -> float:
    return float(series.reindex(years).std(ddof=1)) if not series.empty else np.nan


def _at(series: pd.Series, year: int) -> float:
    value = series.get(year, np.nan)
    return float(value) if pd.notna(value) else np.nan


def build_country_features(clean: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for code, country in ASEAN_COUNTRIES.items():
        gdp = _series(clean, code, "NGDP_RPCH")
        inflation = _series(clean, code, "PCPIPCH")
        debt = _series(clean, code, "GGXWDG_NGDP")
        unemployment = _series(clean, code, "LUR")
        current_account = _series(clean, code, "BCA_NGDPD")

        pre_growth = _mean(gdp, PRE_YEARS)
        covid_growth = _at(gdp, COVID_YEAR)
        recovery_growth = _mean(gdp, RECOVERY_YEARS)
        pre_inflation = _mean(inflation, PRE_YEARS)
        post_inflation = _mean(inflation, RECOVERY_YEARS)
        debt_2019 = _at(debt, 2019)
        debt_2024 = _at(debt, 2024)
        pre_unemployment = _mean(unemployment, PRE_YEARS)
        post_unemployment = _mean(unemployment, RECOVERY_YEARS)
        pre_current_account = _mean(current_account, PRE_YEARS)
        post_current_account = _mean(current_account, RECOVERY_YEARS)

        rows.append(
            {
                "country_code": code,
                "country": country,
                "pre_growth": pre_growth,
                "covid_growth": covid_growth,
                "covid_shock": covid_growth - pre_growth,
                "recovery_growth": recovery_growth,
                "recovery_gap": recovery_growth - pre_growth,
                "growth_volatility_pre": _std(gdp, PRE_YEARS),
                "growth_volatility_post": _std(gdp, RECOVERY_YEARS),
                "pre_inflation": pre_inflation,
                "post_inflation": post_inflation,
                "inflation_cost": post_inflation - pre_inflation,
                "debt_2019": debt_2019,
                "debt_2024": debt_2024,
                "debt_cost": debt_2024 - debt_2019,
                "pre_unemployment": pre_unemployment,
                "post_unemployment": post_unemployment,
                "unemployment_change": post_unemployment - pre_unemployment,
                "pre_current_account": pre_current_account,
                "post_current_account": post_current_account,
                "current_account_change": post_current_account - pre_current_account,
            }
        )
    result = pd.DataFrame(rows)
    FEATURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(FEATURE_PATH, index=False, encoding="utf-8-sig")
    return result


def build_transparent_ranking(features: pd.DataFrame) -> pd.DataFrame:
    """Rank separate dimensions; intentionally do not create a weighted composite score."""
    ranked = features.copy()
    ranked["rank_recovery_gap"] = ranked["recovery_gap"].rank(ascending=False, method="min")
    ranked["rank_low_inflation_cost"] = ranked["inflation_cost"].rank(ascending=True, method="min")
    ranked["rank_low_debt_cost"] = ranked["debt_cost"].rank(ascending=True, method="min")
    ranked["rank_unemployment_improvement"] = ranked["unemployment_change"].rank(ascending=True, method="min")
    ranked["rank_external_improvement"] = ranked["current_account_change"].rank(ascending=False, method="min")
    recovery_median = ranked["recovery_gap"].median()
    inflation_median = ranked["inflation_cost"].median()
    debt_median = ranked["debt_cost"].median()
    ranked["tradeoff_profile"] = ranked.apply(
        lambda row: (
            "Above-median recovery + lower inflation/debt cost"
            if row["recovery_gap"] >= recovery_median
            and row["inflation_cost"] <= inflation_median
            and row["debt_cost"] <= debt_median
            else "Above-median recovery + higher cost"
            if row["recovery_gap"] >= recovery_median
            and (row["inflation_cost"] > inflation_median or row["debt_cost"] > debt_median)
            else "Below-median recovery + higher cost"
            if row["recovery_gap"] < recovery_median
            and (row["inflation_cost"] > inflation_median or row["debt_cost"] > debt_median)
            else "Below-median recovery + lower cost"
        ),
        axis=1,
    )
    return ranked.sort_values("recovery_gap", ascending=False).reset_index(drop=True)
