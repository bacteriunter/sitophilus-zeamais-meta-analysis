#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
import re

PROJECT = Path.home() / "sitophilus_meta"

INPUT = PROJECT / "03_screening" / "high_priority.csv"
OUTDIR = PROJECT / "03_screening" / "refined"

OUTDIR.mkdir(parents=True, exist_ok=True)

OUT = OUTDIR / "refined_candidates.csv"


def match(text, pattern):
    return bool(re.search(pattern, text, flags=re.I))


df = pd.read_csv(INPUT)

df["title"] = df["title"].fillna("").astype(str)
df["abstract"] = df["abstract"].fillna("").astype(str)

df["title_low"] = df["title"].str.lower()
df["text"] = (
    df["title"] + " " + df["abstract"]
).str.lower()


# ==========================================================
# ESPECIE EN TÍTULO
# ==========================================================

zeamais = r"\bsitophilus\s+zeamais\b"

df["zeamais_title"] = df["title_low"].apply(
    lambda x: match(x, zeamais)
)


# ==========================================================
# MAÍZ
# ==========================================================

maize = (
    r"\b(maize|corn|zea\s+mays|maiz|maíz)\b"
)

df["maize_title"] = df["title_low"].apply(
    lambda x: match(x, maize)
)

df["maize_text"] = df["text"].apply(
    lambda x: match(x, maize)
)


# ==========================================================
# INTERVENCIONES NATURALES
# ==========================================================

botanical = (
    r"\b("
    r"botanical|botanicals|"
    r"plant powder|plant powders|"
    r"leaf powder|leaf powders|"
    r"seed powder|seed powders|"
    r"plant extract|plant extracts|"
    r"leaf extract|leaf extracts|"
    r"seed extract|seed extracts|"
    r"essential oil|essential oils|"
    r"vegetable oil|vegetable oils|"
    r"medicinal plant|medicinal plants|"
    r"bioactive plant|bioactive plants|"
    r"plant material|plant materials|"
    r"plant product|plant products"
    r")\b"
)

ash_material = (
    r"\b("
    r"wood ash|rice husk ash|ash|ashes|"
    r"diatomaceous earth|"
    r"inert dust|inert dusts|"
    r"clay|river sand|sand|"
    r"charcoal|bone charcoal|"
    r"rice husk silica"
    r")\b"
)

physical = (
    r"\b("
    r"hermetic|airtight|"
    r"modified atmosphere|"
    r"controlled atmosphere|"
    r"temperature|thermal|"
    r"heating|cooling|"
    r"cold storage|"
    r"solar heating"
    r")\b"
)

df["botanical_refined"] = df["text"].apply(
    lambda x: match(x, botanical)
)

df["natural_refined"] = df["text"].apply(
    lambda x: match(x, ash_material)
)

df["physical_refined"] = df["text"].apply(
    lambda x: match(x, physical)
)

df["intervention_refined"] = (
    df["botanical_refined"] |
    df["natural_refined"] |
    df["physical_refined"]
)


# ==========================================================
# OUTCOMES
# ==========================================================

outcome = (
    r"\b("
    r"mortality|survival|survivorship|"
    r"progeny|offspring|"
    r"adult emergence|emergence|"
    r"infestation|infested|"
    r"grain damage|kernel damage|"
    r"weight loss|mass loss|"
    r"germination|viability|"
    r"repellency|repellent|"
    r"oviposition|"
    r"insecticidal activity|"
    r"insecticidal effect|"
    r"toxicity"
    r")\b"
)

df["outcome_refined"] = df["text"].apply(
    lambda x: match(x, outcome)
)


# ==========================================================
# MODERADORES
# ==========================================================

temperature = (
    r"\b(temperature|temperatures|thermal|heat|cold|cooling)\b"
)

moisture = (
    r"\b("
    r"grain moisture|moisture content|"
    r"relative humidity|humidity"
    r")\b"
)

storage_time = (
    r"\b("
    r"storage time|storage period|"
    r"storage duration|days of storage|"
    r"weeks of storage|months of storage"
    r")\b"
)

