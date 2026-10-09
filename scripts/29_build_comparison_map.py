#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT / "05_extraction/mortality/analytic/"
    "mortality_analytic_expanded.csv"
)

OUTDIR = PROJECT / "06_effect_sizes"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "mortality_comparison_map.csv"
SUMMARY = OUTDIR / "mortality_comparison_summary.csv"

df = pd.read_csv(INPUT)

# ----------------------------------------------------------
# Excluir controles sintéticos
# ----------------------------------------------------------

natural = df[
    df["arm_type"] == "NATURAL_TREATMENT"
].copy()

controls = df[
    df["arm_type"] == "NEGATIVE_CONTROL"
].copy()


# ----------------------------------------------------------
# Identificador experimental
#
# Por defecto:
# estudio + tabla + escala + tiempo
#
# Algunos estudios requieren reglas específicas.
# ----------------------------------------------------------

def experiment_id(row):

    study = row["study_record_id"]
    table = str(row["table_number"])
    scale = row["outcome_scale"]

    time = row["time_h"]
    time_txt = "NA" if pd.isna(time) else str(int(float(time)))

    # SZ_00401:
    # controles separados por variedad de maíz
    if study == "SZ_00401":

        text = str(row["treatment"]).lower()

        if "moderately-resistant" in text:
            subgroup = "MODERATELY_RESISTANT"
        else:
            subgroup = "RESISTANT"

        return (
            f"{study}_T{table}_{subgroup}_"
            f"{scale}_{time_txt}h"
        )

    # resto
    return (
        f"{study}_T{table}_{scale}_{time_txt}h"
    )


df["experiment_id"] = df.apply(
    experiment_id,
    axis=1
)

natural = df[
    df["arm_type"] == "NATURAL_TREATMENT"
].copy()

controls = df[
    df["arm_type"] == "NEGATIVE_CONTROL"
].copy()


# ----------------------------------------------------------
# Controles disponibles por experimento
# ----------------------------------------------------------

control_groups = {}

for exp_id, g in controls.groupby("experiment_id"):

    control_groups[exp_id] = g.copy()


# ----------------------------------------------------------
# Construir mapa
# ----------------------------------------------------------

rows = []

for _, trt in natural.iterrows():

    exp_id = trt["experiment_id"]

    candidates = control_groups.get(
        exp_id,
        pd.DataFrame()
    )

    status = None
    control_id = None
    control_mean = None
    control_disp = None
    control_disp_type = None
    control_total_n = None
    control_deaths = None

    if len(candidates) == 0:

        status = "NO_CONTROL"

    else:

        # --------------------------------------------------
        # Si existen varios controles idénticos dentro del
        # mismo experimento, no son controles independientes.
        # Comprobamos si son equivalentes.
        # --------------------------------------------------

        check_cols = [
            "mortality_mean",
            "dispersion_value",
            "dispersion_type",
            "outcome_scale",
            "total_n",
            "deaths"
        ]

        unique_controls = (
            candidates[check_cols]
            .drop_duplicates()
        )

        if len(unique_controls) == 1:

            c = candidates.iloc[0]

            status = "MATCHED"

            control_id = c["effect_record_id"]
            control_mean = c["mortality_mean"]
            control_disp = c["dispersion_value"]
            control_disp_type = c["dispersion_type"]
            control_total_n = c["total_n"]
            control_deaths = c["deaths"]

        else:

            status = "MULTIPLE_NONIDENTICAL_CONTROLS"

    rows.append({

        "study_record_id":
            trt["study_record_id"],

        "experiment_id":
            exp_id,

        "table_number":
            trt["table_number"],

        "treatment_effect_record_id":
            trt["effect_record_id"],

        "treatment":
            trt["treatment"],

        "formulation":
            trt["formulation"],

        "dose":
            trt["dose"],

        "dose_unit":
            trt["dose_unit"],

        "time_h":
            trt["time_h"],

        "outcome_scale":
            trt["outcome_scale"],

        "treatment_mean":
            trt["mortality_mean"],

        "treatment_dispersion":
            trt["dispersion_value"],

        "treatment_dispersion_type":
            trt["dispersion_type"],

        "treatment_total_n":
            trt["total_n"],

        "treatment_deaths":
            trt["deaths"],

        "control_effect_record_id":
            control_id,

        "control_mean":
            control_mean,

        "control_dispersion":
            control_disp,

        "control_dispersion_type":
            control_disp_type,

        "control_total_n":
            control_total_n,

        "control_deaths":
            control_deaths,

        "comparison_status":
            status
    })


