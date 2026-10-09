#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

AUDIT = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/"
    "progeny_table_audit.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/tables"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUT_CSV = OUTDIR / "progeny_tables_identified.csv"
OUT_TXT = OUTDIR / "progeny_tables_evidence.txt"


# ==========================================================
# SOLO EXTRACT_HIGH
# ==========================================================

audit = pd.read_csv(AUDIT)

targets = sorted(
    audit.loc[
        audit["status"] == "EXTRACT_HIGH",
        "study_record_id"
    ].unique()
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


# ==========================================================
# PATRONES DE OUTCOME
# ==========================================================

outcome_re = re.compile(
    r"(?:"
    r"\bF\s*1\b.{0,100}?"
    r"(?:progeny|emergence|adult)"
    r"|"
    r"\b(?:progeny|offspring).{0,100}?"
    r"(?:emergence|production|adult)"
    r"|"
    r"\badult emergence\b"
    r"|"
    r"\bemerged adults?\b"
    r"|"
    r"\bnew(?:ly)? emerged adults?\b"
    r"|"
    r"\breproduction inhibition\b"
    r")",
    re.I | re.S
)

table_re = re.compile(
    r"\bTable\s+(\d+)\s*[:.]?",
    re.I
)


# ==========================================================
# CLASIFICACIÓN
# ==========================================================

def classify_metric(text):

    count = bool(
        re.search(
            r"\b(?:F\s*1\s+progeny|"
            r"number of (?:emerged )?adults|"
            r"new(?:ly)? emerged adults|"
            r"adult emergence|"
            r"progeny production)\b",
            text,
            re.I
        )
    )

    reduction = bool(
        re.search(
            r"\b(?:reduction|"
            r"reproduction inhibition|"
            r"inhibition rate|"
            r"IR\s*\(%\))\b",
            text,
            re.I
        )
    )

    percent_emergence = bool(
        re.search(
            r"\b(?:percentage|percent)\s+"
            r"(?:adult\s+)?emergence\b"
            r"|\bemergence\s*\(%\)",
            text,
            re.I
        )
    )

    metrics = []

    if count:
        metrics.append("COUNT")

    if reduction:
        metrics.append("PERCENT_REDUCTION")

    if percent_emergence:
        metrics.append("PERCENT_EMERGENCE")

    return ";".join(metrics)


def dispersion(text):

    if re.search(
        r"(?:mean\s*)?±\s*"
        r"(?:SE|S\.E\.|SEM|standard error)",
        text,
        re.I
    ):
        return "SE"

    if re.search(
        r"(?:mean\s*)?±\s*"
        r"(?:SD|S\.D\.|standard deviation)",
        text,
        re.I
    ):
        return "SD"

    if re.search(
        r"mean.{0,60}standard error",
        text,
        re.I | re.S
    ):
        return "SE"

    if re.search(
        r"mean.{0,60}standard deviation",
        text,
        re.I | re.S
    ):
        return "SD"

    return "UNKNOWN"


def clean(text):

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ==========================================================
# IDENTIFICAR TABLAS
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


    # ------------------------------------------------------
    # Localizar cada encabezado Table X
    # ------------------------------------------------------

    table_hits = list(
        table_re.finditer(combined)
    )

    study_records = []


    for i, hit in enumerate(table_hits):

        table_number = hit.group(1)

        start = hit.start()

        if i + 1 < len(table_hits):
            end = table_hits[i + 1].start()
        else:
            end = min(
                len(combined),
                start + 8000
            )

        # limitar bloques absurdamente largos
        end = min(
            end,
            start + 8000
        )

        block = clean(
            combined[start:end]
        )

        # ¿El bloque realmente contiene progenie?
        if not outcome_re.search(block):
            continue


        metric = classify_metric(block)
        disp = dispersion(block)

        has_control = bool(
            re.search(
                r"\b(?:control|untreated|negative control)\b",
                block,
                re.I
            )
        )

        has_plusminus = bool(
            re.search(
                r"\d+(?:\.\d+)?\s*±\s*"
                r"\d+(?:\.\d+)?",
                block
            )
        )

        has_dose = bool(
            re.search(
                r"\b(?:dose|dosage|concentration|rate)\b",
                block,
                re.I
            )
        )

        has_sitophilus = bool(
            re.search(
                r"\b(?:Sitophilus\s+zeamais|S\.\s*zeamais)\b",
                block,
                re.I
            )
        )

        has_maize = bool(
            re.search(
                r"\b(?:maize|corn|Zea\s+mays)\b",
                block,
                re.I
            )
        )


        # --------------------------------------------------
        # Clasificación conservadora
        # --------------------------------------------------

        score = sum([
            bool(metric),
            has_control,
            has_plusminus,
            has_dose,
            has_sitophilus,
            has_maize
        ])

        if (
            score >= 5
            and has_control
            and bool(metric)
        ):
            status = "SELECT"

        elif score >= 3:
            status = "REVIEW"

        else:
            status = "REJECT"


        rec = {
            "study_record_id":
                study,

            "table_number":
                table_number,

            "metric":
                metric,

            "dispersion":
                disp,

            "control":
                has_control,

            "plus_minus":
                has_plusminus,

            "dose":
                has_dose,

            "sitophilus_zeamais":
                has_sitophilus,

            "maize":
                has_maize,

            "status":
                status
        }

        records.append(rec)
        study_records.append(
            (rec, block)
        )


    # ------------------------------------------------------
    # Evidencia
    # ------------------------------------------------------

    if study_records:

        evidence.append("")
        evidence.append("=" * 100)
        evidence.append(study)
        evidence.append("=" * 100)

        for rec, block in study_records:

            evidence.append(
                f"TABLE {rec['table_number']} | "
                f"{rec['status']} | "
                f"{rec['metric']} | "
                f"{rec['dispersion']} | "
                f"CONTROL={rec['control']} | "
                f"DOSE={rec['dose']} | "
                f"SZ={rec['sitophilus_zeamais']} | "
                f"MAIZE={rec['maize']}"
            )

            evidence.append(
                block[:3500]
            )

            evidence.append("")


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
# RESUMEN
# ==========================================================

print("\n==========================================")
print("TABLAS F1/PROGENIE IDENTIFICADAS")
print("==========================================\n")

print("Estudios objetivo:", len(targets))
print("Estudios con tabla detectada:",
      df["study_record_id"].nunique())

print("Tablas detectadas:", len(df))


print("\n==========================================")
print("ESTADO")
print("==========================================\n")

print(
    df["status"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("MÉTRICA")
print("==========================================\n")

metric_summary = (
    df["metric"]
    .fillna("")
    .str.get_dummies(sep=";")
    .sum()
    .sort_values(
        ascending=False
    )
)

print(metric_summary.to_string())


print("\n==========================================")
print("DISPERSIÓN")
print("==========================================\n")

print(
    df["dispersion"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("SELECT POR ESTUDIO")
print("==========================================\n")

selected = df[
    df["status"] == "SELECT"
]

for study, g in selected.groupby(
    "study_record_id"
):

    values = []

    for _, r in g.iterrows():

        values.append(
            f"T{r['table_number']}"
            f"[{r['metric'] or 'UNKNOWN'};"
            f"{r['dispersion']}]"
        )

    print(
        study,
        " -> ",
        ", ".join(values)
    )


print("\n==========================================")
print("TOTALES SELECT")
print("==========================================\n")

print(
    "Estudios:",
    selected["study_record_id"].nunique()
)

print(
    "Tablas:",
    len(selected)
)


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_CSV)
print(OUT_TXT)