dose = (
    r"\b("
    r"dose|doses|dosage|"
    r"concentration|concentrations|"
    r"g/kg|g kg|ml/kg|ml kg|"
    r"percent|percentage"
    r")\b"
)

df["mod_temperature"] = df["text"].apply(
    lambda x: match(x, temperature)
)

df["mod_moisture"] = df["text"].apply(
    lambda x: match(x, moisture)
)

df["mod_storage_time"] = df["text"].apply(
    lambda x: match(x, storage_time)
)

df["mod_dose"] = df["text"].apply(
    lambda x: match(x, dose)
)


# ==========================================================
# CLASIFICACIÓN
# ==========================================================

def classify(row):

    # Muy probable:
    # S. zeamais explícito en título + maíz +
    # intervención + outcome

    if (
        row["zeamais_title"]
        and row["maize_text"]
        and row["intervention_refined"]
        and row["outcome_refined"]
    ):
        return "A_VERY_LIKELY"

    # Probable: especie en título e intervención
    if (
        row["zeamais_title"]
        and row["intervention_refined"]
        and row["outcome_refined"]
    ):
        return "B_LIKELY"

    # Posible: especie puede aparecer sólo en abstract
    if (
        row["maize_text"]
        and row["intervention_refined"]
        and row["outcome_refined"]
    ):
        return "C_REVIEW"

    return "D_LOW"


df["refined_priority"] = df.apply(
    classify,
    axis=1
)


# ==========================================================
# GUARDAR
# ==========================================================

keep = [
    "study_record_id",
    "year",
    "title",
    "abstract",
    "journal",
    "doi",
    "refined_priority",
    "zeamais_title",
    "maize_text",
    "botanical_refined",
    "natural_refined",
    "physical_refined",
    "outcome_refined",
    "mod_temperature",
    "mod_moisture",
    "mod_storage_time",
    "mod_dose"
]

df[keep].to_csv(
    OUT,
    index=False,
    encoding="utf-8"
)

for group in [
    "A_VERY_LIKELY",
    "B_LIKELY",
    "C_REVIEW",
    "D_LOW"
]:

    df[df["refined_priority"] == group][keep].to_csv(
        OUTDIR / f"{group}.csv",
        index=False,
        encoding="utf-8"
    )


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("REFINAMIENTO DE CANDIDATOS HIGH")
print("==========================================\n")

print(f"Registros evaluados: {len(df)}")

print("\nClasificación:")

for group in [
    "A_VERY_LIKELY",
    "B_LIKELY",
    "C_REVIEW",
    "D_LOW"
]:
    n = (df["refined_priority"] == group).sum()
    print(f"{group:20s} {n}")


print("\nIntervenciones refinadas:")

print(
    f"Botánicos:             "
    f"{df['botanical_refined'].sum()}"
)

print(
    f"Ceniza/materiales:     "
    f"{df['natural_refined'].sum()}"
)

print(
    f"Físicas/temperatura:   "
    f"{df['physical_refined'].sum()}"
)


print("\nModeradores potenciales:")

print(
    f"Temperatura:           "
    f"{df['mod_temperature'].sum()}"
)

print(
    f"Humedad:               "
    f"{df['mod_moisture'].sum()}"
)

print(
    f"Tiempo almacenamiento: "
    f"{df['mod_storage_time'].sum()}"
)

print(
    f"Dosis/concentración:   "
    f"{df['mod_dose'].sum()}"
)


print("\n==========================================")
print("15 EJEMPLOS A_VERY_LIKELY")
print("==========================================\n")

examples = df[
    df["refined_priority"] == "A_VERY_LIKELY"
].head(15)

for _, row in examples.iterrows():

    print(row["title"])

    mods = []

    if row["mod_temperature"]:
        mods.append("temperatura")

    if row["mod_moisture"]:
        mods.append("humedad")

    if row["mod_storage_time"]:
        mods.append("tiempo")

    if row["mod_dose"]:
        mods.append("dosis")

    if mods:
        print(
            "   Moderadores: "
            + ", ".join(mods)
        )

    print()


print(f"Archivo:\n{OUT}")
