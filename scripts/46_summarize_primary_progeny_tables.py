#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

PRIMARY = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/"
    "progeny_primary_evidence_audit.csv"
)

OUT = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/"
    "progeny_primary_table_context.txt"
)

df = pd.read_csv(PRIMARY)

text_files = []

for root in [
    PROJECT / "05_extraction",
    PROJECT / "04_pdfs"
]:
    if root.exists():
        text_files.extend(root.rglob("*.txt"))


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
    return re.sub(r"\s+", " ", x).strip()


report = []

for _, r in df.iterrows():

    study = r["study_record_id"]
    table = str(r["table_number"])

    text = get_text(study)

    matches = list(
        re.finditer(
            rf"\bTable\s+{re.escape(table)}\b",
            text,
            re.I
        )
    )

    report.append("=" * 100)
    report.append(
        f"{study} | TABLE {table} | "
        f"{r['metric']} | "
        f"{r['dispersion_evidence']} | "
        f"{r['final_status']}"
    )
    report.append("=" * 100)

    if not matches:
        report.append("TABLE NOT FOUND")
        report.append("")
        continue

    # Preferir la aparición con señales de progenie
    candidates = []

    for m in matches:

        start = max(0, m.start() - 300)
        end = min(len(text), m.start() + 3000)

        block = clean(text[start:end])

        score = sum([
            bool(re.search(
                r"\bF\s*1\b",
                block,
                re.I
            )),
            bool(re.search(
                r"\bprogeny\b",
                block,
                re.I
            )),
            bool(re.search(
                r"\bemerg(?:ence|ed)\b",
                block,
                re.I
            )),
            bool(re.search(
                r"\bcontrol\b",
                block,
                re.I
            )),
            bool(re.search(
                r"±",
                block
            ))
        ])

        candidates.append(
            (score, block)
        )

    candidates.sort(
        key=lambda x: (
            x[0],
            len(x[1])
        ),
        reverse=True
    )

    best = candidates[0][1]

    # Mantenerlo compacto:
    # suficiente para ver caption, columnas y primeras filas.
    report.append(best[:2200])
    report.append("")


OUT.write_text(
    "\n".join(report),
    encoding="utf-8"
)

print("\n==========================================")
print("RESUMEN DE TABLAS F1")
print("==========================================\n")

print("Estudios:", len(df))
print("Archivo generado:")
print(OUT)

print("\nPara inspeccionarlo:")
print(
    "sed -n '1,220p' "
    + str(OUT)
)
