#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

TABLES = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/tables/"
    "progeny_tables_identified.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/final"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUT_CSV = OUTDIR / "progeny_tables_validated.csv"
OUT_TXT = OUTDIR / "progeny_tables_validated_evidence.txt"


# ==========================================================
# TABLAS CANDIDATAS
# ==========================================================

df = pd.read_csv(TABLES)

# SELECT + REVIEW.
# No queremos depender de la selección previa de una sola tabla.
df = df[
    df["status"].isin(["SELECT", "REVIEW"])
].copy()

df = df.drop_duplicates(
    subset=[
        "study_record_id",
        "table_number"
    ]
)


# ==========================================================
# TEXTOS
# ==========================================================

text_files = []

for root in [
    PROJECT / "05_extraction",
    PROJECT / "04_pdfs"
]:
    if root.exists():
        text_files.extend(
            root.rglob("*.txt")
        )


def get_text(study):

    files = [
        f for f in text_files
        if study.lower() in str(f).lower()
    ]

    combined = ""

    for f in files:

        try:
            combined += "\n" + f.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            pass

    return combined


def clean(x):

    return re.sub(
        r"\s+",
        " ",
        x
    ).strip()


# ==========================================================
# PATRONES
# ==========================================================

F1_STRONG = re.compile(
    r"(?:"
    r"\bF\s*1\s+(?:adult\s+)?(?:progeny|emergence)"
    r"|"
    r"\bmean\s+(?:number\s+of\s+)?F\s*1"
    r"|"
    r"\bnumber\s+of\s+F\s*1"
    r"|"
    r"\bF\s*1\s+adults?\s+emerged"
    r"|"
    r"\bprogeny\s+(?:production|emergence|number)"
    r"|"
    r"\bnumber\s+of\s+(?:adult\s+)?(?:progeny|emerged\s+adults)"
    r"|"
    r"\badult\s+emergence"
    r")",
    re.I
)

F1_SUPPORT = re.compile(
    r"\b(?:progeny|offspring|emerged adults?|"
    r"adult emergence|reproduction inhibition)\b",
    re.I
)

SZ = re.compile(
    r"\b(?:Sitophilus\s+zeamais|S\.\s*zeamais)\b",
    re.I
)

MAIZE = re.compile(
    r"\b(?:maize|Zea\s+mays|corn)\b",
    re.I
)

CONTROL = re.compile(
    r"\b(?:untreated|control|negative control|check)\b",
    re.I
)

PLUSMINUS = re.compile(
    r"\d+(?:\.\d+)?\s*±\s*\d+(?:\.\d+)?"
)

SE = re.compile(
    r"(?:"
    r"\bmean(?:s)?\s*±\s*(?:SE|S\.E\.|SEM)\b"
    r"|"
    r"\bmean(?:s)?.{0,80}\bstandard error\b"
    r"|"
    r"\b±\s*SE\b"
    r")",
    re.I | re.S
)

SD = re.compile(
    r"(?:"
    r"\bmean(?:s)?\s*±\s*(?:SD|S\.D\.)\b"
    r"|"
    r"\bmean(?:s)?.{0,80}\bstandard deviation\b"
    r"|"
    r"\b±\s*SD\b"
    r")",
    re.I | re.S
)


# Outcomes que pueden producir falsos positivos.
WRONG_OUTCOME = re.compile(
    r"(?:"
    r"\bpercentage\s+mortality\b"
    r"|"
    r"\bmean\s+percentage\s+mortality\b"
    r"|"
    r"\bmortality\s*\(%\)"
    r"|"
    r"\brepellency\s+rate\b"
    r"|"
    r"\bpercentage\s+repellency\b"
    r"|"
    r"\bseed\s+germination\b"
    r"|"
    r"\bpercentage\s+germination\b"
    r"|"
    r"\bgrain\s+weight\s+loss\b"
    r"|"
    r"\bpercentage\s+weight\s+loss\b"
    r"|"
    r"\bphytochemical\b"
    r"|"
    r"\bLC\s*50\b"
    r"|"
    r"\bLD\s*50\b"
    r"|"
    r"\bANOVA\b"
    r")",
    re.I
)

