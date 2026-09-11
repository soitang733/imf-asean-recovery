from __future__ import annotations

import argparse

from src.crosscheck import run_world_bank_crosscheck


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-check IMF WEO GDP growth with World Bank data.")
    parser.add_argument("--force-download", action="store_true", help="Refresh World Bank raw JSON.")
    args = parser.parse_args()
    comparison, summary = run_world_bank_crosscheck(force_download=args.force_download)
    print(f"Comparison rows: {len(comparison)}")
    print(f"Countries: {summary['country_code'].nunique()}")
    print(summary.to_string(index=False))
