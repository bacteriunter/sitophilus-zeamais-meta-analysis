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
    "mortality_study_map.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "dispersion"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTDIR /
    "dispersion_classification.csv"
)

EVIDENCE_OUTPUT = (
    OUTDIR /
    "dispersion_evidence.csv"
)


# ==========================================================
# PATRONES
# ==========================================================

sd_patterns = [
    r"mean\s*[±+/-]+\s*standard deviation",
    r"means?\s+and\s+standard deviations?",
    r"mean\s*\(\s*sd\s*\)",
    r"mean\s*[±+/-]+\s*sd\b",
    r"\bmean\s*±\s*sd\b",
    r"\bmeans?\s*±\s*sd\b",
    r"\bstandard deviation\b",
]

se_patterns = [
    r"mean\s*[±+/-]+\s*standard error",
    r"means?\s+and\s+standard errors?",
    r"mean\s*\(\s*se\s*\)",
    r"mean\s*[±+/-]+\s*se\b",
    r"\bmean\s*±\s*se\b",
    r"\bmean\s*±\s*sem\b",
    r"\bmeans?\s*±\s*sem\b",
    r"\bstandard error of the mean\b",
    r"\bstandard error\b",
    r"\bSEM\b",
]

ci_patterns = [
    r"\bconfidence interval\b",
    r"\b95\s*%\s*CI\b",
    r"\b95%\s*confidence\b",
]

generic_mean_patterns = [
    r"mean\s*±",
    r"means?\s*±",
    r"mean\s*\+/-",
    r"means?\s*\+/-",
]

table_note_patterns = [
    r"values?\s+are\s+means?",
    r"values?\s+represent\s+means?",
    r"data\s+are\s+means?",
    r"results?\s+are\s+expressed\s+as",
    r"values?\s+are\s+expressed\s+as",
    r"mean\s+values?",
]


# ==========================================================
# FUNCIONES
# ==========================================================

def find_matches(
    text,
    patterns,
    radius=350
):

    evidence = []

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            text,
            flags=re.I
        ):

            start = max(
                0,
                match.start() - radius
            )

            end = min(
                len(text),
                match.end() + radius
            )

            fragment = text[
                start:end
            ]

            fragment = re.sub(
                r"\s+",
                " ",
                fragment
            ).strip()

            evidence.append(
                fragment
            )

    # eliminar duplicados
    unique = []

    for fragment in evidence:

        if fragment not in unique:
            unique.append(
                fragment
            )

    return unique


# ==========================================================
# LEER
# ==========================================================

df = pd.read_csv(
    INPUT
)

records = []
evidence_records = []


print("\n==========================================")
print("IDENTIFICACIÓN DE DISPERSIÓN")
print("==========================================\n")

print(
    f"Estudios: {len(df)}"
)


# ==========================================================
# PROCESAR
# ==========================================================

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


    sd_evidence = find_matches(
        text,
        sd_patterns
    )

    se_evidence = find_matches(
        text,
        se_patterns
    )

    ci_evidence = find_matches(
        text,
        ci_patterns
    )

    generic_evidence = find_matches(
        text,
        generic_mean_patterns
    )

    note_evidence = find_matches(
        text,
        table_note_patterns
    )


    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    if (
        len(sd_evidence) > 0
        and len(se_evidence) == 0
    ):

        dispersion_type = "SD"

    elif (
        len(se_evidence) > 0
        and len(sd_evidence) == 0
    ):

        dispersion_type = "SE"

    elif (
        len(sd_evidence) > 0
        and len(se_evidence) > 0
    ):

        dispersion_type = "MIXED_SD_SE"

    elif (
        len(ci_evidence) > 0
        and len(generic_evidence) == 0
    ):

        dispersion_type = "CI_ONLY"

    elif len(generic_evidence) > 0:

        dispersion_type = "PLUSMINUS_UNKNOWN"

    else:

        dispersion_type = "NO_DISPERSION_INFO"


    records.append({

        "study_record_id":
            row["study_record_id"],

        "title":
            row["title"],

        "dispersion_type":
            dispersion_type,

        "n_sd_evidence":
            len(sd_evidence),

        "n_se_evidence":
            len(se_evidence),

        "n_ci_evidence":
            len(ci_evidence),

        "n_generic_plusminus":
            len(generic_evidence),

        "n_table_notes":
            len(note_evidence),

        "mortality_structure":
            row["mortality_structure"],

        "text_file":
            str(path)
    })


    # ======================================================
    # EVIDENCIA
    # ======================================================

    categories = {

        "SD":
            sd_evidence,

        "SE":
            se_evidence,

        "CI":
            ci_evidence,

        "GENERIC_PLUSMINUS":
            generic_evidence,

        "TABLE_NOTE":
            note_evidence
    }


    for category, fragments in (
        categories.items()
    ):

        for number, fragment in enumerate(
            fragments[:10],
            start=1
        ):

            evidence_records.append({

                "study_record_id":
                    row["study_record_id"],

                "title":
                    row["title"],

                "evidence_type":
                    category,

                "evidence_number":
                    number,

                "evidence_text":
                    fragment
            })


    if (
        i % 10 == 0
        or i == len(df)
    ):

        print(
            f"Procesados: "
            f"{i}/{len(df)}"
        )


# ==========================================================
# GUARDAR
# ==========================================================

out = pd.DataFrame(
    records
)

evidence = pd.DataFrame(
    evidence_records
)


out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

evidence.to_csv(
    EVIDENCE_OUTPUT,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("RESULTADO DE DISPERSIÓN")
print("==========================================\n")

print(
    out[
        "dispersion_type"
    ]
    .value_counts()
    .to_string()
)


print("\nCon evidencia explícita:")

print(
    "SD:",
    (
        out["dispersion_type"]
        == "SD"
    ).sum()
)

print(
    "SE:",
    (
        out["dispersion_type"]
        == "SE"
    ).sum()
)

print(
    "Mixto SD/SE:",
    (
        out["dispersion_type"]
        == "MIXED_SD_SE"
    ).sum()
)

print(
    "± desconocido:",
    (
        out["dispersion_type"]
        == "PLUSMINUS_UNKNOWN"
    ).sum()
)


print("\n==========================================")
print("ESTUDIOS CON ± DESCONOCIDO")
print("==========================================\n")

unknown = out[
    out["dispersion_type"]
    == "PLUSMINUS_UNKNOWN"
]

print(
    f"Total: {len(unknown)}\n"
)

for _, row in unknown.iterrows():

    print(
        row["study_record_id"],
        "|",
        row["title"]
    )


print("\n==========================================")
print("ESTUDIOS MIXTOS SD/SE")
print("==========================================\n")

mixed = out[
    out["dispersion_type"]
    == "MIXED_SD_SE"
]

print(
    f"Total: {len(mixed)}\n"
)

for _, row in mixed.iterrows():

    print(
        row["study_record_id"],
        "|",
        row["title"]
    )


print(
    f"\nClasificación:\n{OUTPUT}"
)

print(
    f"\nEvidencia:\n{EVIDENCE_OUTPUT}"
)
