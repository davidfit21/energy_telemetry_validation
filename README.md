# Energy Telemetry Validation

## Overview

This repository contains a Version 1 engineering-validation pipeline for an energy telemetry dataset. The project converts raw meter telemetry into Parquet, audits sampling and data quality, applies documented cleaning rules, and validates the resulting dataset using electrical-engineering consistency checks.

The current release should be understood as:

**Version 1 validated dataset + engineering validation methodology**

It is not yet a final academic release. Links to a paper, DOI, Hugging Face dataset, OpenML benchmark, or technical articles should be added only after those outputs exist.

## Research Objective

The objective is to evaluate whether multi-meter building energy telemetry can be transformed into a scientifically useful validated dataset by combining data-quality auditing with physics-grounded electrical validation.

The pipeline addresses questions such as:

* Are timestamps aligned across devices?
* Are cumulative energy counters monotonic and physically usable?
* Do three-phase totals agree with their phase-level measurements?
* Do parent meters approximately conserve power relative to child meters?
* Are voltage, current, frequency, power factor, and maximum-demand measurements physically plausible?
* Which anomalies represent telemetry errors, and which reflect incomplete downstream metering coverage?

## Dataset

The original dataset consists of raw energy telemetry files for 24 electrical devices/meters.

The available device groups include:

* Parent and distribution-board meters: `ADB`, `IUDB`, `NDB`, `UDB1`, `UDB2`, `UDB3`
* Unit load controllers: `ULC1` through `ULC12`
* Cooling/CRAC meters: `CRAC1` through `CRAC6`

The telemetry includes electrical measurements such as:

* Three-phase active, apparent, capacitive reactive, and inductive reactive power
* Phase-level active, apparent, capacitive reactive, and inductive reactive power
* Phase currents
* Neutral current
* Phase-to-neutral and line-to-line voltages
* Frequency
* Power factor and cos phi
* Current and voltage THD
* Maximum demand counters
* Cumulative energy counters

The raw files are stored as CSV-like `.txt` files in the parent `csv/` directory.

The current raw-data source is documented in `csv/README.txt`.

If a formal public source or citation exists for the original dataset, it should replace or supplement the temporary source reference.

## Original Dataset

This project is based on the original energy telemetry dataset published by the original data provider.

The original raw telemetry data are not redistributed in this repository. Users should obtain the original dataset directly from the official source before running the processing and validation pipeline.

**Original dataset repository:**  
[LINK]

**Original dataset / data source:**  
[LINK]

The original dataset should be downloaded and placed in the `csv/` directory before running the processing pipeline.

The original dataset's licensing and data-use conditions apply to the source data. Users should consult the original source for the applicable terms.

## Processing Pipeline

The processing pipeline is organized as numbered scripts and notebooks and should be run in order.

```text
Original CSV/TXT
      |
      v
CSV/TXT to Parquet
      |
      v
Aligned Parquet
      |
      v
Sampling Analysis
      |
      v
Data Audit
      |
      v
Data Cleaning
      |
      v
Cleaned Parquet
      |
      v
Engineering Electrical Validation
      |
      +-- Parent-child conservation
      +-- Voltage relationships
      +-- Current relationships
      +-- Three-phase relationships
      +-- Neutral current approximation
      +-- Energy counter validation
      +-- Maximum demand checks
      +-- Physical plausibility
      +-- Power factor / cos phi
      +-- Frequency
      |
      v
Validated Dataset, Version 1
```

### Pipeline Steps

#### 1. `scripts/1_prepare_parquet.py`

Converts the raw `.txt` telemetry files from `csv/` into aligned Parquet files in `processing/parquet_aligned/`.

The script aligns all datasets to the common analysis window:

* Start: `2018-08-09`
* End: `2022-04-12`

It also records timestamp integrity checks, including duplicate timestamps and backwards timestamps.

#### 2. `scripts/2_schema_validation.py`

Checks column consistency across the aligned Parquet datasets.

This step identifies:

* Columns present in all datasets
* Columns missing from some devices
* Per-device data types
* Schema differences between meters

#### 3. `notebooks/3_sampling_analysis.ipynb`

Audits timestamp spacing and sampling consistency.

This notebook checks:

* Row counts
* Start and end timestamps
* Median, minimum, and maximum sampling intervals
* Duplicate timestamps
* Backwards timestamps
* Gaps greater than 5 minutes, 1 hour, and 1 day
* Whether long gaps are consistent across devices

