# ASEAN post-COVID recovery analysis

## Dataset

- Source: IMF World Economic Outlook, April 2026 vintage, via SDMX 2.1 API.
- Retrieval timestamp: 2026-09-11T02:26:51.435214+00:00.
- IMF publication date in the SDMX response: 2026-04-14T13:00:00Z; update date: 2026-04-15T13:00:00Z.
- Scope: 10 ASEAN economies, five indicators, annual data from 2015 to 2024.
- SDMX query: `https://api.imf.org/external/sdmx/2.1/data/IMF.RES,WEO,+/BRN+KHM+IDN+LAO+MYS+MMR+PHL+SGP+THA+VNM.NGDP_RPCH+PCPIPCH+GGXWDG_NGDP+LUR+BCA_NGDPD.A?startPeriod=2015&endPeriod=2024`
- Raw rows: 470; clean rows: 500; duplicate rows: 0; missing values inside returned observations: 30.

## Missing data and coverage

There are 3 country-indicator pairs with less than 70% coverage during 2015–2024. Countries were not automatically dropped.

The raw IMF WEO April 2026 response contains no LUR series for Cambodia, Lao P.D.R. or Myanmar. These are source-level missing values, not parser failures. They remain NA: no interpolation and no alternative source is used.

| country    | indicator_code   |   coverage_2015_2024 | missing_years                                     |
|:-----------|:-----------------|---------------------:|:--------------------------------------------------|
| Cambodia   | LUR              |                 0.00 | 2015,2016,2017,2018,2019,2020,2021,2022,2023,2024 |
| Lao P.D.R. | LUR              |                 0.00 | 2015,2016,2017,2018,2019,2020,2021,2022,2023,2024 |
| Myanmar    | LUR              |                 0.00 | 2015,2016,2017,2018,2019,2020,2021,2022,2023,2024 |

## Methodology

The pipeline compares 2015–2019 with the 2020 shock and the 2021–2024 recovery, then calculates transparent growth, inflation, debt, labor-market and external-balance features. It detects z-score outliers and evaluates KMeans and Ward hierarchical clustering for k=2 to 5 using only features with complete ASEAN-10 coverage, followed by RobustScaler transformation. Missing values are never imputed. No arbitrary composite recovery score is used.

## Main findings

- The highest recovery gap is observed for **Singapore** (2.12 percentage points versus its pre-COVID baseline).
- The lowest inflation cost is observed for **Indonesia** (-1.03 pp).
- The lowest debt cost is observed for **Vietnam** (-9.83 pp of GDP). These dimensions are not combined into a weighted score.
- Trade-off charts should be treated as descriptive co-movement, not causal evidence.

### Separate-dimension ranking

| country           |   covid_shock |   recovery_gap |   inflation_cost |   debt_cost |   unemployment_change |   current_account_change | tradeoff_profile                        |
|:------------------|--------------:|---------------:|-----------------:|------------:|----------------------:|-------------------------:|:----------------------------------------|
| Singapore         |         -6.72 |           2.12 |             3.81 |       38.36 |                  0.06 |                     0.67 | Above-median recovery + higher cost               |
| Malaysia          |        -10.36 |           0.34 |             0.62 |       12.76 |                  0.46 |                    -0.38 | Above-median recovery + lower inflation/debt cost |
| Brunei Darussalam |          0.66 |           0.01 |             1.62 |       -0.25 |                 -2.85 |                     2.62 | Above-median recovery + lower inflation/debt cost |
| Indonesia         |         -7.10 |          -0.26 |            -1.03 |        9.60 |                  0.06 |                     2.35 | Above-median recovery + lower inflation/debt cost |
| Philippines       |        -16.10 |          -0.45 |             2.24 |       19.65 |                 -0.24 |                    -2.81 | Above-median recovery + higher cost               |
| Thailand          |         -9.51 |          -1.06 |             1.89 |       21.85 |                  0.26 |                    -8.38 | Below-median recovery + higher cost               |
| Vietnam           |         -4.22 |          -1.31 |             0.33 |       -9.83 |                  0.26 |                     1.89 | Below-median recovery + lower cost                |
| Cambodia          |        -10.64 |          -2.82 |             0.49 |        4.90 |                nan    |                    -4.27 | Below-median recovery + lower cost                |
| Lao P.D.R.        |         -6.85 |          -3.35 |            18.46 |       25.55 |                nan    |                    11.17 | Below-median recovery + higher cost               |
| Myanmar           |        -15.35 |          -8.31 |            16.06 |       13.02 |                nan    |                     2.26 | Below-median recovery + higher cost               |

