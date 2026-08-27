from pathlib import Path
import pandas as pd

# =============================================================================
# Configuration
# =============================================================================

# Project root (energydata-master)
BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_DIR = BASE_DIR / "csv"
OUTPUT_DIR = BASE_DIR / "processing" / "parquet_aligned"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COMMON_START = "2018-08-09"
COMMON_END = "2022-04-12"

# =============================================================================
# Locate raw TXT files
# =============================================================================

files = sorted([
    f for f in INPUT_DIR.iterdir()
    if f.suffix == ".txt"
    and f.name not in ["README.txt", "temp.txt"]
])

print(f"Found {len(files)} files.\n")

summary = []

# =============================================================================
# Convert → Align → Save
# =============================================================================

for file in files:

    device = file.stem.upper()

    print("=" * 90)
    print(f"Processing: {device}")

    # -------------------------------------------------------------------------
    # Read raw TXT
    # -------------------------------------------------------------------------

    df = pd.read_csv(
        file,
        parse_dates=["timeval"]
    )

    # -------------------------------------------------------------------------
    # Create datetime index
    # -------------------------------------------------------------------------

    df.set_index("timeval", inplace=True)

    # -------------------------------------------------------------------------
    # Sort timestamps
    # -------------------------------------------------------------------------

    df.sort_index(inplace=True)

    # -------------------------------------------------------------------------
    # Align to common analysis window
    # -------------------------------------------------------------------------

    df = df.loc[COMMON_START:COMMON_END]

    # -------------------------------------------------------------------------
    # Timestamp integrity
    # -------------------------------------------------------------------------

    duplicate_timestamps = df.index.duplicated().sum()

    backwards_timestamps = (
        df.index.to_series().diff() < pd.Timedelta(0)
    ).sum()

    # -------------------------------------------------------------------------
    # Save aligned parquet
    # -------------------------------------------------------------------------

    output_file = OUTPUT_DIR / f"{file.stem}.parquet"

    df.to_parquet(
        output_file,
        engine="pyarrow",
        compression="snappy"
    )

    size_mb = output_file.stat().st_size / 1e6

    print(f"Rows                 : {len(df):,}")
    print(f"Columns              : {len(df.columns)}")
    print(f"Date Start           : {df.index.min()}")
    print(f"Date End             : {df.index.max()}")
    print(f"Duplicate Timestamps : {duplicate_timestamps}")
    print(f"Backwards Timestamps : {backwards_timestamps}")
    print(f"Parquet Size         : {size_mb:.2f} MB")
    print()

    summary.append({

        "Device": device,
        "Rows": len(df),
        "Columns": len(df.columns),

        "Date_Start": df.index.min(),
        "Date_End": df.index.max(),

        "Duplicate_Timestamps": duplicate_timestamps,
        "Backwards_Timestamps": backwards_timestamps,

        "Parquet_Size_MB": round(size_mb, 2)

    })

# =============================================================================
# Save summary
# =============================================================================

summary_df = pd.DataFrame(summary)

summary_file = OUTPUT_DIR / "prepare_parquet_summary.csv"

summary_df.to_csv(summary_file, index=False)

print("=" * 90)
print("Preparation complete.")
print(f"Aligned parquet files : {OUTPUT_DIR}")
print(f"Summary               : {summary_file}")
print("=" * 90)