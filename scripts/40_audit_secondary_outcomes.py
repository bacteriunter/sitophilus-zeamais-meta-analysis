#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

TEXT_ROOTS = [
    PROJECT / "05_extraction",
    PROJECT / "04_pdfs"
]

OUTDIR = PROJECT / "05_extraction" / "secondary_outcomes"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUTDIR / "secondary_outcome_audit.csv"
OUT_TXT = OUTDIR / "secondary_outcome_evidence.txt"


# ==========================================================
# ESTUDIOS CON TEXTO COMPLETO
# ==========================================================

text_files = []

for root in TEXT_ROOTS:
    if root.exists():
        text_files.extend(root.rglob("*.txt"))


# Identificar IDs disponibles
study_pattern = re.compile(r"SZ_\d{5}", re.I)

study_files = {}

for f in text_files:

    match = study_pattern.search(str(f))

    if not match:
        continue

    study = match.group(0).upper()

    # Preferir un único archivo por estudio.
    # Si hay varios, se combinarán posteriormente.
    study_files.setdefault(study, []).append(f)


# ==========================================================
# OUTCOMES
# ==========================================================

OUTCOMES = {

    "PROGENY_F1": [
        r"\bF1\b",
        r"\bF1 progeny\b",
        r"\bprogeny\b",
        r"\boffspring\b",
        r"\badult emergence\b",
        r"\bemerged adults?\b",
        r"\breproduction inhibition\b",
    ],

    "WEIGHT_LOSS": [
        r"\bweight loss\b",
        r"\bweight-loss\b",
        r"\bgrain weight loss\b",
        r"\bpercentage weight loss\b",
        r"\bpercent weight loss\b",
    ],

    "DAMAGE": [
        r"\bgrain damage\b",
        r"\bseed damage\b",
        r"\bpercentage damage\b",
        r"\bpercent damage\b",
        r"\bdamaged grains?\b",
        r"\bdamage index\b",
    ],

    "GERMINATION": [
        r"\bgermination\b",
        r"\bgermination percentage\b",
        r"\bpercent germination\b",
        r"\bgermination rate\b",
        r"\bseed viability\b",
    ]
}


# ==========================================================
# SEÑALES DE DATOS CUANTITATIVOS
# ==========================================================

quant_patterns = {

    "PLUS_MINUS":
        r"\d+(?:\.\d+)?\s*±\s*\d+(?:\.\d+)?",

    "MEAN_SE_SD":
        r"\bmean\b.{0,40}\b(?:SE|SEM|SD|standard error|standard deviation)\b",

    "PERCENT":
        r"\d+(?:\.\d+)?\s*%",

    "TABLE":
        r"\btable\s+\d+",

    "CONTROL":
        r"\b(?:control|untreated|negative control)\b",

    "REPLICATION":
        r"\b(?:three|four|five|six|\d+)\s+(?:replicates|replications)\b",
}


# ==========================================================
# FUNCIÓN LIMPIEZA
# ==========================================================

def clean(text):
    return re.sub(r"\s+", " ", text).strip()


# ==========================================================
# AUDITORÍA
# ==========================================================

records = []
evidence_lines = []

