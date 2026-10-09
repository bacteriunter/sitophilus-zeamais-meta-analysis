#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path


PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "05_extraction" /
    "experimental_audit" /
    "EXTRACT_HIGH.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "numeric_audit"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = OUTDIR / "numeric_audit.csv"


# ==========================================================
# PATRONES
# ==========================================================

patterns = {

    "mean_plusminus": (
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:±|\+/-|\+-)\s*"
        r"\d+(?:\.\d+)?"
    ),

    "percentage": (
        r"\b\d+(?:\.\d+)?\s*%"
    ),

    "sd_se": (
        r"\b(?:SD|SE|SEM)\s*"
        r"(?:=|:)?\s*"
        r"\d+(?:\.\d+)?"
    ),

    "mean_sd_text": (
        r"\bmean\s*(?:±|\+/-|\+-)\s*"
        r"(?:SD|SE|SEM)"
    ),

    "sample_n": (
        r"\bn\s*=\s*\d+"
    ),

    "table": (
        r"\btable\s+\d+"
    )
}


outcome_patterns = {

    "mortality": (
        r"\b(?:mortality|dead insects?|"
        r"adult mortality)\b"
    ),

    "progeny": (
        r"\b(?:progeny|offspring|"
        r"adult emergence|F1)\b"
    ),

    "weight_loss": (
        r"\b(?:weight loss|mass loss)\b"
    ),

    "damage": (
        r"\b(?:grain damage|kernel damage|"
        r"damaged grains?)\b"
    ),

    "germination": (
        r"\b(?:germination|seed viability)\b"
    )
}


# ==========================================================
# FUNCIÓN
# ==========================================================

def count_pattern(text, pattern):

    return len(
        re.findall(
            pattern,
            text,
            flags=re.I
        )
    )


def outcome_numeric_context(
    text,
    pattern,
    radius=350
):

    matches = list(
        re.finditer(
            pattern,
            text,
            flags=re.I
        )
    )

    numeric_windows = 0

    for m in matches:

        start = max(
            0,
            m.start() - radius
        )

        end = min(
            len(text),
            m.end() + radius
        )

        window = text[start:end]

        # número decimal/entero
        if re.search(
            r"\b\d+(?:\.\d+)?\b",
            window
        ):

            numeric_windows += 1

    return numeric_windows


# ==========================================================
# PROCESAR
# ==========================================================

df = pd.read_csv(INPUT)

records = []


print("\n==========================================")
print("AUDITORÍA DE RESULTADOS NUMÉRICOS")
print("==========================================\n")

print(
    f"Artículos: {len(df)}"
)


for i, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

    path = Path(
        str(row["text_file"])
    )

    if not path.exists():
        continue

    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


    record = {

        "study_record_id":
            row["study_record_id"],

        "title":
            row["title"],

        "doi":
            row.get("doi"),

        "source_format":
            row.get("source_format"),

        "text_file":
            str(path)
    }


    # ------------------------------------------------------
    # ESTRUCTURAS NUMÉRICAS
    # ------------------------------------------------------

    for name, pattern in patterns.items():

        record[
            f"n_{name}"
        ] = count_pattern(
            text,
            pattern
        )


    # ------------------------------------------------------
    # OUTCOMES + NÚMEROS CERCANOS
    # ------------------------------------------------------

    for name, pattern in (
        outcome_patterns.items()
    ):

        record[
            f"{name}_numeric_windows"
        ] = outcome_numeric_context(
            text,
            pattern
        )


    # ------------------------------------------------------
    # SCORE
    # ------------------------------------------------------

    score = 0

    if record["n_mean_plusminus"] > 0:
        score += 3

    if record["n_percentage"] > 0:
        score += 2

    if record["n_sd_se"] > 0:
        score += 2

    if record["n_sample_n"] > 0:
        score += 1

    if record["n_table"] > 0:
        score += 2

    numeric_outcomes = sum(
        record[f"{x}_numeric_windows"] > 0
        for x in outcome_patterns
    )

    score += numeric_outcomes * 2

    record[
        "numeric_outcomes"
    ] = numeric_outcomes

    record[
        "numeric_score"
    ] = score


    if (
        numeric_outcomes >= 1
        and (
            record["n_mean_plusminus"] > 0
            or record["n_percentage"] > 0
        )
    ):

        priority = "NUMERIC_HIGH"

    elif numeric_outcomes >= 1:

        priority = "NUMERIC_POSSIBLE"

    else:

        priority = "NUMERIC_LOW"


    record[
        "numeric_priority"
    ] = priority

    records.append(
        record
    )


    if (
        i % 10 == 0
        or i == len(df)
    ):

        print(
            f"Procesados: {i}/{len(df)}"
        )


# ==========================================================
# GUARDAR
# ==========================================================

out = pd.DataFrame(
    records
)

out = out.sort_values(
    "numeric_score",
    ascending=False
)

out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


for category in [
    "NUMERIC_HIGH",
    "NUMERIC_POSSIBLE",
    "NUMERIC_LOW"
]:

    out[
        out["numeric_priority"]
        == category
    ].to_csv(
        OUTDIR /
        f"{category}.csv",
        index=False,
        encoding="utf-8"
    )


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("RESULTADO DE AUDITORÍA NUMÉRICA")
print("==========================================\n")

print(
    f"Estudios evaluados: {len(out)}"
)


print("\nPrioridad:")

for category in [
    "NUMERIC_HIGH",
    "NUMERIC_POSSIBLE",
    "NUMERIC_LOW"
]:

    print(
        f"{category:20s}",
        (
            out["numeric_priority"]
            == category
        ).sum()
    )


print("\nEstructuras numéricas:")

for column in [
    "n_mean_plusminus",
    "n_percentage",
    "n_sd_se",
    "n_sample_n",
    "n_table"
]:

    print(
        f"{column:22s}",
        (out[column] > 0).sum()
    )


print("\nOutcomes con números cercanos:")

for outcome in outcome_patterns:

    column = (
        f"{outcome}_numeric_windows"
    )

    print(
        f"{outcome:18s}",
        (out[column] > 0).sum()
    )


print("\n==========================================")
print("TOP 15 POR INFORMACIÓN NUMÉRICA")
print("==========================================\n")

for _, row in out.head(15).iterrows():

    print(
        f"[{row['numeric_score']}] "
        f"{row['study_record_id']} | "
        f"{row['title']}"
    )

    print(
        "   ±:",
        row["n_mean_plusminus"],
        "| %:",
        row["n_percentage"],
        "| SD/SE:",
        row["n_sd_se"],
        "| n=:",
        row["n_sample_n"],
        "| tablas:",
        row["n_table"]
    )

    available = []

    for outcome in outcome_patterns:

        if (
            row[
                f"{outcome}_numeric_windows"
            ] > 0
        ):

            available.append(
                outcome
            )

    print(
        "   Outcomes:",
        ", ".join(available)
    )

    print()


print(
    f"Archivo:\n{OUTPUT}"
)
