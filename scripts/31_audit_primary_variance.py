#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

MAP = (
    PROJECT / "06_effect_sizes/"
    "mortality_comparison_map_final.csv"
)

DATA = (
    PROJECT / "05_extraction/mortality/analytic/"
    "mortality_analytic_expanded.csv"
)

OUT = (
    PROJECT / "06_effect_sizes/"
    "primary_variance_audit.csv"
)

cmp = pd.read_csv(MAP)
raw = pd.read_csv(DATA)

primary = cmp[
    cmp["analysis_set"] == "PRIMARY_MEAN_MORTALITY"
].copy()


# ==========================================================
# INFORMACIÓN DE N DISPONIBLE
# ==========================================================

# Buscar posibles columnas relacionadas con n/repeticiones
n_columns = [
    c for c in raw.columns
    if any(
        key in c.lower()
        for key in [
            "replicate",
            "replication",
            "sample_n",
            "total_n",
            "insects"
        ]
    )
]

print("\n==========================================")
print("AUDITORÍA DE VARIANZA DEL CONJUNTO PRIMARIO")
print("==========================================\n")

print("Comparaciones primarias:", len(primary))
print(
    "Estudios:",
    primary["study_record_id"].nunique()
)

print("\nColumnas potenciales de n encontradas:")
if n_columns:
    for c in n_columns:
        print(" -", c)
else:
    print(" Ninguna")


# ==========================================================
# DISPERSIÓN POR ESTUDIO
# ==========================================================

rows = []

for study, g in primary.groupby("study_record_id"):

    trt_types = sorted(
        set(
            g["treatment_dispersion_type"]
            .dropna()
            .astype(str)
        )
    )

    ctrl_types = sorted(
        set(
            g["control_dispersion_type"]
            .dropna()
            .astype(str)
        )
    )

    trt_missing = int(
        g["treatment_dispersion"].isna().sum()
    )

    ctrl_missing = int(
        g["control_dispersion"].isna().sum()
    )

    # revisar columnas de n en registros originales
    study_raw = raw[
        raw["study_record_id"] == study
    ]

    n_info = {}

    for c in n_columns:

        vals = (
            study_raw[c]
            .dropna()
            .unique()
            .tolist()
        )

        n_info[c] = vals

    rows.append({
        "study_record_id": study,
        "comparisons": len(g),
        "experiments": g["experiment_id"].nunique(),
        "treatment_dispersion_types":
            ",".join(trt_types),
        "control_dispersion_types":
            ",".join(ctrl_types),
        "missing_treatment_dispersion":
            trt_missing,
        "missing_control_dispersion":
            ctrl_missing,
        "n_information":
            str(n_info)
    })


audit = pd.DataFrame(rows)

audit.to_csv(
    OUT,
    index=False,
    encoding="utf-8"
)


print("\n==========================================")
print("DISPERSIÓN POR ESTUDIO")
print("==========================================\n")

print(
    audit[
        [
            "study_record_id",
            "comparisons",
            "experiments",
            "treatment_dispersion_types",
            "control_dispersion_types",
            "missing_treatment_dispersion",
            "missing_control_dispersion"
        ]
    ].to_string(index=False)
)


print("\n==========================================")
print("INFORMACIÓN DE N")
print("==========================================\n")

for _, r in audit.iterrows():

    print(r["study_record_id"])
    print(" ", r["n_information"])


# ==========================================================
# CASO ESPECIAL SZ_00071
# ==========================================================

print("\n==========================================")
print("SZ_00071 - VERIFICACIÓN ESPECIAL")
print("==========================================\n")

x = primary[
    primary["study_record_id"] == "SZ_00071"
]

print(
    x[
        [
            "treatment",
            "dose",
            "treatment_mean",
            "treatment_dispersion",
            "treatment_dispersion_type",
            "control_mean",
            "control_dispersion",
            "control_dispersion_type"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


print("\n==========================================")
print("RESUMEN GLOBAL")
print("==========================================\n")

print("Tipos tratamiento:")
print(
    primary["treatment_dispersion_type"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nTipos control:")
print(
    primary["control_dispersion_type"]
    .value_counts(dropna=False)
    .to_string()
)

print(f"\nAuditoría:\n{OUT}")
