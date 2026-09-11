from __future__ import annotations

import numpy as np
import pandas as pd

from .config import OUTLIER_Z_THRESHOLD


FEATURE_DIRECTIONS = {
    "covid_shock": "higher_is_better",
    "recovery_gap": "higher_is_better",
    "inflation_cost": "lower_is_better",
    "debt_cost": "lower_is_better",
    "growth_volatility_post": "lower_is_better",
    "unemployment_change": "lower_is_better",
    "current_account_change": "higher_is_better",
}


def detect_outliers(features: pd.DataFrame, threshold: float = OUTLIER_Z_THRESHOLD) -> pd.DataFrame:
    rows = []
    for feature, direction in FEATURE_DIRECTIONS.items():
        values = pd.to_numeric(features[feature], errors="coerce")
        valid = values.dropna()
        if len(valid) < 3 or valid.std(ddof=0) == 0:
            continue
        zscores = (values - valid.mean()) / valid.std(ddof=0)
        for index in zscores[zscores.abs() >= threshold].index:
            z = float(zscores.loc[index])
            desirable_sign = 1 if direction == "higher_is_better" else -1
            classification = "positive_outlier" if np.sign(z) == desirable_sign else "negative_outlier"
            rows.append(
                {
                    "country_code": features.loc[index, "country_code"],
                    "country": features.loc[index, "country"],
                    "feature": feature,
                    "value": values.loc[index],
                    "z_score": z,
                    "classification": classification,
                    "economic_direction": direction,
                }
            )
    columns = [
        "country_code",
        "country",
        "feature",
        "value",
        "z_score",
        "classification",
        "economic_direction",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values("z_score", key=lambda x: x.abs(), ascending=False)

