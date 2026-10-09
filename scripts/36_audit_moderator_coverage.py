#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT / "07_meta_analysis/"
    "mortality_meta_dataset.csv"
)

OUTPUT = (
    PROJECT / "07_meta_analysis/"
    "moderator_coverage.csv"
)

df = pd.read_csv(INPUT)


print("\n==========================================")
print("COBERTURA DE MODERADORES")
print("==========================================\n")

print("Observaciones:", len(df))
print("Estudios:", df["study_id"].nunique())
print("Experimentos:", df["experiment_id_meta"].nunique())
print("Tratamientos:", df["treatment_id"].nunique())


# ==========================================================
# FORMULACIÓN
# ==========================================================

form = (
    df.groupby("formulation", dropna=False)
    .agg(
        observations=("effect_id", "size"),
        studies=("study_id", "nunique"),
        experiments=("experiment_id_meta", "nunique"),
        treatments=("treatment_id", "nunique"),
        mean_mortality=("mortality_pct", "mean"),
        median_mortality=("mortality_pct", "median")
    )
    .reset_index()
    .sort_values(
        ["studies", "observations"],
        ascending=False
    )
)

print("\n==========================================")
print("FORMULACIÓN")
print("==========================================\n")

print(form.to_string(index=False))


# ==========================================================
# UNIDAD DE DOSIS
# ==========================================================

dose_units = (
    df.groupby("dose_unit", dropna=False)
    .agg(
        observations=("effect_id", "size"),
        studies=("study_id", "nunique"),
        experiments=("experiment_id_meta", "nunique"),
        treatments=("treatment_id", "nunique"),
        min_dose=("dose_numeric", "min"),
        max_dose=("dose_numeric", "max")
    )
    .reset_index()
    .sort_values(
        ["studies", "observations"],
        ascending=False
    )
)

print("\n==========================================")
print("UNIDADES DE DOSIS")
print("==========================================\n")

print(dose_units.to_string(index=False))


# ==========================================================
# FORMULACIÓN × ESTUDIO
# ==========================================================

cross = pd.crosstab(
    df["formulation"].fillna("NA"),
    df["study_id"]
)

print("\n==========================================")
print("FORMULACIÓN × ESTUDIO")
print("==========================================\n")

print(cross.to_string())


# ==========================================================
# TIEMPO FINAL
# ==========================================================

time = (
    df.groupby("time_h", dropna=False)
    .agg(
        observations=("effect_id", "size"),
        studies=("study_id", "nunique"),
        experiments=("experiment_id_meta", "nunique"),
        mean_mortality=("mortality_pct", "mean")
    )
    .reset_index()
    .sort_values("time_h")
)

print("\n==========================================")
print("TIEMPO DE EXPOSICIÓN")
print("==========================================\n")

print(time.to_string(index=False))


# ==========================================================
# DOSIS DENTRO DE CADA UNIDAD
# ==========================================================

print("\n==========================================")
print("DOSIS POR UNIDAD")
print("==========================================\n")

for unit, g in df.groupby("dose_unit", dropna=False):

    print(f"\nUNIDAD: {unit}")
    print(" Observaciones:", len(g))
    print(" Estudios:", g["study_id"].nunique())
    print(" Tratamientos:", g["treatment_id"].nunique())

    if g["dose_numeric"].notna().any():
        print(
            " Rango:",
            g["dose_numeric"].min(),
            "a",
            g["dose_numeric"].max()
        )


# ==========================================================
# GUARDAR RESUMEN
# ==========================================================

form["moderator"] = "formulation"
form["level"] = form["formulation"].astype(str)

out_form = form[
    [
        "moderator",
        "level",
        "observations",
        "studies",
        "experiments",
        "treatments"
    ]
]

dose_out = dose_units.copy()
dose_out["moderator"] = "dose_unit"
dose_out["level"] = dose_out["dose_unit"].astype(str)

dose_out = dose_out[
    [
        "moderator",
        "level",
        "observations",
        "studies",
        "experiments",
        "treatments"
    ]
]

out = pd.concat(
    [out_form, dose_out],
    ignore_index=True
)

out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

print(f"\nResumen:\n{OUTPUT}")
