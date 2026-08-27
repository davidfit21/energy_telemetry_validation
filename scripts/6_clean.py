from pathlib import Path

import numpy as np
import pandas as pd

# =============================================================================
# Configuration
# =============================================================================

# Project root (energydata-master)
BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSING_DIR = BASE_DIR / "processing"

INPUT_DIR = PROCESSING_DIR / "parquet_cleaned"
OUTPUT_DIR = PROCESSING_DIR / "parquet_validated"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Validation / Cleaning Parameters
# =============================================================================

# Notebook 5 established that the first four months of telemetry
# should be excluded from the validated dataset.
TRIM_INITIAL_MONTHS = 4

# Long frozen cumulative-energy periods are reported for investigation.
# They are NOT automatically deleted.
LARGE_FLAT_THRESHOLD = pd.Timedelta(days=100)


# =============================================================================
# Confirmed Engineering Corrections
# =============================================================================

# These corrections were established through
# 5_engineering_validation.ipynb.
#
# For each confirmed polarity issue:
#
#   1. Reverse the affected phase measurement.
#   2. Reconstruct the corresponding three-phase total
#      from L1 + corrected L2 + L3.
#
# Only explicitly identified corrections are applied.

POLARITY_FIXES = {

    "ULC10": [

        {
            "phase_col": "L2ActivePower_W",

            "total_col": "ActiveThreePhasePower_W",

            "sum_cols": [
                "L1ActivePower_W",
                "L2ActivePower_W",
                "L3ActivePower_W",
            ],
        },

        {
            "phase_col": "L2ApparentPower_VA",

            "total_col": "ApparentThreePhasePower_VA",

            "sum_cols": [
                "L1ApparentPower_VA",
                "L2ApparentPower_VA",
                "L3ApparentPower_VA",
            ],
        },

        {
            "phase_col": "L2CapacitivePower_var",

            "total_col": "CapacitiveThreePhasePower_var",

            "sum_cols": [
                "L1CapacitivePower_var",
                "L2CapacitivePower_var",
                "L3CapacitivePower_var",
            ],
        },
    ],

    "ULC12": [

        {
            "phase_col": "L2ActivePower_W",

            "total_col": "ActiveThreePhasePower_W",

            "sum_cols": [
                "L1ActivePower_W",
                "L2ActivePower_W",
                "L3ActivePower_W",
            ],
        },
    ],
}

# =============================================================================
# Confirmed Negative-Value Row Removals
# =============================================================================
#
# Engineering/data-quality review identified a small number of negative
# values outside the PowerFactor and CosPhi fields.
#
# Negative PowerFactor/CosPhi values are intentionally preserved because
# these quantities are signed in this telemetry dataset and their negative
# values occur systematically.
#
# For the fields listed below, negative values are treated as invalid
# telemetry observations and the corresponding rows are removed.
#
# Only explicitly identified device/column combinations are removed.
# No rows are removed solely because a PowerFactor or CosPhi field is negative.
# =============================================================================

NEGATIVE_VALUE_REMOVALS = {

    "ULC12": [
        "L2ApparentPower_VA",
        "L2CapacitivePower_var",
    ],

    "CRAC2": [
        "L3ActivePower_W",
        "L3ApparentPower_VA",
        "L3InductivePower_var",
        "InductiveThreePhasePower_var",
    ],

    "CRAC5": [
        "L2ActivePower_W",
        "L2InductivePower_var",
        "L2ApparentPower_VA",
        "InductiveThreePhasePower_var",
    ],

    "CRAC6": [
        "L3ActivePower_W",
        "L3InductivePower_var",
        "L3ApparentPower_VA",
    ],
}


# =============================================================================
# Cumulative Energy Counter Definitions
# =============================================================================

ENERGY_COUNTER_PAIRS = {

    "Active": {
        "subunit": "ConsumedActiveEnergyW_Wh",
        "whole": "ConsumedActiveEnergykW_kWh",
    },

    "Apparent": {
        "subunit": "ConsumedApparentEnergyVAh_VAh",
        "whole": "ConsumedApparentEnergykVAh_kVAh",
    },

    "CapacitiveReactive": {
        "subunit": "ConsumedCapacitiveReactiveEnergyvarhC_varh",
        "whole": "ConsumedCapacitiveReactiveEnergykvarhC_kvarh",
    },

    "InductiveReactive": {
        "subunit": "ConsumedInductiveReactiveEnergyvarhL_varh",
        "whole": "ConsumedInductiveReactiveEnergykvarhL_kvarh",
    },
}


