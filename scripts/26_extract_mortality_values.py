#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "structured" /
    "mortality_table_structure.csv"
)

DISPERSION = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "dispersion" /
    "dispersion_classification.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "values"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = OUTDIR / "mortality_values_raw.csv"
SUMMARY = OUTDIR / "mortality_values_summary.csv"


# ==========================================================
# PATRONES
# ==========================================================

pm_pattern = re.compile(
    r"(?P<mean>\d+(?:\.\d+)?)"
    r"\s*(?:±|\+/-|\+-)\s*"
    r"(?P<disp>\d+(?:\.\d+)?)",
    re.I
)

percent_pattern = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*%",
    re.I
)

synthetic_pattern = re.compile(
    r"\b("
    r"permethrin|"
    r"dichlorvos|"
    r"ddvp|"
    r"deltamethrin|"
    r"malathion|"
    r"cypermethrin|"
    r"pirimiphos|"
    r"phosphine"
    r")\b",
    re.I
)

negative_control_pattern = re.compile(
    r"\b("
    r"untreated control|"
    r"negative control|"
    r"control|"
    r"\bcon\b"
    r")\b",
    re.I
)

temperature_pattern = re.compile(
    r"(?:temp(?:erature)?\.?\s*[=:≈~]?\s*)?"
    r"\d+(?:\.\d+)?\s*±\s*"
    r"\d+(?:\.\d+)?\s*°?\s*C",
    re.I
)

humidity_pattern = re.compile(
    r"(?:r\.?\s*h\.?|relative humidity)"
    r".{0,20}"
    r"\d+(?:\.\d+)?\s*±\s*"
    r"\d+(?:\.\d+)?\s*%",
    re.I
)

statistical_line = re.compile(
    r"^\s*("
    r"F\s*[\(\d]|"
    r"F-test|"
    r"ANOVA|"
    r"analysis of variance|"
    r"mean[s]?\s+followed|"
    r"values?\s+are|"
    r"each datum|"
    r"note[s]?:"
    r")",
    re.I
)


# ==========================================================
# CARGAR DATOS
# ==========================================================

tables = pd.read_csv(INPUT)

disp = pd.read_csv(
    DISPERSION
)

disp_map = dict(
    zip(
        disp["study_record_id"],
        disp["dispersion_type"]
    )
)


# ==========================================================
# SELECCIONAR TABLAS UTILIZABLES
# ==========================================================

usable_structures = [
    "MEAN_DISPERSION_TIME",
    "MEAN_DISPERSION_NO_TIME",
    "EVENT_COUNTS"
]

tables = tables[
    tables["structure"].isin(
        usable_structures
    )
].copy()


# ==========================================================
# EXCLUSIÓN ESPECÍFICA CONFIRMADA
# ==========================================================

tables = tables[
    ~(
        (tables["study_record_id"] == "SZ_00424")
        &
        (tables["table_number"].astype(str) == "3")
    )
].copy()


print("\n==========================================")
print("EXTRACCIÓN DE VALORES DE MORTALIDAD")
print("==========================================\n")

print(
    f"Tablas objetivo: {len(tables)}"
)

print(
    f"Estudios: "
    f"{tables['study_record_id'].nunique()}"
)


# ==========================================================
# EXTRAER
# ==========================================================

records = []


