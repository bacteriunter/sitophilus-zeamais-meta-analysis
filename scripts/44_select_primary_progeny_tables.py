#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/tables/"
    "progeny_tables_identified.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny"
)

OUT = OUTDIR / "progeny_primary_tables.csv"

df = pd.read_csv(INPUT)

df = df[
    df["status"] == "SELECT"
].copy()

# ----------------------------------------------------------
# Normalizar
# ----------------------------------------------------------

for col in [
    "metric",
    "dispersion"
]:
    df[col] = df[col].fillna("")

# Eliminar duplicados exactos de estudio/tabla
# Si el mismo número aparece varias veces con clasificación
# distinta, conservamos las señales mediante ranking posterior.
df = df.drop_duplicates()


# ----------------------------------------------------------
# PUNTUACIÓN
#
# COUNT es prioridad porque es la métrica original.
# Control es indispensable para comparación.
# SE/SD facilita análisis cuantitativo posterior.
# ----------------------------------------------------------

df["has_count"] = (
    df["metric"]
    .str.contains(
        "COUNT",
        case=False,
        na=False
    )
)

df["has_reduction"] = (
    df["metric"]
    .str.contains(
        "PERCENT_REDUCTION",
        case=False,
        na=False
    )
)

df["known_dispersion"] = (
    df["dispersion"]
    .isin(["SE", "SD"])
)

df["score"] = (
    df["has_count"].astype(int) * 4
    +
    df["control"].astype(int) * 4
    +
    df["known_dispersion"].astype(int) * 2
    +
    df["dose"].astype(int)
    +
    df["sitophilus_zeamais"].astype(int)
    +
    df["maize"].astype(int)
)


# ----------------------------------------------------------
# CLASIFICAR TABLAS
# ----------------------------------------------------------

def classify(r):

    if (
        r["has_count"]
        and r["control"]
        and r["known_dispersion"]
    ):
        return "A_COUNT_CONTROL_VARIANCE"

    if (
        r["has_count"]
        and r["control"]
    ):
        return "B_COUNT_CONTROL"

    if r["has_count"]:
        return "C_COUNT_NO_CONTROL_SIGNAL"

    if (
        r["has_reduction"]
        and r["control"]
    ):
        return "D_REDUCTION_ONLY"

    return "E_OTHER"


df["priority_class"] = df.apply(
    classify,
    axis=1
)


# ----------------------------------------------------------
# ORDEN DE PRIORIDAD
# ----------------------------------------------------------

priority_order = {
    "A_COUNT_CONTROL_VARIANCE": 1,
    "B_COUNT_CONTROL": 2,
    "C_COUNT_NO_CONTROL_SIGNAL": 3,
    "D_REDUCTION_ONLY": 4,
    "E_OTHER": 5
}

df["priority_rank"] = (
    df["priority_class"]
    .map(priority_order)
)


# ----------------------------------------------------------
# SELECCIONAR UNA TABLA PRINCIPAL POR ESTUDIO
# ----------------------------------------------------------

df = df.sort_values(
    [
        "study_record_id",
        "priority_rank",
        "score",
        "table_number"
    ],
    ascending=[
        True,
        True,
        False,
        True
    ]
)

primary = (
    df.groupby(
        "study_record_id",
        as_index=False
    )
    .first()
)


# ----------------------------------------------------------
# DECISIÓN
# ----------------------------------------------------------

def decision(r):

    if r["priority_class"] == "A_COUNT_CONTROL_VARIANCE":
        return "READY"

    if r["priority_class"] == "B_COUNT_CONTROL":
        return "EXTRACT_THEN_CHECK_VARIANCE"

    if r["priority_class"] == "C_COUNT_NO_CONTROL_SIGNAL":
        return "CHECK_CONTROL"

    if r["priority_class"] == "D_REDUCTION_ONLY":
        return "SECONDARY_ONLY"

    return "REVIEW"


primary["decision"] = primary.apply(
    decision,
    axis=1
)


# ----------------------------------------------------------
# GUARDAR
# ----------------------------------------------------------

cols = [
    "study_record_id",
    "table_number",
    "metric",
    "dispersion",
    "control",
    "dose",
    "sitophilus_zeamais",
    "maize",
    "priority_class",
    "score",
    "decision"
]

primary[cols].to_csv(
    OUT,
    index=False,
    encoding="utf-8"
)


# ----------------------------------------------------------
# SALIDA
# ----------------------------------------------------------

print("\n==========================================")
print("SELECCIÓN DE TABLAS PRINCIPALES F1")
print("==========================================\n")

print("Estudios:", len(primary))

print("\n==========================================")
print("CLASE DE PRIORIDAD")
print("==========================================\n")

print(
    primary["priority_class"]
    .value_counts()
    .to_string()
)

print("\n==========================================")
print("DECISIÓN")
print("==========================================\n")

print(
    primary["decision"]
    .value_counts()
    .to_string()
)

print("\n==========================================")
print("TABLA SELECCIONADA POR ESTUDIO")
print("==========================================\n")

print(
    primary[cols].to_string(
        index=False
    )
)

print("\n==========================================")
print("DISPERSIÓN DE TABLAS SELECCIONADAS")
print("==========================================\n")

print(
    primary["dispersion"]
    .replace("", "UNKNOWN")
    .value_counts()
    .to_string()
)

print("\nArchivo:")
print(OUT)
