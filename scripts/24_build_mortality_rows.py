#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path


PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "selected_tables" /
    "selected_mortality_tables.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "structured"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = OUTDIR / "mortality_candidate_rows.csv"
SUMMARY = OUTDIR / "mortality_row_summary.csv"


# ==========================================================
# PATRONES
# ==========================================================

number = r"\d+(?:\.\d+)?"

plusminus = re.compile(
    rf"({number})\s*(?:±|\+/-|\+-)\s*({number})",
    re.I
)

percentage = re.compile(
    rf"({number})\s*%",
    re.I
)

plain_number = re.compile(
    rf"\b{number}\b"
)

control_pattern = re.compile(
    r"\b("
    r"control|untreated|con\b"
    r")\b",
    re.I
)

synthetic_pattern = re.compile(
    r"\b("
    r"permethrin|"
    r"dichlorvos|ddvp|"
    r"deltamethrin|"
    r"malathion|"
    r"cypermethrin|"
    r"pirimiphos|"
    r"phosphine"
    r")\b",
    re.I
)

exclude_line = re.compile(
    r"^\s*("
    r"table\s+\d+|"
    r"f\s*[\(\d]|"
    r"f-test|"
    r"note|notes|"
    r"mean[s]?\s+in|"
    r"values?\s+are|"
    r"each\s+datum|"
    r"ns\b|"
    r"p\s*[<>≤≥]|"
    r"journal\b|"
    r"vol\.|"
    r"doi\b"
    r")",
    re.I
)


# ==========================================================
# FUNCIONES
# ==========================================================

def clean_line(line):

    line = line.strip()

    line = re.sub(
        r"\s+",
        " ",
        line
    )

    return line


def classify_row(line):

    if not line:
        return "EMPTY"

    if exclude_line.search(line):
        return "NON_DATA"

    pm = plusminus.findall(line)

    nums = plain_number.findall(line)

    # Filas con uno o más valores media ± dispersión
    if len(pm) >= 1:
        return "MEAN_DISPERSION"

    # Filas control explícitas con números
    if (
        control_pattern.search(line)
        and len(nums) >= 1
    ):
        return "CONTROL_NUMERIC"

    # Filas con varios números:
    # posibles conteos o porcentajes sin ±
    if len(nums) >= 3:
        return "MULTI_NUMERIC"

    return "OTHER"


# ==========================================================
# LEER TABLAS
# ==========================================================

df = pd.read_csv(INPUT)

records = []


print("\n==========================================")
print("CONSTRUCCIÓN DE FILAS DE MORTALIDAD")
print("==========================================\n")

print(f"Tablas: {len(df)}")


# ==========================================================
# PROCESAR
# ==========================================================

for _, row in df.iterrows():

    study = str(
        row["study_record_id"]
    )

    table_number = str(
        row["table_number"]
    )

    text = str(
        row["table_text"]
    )

    lines = text.splitlines()

    for line_number, raw in enumerate(
        lines,
        start=1
    ):

        line = clean_line(raw)

        row_type = classify_row(
            line
        )

        if row_type not in [
            "MEAN_DISPERSION",
            "CONTROL_NUMERIC",
            "MULTI_NUMERIC"
        ]:
            continue


        pm_values = plusminus.findall(
            line
        )

        numeric_values = plain_number.findall(
            line
        )


        records.append({

            "study_record_id":
                study,

            "title":
                row["title"],

            "table_number":
                table_number,

            "line_number":
                line_number,

            "row_type":
                row_type,

            "is_control":
                bool(
                    control_pattern.search(
                        line
                    )
                ),

            "synthetic_arm":
                bool(
                    synthetic_pattern.search(
                        line
                    )
                ),

            "n_mean_dispersion":
                len(pm_values),

            "n_numeric_values":
                len(numeric_values),

            "line_text":
                line
        })


# ==========================================================
# DATAFRAME
# ==========================================================

out = pd.DataFrame(
    records
)


# ==========================================================
# QUITAR DUPLICADOS EXACTOS
# ==========================================================

before = len(out)

out = out.drop_duplicates(
    subset=[
        "study_record_id",
        "table_number",
        "line_text"
    ]
).copy()

duplicates_removed = (
    before - len(out)
)


# ==========================================================
# GUARDAR
# ==========================================================

out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESUMEN POR ESTUDIO
# ==========================================================

summary = (
    out
    .groupby(
        "study_record_id"
    )
    .agg(
        tables=(
            "table_number",
            "nunique"
        ),
        candidate_rows=(
            "line_text",
            "count"
        ),
        mean_dispersion_rows=(
            "n_mean_dispersion",
            lambda x: (x > 0).sum()
        ),
        control_rows=(
            "is_control",
            "sum"
        ),
        synthetic_rows=(
            "synthetic_arm",
            "sum"
        )
    )
    .reset_index()
)

summary.to_csv(
    SUMMARY,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("RESULTADO")
print("==========================================\n")

print(
    f"Filas candidatas: {len(out)}"
)

print(
    f"Duplicados eliminados: "
    f"{duplicates_removed}"
)

print(
    f"Estudios representados: "
    f"{out['study_record_id'].nunique()}"
)


print("\nTipos de fila:")

print(
    out[
        "row_type"
    ]
    .value_counts()
    .to_string()
)


print("\nControles detectados:")

print(
    out[
        "is_control"
    ]
    .value_counts()
    .to_string()
)


print("\nBrazos sintéticos explícitos:")

print(
    out[
        "synthetic_arm"
    ]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("RESUMEN POR ESTUDIO")
print("==========================================\n")

print(
    summary
    .sort_values(
        "candidate_rows",
        ascending=False
    )
    .head(20)
    .to_string(
        index=False
    )
)


print("\n==========================================")
print("MUESTRA DE FILAS")
print("==========================================\n")

sample = out[
    out["row_type"]
    == "MEAN_DISPERSION"
].head(30)

for _, r in sample.iterrows():

    print(
        r["study_record_id"],
        "| T",
        r["table_number"],
        "|",
        r["line_text"][:220]
    )


print(
    f"\nFilas:\n{OUTPUT}"
)

print(
    f"\nResumen:\n{SUMMARY}"
)
