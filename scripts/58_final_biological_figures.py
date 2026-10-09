#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE = Path.home() / "sitophilus_meta"

INPUT = (
    BASE /
    "07_meta_analysis/biological_synthesis/"
    "mortality_biological_master.csv"
)

DOSE_INPUT = (
    BASE /
    "07_meta_analysis/biological_synthesis/"
    "dose_response_groups.csv"
)

FIGDIR = BASE / "08_figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)


# ============================================================
# FUNCIONES
# ============================================================

def sci(name):
    """
    Convierte nombres científicos conocidos a mathtext cursiva.
    Los textos no científicos permanecen normales.
    """

    mapping = {
        "Azadirachta indica":
            r"$\it{Azadirachta\ indica}$",

        "Coleus amboinicus":
            r"$\it{Coleus\ amboinicus}$",

        "Hymenocardia acida":
            r"$\it{Hymenocardia\ acida}$",

        "Lippia lanceolata":
            r"$\it{Lippia\ lanceolata}$",

        "Ocimum gratissimum":
            r"$\it{Ocimum\ gratissimum}$",

        "Plectranthus glandulosus":
            r"$\it{Plectranthus\ glandulosus}$",

        "Syzygium aromaticum":
            r"$\it{Syzygium\ aromaticum}$",

        "Tithonia diversifolia":
            r"$\it{Tithonia\ diversifolia}$",

        "Wedelia trilobata":
            r"$\it{Wedelia\ trilobata}$",

        "Annona senegalensis":
            r"$\it{Annona\ senegalensis}$",

        "Steganotaenia araliacea":
            r"$\it{Steganotaenia\ araliacea}$",

        "Hymenocardia acida + Azadirachta indica":
            r"$\it{Hymenocardia\ acida}$ + "
            r"$\it{Azadirachta\ indica}$",

        "Lippia lanceolata + Azadirachta indica":
            r"$\it{Lippia\ lanceolata}$ + "
            r"$\it{Azadirachta\ indica}$",

        "Plectranthus glandulosus + Hymenocardia acida":
            r"$\it{Plectranthus\ glandulosus}$ + "
            r"$\it{Hymenocardia\ acida}$",

        "Cow horn ash":
            "Ceniza de cuerno bovino",
    }

    return mapping.get(str(name), str(name))


def spanish_preparation(x):

    mapping = {
        "powder": "Polvo",
        "ash": "Ceniza",
        "neem seed oil": "Aceite de semilla",
        "aqueous extract": "Extracto acuoso",
        "ethanolic extract": "Extracto etanólico",
        "methanolic extract": "Extracto metanólico",
        "n-hexane extract": "Extracto n-hexano",
        "essential oil fumigation": "Aceite esencial / fumigación",
        "powder/fumigation": "Polvo / fumigación",
        "extract/fumigation": "Extracto / fumigación",
        "crude extract/contact": "Extracto crudo / contacto",
        "mixture": "Mezcla",
    }

    return mapping.get(str(x), str(x))


def spanish_part(x):

    mapping = {
        "leaf": "Hoja",
        "stem": "Tallo",
        "root": "Raíz",
        "wood": "Madera",
        "seed": "Semilla",
        "not applicable": "No aplica",
        "NR": "No reportado",
    }

    return mapping.get(str(x), str(x))


# ============================================================
# FIGURA 1
# MORTALIDAD GENERAL POR MATERIAL
# ============================================================

order = (
    df.groupby("species_material")["treatment_mean"]
    .median()
    .sort_values()
    .index
    .tolist()
)

positions = {
    name: i for i, name in enumerate(order)
}

fig, ax = plt.subplots(figsize=(10, 8))

for name in order:

    g = df[df["species_material"] == name]

    y = np.full(
        len(g),
        positions[name],
        dtype=float
    )

    if len(g) > 1:
        jitter = np.linspace(
            -0.16,
            0.16,
            len(g)
        )
    else:
        jitter = np.array([0.0])

    ax.scatter(
        g["treatment_mean"],
        y + jitter,
        alpha=0.60,
        s=28
    )


# Medianas
medians = (
    df.groupby("species_material")["treatment_mean"]
    .median()
)

for name in order:

    ax.scatter(
        medians[name],
        positions[name],
        marker="D",
        s=65,
        edgecolor="black",
        linewidth=0.8,
        zorder=5
    )


ax.set_yticks(range(len(order)))

ax.set_yticklabels(
    [sci(x) for x in order],
    fontsize=10
)

ax.set_xlim(-3, 103)

ax.set_xlabel(
    "Mortalidad reportada (%)",
    fontsize=11
)

ax.set_ylabel(
    "Especie vegetal / material natural",
    fontsize=11
)

