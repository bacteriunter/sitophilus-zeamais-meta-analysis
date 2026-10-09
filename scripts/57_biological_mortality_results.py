#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE = Path.home() / "sitophilus_meta"

INPUT = (
    BASE /
    "07_meta_analysis/biological_synthesis/"
    "mortality_biological_master.csv"
)

OUTDIR = BASE / "07_meta_analysis/biological_synthesis"
FIGDIR = BASE / "08_figures"

OUTDIR.mkdir(parents=True, exist_ok=True)
FIGDIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)


# ============================================================
# 1. ETIQUETA BIOLÓGICA
# ============================================================

def make_label(row):

    sp = row["species_material"]
    part = row["plant_part"]
    prep = row["preparation"]

    pieces = [str(sp)]

    if pd.notna(part) and part != "NR":
        pieces.append(str(part))

    if pd.notna(prep) and prep != "NR":
        pieces.append(str(prep))

    return " | ".join(pieces)


df["biological_label"] = df.apply(make_label, axis=1)


# ============================================================
# 2. TABLA FINAL POR ESPECIE / MATERIAL
# ============================================================

species_summary = (
    df.groupby(
        [
            "species_material",
            "intervention_class"
        ],
        dropna=False
    )
    .agg(
        n_observations=("treatment_mean", "size"),
        n_studies=("study_record_id", "nunique"),
        mortality_min=("treatment_mean", "min"),
        mortality_median=("treatment_mean", "median"),
        mortality_mean=("treatment_mean", "mean"),
        mortality_max=("treatment_mean", "max"),
        time_min_h=("time_h", "min"),
        time_max_h=("time_h", "max")
    )
    .reset_index()
)

species_summary.to_csv(
    OUTDIR / "biological_species_summary.csv",
    index=False
)


# ============================================================
# 3. TABLA POR FORMULACIÓN / PARTE
# ============================================================

form_summary = (
    df.groupby(
        [
            "species_material",
            "plant_part",
            "preparation",
            "dose_unit"
        ],
        dropna=False
    )
    .agg(
        n_observations=("treatment_mean", "size"),
        n_studies=("study_record_id", "nunique"),
        dose_min=("dose", "min"),
        dose_max=("dose", "max"),
        time_min_h=("time_h", "min"),
        time_max_h=("time_h", "max"),
        mortality_min=("treatment_mean", "min"),
        mortality_median=("treatment_mean", "median"),
        mortality_max=("treatment_mean", "max")
    )
    .reset_index()
)

form_summary.to_csv(
    OUTDIR / "biological_formulation_summary.csv",
    index=False
)


# ============================================================
# 4. RESPUESTA ALTA OBSERVADA
#
# No significa "mejor tratamiento".
# Solo identifica observaciones >= 90% bajo las condiciones
# específicas de cada experimento.
# ============================================================

high = df[df["treatment_mean"] >= 90].copy()

high = high[
    [
        "study_record_id",
        "species_material",
        "plant_part",
        "preparation",
        "dose",
        "dose_unit",
        "time_h",
        "treatment_mean",
        "control_mean",
        "mortality_basis"
    ]
].sort_values(
    ["time_h", "treatment_mean"],
    ascending=[True, False]
)

high.to_csv(
    OUTDIR / "high_mortality_observations_90pct.csv",
    index=False
)


# ============================================================
# 5. CONSISTENCIA DE RESPUESTA
# ============================================================

consistency = (
    df.groupby(
        "biological_label",
        dropna=False
    )
    .agg(
        n=("treatment_mean", "size"),
        studies=("study_record_id", "nunique"),
        mortality_min=("treatment_mean", "min"),
        mortality_median=("treatment_mean", "median"),
        mortality_max=("treatment_mean", "max"),
        proportion_ge_90=(
            "treatment_mean",
            lambda x: (x >= 90).mean()
        ),
        proportion_ge_75=(
            "treatment_mean",
            lambda x: (x >= 75).mean()
        )
    )
    .reset_index()
)

consistency.to_csv(
    OUTDIR / "biological_response_consistency.csv",
    index=False
)


# ============================================================
# 6. FIGURA — MORTALIDAD POR ESPECIE / MATERIAL
# ============================================================

order = (
    df.groupby("species_material")["treatment_mean"]
    .median()
    .sort_values()
    .index
    .tolist()
)

fig, ax = plt.subplots(figsize=(10, 8))

positions = {
    name: i for i, name in enumerate(order)
}

# puntos individuales
for name in order:

    g = df[df["species_material"] == name]

    y = np.full(len(g), positions[name], dtype=float)

    # jitter determinista para evitar solapamiento
    if len(g) > 1:
        jitter = np.linspace(-0.16, 0.16, len(g))
    else:
        jitter = np.array([0.0])

    ax.scatter(
        g["treatment_mean"],
        y + jitter,
        alpha=0.65,
        s=28
    )

