# Reproducibility

## Purpose

This document explains how to reproduce the Version 1 processing and validation pipeline.

The pipeline should be run in numeric order using the scripts and notebooks in `processing/`.

## Expected Repository Layout

```text
energydata-master/
├── csv/
│   ├── README.txt
│   ├── adb.txt
│   ├── crac1.txt
│   ├── ...
│   └── ulc12.txt
└── processing/
    ├── scripts/
    │   ├── 1_prepare_parquet.py
    │   ├── 2_schema_validation.py
    │   └── 6_clean.py
    ├── notebooks/
    │   ├── 3_sampling_analysis.ipynb
    │   ├── 4_data_audit.ipynb
    │   ├── 5_engineering_validation.ipynb
    │   └── 7_post_clean_checks.ipynb
    ├── parquet_aligned/
    ├── parquet_cleaned/
    └── parquet_validated/
```

## Raw Data

The raw telemetry files are expected in:

`csv/`

The files are `.txt` files that are read using `pandas.read_csv`.

The timestamp column is:

`timeval`

The current raw-data pointer is listed in `csv/README.txt`.

## Python Requirements

The code uses:
- pandas
- numpy
- pyarrow
- matplotlib
- jupyter

A minimal install command is:

```
pip install pandas numpy pyarrow matplotlib jupyter
```

## Step 1: Prepare Aligned Parquet

Run:

```
cd processing
python scripts/1_prepare_parquet.py
```

This script:
- reads `.txt` files from `../csv/`
- parses `timeval` as datetime
- sets `timeval` as the index
- sorts timestamps
- aligns all datasets to the common window
- writes Parquet files to `parquet_aligned/`

Common window: `2018-08-09` to `2022-04-12`

Output: `processing/parquet_aligned/`

The script also writes: `processing/parquet_aligned/prepare_parquet_summary.csv`

## Step 2: Validate Schema

Run:

```
python scripts/2_schema_validation.py
```

This script checks the aligned Parquet files for:
- common columns
- missing columns
- dtype consistency

Input: `processing/parquet_aligned/`

## Step 3: Sampling Analysis

Run notebook:

`notebooks/3_sampling_analysis.ipynb`

This notebook checks:
- timestamp intervals
- duplicate timestamps
- backwards timestamps
- long gaps
- consistency of gaps across devices

Input: `processing/parquet_aligned/`

## Step 4: Data Audit and Initial Cleaning

Run notebook:

`notebooks/4_data_audit.ipynb`

This notebook audits:
- missing values
- zeros
- negatives
- constants
- extremes
- cumulative energy counters

It also produces cleaned Parquet files.

Input: `processing/parquet_aligned/`
Output: `processing/parquet_cleaned/`

## Step 5: Engineering Validation

Run notebook:

`notebooks/5_engineering_validation.ipynb`

This notebook validates:
- three-phase totals against L1 + L2 + L3
- parent-child conservation
- current relationships
- voltage relationships
- neutral current behavior
- cumulative energy counters
- frequency
- THD
- maximum demand
- power factor and cos phi

Input: `processing/parquet_cleaned/`

The findings from this notebook are used by the final cleaning script.

## Step 6: Generate Validated Dataset

Run:

```
python scripts/6_clean.py
```

This script reads: `processing/parquet_cleaned/`
and writes: `processing/parquet_validated/`

It applies the confirmed Version 1 rules:
- remove first 4 months of telemetry from each dataset
- correct confirmed polarity issues
- rebuild affected three-phase totals
- remove selected invalid negative-value rows
- preserve original PowerFactor and CosPhi fields
- preserve original cumulative-energy counters
- add derived cumulative energy counters
- add derived PowerFactor and CosPhi fields
- flag long frozen cumulative-energy periods

## Step 7: Post-Clean Checks

Run notebook:

`notebooks/7_post_clean_checks.ipynb`

This notebook checks the final validated Parquet files.

Input: `processing/parquet_validated/`

## Expected Output Folders

After successful reproduction, the following folders should exist:

```
processing/parquet_aligned/
processing/parquet_cleaned/
processing/parquet_validated/
```

## Notes

- Run the scripts and notebooks in numeric order.
- Some notebooks contain exploratory validation and plots.
- Some validation findings are interpretive, especially parent-child topology gaps.
- The final Version 1 dataset is the contents of `processing/parquet_validated/`.
- The pipeline is conservative: original measured fields are generally retained, and derived fields are added separately.
