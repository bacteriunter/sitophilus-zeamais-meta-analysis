#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

MAP = (
    PROJECT / "06_effect_sizes/"
    "mortality_comparison_map.csv"
)

DATA = (
    PROJECT / "05_extraction/mortality/analytic/"
    "mortality_analytic_expanded.csv"
)

OUT = (
    PROJECT / "06_effect_sizes/"
    "mortality_comparison_map_final.csv"
)

df = pd.read_csv(MAP)
raw = pd.read_csv(DATA)


# ==========================================================
# SZ_00802
#
# Cada tratamiento vegetal tiene su propio control de
# dosis 0 impreso en la tabla.
#
# Emparejamos tratamiento y control por nombre de planta.
# ==========================================================

plants = [
    "Annona senegalensis",
    "Azadirachta indica",
    "Plectranthus glandulosus",
    "Steganotaenia araliacea",
]


for plant in plants:

    trt_mask = (
        (df["study_record_id"] == "SZ_00802")
        &
        (df["treatment"] == plant)
    )

    controls = raw[
        (raw["study_record_id"] == "SZ_00802")
        &
        (raw["arm_type"] == "NEGATIVE_CONTROL")
        &
        (
            raw["treatment"]
            .astype(str)
            .str.contains(
                plant,
                case=False,
                regex=False,
                na=False
            )
        )
    ]

    # Si el control no contiene el nombre de planta,
    # buscar por el orden en que aparecen los controles.
    if len(controls) == 0:

        all_controls = raw[
            (raw["study_record_id"] == "SZ_00802")
            &
            (raw["arm_type"] == "NEGATIVE_CONTROL")
        ].copy()

        all_controls = all_controls.reset_index(drop=True)

        plant_index = plants.index(plant)

        if plant_index < len(all_controls):
            controls = all_controls.iloc[[plant_index]]

    if len(controls) != 1:

        print(
            f"ADVERTENCIA: {plant}: "
            f"{len(controls)} controles encontrados"
        )
        continue

    c = controls.iloc[0]

    df.loc[
        trt_mask,
        "control_effect_record_id"
    ] = c["effect_record_id"]

    df.loc[
        trt_mask,
        "control_mean"
    ] = c["mortality_mean"]

    df.loc[
        trt_mask,
        "control_dispersion"
    ] = c["dispersion_value"]

    df.loc[
        trt_mask,
        "control_dispersion_type"
    ] = c["dispersion_type"]

    df.loc[
        trt_mask,
        "control_total_n"
    ] = c["total_n"]

    df.loc[
        trt_mask,
        "control_deaths"
    ] = c["deaths"]

    df.loc[
        trt_mask,
        "comparison_status"
    ] = "MATCHED"

    df.loc[
        trt_mask,
        "data_type"
    ] = "MEAN_DISPERSION"


# ==========================================================
# DEFINIR CONJUNTOS ANALÍTICOS
# ==========================================================

df["analysis_set"] = "SYSTEMATIC_REVIEW_ONLY"


# Principal:
# mortalidad porcentual + dispersión + control
main_mask = (
    (df["comparison_status"] == "MATCHED")
    &
    (df["data_type"] == "MEAN_DISPERSION")
    &
    (df["outcome_scale"] == "PERCENT_MORTALITY")
)

df.loc[
    main_mask,
    "analysis_set"
] = "PRIMARY_MEAN_MORTALITY"


# Eventos completos
event_mask = (
    (df["comparison_status"] == "MATCHED")
    &
    (df["data_type"] == "EVENT_COUNTS_COMPLETE")
)

df.loc[
    event_mask,
    "analysis_set"
] = "EVENT_COUNTS_SEPARATE"


# Conteos medios
count_mask = (
    (df["comparison_status"] == "MATCHED")
    &
    (df["data_type"] == "MEAN_COUNT_DISPERSION")
)

df.loc[
    count_mask,
    "analysis_set"
] = "MEAN_COUNT_SEPARATE"


# ==========================================================
# GUARDAR
# ==========================================================

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("MAPA FINAL DE COMPARACIONES")
print("==========================================\n")

print("Brazos naturales:", len(df))

print("\nEstado:")
print(
    df["comparison_status"]
    .value_counts()
    .to_string()
)

print("\nConjunto analítico:")
print(
    df["analysis_set"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("ESTUDIOS POR CONJUNTO")
print("==========================================\n")

for aset, g in df.groupby("analysis_set"):

    print(aset)
    print("  Comparaciones:", len(g))
    print(
        "  Estudios:",
        g["study_record_id"].nunique()
    )
    print(
        "  IDs:",
        ", ".join(
            sorted(
                g["study_record_id"].unique()
            )
        )
    )
    print()


print("==========================================")
print("PRIMARY POR ESTUDIO")
print("==========================================\n")

primary = df[
    df["analysis_set"]
    == "PRIMARY_MEAN_MORTALITY"
]

primary_summary = (
    primary.groupby("study_record_id")
    .agg(
        comparisons=(
            "treatment_effect_record_id",
            "size"
        ),
        experiments=(
            "experiment_id",
            "nunique"
        ),
        treatments=(
            "treatment",
            "nunique"
        )
    )
    .reset_index()
)

print(
    primary_summary.to_string(index=False)
)

print(f"\nDataset final:\n{OUT}")
