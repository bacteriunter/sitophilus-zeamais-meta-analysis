#!/usr/bin/env python3

import numpy as np
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT / "06_effect_sizes/"
    "mortality_comparison_map_final.csv"
)

OUTPUT = (
    PROJECT / "06_effect_sizes/"
    "mortality_variance_ready.csv"
)

SUMMARY = (
    PROJECT / "06_effect_sizes/"
    "mortality_variance_ready_summary.csv"
)

df = pd.read_csv(INPUT)

df = df[
    df["analysis_set"] == "PRIMARY_MEAN_MORTALITY"
].copy()


# ==========================================================
# INFORMACIÓN CONFIRMADA DE REPLICACIÓN
# ==========================================================

replicate_n = {
    "SZ_00071": 4,
    "SZ_00124": 4,
    "SZ_00288": 3,
    "SZ_00401": 4,
    "SZ_00424": 4,
    "SZ_00549": 4,
    "SZ_00600": 3,
    "SZ_00668": 3,
    "SZ_00802": 3,
}

df["replicate_n"] = (
    df["study_record_id"]
    .map(replicate_n)
)


# ==========================================================
# CORREGIR DISPERSIÓN DE SZ_00071
#
# Sabemos n=4, pero NO está confirmado que ± sea SE.
# No lo usamos en el análisis principal de varianza.
# ==========================================================

mask_71 = (
    df["study_record_id"] == "SZ_00071"
)

df.loc[
    mask_71,
    "treatment_dispersion_type"
] = "UNKNOWN"

df.loc[
    mask_71,
    "control_dispersion_type"
] = "UNKNOWN"


# ==========================================================
# CONVERTIR DISPERSIÓN A SD
# ==========================================================

def to_sd(value, dtype, n):

    if pd.isna(value):
        return np.nan

    if dtype == "SD":
        return float(value)

    if dtype in ["SE", "SEM"]:

        if pd.isna(n):
            return np.nan

        return float(value) * np.sqrt(float(n))

    return np.nan


df["treatment_sd"] = df.apply(
    lambda r: to_sd(
        r["treatment_dispersion"],
        r["treatment_dispersion_type"],
        r["replicate_n"]
    ),
    axis=1
)

df["control_sd"] = df.apply(
    lambda r: to_sd(
        r["control_dispersion"],
        r["control_dispersion_type"],
        r["replicate_n"]
    ),
    axis=1
)


# ==========================================================
# ELEGIBILIDAD PARA ANÁLISIS BASADO EN VARIANZA
# ==========================================================

df["variance_ready"] = (
    df["replicate_n"].notna()
    &
    df["treatment_sd"].notna()
    &
    df["control_sd"].notna()
)


# ==========================================================
# CONTROL CON SD = 0
#
# No significa error.
# Muchos controles tienen mortalidad 0 en todas las réplicas.
# Lo identificamos porque afecta el cálculo posterior.
# ==========================================================

df["zero_control_sd"] = (
    df["control_sd"] == 0
)

df["zero_treatment_sd"] = (
    df["treatment_sd"] == 0
)


# ==========================================================
# MORTALIDAD CORREGIDA
#
# SZ_00424 reporta corrected cumulative mortality.
# ==========================================================

df["mortality_basis"] = "RAW"

df.loc[
    df["study_record_id"] == "SZ_00424",
    "mortality_basis"
] = "CORRECTED"


# ==========================================================
# GUARDAR
# ==========================================================

df.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


summary = (
    df.groupby("study_record_id")
    .agg(
        comparisons=(
            "treatment_effect_record_id",
            "size"
        ),
        replicate_n=(
            "replicate_n",
            "first"
        ),
        variance_ready=(
            "variance_ready",
            "sum"
        ),
        zero_control_sd=(
            "zero_control_sd",
            "sum"
        ),
        zero_treatment_sd=(
            "zero_treatment_sd",
            "sum"
        ),
        mortality_basis=(
            "mortality_basis",
            "first"
        )
    )
    .reset_index()
)

summary.to_csv(
    SUMMARY,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# SALIDA
# ==========================================================

print("\n==========================================")
print("DATASET LISTO PARA VARIANZA")
print("==========================================\n")

print("Comparaciones primarias:", len(df))

print(
    "Comparaciones variance-ready:",
    int(df["variance_ready"].sum())
)

print(
    "Estudios variance-ready:",
    df.loc[
        df["variance_ready"],
        "study_record_id"
    ].nunique()
)

print(
    "\nComparaciones con SD control = 0:",
    int(df["zero_control_sd"].sum())
)

print(
    "Comparaciones con SD tratamiento = 0:",
    int(df["zero_treatment_sd"].sum())
)


print("\n==========================================")
print("RESUMEN POR ESTUDIO")
print("==========================================\n")

print(summary.to_string(index=False))


print("\n==========================================")
print("TIPOS DE DISPERSIÓN")
print("==========================================\n")

print("Tratamiento:")
print(
    df["treatment_dispersion_type"]
    .value_counts()
    .to_string()
)

print("\nControl:")
print(
    df["control_dispersion_type"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("RANGO DE SD CONVERTIDA")
print("==========================================\n")

ready = df[df["variance_ready"]]

print(
    "Treatment SD:",
    ready["treatment_sd"].min(),
    "a",
    ready["treatment_sd"].max()
)

print(
    "Control SD:",
    ready["control_sd"].min(),
    "a",
    ready["control_sd"].max()
)

print(f"\nDataset:\n{OUTPUT}")
print(f"\nResumen:\n{SUMMARY}")
