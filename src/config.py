from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"

RAW_PATH = DATA_DIR / "raw_imf_weo.xml"
CLEAN_PATH = DATA_DIR / "clean_imf_weo.csv"
METADATA_PATH = DATA_DIR / "metadata.json"
FEATURE_PATH = DATA_DIR / "country_features.csv"
COVERAGE_PATH = OUTPUT_DIR / "data_coverage.csv"
RANKING_PATH = OUTPUT_DIR / "ranking_recovery.csv"
OUTLIER_PATH = OUTPUT_DIR / "outliers.csv"
CLUSTER_PATH = OUTPUT_DIR / "clusters.csv"
CLUSTER_EVAL_PATH = OUTPUT_DIR / "cluster_evaluation.csv"
STORY_PATH = OUTPUT_DIR / "candidate_stories.csv"
SUMMARY_PATH = PROJECT_ROOT / "analysis_summary.md"

SDMX_BASE = "https://api.imf.org/external/sdmx/2.1"
WEO_AGENCY = "IMF.RES"
WEO_FLOW = "WEO"
WEO_VERSION = "+"
WEO_VINTAGE = "April 2026"
START_YEAR = 2015
END_YEAR = 2024
PRE_YEARS = list(range(2015, 2020))
COVID_YEAR = 2020
RECOVERY_YEARS = list(range(2021, 2025))

# The assignment uses the ASEAN-10 analytical scope.
ASEAN_COUNTRIES = {
    "BRN": "Brunei Darussalam",
    "KHM": "Cambodia",
    "IDN": "Indonesia",
    "LAO": "Lao P.D.R.",
    "MYS": "Malaysia",
    "MMR": "Myanmar",
    "PHL": "Philippines",
    "SGP": "Singapore",
    "THA": "Thailand",
    "VNM": "Vietnam",
}

INDICATORS = {
    "NGDP_RPCH": {"name": "Real GDP growth", "unit": "Percent change", "required": True},
    "PCPIPCH": {"name": "Inflation, average consumer prices", "unit": "Percent change", "required": True},
    "GGXWDG_NGDP": {"name": "General government gross debt", "unit": "Percent of GDP", "required": True},
    "LUR": {"name": "Unemployment rate", "unit": "Percent", "required": True},
    "BCA_NGDPD": {"name": "Current account balance", "unit": "Percent of GDP", "required": True},
}

CORE_CLUSTER_FEATURES = [
    "covid_shock",
    "recovery_gap",
    "inflation_cost",
    "debt_cost",
    "growth_volatility_post",
]
OPTIONAL_CLUSTER_FEATURES = ["unemployment_change", "current_account_change"]
# A feature may enter clustering only when every ASEAN-10 economy has a value.
# This prevents model-time imputation from disguising source-level IMF gaps.
OPTIONAL_FEATURE_MIN_COVERAGE = 1.00
OUTLIER_Z_THRESHOLD = 2.0
RANDOM_STATE = 42