#### 4. `notebooks/4_data_audit.ipynb`

Performs data-quality auditing on the aligned Parquet files.

This notebook checks:

* Missing values
* Zero values
* Negative values
* Constant columns
* Extreme values using percentile thresholds
* Cumulative energy counter behavior
* Before/after cleaning plots

It also creates the initial cleaned Parquet outputs in `processing/parquet_cleaned/`.

#### 5. `notebooks/5_engineering_validation.ipynb`

Applies the main engineering validation framework to the cleaned datasets.

This notebook validates:

* Three-phase power totals against phase-level sums
* Parent-child power conservation
* Child-meter contribution to parent-meter totals
* Known topology gaps
* Cumulative energy counters
* Voltage consistency
* Phase and line voltage balance
* Frequency plausibility
* THD plausibility
* Maximum demand counters
* Power factor and cos phi consistency

This notebook also identifies confirmed polarity issues later applied by the cleaning script.

#### 6. `scripts/6_clean.py`

Generates the Version 1 validated Parquet datasets in `processing/parquet_validated/`.

This script applies only explicitly identified cleaning and correction rules:

* Removes the first four months of telemetry from each dataset
* Corrects confirmed L2 polarity issues
* Reconstructs affected three-phase totals after polarity correction
* Removes rows with confirmed invalid negative values for selected device/column pairs
* Preserves signed `PowerFactor` and `CosPhi` fields
* Preserves original measured cumulative-energy counters
* Adds derived cumulative energy counters using trapezoidal integration
* Adds derived PowerFactor and CosPhi columns
* Flags long frozen cumulative-energy periods without modifying them

#### 7. `notebooks/7_post_clean_checks.ipynb`

Performs post-validation checks on `processing/parquet_validated/`.

This notebook verifies the final validated datasets after cleaning and engineering corrections.

## Engineering Validation Framework

The validation framework uses physical and topological relationships expected in electrical telemetry.

### Parent-Child Conservation

Parent meters are compared against the summed measurements of their child meters.

Validated topologies include:

* `UDB1` with child meters `ULC1`, `ULC3`, `ULC5`, `ULC7`, `ULC9`, `ULC11`
* `UDB2` with child meters `ULC2`, `ULC4`, `ULC6`, `ULC8`, `ULC10`, `ULC12`
* `ADB` with child meters `CRAC1` through `CRAC6`
* `IUDB` with child meters `UDB1`, `UDB2`, `UDB3`

Known topology gaps are documented where parent load is not fully represented by available downstream telemetry. For example, ADB also supplies ALC1 and ALC2, and IUDB also supplies UPS1 and UPS2.

### Three-Phase Relationships

Three-phase totals are compared with the sum of L1, L2, and L3 measurements for:

* Active power
* Apparent power
* Capacitive reactive power
* Inductive reactive power

Confirmed polarity corrections are applied only where the engineering validation identified a sign inconsistency:

* `ULC10`: `L2ActivePower_W`, `L2ApparentPower_VA`, `L2CapacitivePower_var`
* `ULC12`: `L2ActivePower_W`

The affected three-phase totals are reconstructed from the corrected phase measurements.

### Voltage Relationships

Voltage validation checks:

* Parent-child voltage consistency
* Phase-to-neutral voltage relationships
* Line-to-line voltage relationships
* Approximate √3 relationship between phase and line voltages
* Phase voltage balance
* Line voltage balance

### Current Relationships

Current validation checks phase-current behavior across the meter hierarchy and compares current relationships where topology and available columns permit.

### Neutral Current Approximation

Where neutral current is available, it is checked against phase-current behavior to identify physically implausible current measurements.

### Energy Counter Validation

Cumulative energy counters are checked for decreasing values, resets, frozen periods, and consistency with instantaneous power measurements.

Original measured cumulative-energy fields are retained. Derived cumulative counters are added separately.

Derived counters include:

* `DerivedConsumedActiveEnergy_kWh`
* `DerivedConsumedApparentEnergy_kVAh`
* `DerivedConsumedCapacitiveReactiveEnergy_kvarh`

### Maximum Demand Checks

Maximum-demand telemetry is checked for negative values and statistical outliers.

Validated columns include:

* `MaximumDemandIAVG_mA`
* `MaximumDemandIL1_mA`
* `MaximumDemandIL2_mA`
* `MaximumDemandIL3_mA`
* `MaximumDemandkWIII_W`
* `MaximumDemandkVAIII_VA`

### Physical Plausibility

