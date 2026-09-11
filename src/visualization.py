from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler

from .clustering import select_cluster_features
from .config import FIGURE_DIR


sns.set_theme(style="whitegrid", context="notebook")


def _save(fig: plt.Figure, filename: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _line_chart(clean: pd.DataFrame, indicator: str, title: str, ylabel: str, filename: str) -> None:
    data = clean[(clean["indicator_code"] == indicator) & clean["year"].between(2015, 2024)]
    fig, ax = plt.subplots(figsize=(12, 6.5))
    sns.lineplot(data=data, x="year", y="value", hue="country", marker="o", ax=ax)
    ax.axvline(2020, color="#222222", linestyle="--", linewidth=1.2, label="COVID shock (2020)")
    ax.axvspan(2015, 2019, color="#4C72B0", alpha=0.05)
    ax.axvspan(2021, 2024, color="#55A868", alpha=0.05)
    ax.set(title=title, xlabel="Year", ylabel=ylabel)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    _save(fig, filename)


def generate_figures(clean: pd.DataFrame, features: pd.DataFrame, clusters: pd.DataFrame) -> list[str]:
    generated = []
    _line_chart(clean, "NGDP_RPCH", "ASEAN real GDP growth: shock and recovery", "Percent", "01_gdp_growth.png")
    generated.append("01_gdp_growth.png")
    _line_chart(clean, "PCPIPCH", "ASEAN inflation before and after COVID-19", "Percent", "02_inflation.png")
    generated.append("02_inflation.png")

    debt = features.sort_values("debt_cost")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    colors = np.where(debt["debt_cost"] >= 0, "#C44E52", "#55A868")
    ax.barh(debt["country"], debt["debt_cost"], color=colors)
    ax.axvline(0, color="#222222", linewidth=1)
    ax.set(title="Change in government gross debt, 2019–2024", xlabel="Percentage points of GDP", ylabel="")
    fig.text(
        0.01,
        0.01,
        "Note: Singapore gross debt is not a measure of net debt; interpret with government assets and institutional context.",
        fontsize=8,
        color="#555555",
    )
    _save(fig, "03_debt_cost.png")
    generated.append("03_debt_cost.png")

    trade = features.dropna(subset=["inflation_cost", "recovery_gap", "debt_cost"])
    fig, ax = plt.subplots(figsize=(10, 7))
    sizes = 80 + 25 * trade["debt_cost"].abs()
    ax.scatter(trade["inflation_cost"], trade["recovery_gap"], s=sizes, alpha=0.72, color="#4C72B0", edgecolor="white")
    for _, row in trade.iterrows():
        ax.annotate(row["country"], (row["inflation_cost"], row["recovery_gap"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.axhline(0, color="#777777", linewidth=0.9)
    ax.axvline(0, color="#777777", linewidth=0.9)
    ax.set(title="Recovery versus inflation cost", xlabel="Inflation cost (pp)", ylabel="Recovery gap (pp)")
    _save(fig, "04_recovery_vs_inflation.png")
    generated.append("04_recovery_vs_inflation.png")

    trade = features.dropna(subset=["debt_cost", "recovery_gap"])
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(trade["debt_cost"], trade["recovery_gap"], s=130, alpha=0.75, color="#DD8452", edgecolor="white")
    for _, row in trade.iterrows():
        ax.annotate(row["country"], (row["debt_cost"], row["recovery_gap"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.axhline(0, color="#777777", linewidth=0.9)
    ax.axvline(0, color="#777777", linewidth=0.9)
    ax.set(title="Recovery versus debt cost", xlabel="Debt cost (pp of GDP)", ylabel="Recovery gap (pp)")
    _save(fig, "05_recovery_vs_debt.png")
    generated.append("05_recovery_vs_debt.png")

    feature_cols, _ = select_cluster_features(features)
    heat = features.set_index("country")[feature_cols]
    imputed = SimpleImputer(strategy="median").fit_transform(heat)
    standardized = RobustScaler().fit_transform(imputed)
    heat_scaled = pd.DataFrame(standardized, index=heat.index, columns=feature_cols)
    fig, ax = plt.subplots(figsize=(11, 7))
    sns.heatmap(heat_scaled, cmap="RdYlBu_r", center=0, linewidths=0.4, ax=ax)
    ax.set(title="Standardized ASEAN shock, recovery and cost features", xlabel="", ylabel="")
    _save(fig, "06_feature_heatmap.png")
    generated.append("06_feature_heatmap.png")

    plot_clusters = clusters.dropna(subset=["pca_1", "pca_2", "cluster_label"])
    if not plot_clusters.empty:
        fig, ax = plt.subplots(figsize=(10, 7))
        sns.scatterplot(data=plot_clusters, x="pca_1", y="pca_2", hue="cluster_label", s=150, ax=ax)
        label_offsets = {
            "Cambodia": (5, 8),
            "Philippines": (5, -10),
            "Indonesia": (5, -9),
            "Vietnam": (5, 7),
        }
        for _, row in plot_clusters.iterrows():
            offset = label_offsets.get(row["country"], (5, 4))
            ax.annotate(
                row["country"],
                (row["pca_1"], row["pca_2"]),
                xytext=offset,
                textcoords="offset points",
                fontsize=8,
            )
        ax.set(title="Data-selected cluster solution (PCA view)", xlabel="PCA component 1", ylabel="PCA component 2")
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
        _save(fig, "07_clusters.png")
        generated.append("07_clusters.png")
    return generated
