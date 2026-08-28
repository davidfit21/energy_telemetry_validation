# Data Dictionary

## Purpose

This document describes the main telemetry columns used in the Version 1 processing and validation pipeline.

Not every device contains every column. Use `scripts/2_schema_validation.py` to inspect actual column availability per device.

## Device Groups

### Parent and Distribution Meters

```text
ADB
IUDB
NDB
UDB1
UDB2
UDB3
```

### Unit Load Controllers

```text
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
```

### CRAC Meters

```text
CRAC1
CRAC2
CRAC3
CRAC4
CRAC5
CRAC6
```

## Timestamp Index

The raw telemetry uses a timestamp column:

`timeval`

During Parquet preparation this becomes the DataFrame datetime index.

The common aligned analysis window is:

`2018-08-09` to `2022-04-12`

## Power Columns

### Three-Phase Power

| Column | Meaning | Unit |
|---|---|---|
| ActiveThreePhasePower_W | total three-phase active power | W |
| ApparentThreePhasePower_VA | total three-phase apparent power | VA |
| CapacitiveThreePhasePower_var | total three-phase capacitive reactive power | var |
| InductiveThreePhasePower_var | total three-phase inductive reactive power | var |

### Phase Active Power

| Column | Meaning | Unit |
|---|---|---|
| L1ActivePower_W | L1 active power | W |
| L2ActivePower_W | L2 active power | W |
| L3ActivePower_W | L3 active power | W |

### Phase Apparent Power

| Column | Meaning | Unit |
|---|---|---|
| L1ApparentPower_VA | L1 apparent power | VA |
| L2ApparentPower_VA | L2 apparent power | VA |
| L3ApparentPower_VA | L3 apparent power | VA |

### Phase Capacitive Reactive Power

| Column | Meaning | Unit |
|---|---|---|
| L1CapacitivePower_var | L1 capacitive reactive power | var |
| L2CapacitivePower_var | L2 capacitive reactive power | var |
| L3CapacitivePower_var | L3 capacitive reactive power | var |

### Phase Inductive Reactive Power

| Column | Meaning | Unit |
|---|---|---|
| L1InductivePower_var | L1 inductive reactive power | var |
| L2InductivePower_var | L2 inductive reactive power | var |
| L3InductivePower_var | L3 inductive reactive power | var |

## Current Columns

| Column | Meaning | Unit |
|---|---|---|
| L1Current_mA | L1 current | mA |
| L2Current_mA | L2 current | mA |
| L3Current_mA | L3 current | mA |
| NeutralCurrentN_mA | neutral current | mA |

## Voltage Columns

### Phase-to-Neutral Voltage

| Column | Meaning | Stored unit |
|---|---|---|
| L1PhaseVoltage_Vx10 | L1 phase voltage | V x 10 |
| L2PhaseVoltage_Vx10 | L2 phase voltage | V x 10 |
| L3PhaseVoltage_Vx10 | L3 phase voltage | V x 10 |

### Line-to-Line Voltage

| Column | Meaning | Stored unit |
|---|---|---|
| L1L2Voltage_Vx10 | L1-L2 line voltage | V x 10 |
| L2L3Voltage_Vx10 | L2-L3 line voltage | V x 10 |
| L3L1Voltage_Vx10 | L3-L1 line voltage | V x 10 |

## Frequency

| Column | Meaning | Stored unit |
|---|---|---|
| L1Frequency_Hzx100 | frequency | Hz x 100 |

To convert to Hz:

```
frequency_Hz = L1Frequency_Hzx100 / 100
```

## THD Columns

### Current THD

| Column | Meaning | Stored unit |
|---|---|---|
| L1CurrentTHD_x10 | L1 current THD | percent x 10 |
| L2CurrentTHD_x10 | L2 current THD | percent x 10 |
| L3CurrentTHD_x10 | L3 current THD | percent x 10 |

### Voltage THD

| Column | Meaning | Stored unit |
|---|---|---|
| L1VoltageTHD_x10 | L1 voltage THD | percent x 10 |
| L2VoltageTHD_x10 | L2 voltage THD | percent x 10 |
| L3VoltageTHD_x10 | L3 voltage THD | percent x 10 |

