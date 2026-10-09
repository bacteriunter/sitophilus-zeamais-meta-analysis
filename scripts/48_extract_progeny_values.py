#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

VALIDATED = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/final/"
    "progeny_tables_validated.csv"
)

EVIDENCE = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/final/"
    "progeny_tables_validated_evidence.txt"
)

OUTDIR = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/final"
)

OUT = OUTDIR / "progeny_values_extracted.csv"
SUMMARY = OUTDIR / "progeny_values_extracted_summary.csv"


# ==========================================================
# TABLAS VÁLIDAS
# ==========================================================

tab = pd.read_csv(VALIDATED)

tab = tab[
    tab["final_status"].isin(
        ["VALID_STRONG", "VALID"]
    )
].copy()

# Exclusión ya establecida por alcance:
# X-ray irradiation
tab = tab[
    tab["study_record_id"] != "SZ_00213"
].copy()


# ==========================================================
# LEER EVIDENCIA
# ==========================================================

text = EVIDENCE.read_text(
    encoding="utf-8",
    errors="ignore"
)


# ==========================================================
# SEPARAR BLOQUES
# ==========================================================

pattern = re.compile(
    r"={50,}\s*"
    r"(SZ_\d{5})\s*\|\s*TABLE\s*(\d+)\s*\|"
    r"\s*([^|]+)\|\s*([^|]+)\|\s*([^=\n]+)"
    r"\s*={50,}"
    r"(.*?)(?="
    r"={50,}\s*SZ_\d{5}\s*\|\s*TABLE|\Z)",
    re.I | re.S
)

blocks = {}

for m in pattern.finditer(text):

    study = m.group(1).strip()
    table = m.group(2).strip()

    block = m.group(6)

    blocks[(study, table)] = block


# ==========================================================
# PATRONES NUMÉRICOS
# ==========================================================

PM = re.compile(
    r"(?<![\d.])"
    r"(\d+(?:\.\d+)?)"
    r"\s*±\s*"
    r"(\d+(?:\.\d+)?)"
)

NUMBER = re.compile(
    r"(?<![A-Za-z0-9.])"
    r"\d+(?:\.\d+)?"
    r"(?![A-Za-z0-9.])"
)

CONTROL = re.compile(
    r"\b(?:untreated|control|negative control|check)\b",
    re.I
)

SYNTHETIC = re.compile(
    r"\b(?:"
    r"permethrin|malathion|pirimiphos|"
    r"dichlorvos|ddvp|gredox|"
    r"synthetic insecticide"
    r")\b",
    re.I
)

ANALYSIS_ROW = re.compile(
    r"\b(?:"
    r"F\s*\(?\d|"
    r"F-value|"
    r"P-value|"
    r"LSD|"
    r"ANOVA|"
    r"EC50|"
    r"LC50|"
    r"LD50|"
    r"df"
    r")\b",
    re.I
)


# ==========================================================
# EXTRAER SEGMENTOS
# ==========================================================

records = []

