# Presentation and defense script

## Five-minute story

### 0:00–0:40 Question

Our question is not simply which ASEAN country grew fastest. We ask which country recovered relative to its own pre-COVID baseline, and what inflation, debt, labor-market and external-balance conditions accompanied that recovery.

### 0:40–1:20 Data

We use the April 2026 IMF WEO vintage through the SDMX 2.1 API. The key follows `COUNTRY.INDICATOR.FREQUENCY`. It requests the assignment's ASEAN-10 scope, five indicators and annual data from 2015 to 2024. Our COVID analysis compares 2015–2019, 2020 and 2021–2024.

### 1:20–2:20 Shock and recovery

The GDP chart shows a shared shock but different magnitudes. The derived feature `covid_shock` subtracts each country’s pre-COVID average from its 2020 growth. `recovery_gap` compares 2021–2024 average growth with the same baseline.

### 2:20–3:30 Strongest story

Lao P.D.R. and Singapore had similar COVID shocks, about -6.85 and -6.72 percentage points. Their recovery gaps then diverged: -3.35 for Lao P.D.R. and +2.12 for Singapore. Lao P.D.R. also had a large inflation cost, while Singapore moved above its former growth baseline.

### 3:30–4:25 Costs and outliers

Myanmar is the clearest negative outlier in recovery gap and post-COVID growth volatility. Lao P.D.R. is an inflation-cost outlier. Singapore is a gross-debt outlier, but we must not interpret gross debt as net debt because its government also holds substantial assets.

### 4:25–5:00 Conclusion

There is no cost-free recovery pattern common to ASEAN. Similar shocks can lead to different paths, while high growth may coexist with inflation, debt or external imbalances. These are descriptive relationships, not causal estimates.

## Three-minute data defense

### What does the API request?

Dataset `IMF.RES,WEO,+`; ten country codes; five indicator codes; annual frequency `A`; years 2015–2024. The raw response is saved as structure-specific SDMX XML. The parser reads Series and Obs attributes, then retains missing observations as NA in a complete country × indicator × year grid.

### How is missing data handled?

The pipeline builds a complete country-by-indicator coverage grid. It does not drop a country for missing years. LUR is absent for Cambodia, Lao P.D.R., Myanmar and Timor-Leste, so unemployment does not enter clustering.

### How are forecasts handled?

The request ends in 2024, so 2025–2026 forecasts are not mixed into the main analysis. If forecasts are added later, they must be stored with an explicit actual/estimate/forecast status.

### Why RobustScaler?

The feature table contains strong outliers, especially inflation and volatility. RobustScaler uses the median and interquartile range and is less dominated by extreme values.

### How is k selected?

The pipeline evaluates KMeans and Ward hierarchical clustering for k=2 through 5. It prefers solutions without singleton clusters, then selects the highest silhouette score. The current result is KMeans k=2 with silhouette approximately 0.438.

### Is there a recovery score?

No. Separate ranks and trade-off plots are used. Story-mining heuristics locate candidate patterns but do not claim a universal winner.