OTHER_SPECIES = re.compile(
    r"\b(?:"
    r"Callosobruchus\s+maculatus|"
    r"C\.\s*maculatus|"
    r"Acanthoscelides\s+obtectus|"
    r"A\.\s*obtectus"
    r")\b",
    re.I
)


# ==========================================================
# OBTENER BLOQUE REAL DE CADA TABLA
# ==========================================================

def table_blocks(text):

    hits = list(
        re.finditer(
            r"\bTable\s+(\d+)\s*[:.]?",
            text,
            re.I
        )
    )

    blocks = []

    for i, hit in enumerate(hits):

        number = hit.group(1)

        # No utilizar un bloque enorme.
        # La siguiente tabla marca el final natural.
        if i + 1 < len(hits):
            end = hits[i + 1].start()
        else:
            end = len(text)

        end = min(
            end,
            hit.start() + 6500
        )

        block = clean(
            text[hit.start():end]
        )

        blocks.append(
            (
                number,
                block
            )
        )

    return blocks


# ==========================================================
# VALIDACIÓN
# ==========================================================

records = []
evidence = []

for _, candidate in df.iterrows():

    study = candidate["study_record_id"]
    table_num = str(candidate["table_number"])

    text = get_text(study)

    if not text:
        continue

    candidates = [
        block
        for number, block in table_blocks(text)
        if str(number) == table_num
    ]

    if not candidates:
        continue


    # ------------------------------------------------------
    # Elegir la aparición de Table X más compatible con F1
    # ------------------------------------------------------

    ranked = []

    for block in candidates:

        header = block[:1200]

        score = 0

        if F1_STRONG.search(header):
            score += 10

        if F1_SUPPORT.search(header):
            score += 4

        if SZ.search(header):
            score += 3

        if MAIZE.search(header):
            score += 2

        if CONTROL.search(block):
            score += 2

        if PLUSMINUS.search(block):
            score += 1

        ranked.append(
            (
                score,
                block
            )
        )

    ranked.sort(
        key=lambda x: (
            x[0],
            len(x[1])
        ),
        reverse=True
    )

    block = ranked[0][1]
    header = block[:1200]


    # ------------------------------------------------------
    # SEÑALES
    # ------------------------------------------------------

    f1_header = bool(
        F1_STRONG.search(header)
    )

    f1_anywhere = bool(
        F1_SUPPORT.search(block)
    )

    sz_header = bool(
        SZ.search(header)
    )

    sz_anywhere = bool(
        SZ.search(block)
    )

    maize_header = bool(
        MAIZE.search(header)
    )

    maize_anywhere = bool(
        MAIZE.search(block)
    )

    control = bool(
        CONTROL.search(block)
    )

    plusminus = bool(
        PLUSMINUS.search(block)
    )


    # ------------------------------------------------------
    # DISPERSIÓN
    # ------------------------------------------------------

    if SE.search(block) and not SD.search(block):
        dispersion = "SE"

    elif SD.search(block) and not SE.search(block):
        dispersion = "SD"

    elif SE.search(block) and SD.search(block):
        dispersion = "MIXED"

    else:
        dispersion = "UNKNOWN"


    # ------------------------------------------------------
    # POSIBLES OUTCOMES INCORRECTOS
    # ------------------------------------------------------

    wrong_header = bool(
        WRONG_OUTCOME.search(
            header[:700]
        )
    )

    other_species_header = bool(
        OTHER_SPECIES.search(
            header[:1200]
        )
    )


    # ------------------------------------------------------
    # CLASIFICACIÓN CONSERVADORA
    # ------------------------------------------------------

    #
    # VALID_STRONG:
    # La propia cabecera/primer bloque identifica F1,
    # S. zeamais y maíz.
    #
    # VALID:
    # F1 está en cabecera y especie/maíz aparecen
    # claramente dentro de la tabla.
    #
    # REVIEW:
    # Hay señal F1 pero no suficiente para aceptar.
    #
    # REJECT:
    # La tabla parece corresponder a otro outcome.
    #

    if (
        f1_header
        and sz_header
        and maize_header
        and not wrong_header
    ):
        final_status = "VALID_STRONG"

    elif (
        f1_header
        and sz_anywhere
        and maize_anywhere
        and not wrong_header
    ):
        final_status = "VALID"

    elif (
        f1_header
        and sz_anywhere
        and not wrong_header
        and not other_species_header
    ):
        final_status = "REVIEW"

    else:
        final_status = "REJECT"


    # ------------------------------------------------------
    # MÉTRICA
    # ------------------------------------------------------

    if re.search(
        r"\b(?:mean\s+)?number\s+of\s+F\s*1"
        r"|\bF\s*1\s+(?:adult\s+)?progeny"
        r"|\bprogeny\s+(?:number|production)\b",
        block,
        re.I
    ):
        metric = "F1_COUNT"

    elif re.search(
        r"\badult\s+emergence\s*\(%\)"
        r"|\bpercentage\s+(?:adult\s+)?emergence\b",
        block,
        re.I
    ):
        metric = "PERCENT_EMERGENCE"

    elif re.search(
        r"\breproduction\s+inhibition"
        r"|\binhibition.{0,30}%"
        r"|\breduction.{0,30}%",
        block,
        re.I
    ):
        metric = "PERCENT_REDUCTION"

    else:
        metric = "F1_UNCLEAR"


    records.append({

        "study_record_id":
            study,

        "table_number":
            table_num,

        "metric":
            metric,

        "dispersion":
            dispersion,

        "control":
            control,

        "plus_minus":
            plusminus,

        "f1_header":
            f1_header,

        "sitophilus_header":
            sz_header,

        "sitophilus_anywhere":
            sz_anywhere,

        "maize_header":
            maize_header,

        "maize_anywhere":
            maize_anywhere,

        "wrong_outcome_header":
            wrong_header,

        "other_species_header":
            other_species_header,

        "final_status":
            final_status
    })


    # Solo guardar evidencia de tablas válidas/review.
    if final_status != "REJECT":

        evidence.append("")
        evidence.append("=" * 100)

        evidence.append(
            f"{study} | TABLE {table_num} | "
            f"{final_status} | "
            f"{metric} | "
            f"{dispersion}"
        )

        evidence.append("=" * 100)

        evidence.append(
            block[:3000]
        )