# =============================================================================
# Logging Helper
# =============================================================================

def log_change(
    log_rows,
    device,
    action,
    column=None,
    rows_affected=0,
    details=None,
):
    """
    Record every cleaning action or important validation finding.
    """

    log_rows.append(
        {
            "Device": device,
            "Action": action,
            "Column": column,
            "Rows_Affected": int(rows_affected),
            "Details": details,
        }
    )


# =============================================================================
# Trim Initial Four Months
# =============================================================================

def trim_to_validation_window(
    df,
    device,
    log_rows,
):
    """
    Remove the first four months of telemetry.

    Notebook 5 established that the initial four-month period
    should not be included in the validated dataset.
    """

    if not isinstance(df.index, pd.DatetimeIndex):

        log_change(
            log_rows,
            device,
            "trim_initial_months_skipped",
            details=(
                "Index is not a DatetimeIndex. "
                "Initial four-month trim was not applied."
            ),
        )

        return df

    df = df.sort_index()

    first_timestamp = df.index.min()

    cutoff_timestamp = (
        first_timestamp
        + pd.DateOffset(
            months=TRIM_INITIAL_MONTHS
        )
    )

    before_rows = len(df)

    df = df.loc[
        df.index >= cutoff_timestamp
    ].copy()

    rows_removed = (
        before_rows - len(df)
    )

    log_change(
        log_rows,
        device,
        "trim_initial_months",
        rows_affected=rows_removed,
        details=(
            f"Removed the first "
            f"{TRIM_INITIAL_MONTHS} months of telemetry. "
            f"Original first timestamp: {first_timestamp}. "
            f"Validation window begins: {cutoff_timestamp}."
        ),
    )

    return df


# =============================================================================
# Apply Confirmed Polarity Corrections
# =============================================================================

def apply_polarity_fixes(
    df,
    device,
    log_rows,
):
    """
    Apply confirmed phase-polarity corrections.

    Only device/phase combinations explicitly identified
    in POLARITY_FIXES are modified.
    """

    fixes = POLARITY_FIXES.get(
        device,
        [],
    )

    for fix in fixes:

        phase_col = fix["phase_col"]

        total_col = fix["total_col"]

        sum_cols = fix["sum_cols"]

        required_columns = [
            phase_col,
            total_col,
            *sum_cols,
        ]

        missing = [
            col
            for col in required_columns
            if col not in df.columns
        ]

        if missing:

            log_change(
                log_rows,
                device,
                "polarity_fix_skipped",
                column=phase_col,
                details=(
                    f"Required columns missing: {missing}"
                ),
            )

            continue

        # ---------------------------------------------------------------------
        # Reverse polarity of affected phase
        # ---------------------------------------------------------------------

        df[phase_col] = -df[phase_col]

        # ---------------------------------------------------------------------
        # Reconstruct three-phase total
        # ---------------------------------------------------------------------

        df[total_col] = df[
            sum_cols
        ].sum(axis=1)

        log_change(
            log_rows,
            device,
            "polarity_corrected_and_three_phase_total_rebuilt",
            column=phase_col,
            rows_affected=len(df),
            details=(
                f"Reversed polarity of {phase_col}. "
                f"Rebuilt {total_col} using "
                f"{sum_cols[0]} + "
                f"{sum_cols[1]} + "
                f"{sum_cols[2]}."
            ),
        )

    return df


# =============================================================================
# Remove Confirmed Negative-Value Rows
# =============================================================================

