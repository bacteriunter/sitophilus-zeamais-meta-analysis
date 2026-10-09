#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

MAP = (
    PROJECT / "06_effect_sizes/"
    "mortality_comparison_map_final.csv"
)

OUT = (
    PROJECT / "06_effect_sizes/"
    "replication_evidence_audit.txt"
)

cmp = pd.read_csv(MAP)

studies = sorted(
    cmp.loc[
        cmp["analysis_set"] == "PRIMARY_MEAN_MORTALITY",
        "study_record_id"
    ].unique()
)

# ----------------------------------------------------------
# Buscar archivos de texto extraídos
# ----------------------------------------------------------

text_files = []

for root in [
    PROJECT / "05_extraction",
    PROJECT / "04_pdfs"
]:
    if root.exists():
        text_files.extend(
            list(root.rglob("*.txt"))
        )


# ----------------------------------------------------------
# Patrones muy conservadores
# ----------------------------------------------------------

patterns = [
    # replicaciones
    r".{0,120}\b(?:three|four|five|six|\d+)\s+"
    r"(?:replicates|replications)\b.{0,120}",

    r".{0,120}\b(?:replicated|replicate)\s+"
    r"(?:three|four|five|six|\d+)\s+times\b.{0,120}",

    # insectos por réplica
    r".{0,120}\b\d+\s+"
    r"(?:adult\s+)?(?:insects|weevils)\b.{0,120}",

    # dispersión
    r".{0,120}\bmean(?:s)?\s*[±+/-]+\s*"
    r"(?:SE|SEM|SD|S\.E\.|S\.D\.)\b.{0,120}",

    r".{0,120}\b(?:standard error|standard deviation)\b.{0,120}",
]


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


lines = []

lines.append("=" * 100)
lines.append("AUDITORÍA AUTOMÁTICA DE REPLICACIÓN Y DISPERSIÓN")
lines.append("=" * 100)


for study in studies:

    lines.append("")
    lines.append("=" * 100)
    lines.append(study)
    lines.append("=" * 100)

    # localizar todos los txt asociados al estudio
    matches = [
        f for f in text_files
        if study.lower() in str(f).lower()
    ]

    if not matches:
        lines.append("NO SE ENCONTRÓ TXT ASOCIADO")
        continue

    found = []

    for f in matches:

        try:
            text = f.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            continue

        for pattern in patterns:

            for m in re.finditer(
                pattern,
                text,
                flags=re.I | re.S
            ):

                snippet = clean(m.group(0))

                if snippet not in found:
                    found.append(snippet)

    if not found:
        lines.append("SIN EVIDENCIA AUTOMÁTICA")
        continue

    for i, snippet in enumerate(found[:30], 1):
        lines.append(f"[{i}] {snippet}")


OUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("\n==========================================")
print("AUDITORÍA DE REPLICACIÓN")
print("==========================================\n")

print("Estudios:", len(studies))

for study in studies:

    matches = [
        f for f in text_files
        if study.lower() in str(f).lower()
    ]

    print(
        f"{study}: "
        f"{len(matches)} archivo(s) de texto"
    )

print(
    "\nResultado guardado en:\n"
    f"{OUT}"
)

print(
    "\nPara mostrar únicamente la evidencia:"
)

print(
    f"\ncat {OUT}"
)