To convert to percent:

```
THD_percent = THD_column / 10
```

## Power Factor and Cos Phi

### Recorded Fields

| Column | Meaning | Stored unit |
|---|---|---|
| ThreePhasePowerFactor_x100 | recorded three-phase power factor | PF x 100 |
| L1PowerFactor_x100 | recorded L1 power factor | PF x 100 |
| L2PowerFactor_x100 | recorded L2 power factor | PF x 100 |
| L3PowerFactor_x100 | recorded L3 power factor | PF x 100 |
| ThreePhaseCosPhi_x100 | recorded three-phase cos phi | cos phi x 100 |
| CosPhiL1_x100 | recorded L1 cos phi | cos phi x 100 |
| CosPhiL2_x100 | recorded L2 cos phi | cos phi x 100 |
| CosPhiL3_x100 | recorded L3 cos phi | cos phi x 100 |

### Derived Fields

| Column | Meaning |
|---|---|
| DerivedThreePhasePowerFactor_x100 | derived three-phase power factor |
| DerivedThreePhaseCosPhi_x100 | derived three-phase cos phi |
| DerivedL1PowerFactor_x100 | derived L1 power factor |
| DerivedL1CosPhi_x100 | derived L1 cos phi |
| DerivedL2PowerFactor_x100 | derived L2 power factor |
| DerivedL2CosPhi_x100 | derived L2 cos phi |
| DerivedL3PowerFactor_x100 | derived L3 power factor |
| DerivedL3CosPhi_x100 | derived L3 cos phi |

Derived fields are calculated as:

```
active power / apparent power * 100
```

## Cumulative Energy Counters

### Active Energy

| Column | Meaning | Unit |
|---|---|---|
| ConsumedActiveEnergyW_Wh | subunit active energy counter | Wh |
| ConsumedActiveEnergykW_kWh | whole active energy counter | kWh |

### Apparent Energy

| Column | Meaning | Unit |
|---|---|---|
| ConsumedApparentEnergyVAh_VAh | subunit apparent energy counter | VAh |
| ConsumedApparentEnergykVAh_kVAh | whole apparent energy counter | kVAh |

### Capacitive Reactive Energy

| Column | Meaning | Unit |
|---|---|---|
| ConsumedCapacitiveReactiveEnergyvarhC_varh | subunit capacitive reactive energy counter | varh |
| ConsumedCapacitiveReactiveEnergykvarhC_kvarh | whole capacitive reactive energy counter | kvarh |

### Inductive Reactive Energy

| Column | Meaning | Unit |
|---|---|---|
| ConsumedInductiveReactiveEnergyvarhL_varh | subunit inductive reactive energy counter | varh |
| ConsumedInductiveReactiveEnergykvarhL_kvarh | whole inductive reactive energy counter | kvarh |

### Derived Cumulative Energy

| Column | Derived from |
|---|---|
| DerivedConsumedActiveEnergy_kWh | ActiveThreePhasePower_W |
| DerivedConsumedApparentEnergy_kVAh | ApparentThreePhasePower_VA |
| DerivedConsumedCapacitiveReactiveEnergy_kvarh | CapacitiveThreePhasePower_var |

Derived cumulative energy is calculated using trapezoidal integration.

## Maximum Demand

| Column | Meaning | Unit |
|---|---|---|
| MaximumDemandIAVG_mA | average current maximum demand | mA |
| MaximumDemandIL1_mA | L1 current maximum demand | mA |
| MaximumDemandIL2_mA | L2 current maximum demand | mA |
| MaximumDemandIL3_mA | L3 current maximum demand | mA |
| MaximumDemandkWIII_W | three-phase active-power maximum demand | W |
| MaximumDemandkVAIII_VA | three-phase apparent-power maximum demand | VA |

## CO2

| Column | Meaning | Stored unit |
|---|---|---|
| ConsumedCO2Emissions_x10 | recorded CO2 emissions counter/estimate | x10 |

## Notes

- Original measured columns are preserved where possible.
- Derived columns are added separately.
- Some meters may not contain all fields.
- Use schema validation before assuming a column exists for every device.