for _, r in tab.iterrows():

    study = r["study_record_id"]
    table_num = str(r["table_number"])
    metric = r["metric"]
    dispersion_type = r["dispersion"]

    block = blocks.get(
        (study, table_num),
        ""
    )

    if not block:
        continue


    # ------------------------------------------------------
    # Dividir el texto de tabla en segmentos
    # ------------------------------------------------------

    segments = re.split(
        r"\n+|(?<=[.;])\s+",
        block
    )

    segment_index = 0

    for seg in segments:

        seg = re.sub(
            r"\s+",
            " ",
            seg
        ).strip()

        if not seg:
            continue

        # Evitar líneas puramente estadísticas
        if ANALYSIS_ROW.search(seg):
            continue

        pm_values = list(
            PM.finditer(seg)
        )

        nums = NUMBER.findall(seg)

        if not pm_values and len(nums) < 2:
            continue

        segment_index += 1


        # --------------------------------------------------
        # Clasificación preliminar del brazo
        # --------------------------------------------------

        if SYNTHETIC.search(seg):
            arm_signal = "SYNTHETIC_POSITIVE"

        elif CONTROL.search(seg):
            arm_signal = "NEGATIVE_CONTROL"

        else:
            arm_signal = "NATURAL_CANDIDATE"


        # --------------------------------------------------
        # Valores media ± dispersión
        # --------------------------------------------------

        if pm_values:

            for j, pm in enumerate(
                pm_values,
                start=1
            ):

                mean = float(
                    pm.group(1)
                )

                disp = float(
                    pm.group(2)
                )

                records.append({

                    "study_record_id":
                        study,

                    "table_number":
                        table_num,

                    "table_metric":
                        metric,

                    "dispersion_type":
                        dispersion_type,

                    "segment_index":
                        segment_index,

                    "value_index":
                        j,

                    "value_type":
                        "MEAN_DISPERSION",

                    "mean":
                        mean,

                    "dispersion":
                        disp,

                    "arm_signal":
                        arm_signal,

                    "raw_segment":
                        seg[:1500]
                })


        # --------------------------------------------------
        # Valores sin ±
        # --------------------------------------------------

        else:

            records.append({

                "study_record_id":
                    study,

                "table_number":
                    table_num,

                "table_metric":
                    metric,

                "dispersion_type":
                    dispersion_type,

                "segment_index":
                    segment_index,

                "value_index":
                    1,

                "value_type":
                    "NUMERIC_ONLY",

                "mean":
                    None,

                "dispersion":
                    None,

                "arm_signal":
                    arm_signal,

                "raw_segment":
                    seg[:1500]
            })


# ==========================================================
# DATAFRAME
# ==========================================================

out = pd.DataFrame(records)

if out.empty:

    print(
        "\nNo se extrajeron valores."
    )
    raise SystemExit


# ==========================================================
# ELIMINAR DUPLICADOS
# ==========================================================

before = len(out)

out = out.drop_duplicates(
    subset=[
        "study_record_id",
        "table_number",
        "mean",
        "dispersion",
        "arm_signal",
        "raw_segment"
    ]
).copy()

removed = before - len(out)


# ==========================================================
# CONTROL DE RANGO
# ==========================================================

out["value_plausible"] = True

# Para conteos F1 no imponemos máximo 100.
# Solo descartamos valores negativos, que no deberían existir.
out.loc[
    out["mean"].notna()
    & (out["mean"] < 0),
    "value_plausible"
] = False


# ==========================================================
# GUARDAR
# ==========================================================

out.to_csv(
    OUT,
    index=False,
    encoding="utf-8"
)


summary = (
    out.groupby(
        [
            "study_record_id",
            "table_number",
            "table_metric"
        ],
        dropna=False
    )
    .agg(
        candidate_values=(
            "value_type",
            "size"
        ),
        mean_dispersion_values=(
            "value_type",
            lambda x:
                (x == "MEAN_DISPERSION").sum()
        ),
        numeric_only=(
            "value_type",
            lambda x:
                (x == "NUMERIC_ONLY").sum()
        ),
        control_signals=(
            "arm_signal",
            lambda x:
                (x == "NEGATIVE_CONTROL").sum()
        ),
        synthetic_signals=(
            "arm_signal",
            lambda x:
                (x == "SYNTHETIC_POSITIVE").sum()
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
# SALIDA
# ==========================================================

print("\n==========================================")
print("EXTRACCIÓN NUMÉRICA F1")
print("==========================================\n")

print(
    "Estudios incluidos:",
    out["study_record_id"].nunique()
)

print(
    "Tablas:",
    out[
        [
            "study_record_id",
            "table_number"
        ]
    ].drop_duplicates().shape[0]
)

print(
    "Filas candidatas:",
    len(out)
)

print(
    "Duplicados eliminados:",
    removed
)


print("\n==========================================")
print("TIPO DE VALOR")
print("==========================================\n")

print(
    out["value_type"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("MÉTRICA")
print("==========================================\n")

print(
    out["table_metric"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("DISPERSIÓN")
print("==========================================\n")

print(
    out["dispersion_type"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("SEÑAL DE BRAZO")
print("==========================================\n")

print(
    out["arm_signal"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("POR TABLA")
print("==========================================\n")

print(
    summary.to_string(
        index=False
    )
)


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT)
print(SUMMARY)
