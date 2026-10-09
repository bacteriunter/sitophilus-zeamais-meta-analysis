#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

PROJECT = Path.home() / "sitophilus_meta"

ELIGIBILITY = (
    PROJECT /
    "05_extraction" /
    "scope_eligibility" /
    "scope_eligibility_all.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "mortality"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

WINDOW_OUTPUT = (
    OUTDIR /
    "mortality_evidence_windows.csv"
)

STUDY_OUTPUT = (
    OUTDIR /
    "mortality_study_map.csv"
)


# ==========================================================
# PATRONES
# ==========================================================

mortality_pattern = (
    r"\b("
    r"mortality|"
    r"adult mortality|"
    r"percentage mortality|"
    r"percent mortality|"
    r"corrected mortality|"
    r"mortality rate"
    r")\b"
)

abbott_pattern = (
    r"\b("
    r"abbott|"
    r"corrected mortality|"
    r"mortality correction"
    r")\b"
)

percent_pattern = (
    r"\b\d+(?:\.\d+)?\s*%"
)

plusminus_pattern = (
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:±|\+/-|\+-)\s*"
    r"\d+(?:\.\d+)?"
)

replicate_pattern = (
    r"\b\d+\s+"
    r"(?:replicates|replications)\b"
)

insect_pattern = (
    r"\b\d+\s+"
    r"(?:adults?|insects?|weevils?)\b"
)

time_pattern = (
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:"
    r"h|hr|hrs|hour|hours|"
    r"d|day|days|"
    r"week|weeks"
    r")\b"
)

dose_pattern = (
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:mg|g|kg|ml|µl|ul)"
    r"\s*(?:/|per\s+)"
    r"(?:g|kg|ml|l)\b"
)

lc_pattern = (
    r"\b("
    r"LC50|LC90|LD50|LD90|"
    r"lethal concentration|"
    r"lethal dose"
    r")\b"
)

table_pattern = (
    r"\btable\s+\d+\b"
)


# ==========================================================
# FUNCIONES
# ==========================================================

def clean(text):

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def count_matches(
    text,
    pattern
):

    return len(
        re.findall(
            pattern,
            text,
            flags=re.I
        )
    )


def get_windows(
    text,
    radius=1200,
    max_windows=12
):

    matches = list(
        re.finditer(
            mortality_pattern,
            text,
            flags=re.I
        )
    )

    windows = []
    used = []

    for match in matches:

        start = max(
            0,
            match.start() - radius
        )

        end = min(
            len(text),
            match.end() + radius
        )

        # Evitar fragmentos prácticamente iguales
        duplicate = False

        for old_start, old_end in used:

            intersection = max(
                0,
                min(end, old_end)
                - max(start, old_start)
            )

            smaller = min(
                end - start,
                old_end - old_start
            )

            if (
                smaller > 0
                and intersection / smaller
                > 0.70
            ):

                duplicate = True
                break

        if duplicate:
            continue

        fragment = clean(
            text[start:end]
        )

        windows.append(
            fragment
        )

        used.append(
            (start, end)
        )

        if (
            len(windows)
            >= max_windows
        ):
            break

    return windows


# ==========================================================
# LEER ELEGIBILIDAD
# ==========================================================

df = pd.read_csv(
    ELIGIBILITY
)

# Principal:
# INCLUDE + evidencia numérica de mortalidad

target = df[
    (
        df["scope_status"]
        == "INCLUDE"
    )
    &
    (
        df[
            "mortality_numeric_windows"
        ] > 0
    )
].copy()


print("\n==========================================")
print("EXTRACCIÓN DE EVIDENCIA DE MORTALIDAD")
print("==========================================\n")

print(
    f"Estudios objetivo: {len(target)}"
)


# ==========================================================
# PROCESAR
# ==========================================================

window_records = []
study_records = []


