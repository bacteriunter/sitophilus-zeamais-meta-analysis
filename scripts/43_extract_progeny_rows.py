#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

TABLE_AUDIT = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/tables/"
    "progeny_tables_identified.csv"
)

EVIDENCE = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/tables/"
    "progeny_tables_evidence.txt"
)

OUTDIR = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/rows"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUT_CSV = OUTDIR / "progeny_candidate_rows.csv"
OUT_SUMMARY = OUTDIR / "progeny_candidate_rows_summary.csv"


# ==========================================================
# TABLAS SELECT
# ==========================================================

audit = pd.read_csv(TABLE_AUDIT)

sel = audit[
    audit["status"] == "SELECT"
].copy()

# Eliminar registros idénticos del detector
sel = sel.drop_duplicates(
    subset=[
        "study_record_id",
        "table_number",
        "metric",
        "dispersion"
    ]
)

print("\n==========================================")
print("EXTRACCIÓN DE FILAS F1/PROGENIE")
print("==========================================\n")

print("Tablas SELECT después de deduplicar:", len(sel))
print(
    "Estudios:",
    sel["study_record_id"].nunique()
)


# ==========================================================
# LEER BLOQUES DE EVIDENCIA
# ==========================================================

text = EVIDENCE.read_text(
    encoding="utf-8",
    errors="ignore"
)


# Cada bloque de estudio
study_blocks = re.split(
    r"={50,}\s*(SZ_\d{5})\s*={50,}",
    text
)

blocks = {}

for i in range(
    1,
    len(study_blocks),
    2
):
    study = study_blocks[i]
    content = study_blocks[i + 1]

    blocks[study] = content


# ==========================================================
# EXTRAER BLOQUES TABLE X
# ==========================================================

def get_table_blocks(content):

    pattern = re.compile(
        r"TABLE\s+(\d+)\s+\|.*?(?="
        r"TABLE\s+\d+\s+\||\Z)",
        re.I | re.S
    )

    result = []

    for m in pattern.finditer(content):

        number = m.group(1)
        block = m.group(0)

        result.append(
            (number, block)
        )

    return result


# ==========================================================
# PATRÓN DE FILAS NUMÉRICAS
#
# No intenta interpretar todavía la estructura completa.
# Solo captura líneas/segmentos con números y ±.
# ==========================================================

plusminus_re = re.compile(
    r"(?P<mean>\d+(?:\.\d+)?)"
    r"\s*±\s*"
    r"(?P<disp>\d+(?:\.\d+)?)"
)

number_re = re.compile(
    r"(?<![A-Za-z])"
    r"\d+(?:\.\d+)?"
    r"(?![A-Za-z])"
)


records = []


# ==========================================================
# PROCESAR TABLAS
# ==========================================================

for _, row in sel.iterrows():

    study = row["study_record_id"]
    table_number = str(row["table_number"])

    content = blocks.get(
        study,
        ""
    )

    if not content:
        continue

    table_candidates = [
        b
        for n, b in get_table_blocks(content)
        if str(n) == table_number
    ]

    if not table_candidates:
        continue


    # Puede haber más de un bloque con el mismo número
    # por duplicación del PDF. Conservamos el más largo.
    block = max(
        table_candidates,
        key=len
    )


    # ------------------------------------------------------
    # Dividir en segmentos manejables
    # ------------------------------------------------------

    segments = re.split(
        r"(?<=[.;])\s+|\n+",
        block
    )

    candidate_index = 0

    for segment in segments:

        segment = re.sub(
            r"\s+",
            " ",
            segment
        ).strip()

        if not segment:
            continue


        pm = list(
            plusminus_re.finditer(
                segment
            )
        )

        nums = number_re.findall(
            segment
        )


        # Solo conservar segmentos con información numérica
        if not pm and len(nums) < 2:
            continue


        # Evitar encabezados estadísticos obvios
        if re.search(
            r"\b(?:ANOVA|F-value|P-value|"
            r"LC50|LC90|LD50|LD90|"
            r"regression|R2|R²)\b",
            segment,
            re.I
        ):
            continue


        candidate_index += 1


        # --------------------------------------------------
        # Valores mean ± dispersion
        # --------------------------------------------------

        if pm:

            for j, m in enumerate(pm, 1):

                records.append({

                    "study_record_id":
                        study,

                    "table_number":
                        table_number,

                    "table_metric":
                        row["metric"],

                    "table_dispersion":
                        row["dispersion"],

                    "candidate_segment":
                        candidate_index,

                    "value_index":
                        j,

                    "value_type":
                        "MEAN_DISPERSION",

                    "mean":
                        float(
                            m.group("mean")
                        ),

                    "dispersion":
                        float(
                            m.group("disp")
                        ),

                    "raw_segment":
                        segment[:1000]
                })


        # --------------------------------------------------
        # Segmentos numéricos sin ±
        # --------------------------------------------------

        else:

            records.append({

                "study_record_id":
                    study,

                "table_number":
                    table_number,

                "table_metric":
                    row["metric"],

                "table_dispersion":
                    row["dispersion"],

                "candidate_segment":
                    candidate_index,

                "value_index":
                    1,

                "value_type":
                    "NUMERIC_ONLY",

                "mean":
                    None,

                "dispersion":
                    None,

                "raw_segment":
                    segment[:1000]
            })