def remove_confirmed_negative_values(
    df,
    device,
    log_rows,
):
    """
    Remove rows containing confirmed invalid negative values in
    non-PowerFactor/CosPhi telemetry fields.

    Negative PowerFactor and CosPhi values are intentionally preserved.
    Only explicitly identified device/column combinations in
    NEGATIVE_VALUE_REMOVALS are evaluated.

    A row is removed if any configured column for that device
    contains a negative value.
    """

    columns = NEGATIVE_VALUE_REMOVALS.get(
        device,
        [],
    )

    if not columns:
        return df

    # Only process columns that actually exist
    existing_columns = [
        col
        for col in columns
        if col in df.columns
    ]

    missing_columns = [
        col
        for col in columns
        if col not in df.columns
    ]

    # Report configured columns that are unavailable
    if missing_columns:

        log_change(
            log_rows,
            device,
            "negative_value_removal_columns_missing",
            details=(
                f"Configured columns not found: "
                f"{missing_columns}"
            ),
        )

    if not existing_columns:
        return df

    # -------------------------------------------------------------------------
    # Identify rows containing at least one negative value
    # -------------------------------------------------------------------------

    negative_mask = (
        df[existing_columns]
        .lt(0)
        .any(axis=1)
    )

    rows_removed = int(
        negative_mask.sum()
    )

    if rows_removed == 0:
        return df

    # -------------------------------------------------------------------------
    # Record exactly which columns caused the removals
    # -------------------------------------------------------------------------

    for column in existing_columns:

        column_mask = (
            df[column] < 0
        )

        column_rows_removed = int(
            column_mask.sum()
        )

        if column_rows_removed == 0:
            continue

        log_change(
            log_rows,
            device,
            "negative_value_rows_removed",
            column=column,
            rows_affected=column_rows_removed,
            details=(
                f"Removed rows where {column} "
                f"contained a negative value. "
                f"PowerFactor/CosPhi fields were "
                f"excluded from this rule."
            ),
        )

    # -------------------------------------------------------------------------
    # Remove affected rows
    # -------------------------------------------------------------------------

    df = df.loc[
        ~negative_mask
    ].copy()

    return df



# =============================================================================
# Derived Cumulative Energy Counters
# =============================================================================
#
# Create engineering-derived cumulative active and apparent energy counters
# from the validated instantaneous three-phase power measurements.
#
# IMPORTANT:
# - Original measured cumulative-energy columns are NOT modified.
# - Two new derived columns are added to every device.
# - ULC10 automatically uses its polarity-corrected three-phase power because
#   the polarity corrections are applied earlier in the pipeline.
# - Integration is performed using the trapezoidal rule.
# - Integration is NOT performed across large timestamp gaps.
# - At a gap, the derived counter carries its previous value forward.
#
# Derived columns:
#   DerivedConsumedActiveEnergy_kWh
#   DerivedConsumedApparentEnergy_kVAh
#   DerivedConsumedCapacitiveReactiveEnergy_kvarh
# =============================================================================


DERIVED_ENERGY_CONFIG = {
    "Active": {
        "power_col": "ActiveThreePhasePower_W",
        "derived_col": "DerivedConsumedActiveEnergy_kWh",
    },

    "Apparent": {
        "power_col": "ApparentThreePhasePower_VA",
        "derived_col": "DerivedConsumedApparentEnergy_kVAh",
    },

    "CapacitiveReactive": {
        "power_col": "CapacitiveThreePhasePower_var",
        "derived_col": "DerivedConsumedCapacitiveReactiveEnergy_kvarh",
    },
}


MAX_INTEGRATION_GAP = pd.Timedelta(minutes=2)


