#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
import re

PROJECT = Path.home() / "sitophilus_meta"

INPUT = PROJECT / "01_search" / "openalex_raw.csv"
OUTDIR = PROJECT / "03_screening"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "openalex_relevant.csv"


# ==========================================================
# LEER
# ==========================================================

df = pd.read_csv(INPUT)

df["title"] = df["title"].fillna("").astype(str)
df["abstract"] = df["abstract"].fillna("").astype(str)

df["text"] = (
    df["title"] + " " + df["abstract"]
).str.lower()


print("\n==========================================")
print("FILTRO DE RELEVANCIA — OPENALEX")
print("==========================================\n")

print(f"Registros iniciales: {len(df)}")
print(f"OpenAlex ID únicos: {df['openalex_id'].nunique()}")


# ==========================================================
# 1. SITOPHILUS ZEAMAIS EXPLÍCITO
# ==========================================================

species_pattern = re.compile(
    r"\bsitophilus\s+zeamais\b",
    flags=re.IGNORECASE
)

df["has_zeamais"] = df["text"].apply(
    lambda x: bool(species_pattern.search(x))
)

species_df = df[df["has_zeamais"]].copy()

print(
    f"\nCon 'Sitophilus zeamais' explícito "
    f"en título/resumen: {len(species_df)}"
)


# ==========================================================
# 2. MAÍZ
# ==========================================================

maize_pattern = re.compile(
    r"\b(maize|corn|zea\s+mays|maíz|maiz)\b",
    flags=re.IGNORECASE
)

species_df["has_maize"] = species_df["text"].apply(
    lambda x: bool(maize_pattern.search(x))
)


# ==========================================================
# 3. BOTÁNICOS
# ==========================================================

botanical_pattern = re.compile(
    r"\b("
    r"botanical|botanicals|"
    r"plant extract|plant extracts|"
    r"plant powder|plant powders|"
    r"essential oil|essential oils|"
    r"leaf powder|seed powder|"
    r"medicinal plant|medicinal plants|"
    r"phytochemical|"
    r"extract|extracts"
    r")\b",
    flags=re.IGNORECASE
)

species_df["botanical"] = species_df["text"].apply(
    lambda x: bool(botanical_pattern.search(x))
)


# ==========================================================
# 4. MATERIALES NATURALES
# ==========================================================

natural_pattern = re.compile(
    r"\b("
    r"ash|ashes|wood ash|"
    r"diatomaceous earth|"
    r"clay|sand|"
    r"inert dust|inert dusts"
    r")\b",
    flags=re.IGNORECASE
)

species_df["natural_material"] = species_df["text"].apply(
    lambda x: bool(natural_pattern.search(x))
)


# ==========================================================
# 5. TEMPERATURA / MANEJO TÉRMICO
# ==========================================================

temperature_pattern = re.compile(
    r"\b("
    r"temperature|temperatures|"
    r"thermal|heat|heating|"
    r"cold|cooling"
    r")\b",
    flags=re.IGNORECASE
)

species_df["temperature"] = species_df["text"].apply(
    lambda x: bool(temperature_pattern.search(x))
)


# ==========================================================
# 6. ALMACENAMIENTO
# ==========================================================

storage_pattern = re.compile(
    r"\b("
    r"storage|stored|"
    r"grain storage|"
    r"hermetic|"
    r"silo|silos|"
    r"postharvest|post-harvest"
    r")\b",
    flags=re.IGNORECASE
)

species_df["storage"] = species_df["text"].apply(
    lambda x: bool(storage_pattern.search(x))
)


# ==========================================================
# 7. MAÍZ NATIVO / VARIEDADES
# ==========================================================

native_pattern = re.compile(
    r"\b("
    r"native maize|native corn|"
    r"local maize|local corn|"
    r"landrace|landraces|"
    r"maize variety|maize varieties|"
    r"corn variety|corn varieties|"
    r"cultivar|cultivars"
    r")\b",
    flags=re.IGNORECASE
)

species_df["maize_origin"] = species_df["text"].apply(
    lambda x: bool(native_pattern.search(x))
)


# ==========================================================
# DEDUPLICAR POR OPENALEX ID
# ==========================================================

unique = (
    species_df
    .sort_values("openalex_id")
    .drop_duplicates(
        subset=["openalex_id"],
        keep="first"
    )
    .copy()
)


# ==========================================================
# CANDIDATO PRINCIPAL
# ==========================================================

unique["candidate"] = (
    unique["has_maize"] &
    (
        unique["botanical"] |
        unique["natural_material"] |
        unique["temperature"] |
        unique["storage"] |
        unique["maize_origin"]
    )
)


# ==========================================================
# GUARDAR
# ==========================================================

columns = [
    "openalex_id",
    "doi",
    "title",
    "abstract",
    "authors",
    "journal",
    "year",
    "cited_by_count",
    "has_maize",
    "botanical",
    "natural_material",
    "temperature",
    "storage",
    "maize_origin",
    "candidate"
]

unique[columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("DESPUÉS DE DEDUPLICAR")
print("==========================================")

print(f"Registros únicos con S. zeamais: {len(unique)}")

print("\nClasificación temática:")

print(f"Con maíz:                 {unique['has_maize'].sum()}")
print(f"Botánicos:                {unique['botanical'].sum()}")
print(f"Materiales naturales:     {unique['natural_material'].sum()}")
print(f"Temperatura:              {unique['temperature'].sum()}")
print(f"Almacenamiento:           {unique['storage'].sum()}")
print(f"Maíz nativo/variedad:     {unique['maize_origin'].sum()}")

print(
    f"\nCandidatos principales:   "
    f"{unique['candidate'].sum()}"
)

print(f"\nArchivo generado:\n{OUTPUT}")
