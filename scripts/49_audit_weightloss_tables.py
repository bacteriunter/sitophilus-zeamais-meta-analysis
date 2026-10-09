#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

AUDIT = (
    PROJECT /
    "05_extraction/secondary_outcomes/"
    "secondary_outcome_audit.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction/secondary_outcomes/weight_loss"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUT_CSV = OUTDIR / "weightloss_table_audit.csv"
OUT_TXT = OUTDIR / "weightloss_table_evidence.txt"


# ==========================================================
# CANDIDATOS
# ==========================================================

audit = pd.read_csv(AUDIT)

# Detectar nombres de columnas disponibles
print("\nColumnas del audit:")
print(", ".join(audit.columns))


# ----------------------------------------------------------
# Seleccionar estudios WEIGHT_LOSS HIGH/POSSIBLE
# ----------------------------------------------------------

required_columns = {
    "study_record_id",
    "outcome",
    "extractability"
}

missing = required_columns - set(audit.columns)

if missing:
    raise ValueError(
        f"Faltan columnas requeridas: {sorted(missing)}"
    )

targets = audit[
    (audit["outcome"] == "WEIGHT_LOSS")
    &
    (
        audit["extractability"]
        .isin(["HIGH", "POSSIBLE"])
    )
].copy()

print(
    "\nCandidatos WEIGHT_LOSS HIGH/POSSIBLE:",
    len(targets)
)

print(
    "HIGH:",
    (targets["extractability"] == "HIGH").sum()
)

print(
    "POSSIBLE:",
    (targets["extractability"] == "POSSIBLE").sum()
)

# ==========================================================
# IDENTIFICADOR DEL ESTUDIO
# ==========================================================

possible_ids = [
    "study_record_id",
    "study_id",
    "record_id"
]

id_col = None

for c in possible_ids:
    if c in targets.columns:
        id_col = c
        break

if id_col is None:
    raise ValueError(
        "No se encontró columna de identificador de estudio."
    )

study_ids = sorted(
    targets[id_col]
    .dropna()
    .astype(str)
    .unique()
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

WEIGHT_STRONG = re.compile(
    r"(?:"
    r"\bpercentage\s+(?:grain\s+)?weight\s+loss\b"
    r"|"
    r"\bpercent\s+(?:grain\s+)?weight\s+loss\b"
    r"|"
    r"\b%\s*(?:grain\s+)?weight\s+loss\b"
    r"|"
    r"\bmean\s+(?:percentage\s+)?weight\s+loss\b"
    r"|"
    r"\bgrain\s+weight\s+loss\b"
    r"|"
    r"\bweight\s+loss\s*\(%\)"
    r")",
    re.I
)

PERCENT = re.compile(
    r"(?:"
    r"\bpercentage\s+(?:grain\s+)?weight\s+loss\b"
    r"|"
    r"\bpercent\s+(?:grain\s+)?weight\s+loss\b"
    r"|"
    r"\bweight\s+loss\s*\(%\)"
    r"|"
    r"\b%\s*(?:grain\s+)?weight\s+loss\b"
    r")",
    re.I
)

GRAMS = re.compile(
    r"(?:"
    r"\bweight\s+loss\s*\(g\)"
    r"|"
    r"\bweight\s+loss\s+in\s+g\b"
    r"|"
    r"\bweight\s+loss\s+\(grams?\)"
    r")",
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
    r"\bmean(?:s)?\s*±\s*(?:SE|SEM|S\.E\.)\b"
    r"|"
    r"\bstandard error\b"
    r")",
    re.I
)

SD = re.compile(
    r"(?:"
    r"\bmean(?:s)?\s*±\s*(?:SD|S\.D\.)\b"
    r"|"
    r"\bstandard deviation\b"
    r")",
    re.I
)

REPLICATION = re.compile(
    r"(?:"
    r"\b(?:three|four|five|six|\d+)\s+"
    r"(?:replicates|replications)\b"
    r"|"
    r"\breplicated\s+"
    r"(?:three|four|five|six|\d+)\s+times\b"
    r")",
    re.I
)


# ==========================================================
# TABLAS
# ==========================================================

def get_tables(text):

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

        if i + 1 < len(hits):
            end = hits[i + 1].start()
        else:
            end = len(text)

        end = min(
            end,
            hit.start() + 6000
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
# AUDITAR
# ==========================================================

records = []
evidence = []

for study in study_ids:

    text = get_text(study)

    if not text:
        continue

    replication = bool(
        REPLICATION.search(text)
    )

    seen = set()

    for table_number, block in get_tables(text):

        # Evitar copias idénticas de la misma tabla
        key = (
            table_number,
            block[:500]
        )

        if key in seen:
            continue

        seen.add(key)

        header = block[:1400]

        if not WEIGHT_STRONG.search(header):
            continue

        weight_percent = bool(
            PERCENT.search(header)
        )

        weight_grams = bool(
            GRAMS.search(header)
        )

        sz = bool(
            SZ.search(block)
        )

        maize = bool(
            MAIZE.search(block)
        )

        control = bool(
            CONTROL.search(block)
        )

        plusminus = bool(
            PLUSMINUS.search(block)
        )


        # ----------------------------------------------
        # Tipo de métrica
        # ----------------------------------------------

        if weight_percent and not weight_grams:
            metric = "PERCENT_WEIGHT_LOSS"

        elif weight_grams and not weight_percent:
            metric = "ABSOLUTE_WEIGHT_LOSS_G"

        elif weight_percent and weight_grams:
            metric = "MIXED_WEIGHT_LOSS"

        else:
            metric = "WEIGHT_LOSS_UNCLEAR"


        # ----------------------------------------------
        # Dispersión
        # ----------------------------------------------

        if SE.search(block) and not SD.search(block):
            dispersion = "SE"

        elif SD.search(block) and not SE.search(block):
            dispersion = "SD"

        elif SE.search(block) and SD.search(block):
            dispersion = "MIXED"

        else:
            dispersion = "UNKNOWN"


        # ----------------------------------------------
        # Estado
        # ----------------------------------------------

        if (
            metric == "PERCENT_WEIGHT_LOSS"
            and sz
            and maize
            and control
            and plusminus
        ):
            status = "HIGH"

        elif (
            metric == "PERCENT_WEIGHT_LOSS"
            and sz
            and maize
            and control
        ):
            status = "POSSIBLE"

        elif (
            metric == "ABSOLUTE_WEIGHT_LOSS_G"
            and sz
            and maize
            and control
        ):
            status = "SEPARATE_SCALE"

        else:
            status = "REVIEW"


        records.append({

            "study_record_id":
                study,

            "table_number":
                table_number,

            "metric":
                metric,

            "dispersion":
                dispersion,

            "sitophilus_zeamais":
                sz,

            "maize":
                maize,

            "control":
                control,

            "plus_minus":
                plusminus,

            "replication_signal":
                replication,

            "status":
                status
        })


        evidence.append("")
        evidence.append("=" * 100)

        evidence.append(
            f"{study} | TABLE {table_number} | "
            f"{metric} | {dispersion} | {status}"
        )

        evidence.append("=" * 100)

        evidence.append(
            block[:3000]
        )


# ==========================================================
# RESULTADOS
# ==========================================================

out = pd.DataFrame(records)

if out.empty:

    print("\nNo se detectaron tablas de pérdida de peso.")
    raise SystemExit


# Eliminar duplicados estudio/tabla/métrica
out = out.drop_duplicates(
    subset=[
        "study_record_id",
        "table_number",
        "metric"
    ]
).copy()


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
# TERMINAL
# ==========================================================

print("\n==========================================")
print("AUDITORÍA DE PÉRDIDA DE PESO")
print("==========================================\n")

print(
    "Estudios candidatos iniciales:",
    len(study_ids)
)

print(
    "Estudios con tabla detectada:",
    out["study_record_id"].nunique()
)

print(
    "Tablas detectadas:",
    len(out)
)


print("\n==========================================")
print("ESTADO")
print("==========================================\n")

print(
    out["status"]
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

print(
    out["dispersion"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("HIGH POR ESTUDIO")
print("==========================================\n")

high = out[
    out["status"] == "HIGH"
]

if high.empty:

    print("Ninguno")

else:

    for study, g in high.groupby(
        "study_record_id"
    ):

        pieces = [
            f"T{r.table_number}"
            f"[{r.metric};{r.dispersion}]"
            for _, r in g.iterrows()
        ]

        print(
            study,
            " -> ",
            ", ".join(pieces)
        )


print("\n==========================================")
print("TOTALES HIGH")
print("==========================================\n")

print(
    "Estudios:",
    high["study_record_id"].nunique()
)

print(
    "Tablas:",
    len(high)
)

print(
    "Con dispersión conocida:",
    int(
        high["dispersion"]
        .isin(["SE", "SD"])
        .sum()
    )
)

print(
    "Con replicación detectada:",
    int(
        high["replication_signal"]
        .sum()
    )
)


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_CSV)
print(OUT_TXT)
