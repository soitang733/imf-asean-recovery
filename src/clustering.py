from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import RobustScaler

from .config import (
    CORE_CLUSTER_FEATURES,
    OPTIONAL_CLUSTER_FEATURES,
    OPTIONAL_FEATURE_MIN_COVERAGE,
    RANDOM_STATE,
)


def select_cluster_features(features: pd.DataFrame) -> tuple[list[str], dict[str, float]]:
    coverage = {column: float(features[column].notna().mean()) for column in OPTIONAL_CLUSTER_FEATURES}
    selected = [column for column in CORE_CLUSTER_FEATURES if features[column].notna().sum() >= 3]
    selected.extend(
        column for column in OPTIONAL_CLUSTER_FEATURES if coverage[column] >= OPTIONAL_FEATURE_MIN_COVERAGE
    )
    return selected, coverage


def _economic_label(profile: pd.Series, medians: pd.Series) -> str:
    recovery_high = profile["recovery_gap"] >= medians["recovery_gap"]
    inflation_high = profile["inflation_cost"] > medians["inflation_cost"]
    debt_high = profile["debt_cost"] > medians["debt_cost"]
    if recovery_high and not inflation_high and not debt_high:
        return "Resilient recoverers"
    if recovery_high and (inflation_high or debt_high):
        return "Strong but expensive recoverers"
    if not recovery_high and inflation_high and debt_high:
        return "Weak and costly recoverers"
    return "Stable or slow economies"


def run_clustering(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    feature_cols, optional_coverage = select_cluster_features(features)
    complete_core = features.dropna(subset=["country_code"]).copy()
    work = complete_core.dropna(subset=feature_cols).reset_index(drop=True)
    if len(work) < 4 or len(feature_cols) < 2:
        empty = features[["country_code", "country"]].assign(cluster=np.nan, cluster_label="Insufficient data")
        return empty, pd.DataFrame(), {"selected_features": feature_cols, "optional_coverage": optional_coverage}

    scaled = RobustScaler().fit_transform(work[feature_cols])
    evaluations = []
    candidates: dict[tuple[str, int], np.ndarray] = {}
    max_k = min(5, len(work) - 1)
    for k in range(2, max_k + 1):
        models = {
            "kmeans": KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=50),
            "hierarchical": AgglomerativeClustering(n_clusters=k, linkage="ward"),
        }
        for method, model in models.items():
            labels = model.fit_predict(scaled)
            counts = pd.Series(labels).value_counts()
            score = silhouette_score(scaled, labels) if len(counts) > 1 else np.nan
            evaluations.append(
                {
                    "method": method,
                    "k": k,
                    "silhouette": score,
                    "smallest_cluster": int(counts.min()),
                    "economically_reviewable": bool(counts.min() >= 2),
                }
            )
            candidates[(method, k)] = labels

    evaluation = pd.DataFrame(evaluations)
    preferred = evaluation[evaluation["economically_reviewable"]]
    if preferred.empty:
        preferred = evaluation
    best = preferred.sort_values(["silhouette", "smallest_cluster"], ascending=False).iloc[0]
    best_labels = candidates[(best["method"], int(best["k"]))]
    work["cluster"] = best_labels

    profile = work.groupby("cluster")[feature_cols].mean()
    medians = work[feature_cols].median()
    sizes = work["cluster"].value_counts()
    labels = {}
    for cluster, row in profile.iterrows():
        economic_name = _economic_label(row, medians)
        if sizes.loc[cluster] > len(work) / 2:
            economic_name = "Lower-cost and less-volatile majority"
        labels[cluster] = f"Cluster {cluster}: {economic_name}"
    work["cluster_label"] = work["cluster"].map(labels)

    pca = PCA(n_components=2, random_state=RANDOM_STATE).fit_transform(scaled)
    work["pca_1"] = pca[:, 0]
    work["pca_2"] = pca[:, 1]
    result = features[["country_code", "country"]].merge(
        work[["country_code", "cluster", "cluster_label", "pca_1", "pca_2"]],
        on="country_code",
        how="left",
    )
    meta = {
        "selected_features": feature_cols,
        "optional_coverage": optional_coverage,
        "method": str(best["method"]),
        "k": int(best["k"]),
        "silhouette": float(best["silhouette"]),
        "labels": labels,
    }
    return result, evaluation, meta
