#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import numpy as np
import re

BASE = Path.home() / "sitophilus_meta"

INPUT = BASE / "07_meta_analysis/mortality_meta_dataset.csv"

OUTDIR = BASE / "07_meta_analysis/biological_synthesis"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER = OUTDIR / "mortality_biological_master.csv"
OUT_SUMMARY = OUTDIR / "mortality_biological_summary.csv"

df = pd.read_csv(INPUT)


# ============================================================
# 1. Clasificación biológica
# ============================================================

def classify(row):

    t = str(row["treatment"]).strip()
    f = str(row["formulation"]).strip()

    species = "NR"
    material = "NR"
    plant_part = "NR"
    preparation = "NR"
    intervention_class = "NR"

    # --------------------------------------------------------
    # Plectranthus glandulosus
    # --------------------------------------------------------
    if "Plectranthus glandulosus" in t:
        species = "Plectranthus glandulosus"
        material = "plant material"
        intervention_class = "botanical"

        if f == "powder":
            preparation = "powder"

    # --------------------------------------------------------
    # Hymenocardia acida
    # --------------------------------------------------------
    elif "Hymenocardia acida" in t or t == "H. acida":
        species = "Hymenocardia acida"
        intervention_class = "natural material"

        if "wood ash" in t.lower():
            material = "wood ash"
            preparation = "ash"
        else:
            material = "plant-derived material"

    # --------------------------------------------------------
    # PG + HA mixtures
    # --------------------------------------------------------
    elif re.fullmatch(r"\d+PG\d+HA", t):
        species = "Plectranthus glandulosus + Hymenocardia acida"
        material = "plant material + wood ash"
        preparation = "mixture"
        intervention_class = "botanical/natural material mixture"

    # --------------------------------------------------------
    # Cow horn ash
    # --------------------------------------------------------
    elif "Cow Horn Ash" in t:
        species = "NA"
        material = "cow horn ash"
        preparation = "ash"
        intervention_class = "natural material"

    # --------------------------------------------------------
    # Tithonia diversifolia
    # --------------------------------------------------------
    elif "Tithonia diversifolia" in t:
        species = "Tithonia diversifolia"
        material = "plant extract"
        intervention_class = "botanical"

        if "Aqueous" in t:
            preparation = "aqueous extract"
        elif "Ethanol" in t:
            preparation = "ethanolic extract"
        elif "Methanol" in t:
            preparation = "methanolic extract"
        elif "N-Hexene" in t:
            preparation = "n-hexane extract"

    # --------------------------------------------------------
    # Syzygium aromaticum
    # --------------------------------------------------------
    elif "Syzygium aromaticum" in t:
        species = "Syzygium aromaticum"
        material = "plant powder"
        preparation = "powder"
        intervention_class = "botanical"

    # --------------------------------------------------------
    # Azadirachta indica
    # --------------------------------------------------------
    elif t in ["A. indica", "Azadirachta indica"]:
        species = "Azadirachta indica"
        material = "plant-derived material"
        intervention_class = "botanical"

        if f == "powder":
            preparation = "powder"

    # --------------------------------------------------------
    # Lippia lanceolata
    # --------------------------------------------------------
    elif t == "L. lanceolata":
        species = "Lippia lanceolata"
        material = "plant-derived material"
        intervention_class = "botanical"

    # --------------------------------------------------------
    # Lippia + Azadirachta
    # --------------------------------------------------------
    elif "L. lanceolata + A. indica" in t:
        species = "Lippia lanceolata + Azadirachta indica"
        material = "plant mixture"
        preparation = "mixture"
        intervention_class = "botanical mixture"

    # --------------------------------------------------------
    # Hymenocardia + Azadirachta
    # --------------------------------------------------------
    elif "H. acida + A. indica" in t:
        species = "Hymenocardia acida + Azadirachta indica"
        material = "plant-derived mixture"
        preparation = "mixture"
        intervention_class = "botanical/natural material mixture"

    # --------------------------------------------------------
    # Wedelia trilobata
    # --------------------------------------------------------
    elif "Wedelia trilobata" in t:
        species = "Wedelia trilobata"
        intervention_class = "botanical"

        if "essential oil" in t:
            material = "essential oil"
            preparation = "essential oil fumigation"

        elif "powder" in t:
            material = "plant powder"
            preparation = "powder"

    # --------------------------------------------------------
    # Coleus amboinicus
    # --------------------------------------------------------
    elif "Coleus amboinicus" in t:
        species = "Coleus amboinicus"
        intervention_class = "botanical"

        if "Leaf" in t:
            plant_part = "leaf"
        elif "Stem" in t:
            plant_part = "stem"
        elif "Root" in t:
            plant_part = "root"

        material = "plant material"

        if f and f != "nan":
            preparation = f

    # --------------------------------------------------------
    # Ocimum gratissimum
    # --------------------------------------------------------
    elif "Ocimum gratissimum" in t:
        species = "Ocimum gratissimum"
        material = "plant powder"
        preparation = "powder"
        intervention_class = "botanical"

    # --------------------------------------------------------
    # Steganotaenia araliacea
    # --------------------------------------------------------
    elif "Steganotaenia araliacea" in t:
        species = "Steganotaenia araliacea"
        material = "plant powder"
        preparation = "powder"
        intervention_class = "botanical"

    # --------------------------------------------------------
    # Annona senegalensis
    # --------------------------------------------------------
    elif "Annona senegalensis" in t:
        species = "Annona senegalensis"
        material = "plant powder"
        preparation = "powder"
        intervention_class = "botanical"

    return pd.Series({
        "species_material": species,
        "material": material,
        "plant_part": plant_part,
        "preparation": preparation,
        "intervention_class": intervention_class
    })


