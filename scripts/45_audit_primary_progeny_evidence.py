#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

PRIMARY = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/"
    "progeny_primary_tables.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny"
)

OUT_CSV = OUTDIR / "progeny_primary_evidence_audit.csv"
OUT_TXT = OUTDIR / "progeny_primary_evidence_audit.txt"

df = pd.read_csv(PRIMARY)

# ==========================================================
# LOCALIZAR TEXTOS
# ==========================================================

text_files = []

for root in [
    PROJECT / "05_extraction",
    PROJECT / "04_pdfs"
]:
    if root.exists():
        text_files.extend(root.rglob("*.txt"))


def get_study_text(study):

    files = [
        f for f in text_files
        if study.lower() in str(f).lower()
    ]

    text = ""

    for f in files:
        try:
            text += "\n" + f.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            pass

    return text


def clean(x):
    return re.sub(r"\s+", " ", x).strip()


# ==========================================================
# PATRONES
# ==========================================================

SE_PATTERNS = [
    r"\bmean(?:s)?\s*±\s*(?:SE|S\.E\.|SEM)\b",
    r"\bmean(?:s)?.{0,80}\bstandard error\b",
    r"\bvalues?.{0,80}\bstandard error\b",
]

SD_PATTERNS = [
    r"\bmean(?:s)?\s*±\s*(?:SD|S\.D\.)\b",
    r"\bmean(?:s)?.{0,80}\bstandard deviation\b",
    r"\bvalues?.{0,80}\bstandard deviation\b",
]

REPLICATION_PATTERNS = [
    r"\b(?:each\s+)?treatment.{0,100}?"
    r"(?:replicated|replicate(?:d)?|replications?)\s*"
    r"(?:three|four|five|six|\d+)\s*(?:times)?",

    r"\b(?:three|four|five|six|\d+)\s+"
    r"(?:replicates|replications)\b",

    r"\b(?:replicated|replicate(?:d)?)\s*"
    r"(?:three|four|five|six|\d+)\s*(?:times)?",
]

MAIZE_PATTERNS = [
    r"\bmaize\b",
    r"\bcorn\b",
    r"\bZea\s+mays\b",
]

OTHER_GRAIN_PATTERNS = [
    r"\bsorghum\b",
    r"\brice\b",
    r"\bwheat\b",
    r"\bmillet\b",
    r"\bcowpea\b",
    r"\bbean(?:s)?\b",
]


# ==========================================================
# AUDITORÍA
# ==========================================================

records = []
report = []

