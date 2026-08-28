# Validation Methodology

## Purpose

This document describes the Version 1 engineering validation methodology used for the energy telemetry pipeline.

The goal is to convert raw electrical telemetry into a validated dataset by checking timestamp quality, schema consistency, data quality, and physics-based electrical relationships.

## Pipeline Position

Validation is performed after the raw telemetry has been converted to aligned Parquet and after initial cleaning.

```text
Raw CSV/TXT
    |
    v
Aligned Parquet
    |
    v
Sampling analysis
    |
    v
Data audit
    |
    v
Cleaned Parquet
    |
    v
Engineering validation
    |
    v
Validated Parquet
```

## Sampling Validation

Notebook: `notebooks/3_sampling_analysis.ipynb`

The sampling analysis checks:
- row counts per device
- start and end timestamps
- median sampling interval
- minimum and maximum sampling interval
- duplicate timestamps
- backwards timestamps
- gaps greater than 5 minutes
- gaps greater than 1 hour
- gaps greater than 1 day
- consistency of long gaps across devices

## Schema Validation

Script: `scripts/2_schema_validation.py`

Schema validation checks:
- columns present in all datasets
- columns missing from some datasets
- per-device data types
- whether data types match a reference dtype

This is important because not every meter reports every telemetry field.

## Data Audit

Notebook: `notebooks/4_data_audit.ipynb`

The data audit checks each metric for:
- missing values
- zero values
- negative values
- number of unique values
- constant columns
- mean, standard deviation, min, median, max
- extreme values using percentile thresholds

Extreme values are flagged statistically but not automatically removed unless later engineering validation confirms they are invalid.

## Cumulative Counter Validation

Cumulative energy counters are checked for resets, decreasing values, frozen periods, and consistency with instantaneous power.

The main cumulative counter families are:
- active energy
- apparent energy
- capacitive reactive energy
- inductive reactive energy

The original cumulative-energy columns are preserved in the validated dataset.

Derived cumulative energy columns are added separately using trapezoidal integration from instantaneous power measurements:
- `DerivedConsumedActiveEnergy_kWh`
- `DerivedConsumedApparentEnergy_kVAh`
- `DerivedConsumedCapacitiveReactiveEnergy_kvarh`

Integration is not performed across large timestamp gaps.

## Three-Phase Power Validation

Notebook: `notebooks/5_engineering_validation.ipynb`

Three-phase power totals are checked against the sum of phase-level measurements.

Validated power families:
- active power
- apparent power
- capacitive reactive power
- inductive reactive power

General relationship:

```
Three-phase total ~= L1 + L2 + L3
```

Example columns:
- `ActiveThreePhasePower_W`
- `L1ActivePower_W`
- `L2ActivePower_W`
- `L3ActivePower_W`

## Confirmed Polarity Corrections

Engineering validation identified confirmed L2 polarity issues.

Corrections applied in `scripts/6_clean.py`:

| Device | Affected column | Correction |
|---|---|---|
| ULC10 | L2ActivePower_W | multiply by -1 |
| ULC10 | L2ApparentPower_VA | multiply by -1 |
| ULC10 | L2CapacitivePower_var | multiply by -1 |
| ULC12 | L2ActivePower_W | multiply by -1 |

After each polarity correction, the affected three-phase total is rebuilt from the corrected phase values.

## Parent-Child Conservation

Parent meters are compared against the sum of their child meters.

General relationship:

```
Parent meter ~= sum(child meters)
```

This is checked for the main three-phase power families.

Some conservation gaps are expected because the available telemetry does not include every downstream load.

Known expected topology gaps:

| Parent | Reason |
|---|---|
| ADB | ADB also feeds ALC1 and ALC2, which are not included in the telemetry dataset. |
| IUDB | IUDB also feeds UPS1 and UPS2, which are not included in the telemetry dataset. |

## Voltage Validation

Voltage validation checks:
- parent-child voltage consistency
- phase-to-neutral voltage relationships
- line-to-line voltage relationships
- approximate sqrt(3) relationship between phase and line voltage
- phase voltage balance
- line voltage balance

The engineering notebook reports that parent-child voltage comparisons produced mean absolute errors below 0.5%.

## Current Validation

Current validation checks phase-current relationships where the required columns are available.

Main current columns:
- `L1Current_mA`
- `L2Current_mA`
- `L3Current_mA`
- `NeutralCurrentN_mA`

Neutral current is checked where applicable as an approximation against phase-current behavior.

## Frequency Validation

Frequency is checked using:

`L1Frequency_Hzx100`

Validation settings from the code:
- Nominal frequency: 50.0 Hz
- Tolerance: +/- 0.5 Hz
- Sanity range: 40.0 Hz to 60.0 Hz

The stored column is divided by 100 before validation.

## THD Validation

THD checks are performed for current and voltage THD.

Current THD columns:
- `L1CurrentTHD_x10`
- `L2CurrentTHD_x10`
- `L3CurrentTHD_x10`

Voltage THD columns:
- `L1VoltageTHD_x10`
- `L2VoltageTHD_x10`
- `L3VoltageTHD_x10`

The stored THD values are divided by 10 before interpretation as percentages.

Voltage THD above 8% is used as a screening criterion, not as a universal failure rule.

## Maximum Demand Validation

Maximum-demand telemetry is checked for negative values and IQR outliers.

Columns checked:
- `MaximumDemandIAVG_mA`
- `MaximumDemandIL1_mA`
- `MaximumDemandIL2_mA`
- `MaximumDemandIL3_mA`
- `MaximumDemandkWIII_W`
- `MaximumDemandkVAIII_VA`

## Power Factor and Cos Phi Validation

Recorded `PowerFactor` and `CosPhi` fields are retained unchanged.

Derived `PowerFactor` and `CosPhi` fields are added from active/apparent power ratios.

General relationship:

```
PF = active power / apparent power
```

Derived values are clipped to the physical range [-1, 1] and multiplied by 100.

## Cleaning Philosophy

The Version 1 cleaning approach is conservative.

The pipeline:
- preserves original measured cumulative-energy counters
- preserves original PowerFactor and CosPhi fields
- applies only confirmed polarity corrections
- removes only explicitly identified invalid negative-value rows
- adds derived fields separately instead of overwriting original fields
- flags long frozen cumulative-energy periods rather than fabricating replacements