# ==========================================================
# GUARDAR
# ==========================================================

out = pd.DataFrame(records)

out.to_csv(
    OUT_CSV,
    index=False,
    encoding="utf-8"
)

OUT_TXT.write_text(
    "\n".join(evidence),
    encoding="utf-8"
)


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("VALIDACIÓN DEFINITIVA DE TABLAS F1")
print("==========================================\n")

print(
    "Tablas candidatas evaluadas:",
    len(out)
)

print(
    "Estudios evaluados:",
    out["study_record_id"].nunique()
)


print("\n==========================================")
print("ESTADO")
print("==========================================\n")

print(
    out["final_status"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("MÉTRICA")
print("==========================================\n")

print(
    out["metric"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("DISPERSIÓN")
print("==========================================\n")

valid = out[
    out["final_status"].isin(
        ["VALID_STRONG", "VALID"]
    )
]

if not valid.empty:

    print(
        valid["dispersion"]
        .value_counts()
        .to_string()
    )


print("\n==========================================")
print("TABLAS F1 VÁLIDAS")
print("==========================================\n")

if valid.empty:

    print("Ninguna")

else:

    for study, g in valid.groupby(
        "study_record_id"
    ):

        pieces = []

        for _, r in g.iterrows():

            pieces.append(
                f"T{r['table_number']}"
                f"[{r['metric']};"
                f"{r['dispersion']};"
                f"{r['final_status']}]"
            )

        print(
            study,
            " -> ",
            ", ".join(pieces)
        )


print("\n==========================================")
print("TOTALES VÁLIDOS")
print("==========================================\n")

print(
    "Estudios:",
    valid["study_record_id"].nunique()
)

print(
    "Tablas:",
    len(valid)
)

print(
    "Con control:",
    int(valid["control"].sum())
)

print(
    "Con ±:",
    int(valid["plus_minus"].sum())
)


print("\n==========================================")
print("REVIEW")
print("==========================================\n")

review = out[
    out["final_status"] == "REVIEW"
]

if review.empty:

    print("Ninguna")

else:

    print(
        review[
            [
                "study_record_id",
                "table_number",
                "metric",
                "dispersion"
            ]
        ].to_string(
            index=False
        )
    )


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_CSV)
print(OUT_TXT)
