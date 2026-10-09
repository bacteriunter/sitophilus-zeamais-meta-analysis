#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

INPUT = PROJECT / "03_screening" / "high_priority.csv"
OUTDIR = PROJECT / "03_screening" / "audit"

OUTDIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

# ==========================================================
# CLASIFICACIÓN PRINCIPAL
# ==========================================================

def category(row):

    cats = []

    if row.get("botanical", False):
        cats.append("BOTANICAL")

    if row.get("natural_material", False):
        cats.append("NATURAL_MATERIAL")

    if row.get("physical", False):
        cats.append("PHYSICAL")

    if row.get("native_maize", False):
        cats.append("NATIVE_MAIZE")

    return ";".join(cats)


df["categories"] = df.apply(category, axis=1)


# ==========================================================
# GUARDAR POR CATEGORÍA
# ==========================================================

groups = {
    "botanical": df[df["botanical"] == True],
    "natural_material": df[df["natural_material"] == True],
    "physical": df[df["physical"] == True],
    "native_maize": df[df["native_maize"] == True]
}

for name, subset in groups.items():

    subset.to_csv(
        OUTDIR / f"high_{name}.csv",
        index=False,
        encoding="utf-8"
    )


# ==========================================================
# TABLA RESUMIDA PARA INSPECCIÓN
# ==========================================================

audit_columns = [
    "study_record_id",
    "year",
    "title",
    "journal",
    "doi",
    "categories",
    "score"
]

audit = df[audit_columns].copy()

audit = audit.sort_values(
    ["categories", "year"],
    ascending=[True, False]
)

audit.to_csv(
    OUTDIR / "high_titles_audit.csv",
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("AUDITORÍA HIGH PRIORITY")
print("==========================================\n")

print(f"Total HIGH: {len(df)}")

print("\nCategorías (pueden solaparse):")

for name, subset in groups.items():
    print(f"{name:22s} {len(subset)}")


print("\nCombinaciones:")

print(
    df["categories"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("20 TÍTULOS DE EJEMPLO")
print("==========================================\n")

sample = (
    df.sort_values(
        "score",
        ascending=False
    )
    .head(20)
)

for _, row in sample.iterrows():

    print(
        f"[{row['score']}] "
        f"{row['title']}"
    )

    print(
        f"    {row['categories']}"
    )

    print()


print(
    "\nArchivo de auditoría:\n"
    f"{OUTDIR / 'high_titles_audit.csv'}"
)