for _, row in tables.iterrows():

    study = str(
        row["study_record_id"]
    )

    table_number = str(
        row["table_number"]
    )

    text = str(
        row["table_text"]
    )

    structure = str(
        row["structure"]
    )

    dispersion_type = disp_map.get(
        study,
        "UNKNOWN"
    )


    for line_number, raw_line in enumerate(
        text.splitlines(),
        start=1
    ):

        line = re.sub(
            r"\s+",
            " ",
            raw_line
        ).strip()

        if not line:
            continue

        if statistical_line.search(line):
            continue

        # ------------------------------------------
        # Excluir condiciones ambientales
        # ------------------------------------------

        temp = bool(
            temperature_pattern.search(
                line
            )
        )

        humidity = bool(
            humidity_pattern.search(
                line
            )
        )

        if temp or humidity:
            continue


        # ------------------------------------------
        # Media ± dispersión
        # ------------------------------------------

        matches = list(
            pm_pattern.finditer(
                line
            )
        )

        for value_number, match in enumerate(
            matches,
            start=1
        ):

            mean = float(
                match.group("mean")
            )

            dispersion_value = float(
                match.group("disp")
            )

            # mortalidad debe estar entre 0 y 100
            if not (
                0 <= mean <= 100
            ):
                continue

            # dispersión absurda para porcentaje
            if dispersion_value > 100:
                continue


            # --------------------------------------
            # Tipo de dispersión
            # --------------------------------------

            if dispersion_type == "SD":

                dtype = "SD"

            elif dispersion_type == "SE":

                dtype = "SE"

            elif dispersion_type == "CI_ONLY":

                dtype = "UNKNOWN"

            elif dispersion_type == "PLUSMINUS_UNKNOWN":

                dtype = "UNKNOWN"

            elif dispersion_type == "MIXED_SD_SE":

                dtype = "MIXED_UNKNOWN"

            else:

                dtype = "UNKNOWN"


            # --------------------------------------
            # Control
            # --------------------------------------

            is_negative_control = bool(
                negative_control_pattern.search(
                    line
                )
            )

            is_synthetic = bool(
                synthetic_pattern.search(
                    line
                )
            )


            if is_synthetic:

                arm_type = (
                    "SYNTHETIC_POSITIVE_CONTROL"
                )

            elif is_negative_control:

                arm_type = (
                    "NEGATIVE_CONTROL"
                )

            else:

                arm_type = (
                    "CANDIDATE_TREATMENT"
                )


            records.append({

                "study_record_id":
                    study,

                "title":
                    row["title"],

                "table_number":
                    table_number,

                "structure":
                    structure,

                "line_number":
                    line_number,

                "value_number":
                    value_number,

                "mortality_mean":
                    mean,

                "dispersion_value":
                    dispersion_value,

                "dispersion_type":
                    dtype,

                "arm_type":
                    arm_type,

                "line_text":
                    line,

                "source_type":
                    "MEAN_DISPERSION"
            })


        # ------------------------------------------
        # EVENT_COUNTS:
        # conservar líneas numéricas aunque
        # no tengan ± para parser posterior
        # ------------------------------------------

        if (
            structure == "EVENT_COUNTS"
            and len(matches) == 0
        ):

            nums = re.findall(
                r"\b\d+(?:\.\d+)?\b",
                line
            )

            if len(nums) >= 3:

                records.append({

                    "study_record_id":
                        study,

                    "title":
                        row["title"],

                    "table_number":
                        table_number,

                    "structure":
                        structure,

                    "line_number":
                        line_number,

                    "value_number":
                        1,

                    "mortality_mean":
                        None,

                    "dispersion_value":
                        None,

                    "dispersion_type":
                        "EVENT_COUNTS",

                    "arm_type":
                        (
                            "NEGATIVE_CONTROL"
                            if negative_control_pattern.search(line)
                            else "CANDIDATE_TREATMENT"
                        ),

                    "line_text":
                        line,

                    "source_type":
                        "EVENT_COUNT_ROW"
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
        "line_number",
        "value_number",
        "mortality_mean",
        "dispersion_value",
        "line_text"
    ]
).copy()

duplicates = (
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
# RESUMEN
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

        extracted_records=(
            "source_type",
            "count"
        ),

        mean_dispersion_values=(
            "source_type",
            lambda x:
                (x == "MEAN_DISPERSION").sum()
        ),

        event_rows=(
            "source_type",
            lambda x:
                (x == "EVENT_COUNT_ROW").sum()
        ),

        negative_control_values=(
            "arm_type",
            lambda x:
                (x == "NEGATIVE_CONTROL").sum()
        ),

        synthetic_values=(
            "arm_type",
            lambda x:
                (
                    x ==
                    "SYNTHETIC_POSITIVE_CONTROL"
                ).sum()
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
    f"Registros extraídos: {len(out)}"
)

print(
    f"Duplicados eliminados: {duplicates}"
)

print(
    f"Estudios representados: "
    f"{out['study_record_id'].nunique()}"
)


print("\nTipo de registro:")

print(
    out[
        "source_type"
    ]
    .value_counts()
    .to_string()
)


print("\nTipo de dispersión:")

print(
    out[
        "dispersion_type"
    ]
    .value_counts()
    .to_string()
)


print("\nTipo de brazo:")

print(
    out[
        "arm_type"
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
        "mean_dispersion_values",
        ascending=False
    )
    .to_string(
        index=False
    )
)


# ==========================================================
# CONTROL DE RANGO
# ==========================================================

numeric = out[
    out["mortality_mean"].notna()
]

print("\n==========================================")
print("CONTROL DE RANGO")
print("==========================================\n")

print(
    "Mínimo:",
    numeric[
        "mortality_mean"
    ].min()
)

print(
    "Máximo:",
    numeric[
        "mortality_mean"
    ].max()
)

print(
    "Valores <0:",
    (
        numeric[
            "mortality_mean"
        ] < 0
    ).sum()
)

print(
    "Valores >100:",
    (
        numeric[
            "mortality_mean"
        ] > 100
    ).sum()
)


print(
    f"\nValores:\n{OUTPUT}"
)

print(
    f"\nResumen:\n{SUMMARY}"
)