## Strongest outliers

| country           | feature                |   value |   z_score | classification   |
|:------------------|:-----------------------|--------:|----------:|:-----------------|
| Myanmar           | growth_volatility_post |    6.98 |      2.54 | negative_outlier |
| Myanmar           | recovery_gap           |   -8.31 |     -2.51 | negative_outlier |
| Brunei Darussalam | unemployment_change    |   -2.85 |     -2.41 | positive_outlier |
| Lao P.D.R.        | current_account_change |   11.17 |      2.17 | positive_outlier |
| Lao P.D.R.        | inflation_cost         |   18.46 |      2.14 | negative_outlier |

## Cluster interpretation

The dashboard recomputes KMeans and hierarchical solutions from complete-coverage features only: covid_shock, recovery_gap, inflation_cost, debt_cost, growth_volatility_post and current_account_change. LUR is excluded and no missing value is imputed.

The leading solution separates Brunei as a one-country cluster. Treat this as an exploratory outlier pattern, not a stable ASEAN typology. The remaining nine economies are explicitly labeled heterogeneous rather than being assigned a common economic profile.

| country           |   cluster | cluster_label                                    |
|:------------------|----------:|:-------------------------------------------------|
| Brunei Darussalam |         0 | Cluster 0: Singleton pattern (interpret cautiously) |
| Cambodia          |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |
| Indonesia         |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |
| Lao P.D.R.        |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |
| Malaysia          |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |
| Myanmar           |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |
| Philippines       |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |
| Singapore         |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |
| Thailand          |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |
| Vietnam           |         1 | Cluster 1: Other ASEAN economies (heterogeneous)    |

## Top three candidate stories

### 1. Similar COVID shock, different recovery

**Countries:** Lao P.D.R.; Singapore

**Evidence:** COVID shocks: -6.85 vs -6.72; recovery gaps: -3.35 vs 2.12 pp.

**Interpretation:** The two economies recovered at different speeds after comparable 2020 shocks.

**Alternative explanation:** Sector composition, policy support, reopening timing, and base effects may differ.

**Limitation:** Descriptive comparison does not identify which factor caused the divergence.

### 2. Strong recovery with a high inflation bill

**Countries:** Singapore

**Evidence:** Recovery gap 2.12 pp; inflation cost 3.81 pp.

**Interpretation:** Growth recovery and higher inflation appeared together.

**Alternative explanation:** Global food and energy shocks may drive inflation independently of domestic recovery.

**Limitation:** Co-movement is not evidence that recovery caused inflation.

### 3. Debt rose while recovery stayed weak

**Countries:** Myanmar

**Evidence:** Debt cost 13.02 pp of GDP; recovery gap -8.31 pp.

**Interpretation:** Higher debt and weaker recovery occurred at the same time.

**Alternative explanation:** Debt definitions, automatic stabilizers, exchange rates, and denominator effects can matter.

**Limitation:** Gross debt is not net debt and is not directly comparable for every institutional setting.

## Figures

- `outputs/figures/01_gdp_growth.png`
- `outputs/figures/02_inflation.png`
- `outputs/figures/03_debt_cost.png`
- `outputs/figures/04_recovery_vs_inflation.png`
- `outputs/figures/05_recovery_vs_debt.png`
- `outputs/figures/06_feature_heatmap.png`
- `outputs/figures/07_clusters.png`

## Limitations

- WEO observations may be revised. This extract ends in 2024 and does not mix later forecasts into the analysis.
- Missing unemployment and current-account data reduce cross-country comparability; optional features enter clustering only when coverage is sufficient.
- Gross debt is not net debt. Singapore is a notable institutional-comparability case.
- Period averages can hide within-period turning points and base effects.
- Outlier results are sensitive to a sample of only 10 countries.
- Clusters summarize similarity; they do not prove common causes or future performance.