# mediana
medians = (
    df.groupby("species_material")["treatment_mean"]
    .median()
)

for name in order:

    ax.scatter(
        medians[name],
        positions[name],
        marker="D",
        s=70,
        edgecolor="black",
        linewidth=0.8,
        zorder=5
    )

ax.set_yticks(range(len(order)))
ax.set_yticklabels(order)

ax.set_xlim(-3, 103)

ax.set_xlabel("Reported mortality (%)")
ax.set_ylabel("Plant species / natural material")

ax.axvline(
    90,
    linestyle="--",
    linewidth=1
)

ax.grid(
    axis="x",
    alpha=0.25
)

fig.tight_layout()

fig.savefig(
    FIGDIR / "biological_mortality_by_material.png",
    dpi=600,
    bbox_inches="tight"
)

fig.savefig(
    FIGDIR / "biological_mortality_by_material.pdf",
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 7. DOSIS–RESPUESTA
#
# Solo grupos con >=3 dosis diferentes.
# No se ajusta regresión.
# Las líneas únicamente conectan observaciones.
# ============================================================

dose_groups = []

group_cols = [
    "study_record_id",
    "species_material",
    "plant_part",
    "preparation",
    "dose_unit",
    "time_h"
]

for keys, g in df.groupby(group_cols, dropna=False):

    if g["dose"].nunique() >= 3:

        g = g.sort_values("dose").copy()

        g["dose_group"] = " | ".join(
            [str(x) for x in keys]
        )

        dose_groups.append(g)


if dose_groups:

    dose_df = pd.concat(
        dose_groups,
        ignore_index=True
    )

    dose_df.to_csv(
        OUTDIR / "dose_response_groups.csv",
        index=False
    )

    # gráfico multipágina no; una figura general con paneles
    labels = dose_df["dose_group"].unique()

    n = len(labels)

    fig_height = max(6, n * 2.2)

    fig, axes = plt.subplots(
        nrows=n,
        ncols=1,
        figsize=(9, fig_height),
        squeeze=False
    )

    for i, label in enumerate(labels):

        ax = axes[i, 0]

        g = dose_df[
            dose_df["dose_group"] == label
        ].sort_values("dose")

        ax.plot(
            g["dose"],
            g["treatment_mean"],
            marker="o"
        )

        unit = g["dose_unit"].iloc[0]

        title_parts = label.split(" | ")

        ax.set_title(
            " | ".join(title_parts[1:4]),
            fontsize=9
        )

        ax.set_xlabel(f"Dose ({unit})")
        ax.set_ylabel("Mortality (%)")
        ax.set_ylim(-5, 105)

        ax.grid(alpha=0.25)

    fig.tight_layout()

    fig.savefig(
        FIGDIR / "biological_dose_response.png",
        dpi=600,
        bbox_inches="tight"
    )

    fig.savefig(
        FIGDIR / "biological_dose_response.pdf",
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# 8. SALIDA EN TERMINAL
# ============================================================

print("\n========================================")
print("BIOLOGICAL SYNTHESIS — FINAL")
print("========================================")

print("\nObservaciones:", len(df))
print("Estudios:", df["study_record_id"].nunique())
print(
    "Especies/materiales:",
    df["species_material"].nunique()
)

print("\n========================================")
print("RESUMEN POR ESPECIE / MATERIAL")
print("========================================")

print(
    species_summary[
        [
            "species_material",
            "n_observations",
            "n_studies",
            "mortality_min",
            "mortality_median",
            "mortality_max"
        ]
    ]
    .sort_values(
        "mortality_median",
        ascending=False
    )
    .to_string(index=False)
)

print("\n========================================")
print("OBSERVACIONES >=90%")
print("========================================")

print("Número:", len(high))
print(
    "Estudios:",
    high["study_record_id"].nunique()
)

print("\nPor especie/material:")

print(
    high["species_material"]
    .value_counts()
    .to_string()
)

print("\n========================================")
print("CONSISTENCIA")
print("========================================")

print(
    consistency[
        [
            "biological_label",
            "n",
            "studies",
            "mortality_median",
            "proportion_ge_75",
            "proportion_ge_90"
        ]
    ]
    .sort_values(
        [
            "proportion_ge_90",
            "mortality_median"
        ],
        ascending=False
    )
    .to_string(index=False)
)

print("\nARCHIVOS GENERADOS:")
print(
    OUTDIR /
    "biological_species_summary.csv"
)
print(
    OUTDIR /
    "biological_formulation_summary.csv"
)
print(
    OUTDIR /
    "high_mortality_observations_90pct.csv"
)
print(
    OUTDIR /
    "biological_response_consistency.csv"
)
print(
    OUTDIR /
    "dose_response_groups.csv"
)

print("\nFIGURAS:")
print(
    FIGDIR /
    "biological_mortality_by_material.png"
)
print(
    FIGDIR /
    "biological_dose_response.png"
)