for study in sorted(study_files):

    combined = ""

    for f in study_files[study]:

        try:
            txt = f.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            continue

        combined += "\n" + txt

    if not combined.strip():
        continue

    evidence_lines.append("")
    evidence_lines.append("=" * 100)
    evidence_lines.append(study)
    evidence_lines.append("=" * 100)

    for outcome, patterns in OUTCOMES.items():

        matches = []

        for pattern in patterns:

            for m in re.finditer(
                pattern,
                combined,
                flags=re.I
            ):

                start = max(
                    0,
                    m.start() - 250
                )

                end = min(
                    len(combined),
                    m.end() + 350
                )

                snippet = clean(
                    combined[start:end]
                )

                if snippet not in matches:
                    matches.append(snippet)

        if not matches:
            continue


        # --------------------------------------------------
        # Combinar ventanas para buscar señales cuantitativas
        # --------------------------------------------------

        evidence_text = " ".join(matches)

        signals = {}

        for name, pattern in quant_patterns.items():

            signals[name] = bool(
                re.search(
                    pattern,
                    evidence_text,
                    flags=re.I | re.S
                )
            )


        # --------------------------------------------------
        # Score simple de extractabilidad
        # --------------------------------------------------

        score = sum([
            signals["PLUS_MINUS"],
            signals["MEAN_SE_SD"],
            signals["PERCENT"],
            signals["TABLE"],
            signals["CONTROL"],
            signals["REPLICATION"],
        ])


        if score >= 4:
            extractability = "HIGH"

        elif score >= 2:
            extractability = "POSSIBLE"

        else:
            extractability = "LOW"


        records.append({

            "study_record_id": study,
            "outcome": outcome,

            "n_keyword_windows":
                len(matches),

            "plus_minus":
                signals["PLUS_MINUS"],

            "mean_se_sd":
                signals["MEAN_SE_SD"],

            "percentage":
                signals["PERCENT"],

            "table_signal":
                signals["TABLE"],

            "control_signal":
                signals["CONTROL"],

            "replication_signal":
                signals["REPLICATION"],

            "extractability":
                extractability
        })


        evidence_lines.append("")
        evidence_lines.append(
            f"[{outcome}] "
            f"windows={len(matches)} "
            f"score={score} "
            f"{extractability}"
        )

        # Solo primeras 3 ventanas:
        # suficiente para auditoría, sin producir miles de líneas.
        for i, snippet in enumerate(
            matches[:3],
            1
        ):

            evidence_lines.append(
                f"  [{i}] {snippet}"
            )


# ==========================================================
# DATAFRAME
# ==========================================================

df = pd.DataFrame(records)

if df.empty:

    print(
        "\nNo se detectaron outcomes secundarios."
    )

    raise SystemExit


df.to_csv(
    OUT_CSV,
    index=False,
    encoding="utf-8"
)

OUT_TXT.write_text(
    "\n".join(evidence_lines),
    encoding="utf-8"
)


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("AUDITORÍA DE OUTCOMES SECUNDARIOS")
print("==========================================\n")

print(
    "Estudios con texto detectados:",
    len(study_files)
)

print(
    "Estudios con algún outcome:",
    df["study_record_id"].nunique()
)


print("\n==========================================")
print("POR OUTCOME")
print("==========================================\n")

summary = (
    df.groupby("outcome")
    .agg(
        studies=("study_record_id", "nunique"),
        high=(
            "extractability",
            lambda x: (x == "HIGH").sum()
        ),
        possible=(
            "extractability",
            lambda x: (x == "POSSIBLE").sum()
        ),
        low=(
            "extractability",
            lambda x: (x == "LOW").sum()
        ),
        tables=("table_signal", "sum"),
        dispersion=("mean_se_sd", "sum"),
        controls=("control_signal", "sum"),
        replication=("replication_signal", "sum")
    )
    .reset_index()
)

print(
    summary.to_string(
        index=False
    )
)


print("\n==========================================")
print("HIGH POR OUTCOME")
print("==========================================\n")

for outcome in sorted(
    df["outcome"].unique()
):

    high = df[
        (df["outcome"] == outcome)
        &
        (df["extractability"] == "HIGH")
    ]

    print(
        f"{outcome}: "
        f"{high['study_record_id'].nunique()} estudios"
    )

    if not high.empty:

        print(
            "  "
            +
            ", ".join(
                sorted(
                    high["study_record_id"]
                    .unique()
                )
            )
        )


print("\n==========================================")
print("DECISIÓN PRELIMINAR")
print("==========================================\n")

for outcome in sorted(
    df["outcome"].unique()
):

    sub = df[
        df["outcome"] == outcome
    ]

    high_n = (
        sub.loc[
            sub["extractability"] == "HIGH",
            "study_record_id"
        ]
        .nunique()
    )

    possible_n = (
        sub.loc[
            sub["extractability"].isin(
                ["HIGH", "POSSIBLE"]
            ),
            "study_record_id"
        ]
        .nunique()
    )

    if high_n >= 5:

        decision = (
            "PRIORIDAD ALTA PARA EXTRACCIÓN"
        )

    elif possible_n >= 4:

        decision = (
            "REVISAR ANTES DE EXTRAER"
        )

    else:

        decision = (
            "PROBABLEMENTE SÍNTESIS NARRATIVA"
        )

    print(
        f"{outcome}: {decision} "
        f"(HIGH={high_n}, "
        f"HIGH+POSSIBLE={possible_n})"
    )


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_CSV)
print(OUT_TXT)