for n, (_, row) in enumerate(
    target.iterrows(),
    start=1
):

    study_id = str(
        row["study_record_id"]
    )

    path = Path(
        str(row["text_file"])
    )

    if not path.exists():
        continue

    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    windows = get_windows(
        text
    )


    # ------------------------------------------------------
    # MAPA DEL ESTUDIO
    # ------------------------------------------------------

    n_mortality = count_matches(
        text,
        mortality_pattern
    )

    n_percent = count_matches(
        text,
        percent_pattern
    )

    n_plusminus = count_matches(
        text,
        plusminus_pattern
    )

    n_replicates = count_matches(
        text,
        replicate_pattern
    )

    n_insects = count_matches(
        text,
        insect_pattern
    )

    n_times = count_matches(
        text,
        time_pattern
    )

    n_doses = count_matches(
        text,
        dose_pattern
    )

    has_abbott = bool(
        re.search(
            abbott_pattern,
            text,
            flags=re.I
        )
    )

    has_lc = bool(
        re.search(
            lc_pattern,
            text,
            flags=re.I
        )
    )

    n_tables = count_matches(
        text,
        table_pattern
    )


    # ------------------------------------------------------
    # CLASIFICAR ESTRUCTURA
    # ------------------------------------------------------

    if (
        n_plusminus > 0
        and n_percent > 0
    ):

        mortality_structure = (
            "PERCENT_AND_PLUSMINUS"
        )

    elif n_percent > 0:

        mortality_structure = (
            "PERCENT_ONLY"
        )

    elif n_plusminus > 0:

        mortality_structure = (
            "PLUSMINUS_ONLY"
        )

    else:

        mortality_structure = (
            "OTHER_NUMERIC"
        )


    study_records.append({

        "study_record_id":
            study_id,

        "title":
            row["title"],

        "doi":
            row.get("doi"),

        "mortality_structure":
            mortality_structure,

        "mortality_mentions":
            n_mortality,

        "percent_values":
            n_percent,

        "plusminus_values":
            n_plusminus,

        "replicate_mentions":
            n_replicates,

        "insect_number_mentions":
            n_insects,

        "time_mentions":
            n_times,

        "dose_mentions":
            n_doses,

        "abbott_correction":
            has_abbott,

        "lc_ld_present":
            has_lc,

        "table_mentions":
            n_tables,

        "n_evidence_windows":
            len(windows),

        "synthetic_present":
            row["synthetic_present"],

        "text_file":
            str(path)
    })


    # ------------------------------------------------------
    # VENTANAS
    # ------------------------------------------------------

    for i, fragment in enumerate(
        windows,
        start=1
    ):

        window_records.append({

            "study_record_id":
                study_id,

            "title":
                row["title"],

            "window_number":
                i,

            "has_percentage":
                bool(
                    re.search(
                        percent_pattern,
                        fragment,
                        flags=re.I
                    )
                ),

            "has_plusminus":
                bool(
                    re.search(
                        plusminus_pattern,
                        fragment,
                        flags=re.I
                    )
                ),

            "has_dose":
                bool(
                    re.search(
                        dose_pattern,
                        fragment,
                        flags=re.I
                    )
                ),

            "has_time":
                bool(
                    re.search(
                        time_pattern,
                        fragment,
                        flags=re.I
                    )
                ),

            "has_insect_n":
                bool(
                    re.search(
                        insect_pattern,
                        fragment,
                        flags=re.I
                    )
                ),

            "has_abbott":
                bool(
                    re.search(
                        abbott_pattern,
                        fragment,
                        flags=re.I
                    )
                ),

            "evidence_text":
                fragment
        })


    if (
        n % 10 == 0
        or n == len(target)
    ):

        print(
            f"Procesados: "
            f"{n}/{len(target)}"
        )


# ==========================================================
# GUARDAR
# ==========================================================

study_df = pd.DataFrame(
    study_records
)

window_df = pd.DataFrame(
    window_records
)

study_df.to_csv(
    STUDY_OUTPUT,
    index=False,
    encoding="utf-8"
)

window_df.to_csv(
    WINDOW_OUTPUT,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("MAPA DE MORTALIDAD")
print("==========================================\n")

print(
    f"Estudios procesados: "
    f"{len(study_df)}"
)

print(
    f"Ventanas generadas: "
    f"{len(window_df)}"
)


print("\nEstructura detectada:")

print(
    study_df[
        "mortality_structure"
    ]
    .value_counts()
    .to_string()
)


print("\nInformación adicional:")

print(
    "Con ±:                 ",
    (
        study_df[
            "plusminus_values"
        ] > 0
    ).sum()
)

print(
    "Con porcentajes:       ",
    (
        study_df[
            "percent_values"
        ] > 0
    ).sum()
)

print(
    "Con número insectos:   ",
    (
        study_df[
            "insect_number_mentions"
        ] > 0
    ).sum()
)

print(
    "Con réplicas:          ",
    (
        study_df[
            "replicate_mentions"
        ] > 0
    ).sum()
)

print(
    "Con dosis:             ",
    (
        study_df[
            "dose_mentions"
        ] > 0
    ).sum()
)

print(
    "Corrección Abbott:     ",
    study_df[
        "abbott_correction"
    ].sum()
)

print(
    "LC/LD presente:        ",
    study_df[
        "lc_ld_present"
    ].sum()
)


print("\nVentanas útiles:")

print(
    "Mortalidad + porcentaje:",
    window_df[
        "has_percentage"
    ].sum()
)

print(
    "Mortalidad + ±:         ",
    window_df[
        "has_plusminus"
    ].sum()
)

print(
    "Mortalidad + dosis:     ",
    window_df[
        "has_dose"
    ].sum()
)

print(
    "Mortalidad + tiempo:    ",
    window_df[
        "has_time"
    ].sum()
)

print(
    "Mortalidad + insectos:  ",
    window_df[
        "has_insect_n"
    ].sum()
)


print("\n==========================================")
print("ESTUDIOS CON MEJOR ESTRUCTURA")
print("==========================================\n")

best = study_df.sort_values(
    [
        "plusminus_values",
        "percent_values",
        "insect_number_mentions"
    ],
    ascending=False
).head(15)


for _, row in best.iterrows():

    print(
        row["study_record_id"],
        "|",
        row["mortality_structure"],
        "| ±",
        row["plusminus_values"],
        "| %",
        row["percent_values"],
        "| insects",
        row["insect_number_mentions"],
        "|",
        row["title"]
    )


print(
    f"\nMapa:\n{STUDY_OUTPUT}"
)

print(
    f"\nEvidencia:\n{WINDOW_OUTPUT}"
)
