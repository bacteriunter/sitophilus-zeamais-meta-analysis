#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

CORE = (
    PROJECT / "05_extraction/mortality/analytic/"
    "mortality_analytic_initial.csv"
)

TABLES = (
    PROJECT / "05_extraction/mortality/structured/"
    "mortality_table_structure.csv"
)

OUTDIR = PROJECT / "05_extraction/mortality/analytic"
OUTPUT = OUTDIR / "mortality_analytic_expanded.csv"
SUMMARY = OUTDIR / "mortality_analytic_expanded_summary.csv"

PM = re.compile(
    r"(\d+(?:\.\d+)?)\s*±\s*"
    r"(\d*(?:\.\d+)?)"
)


def get_table(df, study, table):

    x = df[
        (df["study_record_id"].astype(str) == study) &
        (df["table_number"].astype(str) == str(table))
    ]

    if len(x) == 0:
        raise ValueError(
            f"No encontrada: {study} Table {table}"
        )

    return x.iloc[0]


def add(
    records,
    study,
    table,
    title,
    treatment,
    dose,
    dose_unit,
    time_h,
    mean=None,
    dispersion=None,
    dispersion_type=None,
    arm="NATURAL_TREATMENT",
    formulation=None,
    outcome_scale="PERCENT_MORTALITY",
    total_n=None,
    deaths=None,
):

    records.append({
        "study_record_id": study,
        "table_number": str(table),
        "title": title,
        "treatment": treatment,
        "formulation": formulation,
        "dose": dose,
        "dose_unit": dose_unit,
        "time_h": time_h,
        "mortality_mean": mean,
        "dispersion_value": dispersion,
        "dispersion_type": dispersion_type,
        "arm_type": arm,
        "outcome_scale": outcome_scale,
        "total_n": total_n,
        "deaths": deaths
    })


# ==========================================================
# CARGAR
# ==========================================================

core = pd.read_csv(CORE)
tables = pd.read_csv(TABLES)

records = []

print("\n==========================================")
print("EXPANSIÓN DEL DATASET DE MORTALIDAD")
print("==========================================\n")


# ==========================================================
# SZ_00401 TABLE 1
# Clove powder
# 96 h
# SEM, cuatro réplicas
# ==========================================================

r = get_table(tables, "SZ_00401", 1)

section = None

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    if line.startswith("Resistant maize"):
        section = "Resistant maize"
        continue

    if line.startswith("Moderately-resistant maize"):
        section = "Moderately-resistant maize"
        continue

    if section is None:
        continue

    # natural treatment
    m = re.match(r"^(1\.00|1\.50|2\.00)\s+", line)

    if m:

        vals = PM.findall(line)

        if len(vals) >= 4:

            mean, sem = vals[3]

            add(
                records,
                "SZ_00401",
                1,
                r["title"],
                f"Syzygium aromaticum powder - {section}",
                float(m.group(1)),
                "% w/w",
                96,
                float(mean),
                float(sem),
                "SE",
                formulation="powder"
            )

        continue

    # synthetic
    if line.startswith("Permethrin"):

        vals = PM.findall(line)

        if len(vals) >= 4:

            mean, sem = vals[3]

            add(
                records,
                "SZ_00401",
                1,
                r["title"],
                f"Permethrin - {section}",
                None,
                None,
                96,
                float(mean),
                float(sem),
                "SE",
                arm="SYNTHETIC_POSITIVE_CONTROL"
            )

        continue

    # negative control
    if line.startswith("Control"):

        vals = PM.findall(line)

        if len(vals) >= 4:

            mean, sem = vals[3]

            add(
                records,
                "SZ_00401",
                1,
                r["title"],
                f"Untreated control - {section}",
                0,
                None,
                96,
                float(mean),
                float(sem),
                "SE",
                arm="NEGATIVE_CONTROL"
            )


# ==========================================================
# SZ_00668 TABLE 2
# O. gratissimum ethanolic extract
# direct event counts
# 72 h
# ==========================================================

r = get_table(tables, "SZ_00668", 2)

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    m = re.match(
        r"^(0|30|150|250|750)\s+45\s+",
        line
    )

    if not m:
        continue

    nums = re.findall(
        r"\d+(?:\.\d+)?",
        line
    )

    if len(nums) < 8:
        continue

    dose = float(nums[0])
    total_n = int(float(nums[1]))

    # estructura:
    # dose n dead24 dead48 dead72 totaldead survived mortality survival

    deaths = int(float(nums[5]))
    mortality = float(nums[7])

    arm = (
        "NEGATIVE_CONTROL"
        if dose == 0
        else "NATURAL_TREATMENT"
    )

    add(
        records,
        "SZ_00668",
        2,
        r["title"],
        "Ocimum gratissimum ethanolic extract",
        dose,
        "mg/mL",
        72,
        mortality,
        None,
        "EVENT_COUNTS",
        arm=arm,
        formulation="ethanolic extract",
        outcome_scale="EVENT_PROPORTION",
        total_n=total_n,
        deaths=deaths
    )


