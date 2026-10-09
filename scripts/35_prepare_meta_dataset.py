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
    PROJECT / "07_meta_analysis/"
    "mortality_meta_dataset.csv"
)

SUMMARY = (
    PROJECT / "07_meta_analysis/"
    "mortality_meta_dataset_summary.csv"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

# ==========================================================
# CONJUNTO PRIMARIO
# ==========================================================

df = df[
    df["analysis_set"] == "PRIMARY_MEAN_MORTALITY"
].copy()

df = df.reset_index(drop=True)


# ==========================================================
# VARIABLE DE RESPUESTA
# ==========================================================

df["mortality_pct"] = df["treatment_mean"].astype(float)

df["mortality_prop"] = (
    df["mortality_pct"] / 100.0
)


# ==========================================================
# TRANSFORMACIÓN LOGIT
#
# Solo para permitir valores 0 y 1:
# 0%   -> 0.005
# 100% -> 0.995
#
# Los valores interiores NO se modifican.
# ==========================================================

epsilon = 0.005

df["mortality_prop_logit"] = (
    df["mortality_prop"]
    .clip(
        lower=epsilon,
        upper=1.0 - epsilon
    )
)

df["mortality_logit"] = np.log(
    df["mortality_prop_logit"]
    /
    (1.0 - df["mortality_prop_logit"])
)


# ==========================================================
# IDENTIFICADORES JERÁRQUICOS
# ==========================================================

df["study_id"] = df["study_record_id"]

df["experiment_id_meta"] = (
    df["experiment_id"].astype(str)
)

df["treatment_id"] = (
    df["study_record_id"].astype(str)
    + "__"
    + df["treatment"].astype(str)
)

df["effect_id"] = [
    f"E{i:04d}"
    for i in range(1, len(df) + 1)
]


# ==========================================================
# DOSIS
# ==========================================================

df["dose_numeric"] = pd.to_numeric(
    df["dose"],
    errors="coerce"
)

df["has_dose"] = (
    df["dose_numeric"].notna()
)


# ==========================================================
# BASE DE MORTALIDAD
# ==========================================================

df["mortality_basis"] = "RAW"

df.loc[
    df["study_record_id"] == "SZ_00424",
    "mortality_basis"
] = "CORRECTED"


# ==========================================================
# INDICADORES DE SENSIBILIDAD
# ==========================================================

df["boundary_0_100"] = (
    (df["mortality_pct"] == 0)
    |
    (df["mortality_pct"] == 100)
)

df["raw_mortality_only"] = (
    df["mortality_basis"] == "RAW"
)

df["non_boundary"] = (
    ~df["boundary_0_100"]
)


# ==========================================================
# VALIDACIONES
# ==========================================================

assert len(df) == 154

assert df["mortality_pct"].between(
    0, 100
).all()

assert df["mortality_prop"].between(
    0, 1
).all()

assert np.isfinite(
    df["mortality_logit"]
).all()

assert df["effect_id"].is_unique


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
        effects=("effect_id", "size"),
        experiments=("experiment_id_meta", "nunique"),
        treatments=("treatment_id", "nunique"),
        doses=("dose_numeric", "nunique"),
        mean_mortality=("mortality_pct", "mean"),
        min_mortality=("mortality_pct", "min"),
        max_mortality=("mortality_pct", "max"),
        boundary_values=("boundary_0_100", "sum"),
        mortality_basis=("mortality_basis", "first")
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
print("DATASET PARA META-ANÁLISIS")
print("==========================================\n")

print("Efectos:", len(df))
print(
    "Estudios:",
    df["study_id"].nunique()
)

print(
    "Experimentos:",
    df["experiment_id_meta"].nunique()
)

print(
    "Tratamientos:",
    df["treatment_id"].nunique()
)

print(
    "Con dosis:",
    int(df["has_dose"].sum())
)

print(
    "Valores 0/100:",
    int(df["boundary_0_100"].sum())
)

print(
    "Mortalidad RAW:",
    int(df["raw_mortality_only"].sum())
)

print(
    "Mortalidad CORRECTED:",
    int(
        (
            df["mortality_basis"]
            == "CORRECTED"
        ).sum()
    )
)


print("\n==========================================")
print("RANGO TRANSFORMADO")
print("==========================================\n")

print(
    "Proporción:",
    df["mortality_prop"].min(),
    "a",
    df["mortality_prop"].max()
)

print(
    "Logit:",
    round(df["mortality_logit"].min(), 4),
    "a",
    round(df["mortality_logit"].max(), 4)
)


print("\n==========================================")
print("RESUMEN POR ESTUDIO")
print("==========================================\n")

print(summary.to_string(index=False))

print(f"\nDataset:\n{OUTPUT}")
print(f"\nResumen:\n{SUMMARY}")
