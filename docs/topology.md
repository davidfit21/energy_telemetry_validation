# Electrical Topology

## Purpose

This document describes the electrical meter topology used by the Version 1 validation pipeline.

The topology is used to test whether parent-meter measurements are consistent with the sum of downstream child-meter measurements.

## Device Groups

The dataset contains 24 device telemetry files.

```text
ADB
IUDB
NDB
UDB1
UDB2
UDB3
ULC1
ULC2
ULC3
ULC4
ULC5
ULC6
ULC7
ULC8
ULC9
ULC10
ULC11
ULC12
CRAC1
CRAC2
CRAC3
CRAC4
CRAC5
CRAC6
```

## Main Parent-Child Relationships

The validation notebooks define the following parent-child relationships.

### UDB1 Branch

```text
UDB1
├── ULC1
├── ULC3
├── ULC5
├── ULC7
├── ULC9
└── ULC11
```

### UDB2 Branch

```text
UDB2
├── ULC2
├── ULC4
├── ULC6
├── ULC8
├── ULC10
└── ULC12
```

### ADB Branch

```text
ADB
├── CRAC1
├── CRAC2
├── CRAC3
├── CRAC4
├── CRAC5
└── CRAC6
```

### IUDB Branch

```text
IUDB
├── UDB1
├── UDB2
└── UDB3
```

## Known Missing Downstream Loads

Some parent-child conservation differences are expected because the available telemetry does not include every downstream load.

### ADB

The engineering validation notebook records that ADB also supplies:
- ALC1
- ALC2

These are not represented in the available telemetry dataset.

Therefore, ADB parent-child residuals should not automatically be interpreted as meter faults.

### IUDB

The engineering validation notebook records that IUDB also supplies:
- UPS1
- UPS2

These are not represented in the available telemetry dataset.

Therefore, IUDB conservation residuals are expected to reflect incomplete downstream metering coverage.

## Validation Use

The topology is used for parent-child conservation tests.

General relationship:

```
Parent ~= sum(children)
```

This is checked for:
- active power
- apparent power
- capacitive reactive power
- inductive reactive power

## ULC Pair Comparisons

The engineering validation notebook also compares paired ULC meters.

Pairs:

```
ULC1  <-> ULC2
ULC3  <-> ULC4
ULC5  <-> ULC6
ULC7  <-> ULC8
ULC9  <-> ULC10
ULC11 <-> ULC12
```

These comparisons are used to inspect differences between corresponding branch meters.

## Confirmed Device-Specific Corrections

The validation identified confirmed polarity issues in selected ULC meters.

### ULC10

Corrected fields:
- L2ActivePower_W
- L2ApparentPower_VA
- L2CapacitivePower_var

Rebuilt totals:
- ActiveThreePhasePower_W
- ApparentThreePhasePower_VA
- CapacitiveThreePhasePower_var

### ULC12

Corrected field:
- L2ActivePower_W

Rebuilt total:
- ActiveThreePhasePower_W

## Interpretation Notes

Parent-child conservation is not treated as a simple pass/fail test in all cases.

A residual may indicate:
- measurement error
- polarity error
- missing child telemetry
- incomplete topology information
- valid unmetered downstream load

The Version 1 pipeline therefore combines conservation tests with engineering interpretation.