# ==========================================================
# DATAFRAME
# ==========================================================

df = pd.DataFrame(records)

if df.empty:

    print("No se extrajeron filas candidatas.")
    raise SystemExit


# Eliminar duplicados exactos producidos por texto repetido
before = len(df)

df = df.drop_duplicates(
    subset=[
        "study_record_id",
        "table_number",
        "value_type",
        "mean",
        "dispersion",
        "raw_segment"
    ]
).copy()

removed = before - len(df)


# ==========================================================
# CLASIFICACIÓN PRELIMINAR
# ==========================================================

def classify_segment(text):

    t = text.lower()

    if re.search(
        r"\b(?:control|untreated)\b",
        t
    ):
        arm = "CONTROL"

    elif re.search(
        r"\b(?:permethrin|dichlorvos|ddvp|"
        r"synthetic|insecticide)\b",
        t
    ):
        arm = "POSSIBLE_SYNTHETIC"

    else:
        arm = "CANDIDATE_TREATMENT"


    if re.search(
        r"\b(?:reduction|inhibition|IR\s*\(%\))",
        text,
        re.I
    ):
        metric_signal = "PERCENT_REDUCTION"

    elif re.search(
        r"\b(?:F1|progeny|emergence|"
        r"emerged adults?)\b",
        text,
        re.I
    ):
        metric_signal = "COUNT_OR_EMERGENCE"

    else:
        metric_signal = "UNKNOWN"


    return pd.Series(
        [arm, metric_signal]
    )


df[
    [
        "arm_signal",
        "metric_signal"
    ]
] = df["raw_segment"].apply(
    classify_segment
)


# ==========================================================
# GUARDAR
# ==========================================================

df.to_csv(
    OUT_CSV,
    index=False,
    encoding="utf-8"
)


summary = (
    df.groupby("study_record_id")
    .agg(
        candidate_values=(
            "value_type",
            "size"
        ),
        tables=(
            "table_number",
            "nunique"
        ),
        mean_dispersion=(
            "value_type",
            lambda x:
                (x == "MEAN_DISPERSION").sum()
        ),
        numeric_only=(
            "value_type",
            lambda x:
                (x == "NUMERIC_ONLY").sum()
        ),
        controls=(
            "arm_signal",
            lambda x:
                (x == "CONTROL").sum()
        )
    )
    .reset_index()
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# SALIDA
# ==========================================================

print("\nFilas candidatas:", len(df))
print("Duplicados eliminados:", removed)

print("\n==========================================")
print("TIPO DE VALOR")
print("==========================================\n")

print(
    df["value_type"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("SEÑAL DE BRAZO")
print("==========================================\n")

print(
    df["arm_signal"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("SEÑAL DE MÉTRICA")
print("==========================================\n")

print(
    df["metric_signal"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("POR ESTUDIO")
print("==========================================\n")

print(
    summary.to_string(
        index=False
    )
)


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_CSV)
print(OUT_SUMMARY)
