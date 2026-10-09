#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
from rapidfuzz.fuzz import ratio
import re
import unicodedata

PROJECT = Path.home() / "sitophilus_meta"

PUBMED = PROJECT / "02_deduplication" / "pubmed_unique.csv"
OPENALEX = PROJECT / "03_screening" / "openalex_relevant.csv"

OUTDIR = PROJECT / "02_deduplication"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "master_unique.csv"


def normalize_doi(x):

    if pd.isna(x):
        return ""

    x = str(x).lower().strip()

    x = x.replace("https://doi.org/", "")
    x = x.replace("http://doi.org/", "")
    x = x.replace("doi:", "")

    return x.strip()


def normalize_title(x):

    if pd.isna(x):
        return ""

    x = str(x).lower()

    x = unicodedata.normalize("NFKD", x)
    x = "".join(
        c for c in x
        if not unicodedata.combining(c)
    )

    x = re.sub(r"[^a-z0-9\s]", " ", x)
    x = re.sub(r"\s+", " ", x)

    return x.strip()


print("\n==========================================")
print("INTEGRACIÓN PUBMED + OPENALEX")
print("==========================================\n")


# =========================================================
# LEER
# =========================================================

pub = pd.read_csv(PUBMED)
oa = pd.read_csv(OPENALEX)

print(f"PubMed:   {len(pub)}")
print(f"OpenAlex: {len(oa)}")


# =========================================================
# ESTANDARIZAR
# =========================================================

pub["database"] = "PubMed"
oa["database"] = "OpenAlex"

pub["doi_norm"] = pub["doi"].apply(normalize_doi)
oa["doi_norm"] = oa["doi"].apply(normalize_doi)

pub["title_norm"] = pub["title"].apply(normalize_title)
oa["title_norm"] = oa["title"].apply(normalize_title)


# =========================================================
# DOI COMPARTIDOS
# =========================================================

pub_doi = set(
    pub.loc[
        pub["doi_norm"] != "",
        "doi_norm"
    ]
)

oa_doi = set(
    oa.loc[
        oa["doi_norm"] != "",
        "doi_norm"
    ]
)

shared_doi = pub_doi & oa_doi

print(f"\nDOI compartidos: {len(shared_doi)}")


# =========================================================
# UNIFICAR COLUMNAS
# =========================================================

base_columns = [
    "database",
    "doi",
    "doi_norm",
    "title",
    "title_norm",
    "abstract",
    "authors",
    "journal",
    "year"
]

for col in base_columns:

    if col not in pub.columns:
        pub[col] = ""

    if col not in oa.columns:
        oa[col] = ""


combined = pd.concat(
    [
        pub[base_columns],
        oa[base_columns]
    ],
    ignore_index=True
)

print(
    f"Registros antes de deduplicación: "
    f"{len(combined)}"
)


# =========================================================
# PRIMERA DEDUPLICACIÓN: DOI
# =========================================================

with_doi = combined[
    combined["doi_norm"] != ""
].copy()

without_doi = combined[
    combined["doi_norm"] == ""
].copy()


# Preferimos el registro con abstract más largo

with_doi["abstract_length"] = (
    with_doi["abstract"]
    .fillna("")
    .astype(str)
    .str.len()
)

with_doi = (
    with_doi
    .sort_values(
        "abstract_length",
        ascending=False
    )
    .drop_duplicates(
        subset=["doi_norm"],
        keep="first"
    )
)


# =========================================================
# SEGUNDA DEDUPLICACIÓN: TÍTULO EXACTO
# =========================================================

without_doi["abstract_length"] = (
    without_doi["abstract"]
    .fillna("")
    .astype(str)
    .str.len()
)

without_doi = (
    without_doi
    .sort_values(
        "abstract_length",
        ascending=False
    )
    .drop_duplicates(
        subset=["title_norm"],
        keep="first"
    )
)


merged = pd.concat(
    [
        with_doi,
        without_doi
    ],
    ignore_index=True
)


# =========================================================
# TÍTULOS SIN DOI QUE DUPLICAN ARTÍCULOS CON DOI
# =========================================================

doi_titles = set(
    merged.loc[
        merged["doi_norm"] != "",
        "title_norm"
    ]
)

mask_duplicate_title = (
    (merged["doi_norm"] == "") &
    (merged["title_norm"].isin(doi_titles))
)

n_title_duplicates = mask_duplicate_title.sum()

merged = merged[
    ~mask_duplicate_title
].copy()


# =========================================================
# IDENTIFICADOR
# =========================================================

merged = merged.reset_index(drop=True)

merged.insert(
    0,
    "study_record_id",
    [
        f"SZ_{i:05d}"
        for i in range(1, len(merged) + 1)
    ]
)


# =========================================================
# GUARDAR
# =========================================================

merged = merged.drop(
    columns=["abstract_length"],
    errors="ignore"
)

merged.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


print("\n==========================================")
print("RESULTADO")
print("==========================================")

print(
    f"Duplicados adicionales por título: "
    f"{n_title_duplicates}"
)

print(
    f"Registros únicos combinados: "
    f"{len(merged)}"
)

print(
    f"Con DOI: "
    f"{(merged['doi_norm'] != '').sum()}"
)

print(
    f"Con abstract: "
    f"{merged['abstract'].fillna('').ne('').sum()}"
)

print(f"\nArchivo maestro:\n{OUTPUT}")
