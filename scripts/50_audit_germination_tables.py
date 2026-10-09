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
    "05_extraction/secondary_outcomes/germination"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUT_CSV = OUTDIR / "germination_table_audit.csv"
OUT_TXT = OUTDIR / "germination_table_evidence.txt"


# ==========================================================
# CANDIDATOS
# ==========================================================

audit = pd.read_csv(AUDIT)

required = {
    "study_record_id",
    "outcome",
    "extractability"
}

missing = required - set(audit.columns)

if missing:
    raise ValueError(
        f"Faltan columnas requeridas: {sorted(missing)}"
    )

targets = audit[
    (audit["outcome"] == "GERMINATION")
    &
    (
        audit["extractability"]
        .isin(["HIGH", "POSSIBLE"])
    )
].copy()

study_ids = sorted(
    targets["study_record_id"]
    .dropna()
    .astype(str)
    .unique()
)

print(
    "\nCandidatos GERMINATION HIGH/POSSIBLE:",
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

GERM_STRONG = re.compile(
    r"(?:"
    r"\bpercentage\s+(?:seed\s+)?germination\b"
    r"|"
    r"\bpercent\s+(?:seed\s+)?germination\b"
    r"|"
    r"\bgermination\s*\(%\)"
    r"|"
    r"\bgermination\s+percentage\b"
    r"|"
    r"\bseed\s+germination\b"
    r"|"
    r"\bgermination\s+rate\b"
    r")",
    re.I
)

PERCENT_GERM = re.compile(
    r"(?:"
    r"\bpercentage\s+(?:seed\s+)?germination\b"
    r"|"
    r"\bpercent\s+(?:seed\s+)?germination\b"
    r"|"
    r"\bgermination\s*\(%\)"
    r"|"
    r"\bgermination\s+percentage\b"
    r")",
    re.I
)

COUNT_GERM = re.compile(
    r"(?:"
    r"\bnumber\s+of\s+(?:seeds?\s+)?germinated\b"
    r"|"
    r"\bgerminated\s+seeds?\s*\(n\)"
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
# LOCALIZAR TABLAS
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
            (number, block)
        )

    return blocks


# ==========================================================
# AUDITORÍA
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

        key = (
            table_number,
            block[:500]
        )

        if key in seen:
            continue

        seen.add(key)

        header = block[:1400]

        if not GERM_STRONG.search(header):
            continue


        # --------------------------------------------------
        # Métrica
        # --------------------------------------------------

        percent = bool(
            PERCENT_GERM.search(header)
        )

        count = bool(
            COUNT_GERM.search(header)
        )

        if percent and not count:
            metric = "PERCENT_GERMINATION"

        elif count and not percent:
            metric = "GERMINATED_SEED_COUNT"

        elif percent and count:
            metric = "MIXED_GERMINATION"

        else:
            metric = "GERMINATION_UNCLEAR"


        # --------------------------------------------------
        # Señales experimentales
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Dispersión
        # --------------------------------------------------

        if SE.search(block) and not SD.search(block):
            dispersion = "SE"

        elif SD.search(block) and not SE.search(block):
            dispersion = "SD"

        elif SE.search(block) and SD.search(block):
            dispersion = "MIXED"

        else:
            dispersion = "UNKNOWN"


        # --------------------------------------------------
        # Estado
        # --------------------------------------------------

        if (
            metric == "PERCENT_GERMINATION"
            and sz
            and maize
            and control
            and plusminus
        ):
            status = "HIGH"

        elif (
            metric == "PERCENT_GERMINATION"
            and sz
            and maize
            and control
        ):
            status = "POSSIBLE"

        elif (
            metric == "GERMINATED_SEED_COUNT"
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
# GUARDAR
# ==========================================================

out = pd.DataFrame(records)

if out.empty:

    print(
        "\nNo se detectaron tablas de germinación."
    )
    raise SystemExit


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
# RESUMEN
# ==========================================================

print("\n==========================================")
print("AUDITORÍA DE GERMINACIÓN")
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