def reconstruct_cumulative_energy(
    df,
    power_col,
    derived_col,
    max_gap=MAX_INTEGRATION_GAP,
):
    """
    Reconstruct a cumulative energy counter from instantaneous
    three-phase power using trapezoidal numerical integration.

    The original measured cumulative-energy columns are not modified.

    The derived counter is anchored to zero at the first valid
    observation and then accumulated from instantaneous power.

    Integration is not performed across timestamp gaps larger than
    max_gap. The cumulative value is carried forward across such gaps.
    """

    if power_col not in df.columns:
        return df

    if not isinstance(df.index, pd.DatetimeIndex):
        df[derived_col] = np.nan
        return df

    # -------------------------------------------------------------------------
    # Work only with valid instantaneous power observations
    # -------------------------------------------------------------------------

    power = df[power_col]

    valid = power.notna()

    if valid.sum() == 0:
        df[derived_col] = np.nan
        return df

    work = pd.DataFrame(
        {
            "power": power.loc[valid],
        },
        index=df.index[valid],
    ).sort_index()

    # -------------------------------------------------------------------------
    # Calculate timestamp differences
    # -------------------------------------------------------------------------

    dt = (
        work.index.to_series()
        .diff()
    )

    # -------------------------------------------------------------------------
    # Identify gaps where integration must stop
    # -------------------------------------------------------------------------

    gap = dt > max_gap

    # Each continuous section receives a segment ID.
    work["segment"] = gap.cumsum()

    # -------------------------------------------------------------------------
    # Initialise derived counter
    # -------------------------------------------------------------------------

    work["derived_energy"] = np.nan

    running_energy = 0.0

    # -------------------------------------------------------------------------
    # Integrate each continuous segment
    # -------------------------------------------------------------------------

    for _, segment in work.groupby("segment"):

        if len(segment) == 0:
            continue

        if len(segment) == 1:

            work.loc[
                segment.index,
                "derived_energy"
            ] = running_energy

            continue

        dt_hours = (
            segment.index.to_series()
            .diff()
            .dt.total_seconds()
            / 3600.0
        )

        # Trapezoidal integration:
        #
        # Energy = average power × time
        #
        avg_power = (
            segment["power"]
            + segment["power"].shift(1)
        ) / 2.0

        interval_energy = (
            avg_power / 1000.0
        ) * dt_hours

        # First observation has no preceding interval.
        interval_energy = interval_energy.fillna(0.0)

        cumulative_segment = (
            interval_energy.cumsum()
        )

        cumulative_segment = (
            cumulative_segment
            + running_energy
        )

        work.loc[
            segment.index,
            "derived_energy"
        ] = cumulative_segment

        # Carry final value forward to the next continuous segment.
        running_energy = cumulative_segment.iloc[-1]

    # -------------------------------------------------------------------------
    # Add the derived series back to the original dataframe
    # -------------------------------------------------------------------------

    df[derived_col] = np.nan

    df.loc[
        work.index,
        derived_col
    ] = work["derived_energy"]

    return df


def add_derived_cumulative_energy(
    df,
    device,
    log_rows,
):
    """
    Add derived cumulative active and apparent energy counters.

    The original measured cumulative-energy columns remain unchanged.

    ULC10 receives exactly the same treatment as every other device,
    except that its instantaneous three-phase power has already been
    corrected by apply_polarity_fixes() earlier in the pipeline.
    """

    for metric, config in DERIVED_ENERGY_CONFIG.items():

        power_col = config["power_col"]
        derived_col = config["derived_col"]

        # ---------------------------------------------------------------------
        # Check required instantaneous power column
        # ---------------------------------------------------------------------

        if power_col not in df.columns:

            log_change(
                log_rows,
                device,
                "derived_energy_skipped",
                column=derived_col,
                details=(
                    f"Required instantaneous power column "
                    f"{power_col} was not found."
                ),
            )

            continue

        # ---------------------------------------------------------------------
        # Reconstruct cumulative energy
        # ---------------------------------------------------------------------

        df = reconstruct_cumulative_energy(
            df=df,
            power_col=power_col,
            derived_col=derived_col,
        )

        valid_rows = int(
            df[derived_col].notna().sum()
        )

        log_change(
            log_rows,
            device,
            "derived_cumulative_energy_added",
            column=derived_col,
            rows_affected=valid_rows,
            details=(
                f"Derived from {power_col} using trapezoidal "
                f"integration. Original measured cumulative-energy "
                f"columns were retained unchanged."
            ),
        )

    return df



# =============================================================================
# Derived Power Factor / CosPhi
# =============================================================================
# Recorded PF/CosPhi fields are retained unchanged. Derived fields are calculated
# from the corrected instantaneous active/apparent power fields. ULC10 therefore
# automatically uses its corrected L2 active/apparent power and corrected totals.
# =============================================================================

PF_COSPHI_CONFIG = {
    "ThreePhase": {"active": "ActiveThreePhasePower_W", "apparent": "ApparentThreePhasePower_VA", "pf_derived": "DerivedThreePhasePowerFactor_x100", "cosphi_derived": "DerivedThreePhaseCosPhi_x100"},
    "L1": {"active": "L1ActivePower_W", "apparent": "L1ApparentPower_VA", "pf_derived": "DerivedL1PowerFactor_x100", "cosphi_derived": "DerivedL1CosPhi_x100"},
    "L2": {"active": "L2ActivePower_W", "apparent": "L2ApparentPower_VA", "pf_derived": "DerivedL2PowerFactor_x100", "cosphi_derived": "DerivedL2CosPhi_x100"},
    "L3": {"active": "L3ActivePower_W", "apparent": "L3ApparentPower_VA", "pf_derived": "DerivedL3PowerFactor_x100", "cosphi_derived": "DerivedL3CosPhi_x100"},
}