for _, row in df.iterrows():

    study = row["study_record_id"]
    table_number = str(row["table_number"])

    text = get_study_text(study)

    if not text:
        continue

    # ------------------------------------------------------
    # Ventanas alrededor de Table X
    # ------------------------------------------------------

    table_matches = list(
        re.finditer(
            rf"\bTable\s+{re.escape(table_number)}\b",
            text,
            flags=re.I
        )
    )

    windows = []

    for m in table_matches:

        start = max(0, m.start() - 1800)
        end = min(len(text), m.end() + 5000)

        windows.append(
            clean(text[start:end])
        )

    table_text = " ".join(windows)

    # Contexto global adicional para metodología
    global_text = clean(text)


    # ------------------------------------------------------
    # DISPERSIÓN
    # ------------------------------------------------------

    se_table = any(
        re.search(p, table_text, re.I | re.S)
        for p in SE_PATTERNS
    )

    sd_table = any(
        re.search(p, table_text, re.I | re.S)
        for p in SD_PATTERNS
    )

    se_global = any(
        re.search(p, global_text, re.I | re.S)
        for p in SE_PATTERNS
    )

    sd_global = any(
        re.search(p, global_text, re.I | re.S)
        for p in SD_PATTERNS
    )

    if se_table and not sd_table:
        dispersion_evidence = "SE_TABLE"

    elif sd_table and not se_table:
        dispersion_evidence = "SD_TABLE"

    elif se_table and sd_table:
        dispersion_evidence = "MIXED_TABLE"

    elif se_global and not sd_global:
        dispersion_evidence = "SE_ARTICLE"

    elif sd_global and not se_global:
        dispersion_evidence = "SD_ARTICLE"

    elif se_global and sd_global:
        dispersion_evidence = "MIXED_ARTICLE"

    else:
        dispersion_evidence = "UNKNOWN"


    # ------------------------------------------------------
    # REPLICACIÓN
    # ------------------------------------------------------

    replication_hits = []

    for pattern in REPLICATION_PATTERNS:

        for m in re.finditer(
            pattern,
            global_text,
            re.I | re.S
        ):

            replication_hits.append(
                clean(
                    global_text[
                        max(0, m.start() - 120):
                        min(len(global_text), m.end() + 180)
                    ]
                )
            )

    replication_signal = bool(replication_hits)


    # ------------------------------------------------------
    # HOSPEDERO / GRANO
    # ------------------------------------------------------

    maize_table = any(
        re.search(p, table_text, re.I)
        for p in MAIZE_PATTERNS
    )

    maize_article = any(
        re.search(p, global_text, re.I)
        for p in MAIZE_PATTERNS
    )

    other_grains = sorted(set(
        m.group(0).lower()
        for p in OTHER_GRAIN_PATTERNS
        for m in re.finditer(p, table_text, re.I)
    ))

    if maize_table:
        grain_status = "MAIZE_TABLE"

    elif maize_article:
        grain_status = "MAIZE_ARTICLE"

    else:
        grain_status = "MAIZE_NOT_CONFIRMED"


    # ------------------------------------------------------
    # F1 signal
    # ------------------------------------------------------

    f1_signal = bool(
        re.search(
            r"\b(?:F\s*1|progeny|offspring|"
            r"adult emergence|emerged adults?)\b",
            table_text,
            re.I
        )
    )


    # ------------------------------------------------------
    # DECISIÓN CONSERVADORA
    # ------------------------------------------------------

    if (
        f1_signal
        and grain_status in [
            "MAIZE_TABLE",
            "MAIZE_ARTICLE"
        ]
        and dispersion_evidence in [
            "SE_TABLE",
            "SD_TABLE"
        ]
    ):
        final_status = "READY_STRONG"

    elif (
        f1_signal
        and grain_status in [
            "MAIZE_TABLE",
            "MAIZE_ARTICLE"
        ]
    ):
        final_status = "READY_COUNT_ONLY"

    else:
        final_status = "REVIEW"


    records.append({
        "study_record_id":
            study,

        "table_number":
            table_number,

        "metric":
            row["metric"],

        "previous_dispersion":
            row["dispersion"],

        "dispersion_evidence":
            dispersion_evidence,

        "replication_signal":
            replication_signal,

        "grain_status":
            grain_status,

        "other_grains_near_table":
            ";".join(other_grains),

        "f1_signal":
            f1_signal,

        "final_status":
            final_status
    })


    # ------------------------------------------------------
    # REPORTE DE EVIDENCIA
    # ------------------------------------------------------

    report.append("")
    report.append("=" * 100)
    report.append(
        f"{study} | TABLE {table_number}"
    )
    report.append("=" * 100)

    report.append(
        f"DISPERSION={dispersion_evidence} | "
        f"REPLICATION={replication_signal} | "
        f"GRAIN={grain_status} | "
        f"F1={f1_signal} | "
        f"STATUS={final_status}"
    )

    if other_grains:
        report.append(
            "OTHER_GRAINS_NEAR_TABLE="
            + ",".join(other_grains)
        )

    if replication_hits:
        report.append(
            "REPLICATION EVIDENCE:"
        )

        for hit in replication_hits[:3]:
            report.append(
                "  " + hit
            )

    report.append(
        "TABLE CONTEXT:"
    )

    if windows:
        report.append(
            windows[0][:3500]
        )
    else:
        report.append(
            "NO TABLE WINDOW FOUND"
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
    "\n".join(report),
    encoding="utf-8"
)


# ==========================================================
# SALIDA
# ==========================================================

print("\n==========================================")
print("AUDITORÍA FINAL F1/PROGENIE")
print("==========================================\n")

print("Estudios auditados:", len(out))

print("\n==========================================")
print("ESTADO FINAL")
print("==========================================\n")

print(
    out["final_status"]
    .value_counts()
    .to_string()
)

print("\n==========================================")
print("DISPERSIÓN")
print("==========================================\n")

print(
    out["dispersion_evidence"]
    .value_counts()
    .to_string()
)

print("\n==========================================")
print("REPLICACIÓN")
print("==========================================\n")

print(
    out["replication_signal"]
    .value_counts()
    .to_string()
)

print("\n==========================================")
print("GRANO")
print("==========================================\n")

print(
    out["grain_status"]
    .value_counts()
    .to_string()
)

print("\n==========================================")
print("ESTUDIOS REVIEW")
print("==========================================\n")

review = out[
    out["final_status"] == "REVIEW"
]

if review.empty:
    print("Ninguno")
else:
    print(
        review[
            [
                "study_record_id",
                "table_number",
                "grain_status",
                "dispersion_evidence",
                "f1_signal"
            ]
        ].to_string(index=False)
    )

print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_CSV)
print(OUT_TXT)
