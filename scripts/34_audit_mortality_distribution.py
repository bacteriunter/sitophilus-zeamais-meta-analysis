#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT / "06_effect_sizes/"
    "mortality_comparison_map_final.csv"
)

OUT = (
    PROJECT / "06_effect_sizes/"
    "mortality_distribution_audit.csv"
)

df = pd.read_csv(INPUT)

# Solo conjunto primario
x = df[
    df["analysis_set"] == "PRIMARY_MEAN_MORTALITY"
].copy()

x["mortality_pct"] = x["treatment_mean"]
x["mortality_prop"] = x["mortality_pct"] / 100

x["is_zero"] = x["mortality_pct"] == 0
x["is_hundred"] = x["mortality_pct"] == 100
x["boundary"] = x["is_zero"] | x["is_hundred"]

# ----------------------------------------------------------
# Resumen por estudio
# ----------------------------------------------------------

summary = (
    x.groupby("study_record_id")
    .agg(
        observations=("mortality_pct", "size"),
        min_mortality=("mortality_pct", "min"),
        median_mortality=("mortality_pct", "median"),
        mean_mortality=("mortality_pct", "mean"),
        max_mortality=("mortality_pct", "max"),
        zeros=("is_zero", "sum"),
        hundreds=("is_hundred", "sum"),
        boundaries=("boundary", "sum"),
        experiments=("experiment_id", "nunique"),
        treatments=("treatment", "nunique")
    )
    .reset_index()
)

summary.to_csv(
    OUT,
    index=False,
    encoding="utf-8"
)

print("\n==========================================")
print("DISTRIBUCIÓN DE MORTALIDAD")
print("==========================================\n")

print("Observaciones:", len(x))
print("Estudios:", x["study_record_id"].nunique())

print("\nRango:")
print(
    x["mortality_pct"].min(),
    "a",
    x["mortality_pct"].max()
)

print("\nMedia:", round(x["mortality_pct"].mean(), 3))
print("Mediana:", round(x["mortality_pct"].median(), 3))

print("\nMortalidad = 0:")
print(int(x["is_zero"].sum()))

print("\nMortalidad = 100:")
print(int(x["is_hundred"].sum()))

print("\nTotal en límites 0/100:")
print(int(x["boundary"].sum()))

print(
    "Porcentaje en límites:",
    round(100 * x["boundary"].mean(), 2),
    "%"
)

print("\n==========================================")
print("POR ESTUDIO")
print("==========================================\n")

print(summary.to_string(index=False))


print("\n==========================================")
print("CUANTILES")
print("==========================================\n")

print(
    x["mortality_pct"]
    .quantile([
        0,
        0.05,
        0.10,
        0.25,
        0.50,
        0.75,
        0.90,
        0.95,
        1
    ])
    .to_string()
)


print("\n==========================================")
print("FRECUENCIA POR INTERVALO")
print("==========================================\n")

bins = [-0.001, 10, 25, 50, 75, 90, 99.999, 100]

labels = [
    "0-10",
    ">10-25",
    ">25-50",
    ">50-75",
    ">75-90",
    ">90-<100",
    "100"
]

x["mortality_interval"] = pd.cut(
    x["mortality_pct"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

print(
    x["mortality_interval"]
    .value_counts(sort=False)
    .to_string()
)

print(f"\nResumen:\n{OUT}")
