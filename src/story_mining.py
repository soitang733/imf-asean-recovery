from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd


def _z(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    std = values.std(ddof=0)
    return (values - values.mean()) / std if pd.notna(std) and std else values * 0


def _fmt(value) -> str:
    return "missing" if pd.isna(value) else f"{value:.2f}"


def _story(
    title: str,
    countries: str,
    evidence: str,
    indicators: str,
    metrics: str,
    surprising: str,
    chart: str,
    interpretation: str,
    alternative: str,
    limitation: str,
) -> dict:
    return {
        "title": title,
        "countries_involved": countries,
        "evidence": evidence,
        "relevant_indicators": indicators,
        "derived_metrics": metrics,
        "why_it_is_surprising": surprising,
        "recommended_chart": chart,
        "interpretation": interpretation,
        "alternative_explanation": alternative,
        "limitation": limitation,
    }


def mine_candidate_stories(features: pd.DataFrame, outliers: pd.DataFrame) -> pd.DataFrame:
    work = features.copy()
    for column in ["recovery_gap", "inflation_cost", "debt_cost", "unemployment_change", "current_account_change"]:
        work[f"z_{column}"] = _z(work[column])
    stories = []

    pairs = []
    for left, right in combinations(work.index, 2):
        a, b = work.loc[left], work.loc[right]
        shock_distance = abs(a["covid_shock"] - b["covid_shock"])
        recovery_distance = abs(a["recovery_gap"] - b["recovery_gap"])
        pairs.append((recovery_distance / (shock_distance + 0.25), a, b))
    _, a, b = max(pairs, key=lambda item: item[0])
    stories.append(
        _story(
            "Similar COVID shock, different recovery",
            f"{a['country']}; {b['country']}",
            f"COVID shocks: {_fmt(a['covid_shock'])} vs {_fmt(b['covid_shock'])}; recovery gaps: {_fmt(a['recovery_gap'])} vs {_fmt(b['recovery_gap'])} pp.",
            "NGDP_RPCH",
            "covid_shock; recovery_gap",
            "Similar initial damage was followed by sharply different medium-term growth paths.",
            "GDP growth line chart with pre-COVID baseline",
            "The two economies recovered at different speeds after comparable 2020 shocks.",
            "Sector composition, policy support, reopening timing, and base effects may differ.",
            "Descriptive comparison does not identify which factor caused the divergence.",
        )
    )

    strong_recovery = work[work["recovery_gap"] >= work["recovery_gap"].median()].copy()
    row = strong_recovery.assign(
        signal=strong_recovery["z_recovery_gap"] + strong_recovery["z_inflation_cost"]
    ).sort_values("signal", ascending=False).iloc[0]
    stories.append(
        _story(
            "Strong recovery with a high inflation bill",
            row["country"],
            f"Recovery gap {_fmt(row['recovery_gap'])} pp; inflation cost {_fmt(row['inflation_cost'])} pp.",
            "NGDP_RPCH; PCPIPCH",
            "recovery_gap; inflation_cost",
            "Above-peer recovery coincides with above-peer inflation pressure.",
            "Inflation cost vs recovery gap scatter",
            "Growth recovery and higher inflation appeared together.",
            "Global food and energy shocks may drive inflation independently of domestic recovery.",
            "Co-movement is not evidence that recovery caused inflation.",
        )
    )

    row = work.assign(signal=work["z_debt_cost"] - work["z_recovery_gap"]).sort_values("signal", ascending=False).iloc[0]
    stories.append(
        _story(
            "Debt rose while recovery stayed weak",
            row["country"],
            f"Debt cost {_fmt(row['debt_cost'])} pp of GDP; recovery gap {_fmt(row['recovery_gap'])} pp.",
            "GGXWDG_NGDP; NGDP_RPCH",
            "debt_cost; recovery_gap",
            "A large fiscal balance-sheet change did not coincide with an equally strong growth recovery.",
            "Debt cost vs recovery gap scatter",
            "Higher debt and weaker recovery occurred at the same time.",
            "Debt definitions, automatic stabilizers, exchange rates, and denominator effects can matter.",
            "Gross debt is not net debt and is not directly comparable for every institutional setting.",
        )
    )

    contained_pool = work[work["recovery_gap"] >= work["recovery_gap"].median()].copy()
    row = contained_pool.assign(
        signal=contained_pool["z_recovery_gap"]
        - contained_pool["z_inflation_cost"]
        - contained_pool["z_debt_cost"]
    ).sort_values("signal", ascending=False).iloc[0]
    stories.append(
        _story(
            "Recovery with contained inflation and debt costs",
            row["country"],
            f"Recovery gap {_fmt(row['recovery_gap'])}; inflation cost {_fmt(row['inflation_cost'])}; debt cost {_fmt(row['debt_cost'])}.",
            "NGDP_RPCH; PCPIPCH; GGXWDG_NGDP",
            "recovery_gap; inflation_cost; debt_cost",
            "The economy combines relatively strong recovery with two relatively contained costs.",
            "Bubble trade-off chart",
            "The post-COVID macro mix is favorable relative to ASEAN peers on these dimensions.",
            "A low debt change may reflect denominator growth, accounting coverage, or pre-existing fiscal space.",
            "The conclusion is relative to this sample and period, not a universal resilience ranking.",
        )
    )

    if not outliers.empty:
        out = outliers.iloc[0]
        stories.append(
            _story(
                "ASEAN's clearest statistical outlier",
                out["country"],
                f"{out['feature']}={_fmt(out['value'])}, z-score={_fmt(out['z_score'])}.",
                out["feature"],
                out["feature"],
                "The standardized value lies at least two standard deviations from the ASEAN mean.",
                "Standardized-feature heatmap",
                f"The country is unusually different on {out['feature']} within this sample.",
                "A structural country characteristic or measurement convention may explain the outlier.",
                "With only ten countries, z-scores are sensitive to individual observations.",
            )
        )

    candidates = work[(work["recovery_growth"] > 0) & (work["recovery_gap"] < 0)]
    if not candidates.empty:
        row = candidates.sort_values("recovery_gap").iloc[0]
        stories.append(
            _story(
                "Positive growth, but still below the old baseline",
                row["country"],
                f"Recovery growth {_fmt(row['recovery_growth'])}%; recovery gap {_fmt(row['recovery_gap'])} pp.",
                "NGDP_RPCH",
                "recovery_growth; recovery_gap",
                "Headline growth is positive even though the post-COVID average remains below the pre-COVID norm.",
                "GDP baseline-to-recovery comparison",
                "The economy resumed growth without fully regaining its earlier pace.",
                "Pre-COVID growth may itself have been unusually high or unsustainable.",
                "Period averages hide year-to-year changes and revisions.",
            )
        )

    unemployment = work.dropna(subset=["unemployment_change"])
    if not unemployment.empty:
        row = unemployment.assign(
            signal=unemployment["z_recovery_gap"] + unemployment["z_unemployment_change"]
        ).sort_values("signal", ascending=False).iloc[0]
        stories.append(
            _story(
                "Growth recovery without equal labor-market improvement",
                row["country"],
                f"Recovery gap {_fmt(row['recovery_gap'])}; unemployment change {_fmt(row['unemployment_change'])} pp.",
                "NGDP_RPCH; LUR",
                "recovery_gap; unemployment_change",
                "Output recovery does not automatically imply lower unemployment.",
                "Recovery gap vs unemployment change scatter",
                "GDP and labor-market recovery moved differently.",
                "Labor-force participation and informal employment can affect the unemployment rate.",
                "WEO unemployment coverage is incomplete for several ASEAN economies.",
            )
        )

    external = work.dropna(subset=["current_account_change"])
    if not external.empty:
        row = external.assign(
            signal=external["z_recovery_gap"] - external["z_current_account_change"]
        ).sort_values("signal", ascending=False).iloc[0]
        stories.append(
            _story(
                "Recovery accompanied by a weaker external balance",
                row["country"],
                f"Recovery gap {_fmt(row['recovery_gap'])}; current-account change {_fmt(row['current_account_change'])} pp of GDP.",
                "NGDP_RPCH; BCA_NGDPD",
                "recovery_gap; current_account_change",
                "Stronger activity coincides with a deterioration in the external balance.",
                "Recovery gap vs current-account change scatter",
                "Recovery and a weaker current account appeared together.",
                "Stronger investment or temporary commodity-price effects may widen a deficit.",
                "A current-account deficit is not automatically a vulnerability; financing quality matters.",
            )
        )

    return pd.DataFrame(stories).drop_duplicates("title").reset_index(drop=True)
