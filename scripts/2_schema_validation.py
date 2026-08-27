from pathlib import Path
import pandas as pd

# =============================================================================
# Configuration
# =============================================================================

# Project root (energydata-master)
BASE_DIR = Path(__file__).resolve().parents[2]

PARQUET_DIR = BASE_DIR / "processing" / "parquet_aligned"

# =============================================================================
# Locate parquet files
# =============================================================================

files = sorted(PARQUET_DIR.glob("*.parquet"))

print(f"Checking schema for {len(files)} datasets...\n")

# =============================================================================
# Read schemas
# =============================================================================

schemas = {}
dtypes = {}

for file in files:

    device = file.stem.upper()

    df = pd.read_parquet(file)

    schemas[device] = set(df.columns)
    dtypes[device] = df.dtypes.astype(str).to_dict()

# =============================================================================
# Column consistency
# =============================================================================

all_columns = set.union(*schemas.values())
common_columns = set.intersection(*schemas.values())

print("=" * 100)
print(f"Columns present in ALL datasets ({len(common_columns)})")
print("=" * 100)

for col in sorted(common_columns):
    print(col)

print("\n" + "=" * 100)
print(f"Columns NOT present in all datasets ({len(all_columns - common_columns)})")
print("=" * 100)

for col in sorted(all_columns - common_columns):

    present = sorted(
        device for device, cols in schemas.items()
        if col in cols
    )

    missing = sorted(
        device for device, cols in schemas.items()
        if col not in cols
    )

    print(f"\n{col}")
    print(f"  Present ({len(present)}): {present}")
    print(f"  Missing ({len(missing)}): {missing}")

# =============================================================================
# Build schema matrix
# =============================================================================

rows = []

for col in sorted(all_columns):

    expected_dtype = None

    for device in sorted(schemas):

        present = col in schemas[device]

        dtype = dtypes[device].get(col, None)

        if expected_dtype is None and dtype is not None:
            expected_dtype = dtype

        dtype_match = (
            dtype == expected_dtype
            if present
            else None
        )

        rows.append({

            "Column": col,
            "Device": device,

            "Present": present,

            "Data_Type": dtype,

            "Matches_Reference_Dtype": dtype_match

        })

schema_df = pd.DataFrame(rows)

print("Schema validation complete.")
