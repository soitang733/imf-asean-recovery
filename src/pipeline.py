from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from .clustering import run_clustering
from .config import (
    ASEAN_COUNTRIES,
    CLUSTER_EVAL_PATH,
    CLUSTER_PATH,
    OUTLIER_PATH,
    RANKING_PATH,
    STORY_PATH,
    SUMMARY_PATH,
    WEO_VINTAGE,
)
from .data import prepare_data
from .features import build_country_features, build_transparent_ranking
from .outliers import detect_outliers
from .story_mining import mine_candidate_stories
from .visualization import generate_figures


def _markdown_table(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> str:
    view = df[columns].head(limit) if limit else df[columns]
    return view.to_markdown(index=False, floatfmt=".2f")


def write_summary(
    coverage: pd.DataFrame,
    features: pd.DataFrame,
    ranking: pd.DataFrame,
    outliers: pd.DataFrame,
    clusters: pd.DataFrame,
    cluster_meta: dict,
    stories: pd.DataFrame,
    audit: dict,
    figures: list[str],
) -> None:
    serious = coverage[coverage["serious_gap"]]
    strongest_outliers = outliers.head(8)
    top_stories = stories.head(3)
    best_recovery = ranking.dropna(subset=["recovery_gap"]).iloc[0]
    lowest_inflation = ranking.dropna(subset=["inflation_cost"]).sort_values("inflation_cost").iloc[0]
    lowest_debt = ranking.dropna(subset=["debt_cost"]).sort_values("debt_cost").iloc[0]
    lines = [
        "# ASEAN post-COVID recovery analysis",
        "",
        "## Dataset",
        "",
        f"- Source: IMF World Economic Outlook, {WEO_VINTAGE} vintage, via SDMX 2.1 API.",
        f"- Retrieval timestamp: {datetime.now(timezone.utc).isoformat()}.",
        f"- IMF publication date in the SDMX response: {audit.get('publication_date')}; update date: {audit.get('update_date')}.",
        f"- Scope: {len(ASEAN_COUNTRIES)} ASEAN economies, five indicators, annual data from 2015 to 2024.",
        f"- SDMX query: `{audit['sdmx_url']}`",
        f"- Raw rows: {audit['raw_rows']}; clean rows: {audit['clean_rows']}; duplicate rows: {audit['duplicate_rows']}; missing values inside returned observations: {audit['missing_value_rows']}.",
        "",
        "## Missing data and coverage",
        "",
        f"There are {len(serious)} country-indicator pairs with less than 70% coverage during 2015–2024. Countries were not automatically dropped.",
        "",
    ]
    if not serious.empty:
        lines.extend([_markdown_table(serious, ["country", "indicator_code", "coverage_2015_2024", "missing_years"]), ""])
    lines.extend(
        [
            "## Methodology",
            "",
            "The pipeline compares 2015–2019 with the 2020 shock and the 2021–2024 recovery, then calculates transparent growth, inflation, debt, labor-market and external-balance features. It detects z-score outliers and evaluates KMeans and Ward hierarchical clustering for k=2 to 5 after median imputation and RobustScaler transformation. No arbitrary composite recovery score is used.",
            "",
            "## Main findings",
            "",
            f"- The highest recovery gap is observed for **{best_recovery['country']}** ({best_recovery['recovery_gap']:.2f} percentage points versus its pre-COVID baseline).",
            f"- The lowest inflation cost is observed for **{lowest_inflation['country']}** ({lowest_inflation['inflation_cost']:.2f} pp).",
            f"- The lowest debt cost is observed for **{lowest_debt['country']}** ({lowest_debt['debt_cost']:.2f} pp of GDP). These dimensions are not combined into a weighted score.",
            "- Trade-off charts should be treated as descriptive co-movement, not causal evidence.",
            "",
            "### Separate-dimension ranking",
            "",
            _markdown_table(ranking, ["country", "covid_shock", "recovery_gap", "inflation_cost", "debt_cost", "unemployment_change", "current_account_change", "tradeoff_profile"]),
            "",
            "## Strongest outliers",
            "",
        ]
    )
    lines.append(
        _markdown_table(strongest_outliers, ["country", "feature", "value", "z_score", "classification"])
        if not strongest_outliers.empty
        else "No feature exceeded the configured absolute z-score threshold."
    )
    lines.extend(
        [
            "",
            "## Cluster interpretation",
            "",
            f"Selected method: {cluster_meta.get('method', 'not available')}; k={cluster_meta.get('k', 'NA')}; silhouette={cluster_meta.get('silhouette', float('nan')):.3f}.",
            f"Features used: {', '.join(cluster_meta.get('selected_features', []))}.",
            "Cluster names were assigned only after examining cluster profiles.",
            "",
            _markdown_table(clusters.dropna(subset=["cluster_label"]), ["country", "cluster", "cluster_label"])
            if clusters["cluster_label"].notna().any()
            else "Insufficient data for a defensible cluster solution.",
            "",
            "## Top three candidate stories",
            "",
        ]
    )
    for index, row in top_stories.iterrows():
        lines.extend(
            [
                f"### {index + 1}. {row['title']}",
                "",
                f"**Countries:** {row['countries_involved']}",
                "",
                f"**Evidence:** {row['evidence']}",
                "",
                f"**Interpretation:** {row['interpretation']}",
                "",
                f"**Alternative explanation:** {row['alternative_explanation']}",
                "",
                f"**Limitation:** {row['limitation']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Figures",
            "",
            *[f"- `outputs/figures/{name}`" for name in figures],
            "",
            "## Limitations",
            "",
            "- WEO observations may be revised. This extract ends in 2024 and does not mix later forecasts into the analysis.",
            "- Missing unemployment and current-account data reduce cross-country comparability; optional features enter clustering only when coverage is sufficient.",
            "- Gross debt is not net debt. Singapore is a notable institutional-comparability case.",
            "- Period averages can hide within-period turning points and base effects.",
            f"- Outlier results are sensitive to a sample of only {len(ASEAN_COUNTRIES)} countries.",
            "- Clusters summarize similarity; they do not prove common causes or future performance.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_pipeline(force_download: bool = False) -> dict:
    clean, coverage, audit = prepare_data(force_download=force_download)
    features = build_country_features(clean)
    ranking = build_transparent_ranking(features)
    outliers = detect_outliers(features)
    clusters, cluster_evaluation, cluster_meta = run_clustering(features)
    stories = mine_candidate_stories(features, outliers)

    RANKING_PATH.parent.mkdir(parents=True, exist_ok=True)
    ranking.to_csv(RANKING_PATH, index=False, encoding="utf-8-sig")
    outliers.to_csv(OUTLIER_PATH, index=False, encoding="utf-8-sig")
    clusters.to_csv(CLUSTER_PATH, index=False, encoding="utf-8-sig")
    cluster_evaluation.to_csv(CLUSTER_EVAL_PATH, index=False, encoding="utf-8-sig")
    stories.to_csv(STORY_PATH, index=False, encoding="utf-8-sig")
    figures = generate_figures(clean, features, clusters)
    write_summary(coverage, features, ranking, outliers, clusters, cluster_meta, stories, audit, figures)
    return {
        "clean": clean,
        "coverage": coverage,
        "features": features,
        "ranking": ranking,
        "outliers": outliers,
        "clusters": clusters,
        "cluster_evaluation": cluster_evaluation,
        "cluster_meta": cluster_meta,
        "stories": stories,
        "audit": audit,
        "figures": figures,
    }
