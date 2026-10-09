#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
import re

PROJECT = Path.home() / "sitophilus_meta"

INPUT = PROJECT / "01_search" / "pubmed_raw.csv"
OUTDIR = PROJECT / "02_deduplication"

OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "pubmed_unique.csv"


def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)

    return text.strip()


# =========================
# LEER DATOS
# =========================

df = pd.read_csv(INPUT)

print("\n==========================================")
print("DEDUPLICACIÓN — PUBMED")
print("==========================================\n")

print(f"Registros iniciales: {len(df)}")


# =========================
# NORMALIZAR
# =========================

df["title_clean"] = df["title"].apply(clean_text)

df["doi_clean"] = (
    df["doi"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.strip()
)

df["pmid"] = (
    df["pmid"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# =========================
# CONSERVAR CATEGORÍAS
# =========================

categories = (
    df.groupby("pmid")["search_category"]
    .apply(
        lambda x: "; ".join(
            sorted(set(x.dropna()))
        )
    )
    .reset_index()
    .rename(
        columns={
            "search_category": "search_categories"
        }
    )
)


# =========================
# DEDUPLICAR POR PMID
# =========================

unique = (
    df.sort_values("pmid")
    .drop_duplicates(
        subset=["pmid"],
        keep="first"
    )
    .copy()
)

unique = unique.drop(
    columns=["search_category"],
    errors="ignore"
)

unique = unique.merge(
    categories,
    on="pmid",
    how="left"
)


# =========================
# GUARDAR
# =========================

unique.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


# =========================
# RESUMEN
# =========================

removed = len(df) - len(unique)

print(f"Duplicados eliminados: {removed}")
print(f"Artículos únicos: {len(unique)}")

print("\nDisponibilidad de información:")

print(
    f"Con DOI: "
    f"{(unique['doi_clean'] != '').sum()}"
)

print(
    f"Con resumen: "
    f"{unique['abstract'].notna().sum()}"
)

print(
    f"Con título: "
    f"{unique['title'].notna().sum()}"
)

print("\nCategorías después de deduplicar:")

for category in [
    "general",
    "botanicals",
    "natural_materials",
    "temperature",
    "storage",
    "maize_origin"
]:

    n = unique[
        unique["search_categories"]
        .fillna("")
        .str.contains(category)
    ].shape[0]

    print(f"{category:20s} {n}")

print(f"\nArchivo generado:\n{OUTPUT}")
