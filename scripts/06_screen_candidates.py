#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
import re

PROJECT = Path.home() / "sitophilus_meta"

INPUT = PROJECT / "02_deduplication" / "master_unique.csv"
OUTDIR = PROJECT / "03_screening"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT_ALL = OUTDIR / "screening_scored.csv"
OUTPUT_HIGH = OUTDIR / "high_priority.csv"
OUTPUT_MEDIUM = OUTDIR / "medium_priority.csv"
OUTPUT_NOABS = OUTDIR / "no_abstract.csv"


# ==========================================================
# FUNCIONES
# ==========================================================

def contains(text, pattern):
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


# ==========================================================
# LEER
# ==========================================================

df = pd.read_csv(INPUT)

df["title"] = df["title"].fillna("").astype(str)
df["abstract"] = df["abstract"].fillna("").astype(str)

df["text"] = (
    df["title"] + " " + df["abstract"]
).str.lower()

df["has_abstract"] = (
    df["abstract"].str.strip().str.len() > 0
)


# ==========================================================
# PATRONES
# ==========================================================

species = (
    r"\bsitophilus\s+zeamais\b"
)

maize = (
    r"\b(maize|corn|zea\s+mays|maiz|maíz)\b"
)

botanical = (
    r"\b("
    r"botanical|plant extract|plant extracts|"
    r"plant powder|plant powders|"
    r"leaf powder|seed powder|"
    r"essential oil|essential oils|"
    r"vegetable oil|vegetable oils|"
    r"medicinal plant|medicinal plants|"
    r"phytochemical|"
    r"aqueous extract|ethanolic extract|"
    r"methanolic extract"
    r")\b"
)

natural_material = (
    r"\b("
    r"ash|ashes|wood ash|"
    r"diatomaceous earth|"
    r"inert dust|inert dusts|"
    r"clay|sand"
    r")\b"
)

physical = (
    r"\b("
    r"temperature|thermal|heat|heating|"
    r"cold|cooling|"
    r"hermetic|airtight|"
    r"modified atmosphere|"
    r"controlled atmosphere|"
    r"solarization|solar heating"
    r")\b"
)

storage = (
    r"\b("
    r"storage|stored|stored grain|"
    r"grain storage|postharvest|post-harvest|"
    r"silo|silos|container|containers"
    r")\b"
)

outcome = (
    r"\b("
    r"mortality|adult mortality|"
    r"survival|survivorship|"
    r"emergence|adult emergence|progeny|"
    r"f1|offspring|"
    r"infestation|infested|"
    r"grain damage|kernel damage|damage|"
    r"weight loss|mass loss|"
    r"germination|viability|"
    r"repellency|repellent|"
    r"oviposition|"
    r"insecticidal|toxicity"
    r")\b"
)

experimental = (
    r"\b("
    r"experiment|experimental|"
    r"treatment|treated|"
    r"control|untreated|"
    r"dose|dosage|concentration|"
    r"replicate|replicates|replication|"
    r"bioassay|bioassays|"
    r"exposure|exposed"
    r")\b"
)

native_maize = (
    r"\b("
    r"native maize|native corn|"
    r"local maize|local corn|"
    r"landrace|landraces|"
    r"traditional variety|traditional varieties|"
    r"maize variety|maize varieties|"
    r"corn variety|corn varieties|"
    r"cultivar|cultivars"
    r")\b"
)


# ==========================================================
# DETECTAR SEÑALES
# ==========================================================

patterns = {
    "species": species,
    "maize": maize,
    "botanical": botanical,
    "natural_material": natural_material,
    "physical": physical,
    "storage": storage,
    "outcome": outcome,
    "experimental": experimental,
    "native_maize": native_maize
}

for name, pattern in patterns.items():

    df[name] = df["text"].apply(
        lambda x: contains(x, pattern)
    )


# ==========================================================
# PUNTUACIÓN
# ==========================================================

df["score"] = 0

# Especie y hospedero
df.loc[df["species"], "score"] += 3
df.loc[df["maize"], "score"] += 2

# Intervenciones principales
df.loc[df["botanical"], "score"] += 3
df.loc[df["natural_material"], "score"] += 3
df.loc[df["physical"], "score"] += 2

# Contexto almacenamiento
df.loc[df["storage"], "score"] += 1

# Variables de respuesta
df.loc[df["outcome"], "score"] += 3

# Señal experimental
df.loc[df["experimental"], "score"] += 3

# Interés especial
df.loc[df["native_maize"], "score"] += 1


# ==========================================================
# CLASIFICACIÓN
# ==========================================================

def classify(row):

    if not row["has_abstract"]:
        return "NO_ABSTRACT"

    # Alta prioridad:
    # especie + maíz + intervención + outcome + señal experimental

    intervention = (
        row["botanical"]
        or row["natural_material"]
        or row["physical"]
    )

    if (
        row["species"]
        and row["maize"]
        and intervention
        and row["outcome"]
        and row["experimental"]
    ):
        return "HIGH"

    # Prioridad media

    if row["score"] >= 9:
        return "MEDIUM"

    return "LOW"


df["priority"] = df.apply(
    classify,
    axis=1
)


# ==========================================================
# RAZONES
# ==========================================================

def reasons(row):

    found = []

    for col in [
        "species",
        "maize",
        "botanical",
        "natural_material",
        "physical",
        "storage",
        "outcome",
        "experimental",
        "native_maize"
    ]:

        if row[col]:
            found.append(col)

    return "; ".join(found)


df["signals"] = df.apply(
    reasons,
    axis=1
)


# ==========================================================
# GUARDAR
# ==========================================================

df.to_csv(
    OUTPUT_ALL,
    index=False,
    encoding="utf-8"
)

df[df["priority"] == "HIGH"].to_csv(
    OUTPUT_HIGH,
    index=False,
    encoding="utf-8"
)

df[df["priority"] == "MEDIUM"].to_csv(
    OUTPUT_MEDIUM,
    index=False,
    encoding="utf-8"
)

df[df["priority"] == "NO_ABSTRACT"].to_csv(
    OUTPUT_NOABS,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("SCREENING AUTOMÁTICO")
print("==========================================\n")

print(f"Registros evaluados: {len(df)}")

print("\nPrioridad:")

counts = df["priority"].value_counts()

for category in [
    "HIGH",
    "MEDIUM",
    "LOW",
    "NO_ABSTRACT"
]:
    print(
        f"{category:15s} "
        f"{counts.get(category, 0)}"
    )


print("\nSeñales encontradas:")

for variable in [
    "species",
    "maize",
    "botanical",
    "natural_material",
    "physical",
    "storage",
    "outcome",
    "experimental",
    "native_maize"
]:

    print(
        f"{variable:20s} "
        f"{df[variable].sum()}"
    )


print("\nIntersecciones importantes:")

print(
    "Botánico + outcome:       ",
    (df["botanical"] & df["outcome"]).sum()
)

print(
    "Material natural + outcome:",
    (df["natural_material"] & df["outcome"]).sum()
)

print(
    "Físico + outcome:         ",
    (df["physical"] & df["outcome"]).sum()
)

print(
    "Maíz nativo + outcome:    ",
    (df["native_maize"] & df["outcome"]).sum()
)

print("\nArchivos:")
print(OUTPUT_ALL)
print(OUTPUT_HIGH)
print(OUTPUT_MEDIUM)
print(OUTPUT_NOABS)