bio = df.apply(classify, axis=1)

df = pd.concat([df, bio], axis=1)


# ============================================================
# 2. Tabla biológica principal
# ============================================================

keep = [
    "study_record_id",
    "experiment_id",
    "treatment",
    "species_material",
    "material",
    "plant_part",
    "preparation",
    "intervention_class",
    "dose",
    "dose_unit",
    "time_h",
    "treatment_mean",
    "control_mean",
    "mortality_basis"
]

master = df[keep].copy()

master = master.sort_values(
    ["study_record_id", "species_material", "preparation", "dose"]
)

master.to_csv(OUT_MASTER, index=False)


# ============================================================
# 3. Resumen por tratamiento/preparación
# ============================================================

summary = (
    master
    .groupby(
        [
            "species_material",
            "plant_part",
            "preparation",
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
        min_time_h=("time_h", "min"),
        max_time_h=("time_h", "max")
    )
    .reset_index()
)

summary = summary.sort_values(
    ["mortality_max", "mortality_median"],
    ascending=False
)

summary.to_csv(OUT_SUMMARY, index=False)


# ============================================================
# 4. Salida de control
# ============================================================

print("\n==========================================")
print("TABLA BIOLÓGICA DE MORTALIDAD")
print("==========================================")

print(f"\nObservaciones: {len(master)}")
print(f"Estudios: {master['study_record_id'].nunique()}")
print(
    "Especies/materiales:",
    master["species_material"].nunique()
)

print("\nCLASES DE INTERVENCIÓN:")
print(
    master["intervention_class"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nESPECIES / MATERIALES:")
print(
    master.groupby("species_material")
    .agg(
        n=("treatment_mean", "size"),
        studies=("study_record_id", "nunique"),
        min_mortality=("treatment_mean", "min"),
        median_mortality=("treatment_mean", "median"),
        max_mortality=("treatment_mean", "max")
    )
    .sort_values("max_mortality", ascending=False)
    .to_string()
)

print("\nTOP 20 OBSERVACIONES DE MORTALIDAD:")
print(
    master[
        [
            "study_record_id",
            "species_material",
            "plant_part",
            "preparation",
            "dose",
            "dose_unit",
            "time_h",
            "treatment_mean",
            "mortality_basis"
        ]
    ]
    .sort_values("treatment_mean", ascending=False)
    .head(20)
    .to_string(index=False)
)

print("\nCAMPOS NO RESUELTOS:")
for c in [
    "species_material",
    "material",
    "plant_part",
    "preparation",
    "intervention_class"
]:
    n = (master[c] == "NR").sum()
    print(f"{c}: {n}/{len(master)}")

print("\nARCHIVOS:")
print(OUT_MASTER)
print(OUT_SUMMARY)
