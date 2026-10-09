#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

AUDIT = (
    PROJECT / "05_extraction/secondary_outcomes/"
    "secondary_outcome_audit.csv"
)

OUTDIR = (
    PROJECT / "05_extraction/secondary_outcomes/progeny"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUT_CSV = OUTDIR / "progeny_table_audit.csv"
OUT_TXT = OUTDIR / "progeny_table_evidence.txt"


# ==========================================================
# ESTUDIOS CANDIDATOS
# ==========================================================

audit = pd.read_csv(AUDIT)

targets = sorted(
    audit.loc[
        (audit["outcome"] == "PROGENY_F1")
        &
        (audit["extractability"].isin(
            ["HIGH", "POSSIBLE"]
        )),
        "study_record_id"
    ]
    .unique()
)

print("\n==========================================")
print("AUDITORÍA ESTRUCTURAL F1/PROGENIE")
print("==========================================\n")

print("Candidatos HIGH+POSSIBLE:", len(targets))


# ==========================================================
# LOCALIZAR TEXTOS
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


# ==========================================================
# PATRONES
# ==========================================================

outcome_patterns = [
    r"\bF1\s+progeny\b",
    r"\bF1\s+emergence\b",
    r"\bF1\s+adult emergence\b",
    r"\bprogeny emergence\b",
    r"\badult emergence\b",
    r"\bnumber of emerged adults\b",
    r"\bnew(?:ly)? emerged adults\b",
    r"\bprogeny production\b",
]

table_pattern = re.compile(
    r"\btable\s+(\d+)\b",
    re.I
)

dispersion_patterns = {
    "SE": [
        r"mean\s*±\s*SE\b",
        r"mean\s*±\s*standard error",
        r"mean.{0,40}standard error",
    ],

    "SD": [
        r"mean\s*±\s*SD\b",
        r"mean\s*±\s*standard deviation",
        r"mean.{0,40}standard deviation",
    ]
}

metric_patterns = {

    "COUNT": [
        r"\bnumber of (?:emerged )?adults\b",
        r"\bnew(?:ly)? emerged adults\b",
        r"\bF1 progeny\b",
        r"\bF1 emergence\b",
        r"\bprogeny production\b",
    ],

    "PERCENT_REDUCTION": [
        r"\breduction\b",
        r"\breproduction inhibition\b",
        r"\binhibition rate\b",
        r"\bIR\s*\(%\)",
    ],

    "PERCENT_EMERGENCE": [
        r"\bpercentage emergence\b",
        r"\bpercent emergence\b",
        r"\bemergence\s*\(%\)",
    ]
}


def clean(text):
    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ==========================================================
# AUDITAR
# ==========================================================

records = []
evidence = []

for study in targets:

    matches = [
        f for f in text_files
        if study.lower() in str(f).lower()
    ]

    combined = ""

    for f in matches:

        try:
            combined += "\n" + f.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            pass

    if not combined.strip():
        continue

    windows = []

    for pattern in outcome_patterns:

        for m in re.finditer(
            pattern,
            combined,
            flags=re.I
        ):

            start = max(
                0,
                m.start() - 700
            )

            end = min(
                len(combined),
                m.end() + 1600
            )

            snippet = clean(
                combined[start:end]
            )

            if snippet not in windows:
                windows.append(snippet)

    if not windows:
        continue


    # ======================================================
    # ANALIZAR VENTANAS
    # ======================================================

    evidence_text = " ".join(windows)

    tables = sorted(
        set(
            table_pattern.findall(
                evidence_text
            )
        )
    )


    dispersion = "UNKNOWN"

    for dtype, patterns in dispersion_patterns.items():

        if any(
            re.search(
                p,
                evidence_text,
                flags=re.I | re.S
            )
            for p in patterns
        ):
            dispersion = dtype
            break


    metrics = []

    for metric, patterns in metric_patterns.items():

        if any(
            re.search(
                p,
                evidence_text,
                flags=re.I | re.S
            )
            for p in patterns
        ):
            metrics.append(metric)


    has_plusminus = bool(
        re.search(
            r"\d+(?:\.\d+)?\s*±\s*"
            r"\d+(?:\.\d+)?",
            evidence_text
        )
    )

    has_control = bool(
        re.search(
            r"\b(?:control|untreated|negative control)\b",
            evidence_text,
            flags=re.I
        )
    )

    has_dose = bool(
        re.search(
            r"\b(?:dose|dosage|concentration|rate)\b",
            evidence_text,
            flags=re.I
        )
    )

    has_time = bool(
        re.search(
            r"\b\d+(?:\.\d+)?\s*"
            r"(?:h|hr|hrs|hours|day|days|week|weeks)\b",
            evidence_text,
            flags=re.I
        )
    )

    natural_signal = bool(
        re.search(
            r"\b(?:powder|extract|oil|ash|botanical|plant|"
            r"leaf|leaves|seed|root|stem|wood ash)\b",
            evidence_text,
            flags=re.I
        )
    )


    # ======================================================
    # CLASIFICACIÓN CONSERVADORA
    # ======================================================

    score = sum([
        bool(tables),
        bool(metrics),
        has_plusminus,
        has_control,
        has_dose,
        natural_signal
    ])


    if (
        score >= 5
        and bool(metrics)
        and has_control
    ):
        status = "EXTRACT_HIGH"

    elif score >= 3:
        status = "REVIEW"

    else:
        status = "LOW"


    records.append({

        "study_record_id": study,

        "n_windows":
            len(windows),

        "tables":
            ";".join(tables),

        "metrics":
            ";".join(metrics),

        "dispersion":
            dispersion,

        "plus_minus":
            has_plusminus,

        "control":
            has_control,

        "dose":
            has_dose,

        "time":
            has_time,

        "natural_signal":
            natural_signal,

        "status":
            status
    })


    evidence.append("")
    evidence.append("=" * 100)
    evidence.append(study)
    evidence.append("=" * 100)

    evidence.append(
        f"STATUS={status} | "
        f"TABLES={';'.join(tables) or 'NONE'} | "
        f"METRICS={';'.join(metrics) or 'NONE'} | "
        f"DISPERSION={dispersion} | "
        f"CONTROL={has_control} | "
        f"DOSE={has_dose}"
    )

    for i, snippet in enumerate(
        windows[:4],
        1
    ):
        evidence.append(
            f"[{i}] {snippet}"
        )


# ==========================================================
# GUARDAR
# ==========================================================

df = pd.DataFrame(records)

df.to_csv(
    OUT_CSV,
    index=False,
    encoding="utf-8"
)

OUT_TXT.write_text(
    "\n".join(evidence),
    encoding="utf-8"
)


# ==========================================================
# RESULTADOS
# ==========================================================

print("\nEstudios auditados:", len(df))

print("\n==========================================")
print("ESTADO")
print("==========================================\n")

print(
    df["status"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("MÉTRICAS DETECTADAS")
print("==========================================\n")

metric_counts = (
    df["metrics"]
    .fillna("")
    .str.get_dummies(sep=";")
    .sum()
    .sort_values(
        ascending=False
    )
)

print(metric_counts.to_string())


print("\n==========================================")
print("DISPERSIÓN")
print("==========================================\n")

print(
    df["dispersion"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("EXTRACT_HIGH")
print("==========================================\n")

high = df[
    df["status"] == "EXTRACT_HIGH"
]

print("Estudios:", len(high))

if not high.empty:

    for _, r in high.iterrows():

        print(
            r["study_record_id"],
            "|",
            r["metrics"],
            "|",
            r["dispersion"],
            "| tables:",
            r["tables"]
        )


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_CSV)
print(OUT_TXT)
