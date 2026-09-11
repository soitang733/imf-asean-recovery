import argparse

from src.pipeline import run_pipeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ASEAN IMF WEO shock-recovery pipeline.")
    parser.add_argument("--force-download", action="store_true", help="Refresh the raw SDMX response.")
    args = parser.parse_args()
    result = run_pipeline(force_download=args.force_download)
    print(
        f"Pipeline complete: {len(result['clean'])} observations, "
        f"{len(result['features'])} countries, {len(result['stories'])} candidate stories."
    )

