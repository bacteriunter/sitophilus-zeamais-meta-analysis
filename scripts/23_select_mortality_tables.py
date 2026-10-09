#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "tables" /
    "mortality_tables.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "selected_tables"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTDIR /
    "selected_mortality_tables.csv"
)

REVIEW_OUTPUT = (
    OUTDIR /
    "review_tables.csv"
)

REJECTED_OUTPUT = (
    OUTDIR /
    "rejected_tables.csv"
)


# ==========================================================
# PATRONES
# ==========================================================

strong_mortality = re.compile(
    r"\b("
    r"mortality|"
    r"percentage mortality|"
    r"percent mortality|"
    r"cumulative mortality|"
    r"corrected mortality|"
    r"adult mortality|"
    r"mortality rate|"
    r"mortality of"
    r")\b",
    flags=re.I
)

toxicity = re.compile(
    r"\b("
    r"toxicity|"
    r"toxic effect|"
    r"toxic effects|"
    r"insecticidal activity|"
    r"insecticidal effect|"
    r"insecticidal efficacy|"
    r"adulticidal"
    r")\b",
    flags=re.I
)

lc_ld_only = re.compile(
    r"\b("
    r"LC50|LC90|"
    r"LD50|LD90|"
    r"lethal concentration|"
    r"lethal dose|"
    r"probit"
    r")\b",
    flags=re.I
)

other_outcome = re.compile(
    r"\b("
    r"germination|"
    r"weight loss|"
    r"grain damage|"
    r"seed damage|"
    r"population increase|"
    r"progeny|"
    r"adult emergence|"
    r"repellency|"
    r"repellent|"
    r"oviposition|"
    r"chemical composition|"
    r"phytochemical|"
    r"proximate composition"
    r")\b",
    flags=re.I
)


# ==========================================================
# CLASIFICACIÓN
# ==========================================================

def classify_heading(heading):

    heading = str(
        heading
    )

    has_mortality = bool(
        strong_mortality.search(
            heading
        )
    )

    has_toxicity = bool(
        toxicity.search(
            heading
        )
    )

    has_lc = bool(
        lc_ld_only.search(
            heading
        )
    )

    has_other = bool(
        other_outcome.search(
            heading
        )
    )


    # ------------------------------------------------------
    # Mortalidad explícita
    # ------------------------------------------------------

    if has_mortality:

        return (
            "SELECT",
            "MORTALITY_IN_HEADING"
        )


    # ------------------------------------------------------
    # Toxicidad, pero no LC/LD exclusivamente
    # ------------------------------------------------------

    if (
        has_toxicity
        and not has_lc
        and not has_other
    ):

        return (
            "REVIEW",
            "TOXICITY_HEADING"
        )


    # ------------------------------------------------------
    # LC/LD
    # ------------------------------------------------------

    if has_lc:

        return (
            "REJECT",
            "LC_LD_TABLE"
        )


    # ------------------------------------------------------
    # Otro outcome explícito
    # ------------------------------------------------------

    if has_other:

        return (
            "REJECT",
            "OTHER_OUTCOME"
        )


    # ------------------------------------------------------
    # Encabezado ambiguo
    # ------------------------------------------------------

    return (
        "REVIEW",
        "AMBIGUOUS_HEADING"
    )


# ==========================================================
# LEER
# ==========================================================

df = pd.read_csv(
    INPUT
)


status = []
reason = []


for _, row in df.iterrows():

    result = classify_heading(
        row["table_heading"]
    )

    status.append(
        result[0]
    )

    reason.append(
        result[1]
    )


df["selection_status"] = status
df["selection_reason"] = reason


# ==========================================================
# GUARDAR
# ==========================================================

selected = df[
    df["selection_status"]
    == "SELECT"
].copy()

review = df[
    df["selection_status"]
    == "REVIEW"
].copy()

rejected = df[
    df["selection_status"]
    == "REJECT"
].copy()


selected.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

review.to_csv(
    REVIEW_OUTPUT,
    index=False,
    encoding="utf-8"
)

rejected.to_csv(
    REJECTED_OUTPUT,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("SELECCIÓN DE TABLAS DE MORTALIDAD")
print("==========================================\n")

print(
    f"Tablas iniciales: {len(df)}"
)

print(
    f"SELECT:           {len(selected)}"
)

print(
    f"REVIEW:           {len(review)}"
)

print(
    f"REJECT:           {len(rejected)}"
)


print("\nEstudios representados:")

print(
    "SELECT:",
    selected[
        "study_record_id"
    ].nunique()
)

print(
    "REVIEW:",
    review[
        "study_record_id"
    ].nunique()
)


print("\nRazones:")

print(
    df[
        "selection_reason"
    ]
    .value_counts()
    .to_string()
)


# ==========================================================
# SELECT
# ==========================================================

print("\n==========================================")
print("TABLAS SELECCIONADAS")
print("==========================================\n")

for _, row in selected.iterrows():

    print(
        row["study_record_id"],
        "| Table",
        row["table_number"],
        "|",
        str(
            row["table_heading"]
        )[:180]
    )


# ==========================================================
# REVIEW
# ==========================================================

print("\n==========================================")
print("TABLAS PARA REVISAR")
print("==========================================\n")

print(
    f"Total: {len(review)}\n"
)

for _, row in review.iterrows():

    print(
        row["study_record_id"],
        "| Table",
        row["table_number"],
        "|",
        row["selection_reason"],
        "|",
        str(
            row["table_heading"]
        )[:180]
    )


print(
    f"\nSeleccionadas:\n{OUTPUT}"
)

print(
    f"\nRevisión:\n{REVIEW_OUTPUT}"
)