The pipeline screens telemetry for physically implausible values, including unexpected negatives, extreme values, voltage imbalance, frequency deviations, and inconsistent phase relationships.

### Power Factor / Cos Phi

Recorded `PowerFactor` and `CosPhi` values are retained unchanged.

Derived PowerFactor and CosPhi values are added from active/apparent power ratios:

* `DerivedThreePhasePowerFactor_x100`
* `DerivedThreePhaseCosPhi_x100`
* `DerivedL1PowerFactor_x100`
* `DerivedL1CosPhi_x100`
* `DerivedL2PowerFactor_x100`
* `DerivedL2CosPhi_x100`
* `DerivedL3PowerFactor_x100`
* `DerivedL3CosPhi_x100`

### Frequency

Frequency is checked against a nominal 50 Hz system using a screening tolerance.

## Repository Structure

```text
energy-telemetry-validation/

├── README.md
├── LICENSE
├── .gitignore
│
├── scripts/
│   ├── 1_prepare_parquet.py
│   ├── 2_schema_validation.py
│   └── 6_clean.py
│
└── notebooks/
    ├── 3_sampling_analysis.ipynb
    ├── 4_data_audit.ipynb
    ├── 5_engineering_validation.ipynb
    └── 7_post_clean_checks.ipynb
```

Large raw and intermediate/final Parquet datasets are not stored in this GitHub repository.

## Reproducibility

To reproduce the Version 1 validation pipeline:

### 1. Obtain the original raw telemetry files

Download the original `.txt` telemetry files from the original dataset source.

Place them in:

```text
csv/
```

### 2. Install Python dependencies

The pipeline uses Python with:

* pandas
* numpy
* pyarrow
* matplotlib
* jupyter

### 3. Run the initial processing steps

From the repository root:

```bash
cd processing

python scripts/1_prepare_parquet.py
python scripts/2_schema_validation.py
```

### 4. Run the notebooks in order

```text
notebooks/3_sampling_analysis.ipynb
notebooks/4_data_audit.ipynb
notebooks/5_engineering_validation.ipynb
```

### 5. Generate the final validated Version 1 Parquet files

```bash
python scripts/6_clean.py
```

### 6. Run the post-clean validation

```text
notebooks/7_post_clean_checks.ipynb
```

The expected intermediate and final outputs are:

```text
processing/parquet_aligned/
processing/parquet_cleaned/
processing/parquet_validated/
```

## Validated Dataset

The final validated Version 1 dataset is generated by the validation pipeline and written to:

```text
processing/parquet_validated/
```

The validated dataset will be made available in a separate research-data repository.

The Hugging Face dataset link will be added once it exists.

## Results

The Version 1 validation process established that the telemetry can be made suitable for engineering analysis after documented processing, cleaning, and validation.

Key outcomes include:

* Raw telemetry was converted into aligned Parquet datasets.
* Sampling gaps and timestamp behavior were audited.
* Cumulative energy counter anomalies were identified and cleaned where appropriate.
* Confirmed polarity issues were corrected for specific ULC meters.
* Affected three-phase totals were reconstructed from corrected phase values.
* Parent-child conservation checks were performed across available electrical topology.
* Known topology gaps were identified where downstream loads were not included in the available telemetry.
* Voltage measurements were found to be highly consistent across the electrical hierarchy.
* Derived energy and power-factor fields were added while preserving original measured fields.

More detailed numerical results should be documented separately in the notebooks, validation reports, or a future paper.

## Limitations

This is a Version 1 validated dataset and methodology.

Important limitations include:

* The final academic paper has not yet been published.
* No DOI has been assigned yet.
* No Hugging Face or OpenML release is included yet.
* Some parent-child conservation residuals are caused by incomplete downstream metering coverage.
* Original cumulative energy counters may contain frozen periods or resets.
* Derived energy counters depend on instantaneous power integration and timestamp continuity.
* Validation rules are based on available telemetry columns and known topology information.
* Cleaning corrections are intentionally conservative and only applied where explicitly identified.

## License

The repository code should be licensed according to the `LICENSE` file.

The underlying raw telemetry dataset may be governed by separate terms from the original data provider. Users should check the original dataset source and comply with its data-use conditions.

## Citation

A formal citation will be added once the research release or paper has been published.

For now, cite this repository as a Version 1 engineering-validation pipeline for the energy telemetry dataset.

## Contact

**Maintainer:** Your Name

**GitHub:** `https://github.com/your-github-username`