# ==========================================================
# SZ_00668 TABLE 3
# O. gratissimum powder
# 72 h
# mean ± SD
# ==========================================================

r = get_table(tables, "SZ_00668", 3)

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    m = re.match(
        r"^(0\.0|1\.0|2\.0|3\.0|4\.0|5\.0)\s+",
        line
    )

    if not m:
        continue

    vals = PM.findall(line)

    if len(vals) < 1:
        continue

    # último par antes de survival:
    # mortalidad es el primer mean±SD de la fila
    mean, sd = vals[0]

    dose = float(m.group(1))

    arm = (
        "NEGATIVE_CONTROL"
        if dose == 0
        else "NATURAL_TREATMENT"
    )

    add(
        records,
        "SZ_00668",
        3,
        r["title"],
        "Ocimum gratissimum powder",
        dose,
        "g/20g grain",
        72,
        float(mean),
        float(sd or 0),
        "SD",
        arm=arm,
        formulation="powder"
    )


# ==========================================================
# SZ_00747
# Cryptocarya alba
# percentages + n=200
# No dispersion per treatment
# ==========================================================

r = get_table(tables, "SZ_00747", 1)

# Powder
powder = [
    (5.0, 11.2),
    (10.0, 10.0),
    (20.0, 15.4),
    (40.0, 22.9),
    (80.0, 84.6),
]

for dose, mortality in powder:

    deaths = round(200 * mortality / 100)

    add(
        records,
        "SZ_00747",
        1,
        r["title"],
        "Cryptocarya alba powder",
        dose,
        "g/kg grain",
        None,
        mortality,
        None,
        "EVENT_COUNTS_RECONSTRUCTED",
        formulation="powder",
        outcome_scale="EVENT_PROPORTION",
        total_n=200,
        deaths=deaths
    )


# Essential oil
oil = [
    (2.5, 15.5),
    (5.0, 13.0),
    (10.0, 23.0),
    (20.0, 59.5),
    (40.0, 94.0),
]

for dose, mortality in oil:

    deaths = round(200 * mortality / 100)

    add(
        records,
        "SZ_00747",
        1,
        r["title"],
        "Cryptocarya alba essential oil",
        dose,
        "mL/kg grain",
        None,
        mortality,
        None,
        "EVENT_COUNTS_RECONSTRUCTED",
        formulation="essential oil",
        outcome_scale="EVENT_PROPORTION",
        total_n=200,
        deaths=deaths
    )


# ==========================================================
# SZ_00812 TABLE 2
# Tres extractos
# seleccionar 72 h
# ==========================================================

r = get_table(tables, "SZ_00812", 2)

# Debido a que pdftotext conserva las tres plantas en
# columnas, definimos explícitamente los valores de 72 h
# observados en la tabla.

data_812 = {
    "Glycyrrhiza glabra": [
        (10, 38.18, 6.55),
        (15, 41.82, 1.81),
        (5, 60.00, 19.99),
    ],
    "Chicorium intybus": [
        (15, 69.09, 3.63),
        (10, 70.90, 9.62),
        (5, 89.90, 3.14),
    ],
    "Terminalia chebula": [
        (15, 74.54, 1.81),
        (10, 78.18, 5.45),
        (5, 81.81, 4.81),
    ],
}

for plant, rows in data_812.items():

    for dose, mean, se in rows:

        add(
            records,
            "SZ_00812",
            2,
            r["title"],
            f"{plant} extract",
            dose,
            "%",
            72,
            mean,
            se,
            "SE",
            formulation="plant extract"
        )


# ==========================================================
# SZ_00840 TABLE 1
#
# NO convertir a porcentaje.
# Son medias de mortalidad; conservamos escala original.
# Día 4.
# ==========================================================

r = get_table(tables, "SZ_00840", 1)

