#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path


PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "selected_tables" /
    "selected_mortality_tables.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "structured"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = OUTDIR / "mortality_table_structure.csv"


# ==========================================================
# PATRONES
# ==========================================================

time_pattern = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*"
    r"(hours?|hrs?|hr|h|days?|weeks?)\b",
    re.I
)

mean_dispersion = re.compile(
    r"\d+(?:\.\d+)?\s*"
    r"(?:±|\+/-|\+-)\s*"
    r"\d+(?:\.\d+)?",
    re.I
)

count_terms = re.compile(
    r"\b("
    r"number of deaths|"
    r"number dead|"
    r"total number|"
    r"initial number|"
    r"dead insects?"
    r")\b",
    re.I
)

anova_terms = re.compile(
    r"\b("
    r"analysis of variance|"
    r"anova|"
    r"between-subjects effects"
    r")\b",
    re.I
)

lc_terms = re.compile(
    r"\b("
    r"lc50|lc90|lt50|lt90|"
    r"lethal concentration|"
    r"lethal time"
    r")\b",
    re.I
)

other_species = re.compile(
    r"\b("
    r"callosobruchus maculatus|"
    r"sitophilus oryzae"
    r")\b",
    re.I
)

zeamais = re.compile(
    r"\bsitophilus\s+zeamais\b|"
    r"\bs\.\s*zeamais\b",
    re.I
)


# ==========================================================
# TIEMPOS
# ==========================================================

def normalize_time(value, unit):

    value = float(value)

    unit = unit.lower()

    if unit.startswith(
        ("h", "hr", "hour")
    ):
        return value, "h"

    if unit.startswith("day"):
        return value * 24, "h"

    if unit.startswith("week"):
        return value * 168, "h"

    return None, None


def extract_times(text):

    results = []

    for value, unit in time_pattern.findall(
        text
    ):

        hours, normalized_unit = (
            normalize_time(
                value,
                unit
            )
        )

        if hours is not None:

            results.append(
                {
                    "original":
                        f"{value} {unit}",
                    "hours":
                        hours
                }
            )

    return results


# ==========================================================
# PROCESAR
# ==========================================================

df = pd.read_csv(INPUT)

records = []


print("\n==========================================")
print("CLASIFICACIÓN DE ESTRUCTURA")
print("==========================================\n")

print(
    f"Tablas iniciales: {len(df)}"
)


for _, row in df.iterrows():

    heading = str(
        row["table_heading"]
    )

    text = str(
        row["table_text"]
    )

    combined = (
        heading + "\n" + text
    )


    # ------------------------------------------------------
    # TIEMPOS
    # ------------------------------------------------------

    times = extract_times(
        combined
    )

    unique_times = sorted(
        set(
            x["hours"]
            for x in times
        )
    )

    max_time_h = (
        max(unique_times)
        if unique_times
        else None
    )


    # ------------------------------------------------------
    # ESTRUCTURA
    # ------------------------------------------------------

    n_pm = len(
        mean_dispersion.findall(
            text
        )
    )

    has_counts = bool(
        count_terms.search(
            combined
        )
    )

    has_anova = bool(
        anova_terms.search(
            combined
        )
    )

    has_lc = bool(
        lc_terms.search(
            heading
        )
    )

    has_other_species = bool(
        other_species.search(
            heading
        )
    )

    has_zeamais = bool(
        zeamais.search(
            heading
        )
    )


    # ------------------------------------------------------
    # CLASIFICACIÓN
    # ------------------------------------------------------

    if has_anova:

        structure = "EXCLUDE_ANOVA"

    elif has_lc:

        structure = "EXCLUDE_LC_LT"

    elif (
        has_other_species
        and not has_zeamais
    ):

        structure = "EXCLUDE_OTHER_SPECIES"

    elif has_counts:

        structure = "EVENT_COUNTS"

    elif (
        n_pm >= 3
        and len(unique_times) >= 1
    ):

        structure = "MEAN_DISPERSION_TIME"

    elif n_pm >= 3:

        structure = "MEAN_DISPERSION_NO_TIME"

    else:

        structure = "MANUAL_STRUCTURE"


    records.append({

        "study_record_id":
            row["study_record_id"],

        "title":
            row["title"],

        "table_number":
            row["table_number"],

        "table_heading":
            heading,

        "structure":
            structure,

        "n_mean_dispersion":
            n_pm,

        "n_times_detected":
            len(unique_times),

        "times_hours":
            ";".join(
                str(x)
                for x in unique_times
            ),

        "max_time_h":
            max_time_h,

        "has_event_counts":
            has_counts,

        "has_other_species":
            has_other_species,

        "table_text":
            text
    })


# ==========================================================
# GUARDAR
# ==========================================================

out = pd.DataFrame(
    records
)

out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("RESULTADO")
print("==========================================\n")

print(
    out[
        "structure"
    ]
    .value_counts()
    .to_string()
)


print("\nEstudios por estructura:")

for structure in (
    out["structure"]
    .unique()
):

    subset = out[
        out["structure"]
        == structure
    ]

    print(
        f"{structure:28s}",
        subset[
            "study_record_id"
        ].nunique()
    )


print("\n==========================================")
print("TABLAS POTENCIALMENTE EXTRAÍBLES")
print("==========================================\n")

usable = out[
    out["structure"].isin(
        [
            "EVENT_COUNTS",
            "MEAN_DISPERSION_TIME",
            "MEAN_DISPERSION_NO_TIME"
        ]
    )
]

for _, row in usable.iterrows():

    print(
        row["study_record_id"],
        "| T",
        row["table_number"],
        "|",
        row["structure"],
        "| tiempos:",
        row["times_hours"],
        "| max:",
        row["max_time_h"],
        "h"
    )


print("\n==========================================")
print("MANUAL / EXCLUSIONES")
print("==========================================\n")

manual = out[
    ~out["structure"].isin(
        [
            "EVENT_COUNTS",
            "MEAN_DISPERSION_TIME",
            "MEAN_DISPERSION_NO_TIME"
        ]
    )
]

for _, row in manual.iterrows():

    print(
        row["study_record_id"],
        "| T",
        row["table_number"],
        "|",
        row["structure"],
        "|",
        row["table_heading"][:140]
    )


print(
    f"\nArchivo:\n{OUTPUT}"
)