cmp = pd.DataFrame(rows)


# ----------------------------------------------------------
# Clasificar tipo de información disponible
# ----------------------------------------------------------

def classify(row):

    if row["comparison_status"] != "MATCHED":
        return "NOT_ANALYZABLE"

    scale = row["outcome_scale"]

    if scale == "EVENT_PROPORTION":

        if (
            pd.notna(row["treatment_total_n"])
            and pd.notna(row["treatment_deaths"])
            and pd.notna(row["control_total_n"])
            and pd.notna(row["control_deaths"])
        ):
            return "EVENT_COUNTS_COMPLETE"

        return "EVENT_COUNTS_INCOMPLETE"

    if scale == "PERCENT_MORTALITY":

        if (
            pd.notna(row["treatment_dispersion"])
            and pd.notna(row["control_dispersion"])
        ):
            return "MEAN_DISPERSION"

        return "PERCENT_ONLY"

    if scale == "MEAN_COUNT":

        if (
            pd.notna(row["treatment_dispersion"])
            and pd.notna(row["control_dispersion"])
        ):
            return "MEAN_COUNT_DISPERSION"

        return "MEAN_COUNT_INCOMPLETE"

    return "UNKNOWN"


cmp["data_type"] = cmp.apply(
    classify,
    axis=1
)


# ----------------------------------------------------------
# Guardar
# ----------------------------------------------------------

cmp.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


# ----------------------------------------------------------
# Resumen por estudio
# ----------------------------------------------------------

summary = (
    cmp.groupby("study_record_id")
    .agg(
        natural_arms=(
            "treatment_effect_record_id",
            "size"
        ),
        matched=(
            "comparison_status",
            lambda x: (x == "MATCHED").sum()
        ),
        no_control=(
            "comparison_status",
            lambda x: (x == "NO_CONTROL").sum()
        ),
        ambiguous_control=(
            "comparison_status",
            lambda x: (
                x == "MULTIPLE_NONIDENTICAL_CONTROLS"
            ).sum()
        ),
        data_types=(
            "data_type",
            lambda x: ",".join(
                sorted(set(x))
            )
        )
    )
    .reset_index()
)

summary.to_csv(
    SUMMARY,
    index=False,
    encoding="utf-8"
)


# ----------------------------------------------------------
# Salida
# ----------------------------------------------------------

print("\n==========================================")
print("MAPA DE COMPARACIONES")
print("==========================================\n")

print("Brazos naturales:", len(cmp))

print("\nEstado:")
print(
    cmp["comparison_status"]
    .value_counts()
    .to_string()
)

print("\nTipo de datos:")
print(
    cmp["data_type"]
    .value_counts()
    .to_string()
)

print("\n==========================================")
print("RESUMEN POR ESTUDIO")
print("==========================================\n")

print(
    summary.to_string(index=False)
)

print("\n==========================================")
print("EXPERIMENTOS")
print("==========================================\n")

exp = (
    cmp.groupby(
        [
            "study_record_id",
            "experiment_id",
            "outcome_scale",
            "comparison_status"
        ]
    )
    .size()
    .reset_index(name="natural_arms")
)

print(
    exp.to_string(index=False)
)

print(f"\nMapa:\n{OUTPUT}")
print(f"\nResumen:\n{SUMMARY}")
