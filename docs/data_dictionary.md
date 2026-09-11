# Data dictionary

| Dataset | Indicator | Meaning | Unit | Frequency | Role |
|---|---|---|---|---|---|
| WEO April 2026 | NGDP_RPCH | Real GDP growth | Annual % change | Annual | Required |
| WEO April 2026 | PCPIPCH | Inflation, average consumer prices | Annual % change | Annual | Required |
| WEO April 2026 | GGXWDG_NGDP | General government gross debt | % GDP | Annual | Required |
| WEO April 2026 | LUR | Unemployment rate | % | Annual | Required; NA retained |
| WEO April 2026 | BCA_NGDPD | Current account balance | % GDP | Annual | Required; NA retained |
| World Bank Indicators API | NY.GDP.MKTP.KD.ZG | GDP growth | Annual % change | Annual | External cross-check only |

## Clean data schema

| Field | Description |
|---|---|
| country_code | ISO3-like WEO country code |
| country | Display name |
| year | Annual observation year |
| indicator_code | WEO indicator code |
| value | Numeric observation |
| indicator_name | Human-readable WEO indicator name |
| frequency | SDMX frequency code (`A`) |

## Derived features

| Feature | Formula |
|---|---|
| pre_growth | mean NGDP_RPCH, 2015–2019 |
| covid_growth | NGDP_RPCH, 2020 |
| covid_shock | covid_growth − pre_growth |
| recovery_growth | mean NGDP_RPCH, 2021–2024 |
| recovery_gap | recovery_growth − pre_growth |
| growth_volatility_pre | sample standard deviation, 2015–2019 |
| growth_volatility_post | sample standard deviation, 2021–2024 |
| pre_inflation | mean PCPIPCH, 2015–2019 |
| post_inflation | mean PCPIPCH, 2021–2024 |
| inflation_cost | post_inflation − pre_inflation |
| debt_cost | GGXWDG_NGDP 2024 − 2019 |
| unemployment_change | mean LUR 2021–2024 − mean LUR 2015–2019 |
| current_account_change | mean BCA_NGDPD 2021–2024 − mean BCA_NGDPD 2015–2019 |

Countries are never dropped merely because a few observations are missing. Missing coverage is reported separately.

## IMF–World Bank cross-check schema

| Field | Description |
|---|---|
| country_code | ASEAN-10 country code |
| country | Display name from the IMF configuration |
| year | Annual observation year, 2015–2024 |
| imf_gdp_growth | IMF WEO `NGDP_RPCH` |
| world_bank_gdp_growth | World Bank `NY.GDP.MKTP.KD.ZG` |
| difference_pp | IMF minus World Bank, percentage points |
| absolute_difference_pp | Absolute difference between the two sources |

The World Bank values are validation evidence only. They do not feed the IMF clean dataset, derived features, rankings or clusters.