# Referencia descriptiva de 90 %
ax.axvline(
    90,
    linestyle="--",
    linewidth=1
)

ax.text(
    90.5,
    len(order) - 0.5,
    "90 %",
    fontsize=8,
    va="top"
)

ax.grid(
    axis="x",
    alpha=0.20
)

fig.tight_layout()

fig.savefig(
    FIGDIR /
    "Figura_1_mortalidad_material.png",
    dpi=600,
    bbox_inches="tight"
)

fig.savefig(
    FIGDIR /
    "Figura_1_mortalidad_material.pdf",
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# FIGURA 2 PRINCIPAL
# 6 PANELES BIOLÓGICAMENTE INFORMATIVOS
# ============================================================

fig, axes = plt.subplots(
    3,
    2,
    figsize=(11, 12)
)

axes = axes.flatten()


# ------------------------------------------------------------
# A. Ocimum gratissimum
# ------------------------------------------------------------

ax = axes[0]

g = df[
    df["species_material"].eq(
        "Ocimum gratissimum"
    )
].sort_values("dose")

ax.plot(
    g["dose"],
    g["treatment_mean"],
    marker="o"
)

ax.set_title(
    r"A. $\it{Ocimum\ gratissimum}$ — polvo",
    fontsize=11
)

ax.set_xlabel(
    "Dosis (g/20 g de grano)"
)

ax.set_ylabel("Mortalidad (%)")
ax.set_ylim(-5, 105)
ax.grid(alpha=0.20)


# ------------------------------------------------------------
# B. Syzygium aromaticum
# ------------------------------------------------------------

ax = axes[1]

g = df[
    df["species_material"].eq(
        "Syzygium aromaticum"
    )
].copy()

# Puede contener más de un contexto experimental.
g = g.sort_values("dose")

ax.plot(
    g["dose"],
    g["treatment_mean"],
    marker="o"
)

ax.set_title(
    r"B. $\it{Syzygium\ aromaticum}$ — polvo",
    fontsize=11
)

ax.set_xlabel(
    "Dosis (% p/p)"
)

ax.set_ylabel("Mortalidad (%)")
ax.set_ylim(-5, 105)
ax.grid(alpha=0.20)


# ------------------------------------------------------------
# C. Azadirachta indica
# ------------------------------------------------------------

ax = axes[2]

g = df[
    df["species_material"].eq(
        "Azadirachta indica"
    )
].copy()

for prep, h in g.groupby(
    "preparation",
    dropna=False
):

    h = h.sort_values("dose")

    unit = h["dose_unit"].iloc[0]

    label = (
        f"{spanish_preparation(prep)} "
        f"({unit})"
    )

    ax.plot(
        h["dose"],
        h["treatment_mean"],
        marker="o",
        label=label
    )

ax.set_title(
    r"C. $\it{Azadirachta\ indica}$",
    fontsize=11
)

ax.set_xlabel("Dosis")
ax.set_ylabel("Mortalidad (%)")
ax.set_ylim(-5, 105)

ax.legend(
    fontsize=8,
    frameon=False
)

ax.grid(alpha=0.20)


# ------------------------------------------------------------
# D. Tithonia diversifolia
# ------------------------------------------------------------

ax = axes[3]

g = df[
    df["species_material"].eq(
        "Tithonia diversifolia"
    )
].copy()

for prep, h in g.groupby(
    "preparation",
    dropna=False
):

    h = h.sort_values("dose")

    ax.plot(
        h["dose"],
        h["treatment_mean"],
        marker="o",
        label=spanish_preparation(prep)
    )

ax.set_title(
    r"D. $\it{Tithonia\ diversifolia}$ — extractos",
    fontsize=11
)

unit = g["dose_unit"].iloc[0]

ax.set_xlabel(
    f"Dosis ({unit})"
)

ax.set_ylabel("Mortalidad (%)")
ax.set_ylim(-5, 105)

ax.legend(
    fontsize=8,
    frameon=False
)

ax.grid(alpha=0.20)


# ------------------------------------------------------------
# E. Plectranthus + Hymenocardia
# ------------------------------------------------------------

ax = axes[4]

targets = [
    "Plectranthus glandulosus",
    "Hymenocardia acida",
    "Plectranthus glandulosus + Hymenocardia acida"
]

g = df[
    (df["study_record_id"] == "SZ_00071") &
    (df["species_material"].isin(targets))
].copy()


# Plectranthus individual
h = g[
    g["species_material"].eq(
        "Plectranthus glandulosus"
    )
].sort_values("dose")

if len(h):

    ax.plot(
        h["dose"],
        h["treatment_mean"],
        marker="o",
        label=r"$\it{P.\ glandulosus}$"
    )


# Hymenocardia individual
h = g[
    g["species_material"].eq(
        "Hymenocardia acida"
    )
].sort_values("dose")

if len(h):

    ax.plot(
        h["dose"],
        h["treatment_mean"],
        marker="o",
        label=r"$\it{H.\ acida}$"
    )


# Mezclas: usar nombre original del tratamiento
mix = g[
    g["species_material"].eq(
        "Plectranthus glandulosus + Hymenocardia acida"
    )
].copy()

for treatment, h in mix.groupby("treatment"):

    h = h.sort_values("dose")

    ax.plot(
        h["dose"],
        h["treatment_mean"],
        marker="o",
        label=str(treatment)
    )


ax.set_title(
    r"E. $\it{P.\ glandulosus}$ + $\it{H.\ acida}$",
    fontsize=11
)

ax.set_xlabel("Dosis (g/kg)")
ax.set_ylabel("Mortalidad (%)")
ax.set_ylim(-5, 105)

ax.legend(
    fontsize=7,
    frameon=False,
    ncol=2
)

ax.grid(alpha=0.20)


# ------------------------------------------------------------
# F. Coleus amboinicus
# ------------------------------------------------------------

ax = axes[5]

g = df[
    df["species_material"].eq(
        "Coleus amboinicus"
    )
].copy()


# Para evitar 12 curvas en el panel principal,
# seleccionamos las preparaciones basadas en extractos.
g = g[
    g["preparation"].isin(
        [
            "extract/fumigation",
            "crude extract/contact"
        ]
    )
]


for keys, h in g.groupby(
    ["plant_part", "preparation"],
    dropna=False
):

    part, prep = keys

    h = h.sort_values("dose")

    label = (
        f"{spanish_part(part)} — "
        f"{spanish_preparation(prep)}"
    )

    ax.plot(
        h["dose"],
        h["treatment_mean"],
        marker="o",
        label=label
    )


ax.set_title(
    r"F. $\it{Coleus\ amboinicus}$ — extractos",
    fontsize=11
)

ax.set_xlabel("Dosis")
ax.set_ylabel("Mortalidad (%)")
ax.set_ylim(-5, 105)

ax.legend(
    fontsize=7,
    frameon=False
)

ax.grid(alpha=0.20)


# ------------------------------------------------------------
# Ajustes generales
# ------------------------------------------------------------

for ax in axes:

    ax.tick_params(
        labelsize=9
    )


fig.tight_layout(
    h_pad=2.2,
    w_pad=2.0
)

fig.savefig(
    FIGDIR /
    "Figura_2_dosis_respuesta_seleccionada.png",
    dpi=600,
    bbox_inches="tight"
)

fig.savefig(
    FIGDIR /
    "Figura_2_dosis_respuesta_seleccionada.pdf",
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# FIGURA SUPLEMENTARIA S1
# TODAS LAS SERIES DOSIS–RESPUESTA
# ============================================================

if DOSE_INPUT.exists():

    dose_df = pd.read_csv(DOSE_INPUT)

    labels = dose_df[
        "dose_group"
    ].dropna().unique()

    n = len(labels)

    fig_height = max(
        6,
        n * 2.15
    )

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

        species = (
            g["species_material"]
            .iloc[0]
        )

        prep = (
            g["preparation"]
            .iloc[0]
        )

        part = (
            g["plant_part"]
            .iloc[0]
        )

        title = (
            sci(species)
            + " — "
            + spanish_part(part)
            + " — "
            + spanish_preparation(prep)
        )

        ax.set_title(
            title,
            fontsize=9
        )

        unit = g[
            "dose_unit"
        ].iloc[0]

        ax.set_xlabel(
            f"Dosis ({unit})"
        )

        ax.set_ylabel(
            "Mortalidad (%)"
        )

        ax.set_ylim(
            -5,
            105
        )

        ax.grid(
            alpha=0.20
        )

    fig.tight_layout()

    fig.savefig(
        FIGDIR /
        "Figura_S1_dosis_respuesta_completa.png",
        dpi=400,
        bbox_inches="tight"
    )

    fig.savefig(
        FIGDIR /
        "Figura_S1_dosis_respuesta_completa.pdf",
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# FINAL
# ============================================================

print("\n========================================")
print("FIGURAS BIOLÓGICAS FINALES")
print("========================================")

print("\nFigura 1:")
print(
    FIGDIR /
    "Figura_1_mortalidad_material.png"
)

print("\nFigura 2:")
print(
    FIGDIR /
    "Figura_2_dosis_respuesta_seleccionada.png"
)

print("\nFigura suplementaria S1:")
print(
    FIGDIR /
    "Figura_S1_dosis_respuesta_completa.png"
)

print("\nListo.")