PF_APPARENT_POWER_FLOOR_VA = 1e-9

def add_derived_power_factor_cosphi(df, device, log_rows):
    for _, config in PF_COSPHI_CONFIG.items():
        active_col = config["active"]
        apparent_col = config["apparent"]
        if active_col not in df.columns or apparent_col not in df.columns:
            continue

        valid = df[active_col].notna() & df[apparent_col].notna() & (df[apparent_col].abs() > PF_APPARENT_POWER_FLOOR_VA)
        pf = pd.Series(np.nan, index=df.index, dtype=float)
        pf.loc[valid] = df.loc[valid, active_col] / df.loc[valid, apparent_col]
        pf = pf.clip(-1.0, 1.0)
        derived = pf * 100.0

        df[config["pf_derived"]] = derived
        df[config["cosphi_derived"]] = derived.copy()

        log_change(
            log_rows, device, "derived_power_factor_cosphi_added",
            column=f"{config['pf_derived']}; {config['cosphi_derived']}",
            rows_affected=int(valid.sum()),
            details=f"Derived from {active_col} / {apparent_col}. Original recorded PF/CosPhi fields retained unchanged.",
        )

    return df


# =============================================================================
# Frozen Cumulative Energy Detection
# =============================================================================

def find_large_flat_periods(
    series,
):
    """
    Identify long periods where a cumulative-energy value
    remains unchanged.

    These periods are reported only.
    The underlying data are not modified.
    """

    series = (
        series
        .dropna()
        .sort_index()
    )

    if len(series) < 2:
        return []

    run_id = (
        series
        .ne(series.shift())
        .cumsum()
    )

    periods = []

    for _, block in series.groupby(run_id):

        if len(block) < 2:
            continue

        duration = (
            block.index[-1]
            - block.index[0]
        )

        if duration >= LARGE_FLAT_THRESHOLD:

            periods.append(
                {
                    "start": block.index[0],

                    "end": block.index[-1],

                    "duration_days": (
                        duration.total_seconds()
                        / 86400
                    ),

                    "energy": block.iloc[0],

                    "records": len(block),
                }
            )

    return periods


# =============================================================================
# Report Frozen Energy Counters
# =============================================================================

def report_frozen_energy_counters(
    df,
    device,
    log_rows,
    frozen_rows,
):
    """
    Detect long frozen cumulative-energy periods.

    These periods are reported because notebook 5 identified
    cumulative-counter problems.

    Values are intentionally preserved here rather than replaced
    with fabricated values.
    """

    if not isinstance(
        df.index,
        pd.DatetimeIndex,
    ):
        return df

    for metric, cols in ENERGY_COUNTER_PAIRS.items():

        whole = cols["whole"]

        subunit = cols["subunit"]

        if (
            whole not in df.columns
            or subunit not in df.columns
        ):
            continue

        # Convert the two counter components into a
        # common unit and reconstruct the total counter.

        reconstructed = (
            df[whole]
            + df[subunit] / 1000.0
        )

        periods = find_large_flat_periods(
            reconstructed
        )

        for period in periods:

            mask = (
                (df.index >= period["start"])
                & (
                    df.index
                    <= period["end"]
                )
            )

            rows_affected = int(
                mask.sum()
            )

            frozen_rows.append(
                {
                    "Device": device,
                    "Metric": metric,
                    "Whole_Column": whole,
                    "Subunit_Column": subunit,
                    "Start": period["start"],
                    "End": period["end"],
                    "Duration_Days": period[
                        "duration_days"
                    ],
                    "Frozen_Energy": period[
                        "energy"
                    ],
                    "Rows_Affected": rows_affected,
                    "Action": "flag_only",
                }
            )

            log_change(
                log_rows,
                device,
                "frozen_energy_counter_flagged",
                column=(
                    f"{whole}; {subunit}"
                ),
                rows_affected=rows_affected,
                details=(
                    f"{metric}: cumulative energy "
                    f"remained constant from "
                    f"{period['start']} to "
                    f"{period['end']} "
                    f"({period['duration_days']:.2f} days). "
                    f"No values were modified."
                ),
            )

    return df