current_treatment = None

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    if line.startswith("Control"):

        vals = PM.findall(line)

        if len(vals) >= 4:

            mean, sd = vals[3]

            add(
                records,
                "SZ_00840",
                1,
                r["title"],
                "Untreated control",
                0,
                "ml",
                96,
                float(mean),
                float(sd),
                "SD",
                arm="NEGATIVE_CONTROL",
                outcome_scale="MEAN_COUNT"
            )

        continue

    for name in [
        "Khaya ivorensis",
        "Azadirachta indica",
        "Daksh"
    ]:
        if line.startswith(name):
            current_treatment = name
            break

    m = re.search(
        r"\b(1\.0|2\.0|3\.0)\s+",
        line
    )

    if not m or current_treatment is None:
        continue

    vals = PM.findall(line)

    if len(vals) < 4:
        continue

    mean, sd = vals[-1]

    add(
        records,
        "SZ_00840",
        1,
        r["title"],
        current_treatment,
        float(m.group(1)),
        "ml",
        96,
        float(mean),
        float(sd),
        "SD",
        formulation="oil",
        outcome_scale="MEAN_COUNT"
    )


# ==========================================================
# NUEVOS DATOS
# ==========================================================

new = pd.DataFrame(records)

print("Nuevas filas:", len(new))
print("Nuevos estudios:", new["study_record_id"].nunique())


# ==========================================================
# HOMOLOGAR COLUMNAS CON CORE
# ==========================================================

# Columnas nuevas que el core no tenía
for col in [
    "outcome_scale",
    "total_n",
    "deaths"
]:
    if col not in core.columns:
        core[col] = None

# Datos antiguos son porcentajes
core["outcome_scale"] = (
    core["outcome_scale"]
    .fillna("PERCENT_MORTALITY")
)

# quitar ID anterior para regenerarlo
if "effect_record_id" in core.columns:
    core = core.drop(columns=["effect_record_id"])

# columnas comunes
all_cols = sorted(
    set(core.columns).union(new.columns)
)

for col in all_cols:
    if col not in core.columns:
        core[col] = None
    if col not in new.columns:
        new[col] = None

combined = pd.concat(
    [
        core[all_cols],
        new[all_cols]
    ],
    ignore_index=True
)


# ==========================================================
# NUEVOS IDS
# ==========================================================

combined.insert(
    0,
    "effect_record_id",
    [
        f"MORT_{i:04d}"
        for i in range(1, len(combined) + 1)
    ]
)


# ==========================================================
# VALIDACIÓN
# ==========================================================

combined["valid_mortality_range"] = True

mask_percent = combined["outcome_scale"].isin(
    [
        "PERCENT_MORTALITY",
        "EVENT_PROPORTION"
    ]
)

combined.loc[
    mask_percent,
    "valid_mortality_range"
] = combined.loc[
    mask_percent,
    "mortality_mean"
].between(0, 100)


# ==========================================================
# GUARDAR
# ==========================================================

combined.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


summary = (
    combined.groupby("study_record_id")
    .agg(
        rows=("effect_record_id", "size"),
        natural=(
            "arm_type",
            lambda x: (x == "NATURAL_TREATMENT").sum()
        ),
        negative_controls=(
            "arm_type",
            lambda x: (x == "NEGATIVE_CONTROL").sum()
        ),
        synthetic_controls=(
            "arm_type",
            lambda x: (
                x == "SYNTHETIC_POSITIVE_CONTROL"
            ).sum()
        ),
        outcome_scales=(
            "outcome_scale",
            lambda x: ",".join(sorted(set(x.dropna())))
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
print("RESULTADO EXPANDIDO")
print("==========================================\n")

print("Filas totales:", len(combined))
print(
    "Estudios totales:",
    combined["study_record_id"].nunique()
)

print("\nTipo de brazo:")
print(
    combined["arm_type"]
    .value_counts()
    .to_string()
)

print("\nEscalas:")
print(
    combined["outcome_scale"]
    .value_counts()
    .to_string()
)

print(
    "\nRangos inválidos:",
    (~combined["valid_mortality_range"]).sum()
)

print("\n==========================================")
print("RESUMEN POR ESTUDIO")
print("==========================================\n")

print(summary.to_string(index=False))

print("\n==========================================")
print("NUEVOS ESTUDIOS")
print("==========================================\n")

check = (
    new.groupby(
        [
            "study_record_id",
            "treatment",
            "formulation",
            "outcome_scale"
        ],
        dropna=False
    )
    .agg(
        n=("mortality_mean", "size"),
        min_dose=("dose", "min"),
        max_dose=("dose", "max"),
        min_outcome=("mortality_mean", "min"),
        max_outcome=("mortality_mean", "max")
    )
    .reset_index()
)

print(check.to_string(index=False))

print(f"\nDataset:\n{OUTPUT}")
print(f"\nResumen:\n{SUMMARY}")