# =============================================================================
# Dataset Summary
# =============================================================================

def create_dataset_summary(
    df,
    device,
    input_rows,
    input_cols,
    output_file,
):
    """
    Create a per-device processing summary.
    """

    return {
        "Device": device,

        "Input_Rows": input_rows,

        "Output_Rows": len(df),

        "Rows_Removed": (
            input_rows - len(df)
        ),

        "Input_Columns": input_cols,

        "Output_Columns": len(df.columns),

        "Output_File": str(
            output_file
        ),
    }


# =============================================================================
# Main Processing
# =============================================================================

def main():

    files = sorted(
        INPUT_DIR.glob("*.parquet")
    )

    if not files:

        raise FileNotFoundError(
            f"No parquet files found in "
            f"{INPUT_DIR}"
        )

    log_rows = []

    frozen_rows = []

    summary_rows = []

    print(
        f"Found {len(files)} parquet files "
        f"in {INPUT_DIR}"
    )

    print(
        f"Writing validated parquet files "
        f"to {OUTPUT_DIR}\n"
    )

    # =========================================================================
    # Process every device
    # =========================================================================

    for file in files:

        device = file.stem.upper()

        print("=" * 90)

        print(
            f"Processing {device}"
        )

        # ---------------------------------------------------------------------
        # Load dataset
        # ---------------------------------------------------------------------

        df = pd.read_parquet(
            file
        )

        input_rows = len(df)

        input_cols = len(
            df.columns
        )

        print(
            f"Input rows    : "
            f"{input_rows:,}"
        )

        print(
            f"Input columns : "
            f"{input_cols}"
        )

        # ---------------------------------------------------------------------
        # Ensure chronological ordering
        # ---------------------------------------------------------------------

        if isinstance(
            df.index,
            pd.DatetimeIndex,
        ):

            df = df.sort_index()

        # ---------------------------------------------------------------------
        # 1. Remove first four months
        # ---------------------------------------------------------------------

        df = trim_to_validation_window(df,device,log_rows)

        # ---------------------------------------------------------------------
        # 2. Apply confirmed engineering corrections
        # ---------------------------------------------------------------------

        df = apply_polarity_fixes(df,device,log_rows,)

        # ---------------------------------------------------------------------
        # 3. Remove confirmed invalid negative-value rows
        # ---------------------------------------------------------------------

        df = remove_confirmed_negative_values(df,device,log_rows,)

        # ---------------------------------------------------------------------
        # 4. Add derived PF/CosPhi from corrected power measurements
        # ---------------------------------------------------------------------

        df = add_derived_power_factor_cosphi(df, device, log_rows)

        # ---------------------------------------------------------------------
        # 5. Add derived cumulative active, apparent and capacitive energy
        # ---------------------------------------------------------------------

        df = add_derived_cumulative_energy(df,device,log_rows,)

        # ---------------------------------------------------------------------
        # 6. Detect/report frozen energy counters
        # ---------------------------------------------------------------------

        df = report_frozen_energy_counters(df,device,log_rows,frozen_rows,)

        # ---------------------------------------------------------------------
        # 4. Save validated dataset
        # ---------------------------------------------------------------------

        output_file = (
            OUTPUT_DIR
            / file.name
        )

        df.to_parquet(
            output_file,
            engine="pyarrow",
            compression="snappy",
        )

        # ---------------------------------------------------------------------
        # Create summary
        # ---------------------------------------------------------------------

        summary_rows.append(
            create_dataset_summary(
                df=df,
                device=device,
                input_rows=input_rows,
                input_cols=input_cols,
                output_file=output_file,
            )
        )

        print(
            f"Output rows   : "
            f"{len(df):,}"
        )

        print(
            f"Rows removed  : "
            f"{input_rows - len(df):,}"
        )

        print(
            f"Saved         : "
            f"{output_file}"
        )

    # =========================================================================
    # Create reports
    # =========================================================================

    summary_df = pd.DataFrame(
        summary_rows
    )

    log_df = pd.DataFrame(
        log_rows
    )

    frozen_df = pd.DataFrame(
        frozen_rows
    )

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()