#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT / "05_extraction/mortality/structured/"
    "mortality_table_structure.csv"
)

OUTDIR = PROJECT / "05_extraction/mortality/analytic"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "mortality_analytic_initial.csv"
SUMMARY = OUTDIR / "mortality_analytic_summary.csv"

PM = re.compile(
    r"(\d+(?:\.\d+)?)\s*±\s*(\d+(?:\.\d+)?)"
)


def get_table(df, study, table):
    x = df[
        (df["study_record_id"].astype(str) == study) &
        (df["table_number"].astype(str) == str(table))
    ]

    if len(x) == 0:
        raise ValueError(f"No encontrada: {study} Table {table}")

    return x.iloc[0]


def add_record(
    records,
    study,
    table,
    title,
    treatment,
    dose,
    dose_unit,
    time_h,
    mean,
    dispersion,
    dispersion_type,
    arm_type="NATURAL_TREATMENT",
    formulation=None,
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
        "mortality_mean": float(mean),
        "dispersion_value": float(dispersion),
        "dispersion_type": dispersion_type,
        "arm_type": arm_type
    })


df = pd.read_csv(INPUT)

records = []

print("\n==========================================")
print("DATASET ANALÍTICO CORREGIDO")
print("==========================================\n")


# ==========================================================
# SZ_00071 TABLE 4
# 14 días únicamente
# 5 productos en columnas
# ==========================================================

r = get_table(df, "SZ_00071", 4)

products = [
    "Plectranthus glandulosus",
    "Hymenocardia acida wood ash",
    "25PG75HA",
    "50PG50HA",
    "75PG25HA",
]

in_14_day = False

for raw in str(r["table_text"]).splitlines():

    line = raw.strip()

    if re.match(r"^14\s+days?", line, re.I):
        in_14_day = True
        continue

    if not in_14_day:
        continue

    if line.startswith("F("):
        break

    m = re.match(r"^(0|5|10|20|40)\s+", line)

    if not m:
        continue

    dose = float(m.group(1))
    vals = PM.findall(line)

    if len(vals) != 5:
        continue

    for product, (mean, se) in zip(products, vals):

        arm = (
            "NEGATIVE_CONTROL"
            if dose == 0
            else "NATURAL_TREATMENT"
        )

        add_record(
            records,
            "SZ_00071",
            4,
            r["title"],
            product,
            dose,
            "g/kg",
            336,
            mean,
            se,
            "SE",
            arm
        )

# ==========================================================
# SZ_00124 TABLE 1
# Cow Horn Ash
# Mortalidad al día 7
# Dosis confirmadas: 2, 4 y 6
# ==========================================================

r = get_table(df, "SZ_00124", 1)

cha_doses = [2.0, 4.0, 6.0]
cha_index = 0

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()
    vals = PM.findall(line)

    # ----------------------------------------------
    # Cow Horn Ash
    # ----------------------------------------------

    if (
        cha_index < 3
        and vals
        and (
            line.startswith("CHA ")
            or re.match(r"^(4(?:\.0)?|6(?:\.0)?)\s+", line)
        )
    ):

        # Mortalidad: días 3, 5 y 7.
        # Tomamos día 7 = tercer valor.
        if len(vals) >= 3:

            mean, sd = vals[2]

            add_record(
                records,
                "SZ_00124",
                1,
                r["title"],
                "Cow Horn Ash",
                cha_doses[cha_index],
                "g/100g",
                168,
                mean,
                sd,
                "SD",
                "NATURAL_TREATMENT"
            )

            cha_index += 1

        continue

    # ----------------------------------------------
    # Permethrin
    # ----------------------------------------------

    if line.startswith("Permethrin") and len(vals) >= 3:

        mean, sd = vals[2]

        add_record(
            records,
            "SZ_00124",
            1,
            r["title"],
            "Permethrin",
            0.6,
            "g/100g",
            168,
            mean,
            sd,
            "SD",
            "SYNTHETIC_POSITIVE_CONTROL"
        )

        continue

    # ----------------------------------------------
    # Control negativo
    # ----------------------------------------------

    if line.startswith("CON ") and len(vals) >= 3:

        mean, sd = vals[2]

        add_record(
            records,
            "SZ_00124",
            1,
            r["title"],
            "Untreated control",
            0.0,
            "g/100g",
            168,
            mean,
            sd,
            "SD",
            "NEGATIVE_CONTROL"
        )

# ==========================================================
# SZ_00288 TABLE 3
# 14 días
# ==========================================================

r = get_table(df, "SZ_00288", 3)

current_extract = None

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    if line.startswith("Control"):
        vals = PM.findall(line)
        if vals:
            mean, se = vals[-1]
            add_record(
                records, "SZ_00288", 3, r["title"],
                "Untreated control", 0, None, 336,
                mean, se, "SE", "NEGATIVE_CONTROL"
            )
        continue

    m = re.match(
        r"^(Aqueous|Ethanol|Methanol|N-Hexene)\s+"
        r"(\d+(?:\.\d+)?)",
        line,
        re.I
    )

    if m:
        current_extract = m.group(1)
        dose = float(m.group(2))
    else:
        m = re.match(r"^(\d+(?:\.\d+)?)\s+", line)
        if not m or current_extract is None:
            continue
        dose = float(m.group(1))

    vals = PM.findall(line)

    if len(vals) < 5:
        continue

    mean, se = vals[-1]

    add_record(
        records,
        "SZ_00288",
        3,
        r["title"],
        f"Tithonia diversifolia - {current_extract}",
        dose,
        "ml",
        336,
        mean,
        se,
        "SE"
    )


# ==========================================================
# SZ_00549 TABLE 2
# 12 días
# ==========================================================

r = get_table(df, "SZ_00549", 2)

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    if line.startswith("Control"):
        vals = PM.findall(line)
        if len(vals) >= 3:
            mean, se = vals[-1]
            add_record(
                records, "SZ_00549", 2, r["title"],
                "Untreated control", 0, "g/kg", 288,
                mean, se, "SE", "NEGATIVE_CONTROL"
            )
        continue

    m = re.match(r"^(20|40|60|80)\s+", line)

    if not m:
        continue

    vals = PM.findall(line)

    if len(vals) < 3:
        continue

    mean, se = vals[-1]

    add_record(
        records, "SZ_00549", 2, r["title"],
        "Wedelia trilobata powder",
        float(m.group(1)), "g/kg", 288,
        mean, se, "SE"
    )


# ==========================================================
# SZ_00549 TABLE 4
# 24 h; detener antes de F1
# ==========================================================

r = get_table(df, "SZ_00549", 4)

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    if line.startswith("Effect on F1"):
        break

    if line.startswith("Control"):
        vals = PM.findall(line)
        if len(vals) >= 2:
            mean, se = vals[-1]
            add_record(
                records, "SZ_00549", 4, r["title"],
                "Untreated control", 0, "uL/L air", 24,
                mean, se, "SE", "NEGATIVE_CONTROL"
            )
        continue

    m = re.match(r"^(50|100|150|200|250)\s+", line)

    if not m:
        continue

    vals = PM.findall(line)

    if len(vals) < 2:
        continue

    mean, se = vals[-1]

    add_record(
        records, "SZ_00549", 4, r["title"],
        "Wedelia trilobata essential oil",
        float(m.group(1)), "uL/L air", 24,
        mean, se, "SE",
        formulation="fumigation"
    )


# ==========================================================
# SZ_00600 TABLE 1
# powder, 120 h
# ==========================================================

r = get_table(df, "SZ_00600", 1)

current_dose = None

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    m = re.match(
        r"^(Leaf|Stem|Root)\s+(0\.1|0\.3|0\.6|0\.9|1\.5)\s+",
        line
    )

    if m:
        part = m.group(1)
        current_dose = float(m.group(2))

    else:
        m = re.match(r"^(Leaf|Stem|Root)\s+", line)
        if not m or current_dose is None:
            continue
        part = m.group(1)

    vals = PM.findall(line)

    if len(vals) < 5:
        continue

    mean, disp = vals[-1]

    add_record(
        records, "SZ_00600", 1, r["title"],
        f"Coleus amboinicus {part}",
        current_dose, "g", 120,
        mean, disp, "SE",
        formulation="powder"
    )

# controles T1
add_record(
    records, "SZ_00600", 1, r["title"],
    "Dichlorvos", 0.05, None, 120,
    100, 0, "SE", "SYNTHETIC_POSITIVE_CONTROL"
)

add_record(
    records, "SZ_00600", 1, r["title"],
    "Untreated control", 0, None, 120,
    0, 0, "SE", "NEGATIVE_CONTROL"
)


# ==========================================================
# SZ_00600 TABLE 3
# crude extracts, 120 h
# dosis heredada por bloques Leaf/Stem/Root
# ==========================================================

r = get_table(df, "SZ_00600", 3)

dose_sequence = [0.1, 0.3, 0.6, 0.9, 1.5]
dose_index = 0
block_parts = []

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    if line.startswith("Positive Control") or line.startswith("Control "):
        continue

    m = re.match(r"^(Leaf|Stem|Root)(?:\s+(\d+(?:\.\d+)?))?\s+", line)

    if not m:
        continue

    part = m.group(1)

    if not block_parts:
        current_dose = dose_sequence[dose_index]

    vals = PM.findall(line)

    if len(vals) < 5:
        continue

    mean, se = vals[-1]

    add_record(
        records, "SZ_00600", 3, r["title"],
        f"Coleus amboinicus {part}",
        current_dose, "ml", 120,
        mean, se, "SE",
        formulation="crude extract/contact"
    )

    block_parts.append(part)

    if len(block_parts) == 3:
        block_parts = []
        dose_index += 1
        if dose_index >= len(dose_sequence):
            dose_index = len(dose_sequence) - 1

add_record(
    records, "SZ_00600", 3, r["title"],
    "Dichlorvos", 0.05, None, 120,
    100, 0, "SE", "SYNTHETIC_POSITIVE_CONTROL"
)

add_record(
    records, "SZ_00600", 3, r["title"],
    "Untreated control", 0, None, 120,
    0, 0, "SE", "NEGATIVE_CONTROL"
)


# ==========================================================
# SZ_00600 TABLE 5
# powder + extract, 96 h
# ==========================================================

r = get_table(df, "SZ_00600", 5)

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    m = re.match(
        r"^(Leaf|Stem|Root)\s+"
        r"(0\.1|0\.3|0\.6|0\.9|1\.5)\s+",
        line
    )

    if not m:
        continue

    part = m.group(1)
    dose = float(m.group(2))

    vals = PM.findall(line)

    if len(vals) != 2:
        continue

    # columna 1 = powder
    mean, se = vals[0]

    add_record(
        records, "SZ_00600", 5, r["title"],
        f"Coleus amboinicus {part}",
        dose, "g", 96,
        mean, se, "SE",
        formulation="powder/fumigation"
    )

    # columna 2 = extract
    mean, se = vals[1]

    add_record(
        records, "SZ_00600", 5, r["title"],
        f"Coleus amboinicus {part}",
        dose, "ml", 96,
        mean, se, "SE",
        formulation="extract/fumigation"
    )

add_record(
    records, "SZ_00600", 5, r["title"],
    "Dichlorvos", 0.05, None, 96,
    100, 0, "SE", "SYNTHETIC_POSITIVE_CONTROL"
)

add_record(
    records, "SZ_00600", 5, r["title"],
    "Untreated control", 0, None, 96,
    0, 0, "SE", "NEGATIVE_CONTROL"
)


# ==========================================================
# SZ_00424 TABLE 2
# cinco productos independientes
# ==========================================================

r = get_table(df, "SZ_00424", 2)

sections = [
    ("L. lanceolata", "g/kg"),
    ("H. acida", "g/kg"),
    ("A. indica", "ml/kg"),
    ("L. lanceolata + A. indica", "g/kg"),
    ("H. acida + A. indica", "g/kg"),
]

current_product = None
current_unit = None

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    if line.startswith("L. lanceolata (g/kg) + A. indica"):
        current_product = "L. lanceolata + A. indica"
        current_unit = "g/kg"
        continue

    if line.startswith("H. acida (g/kg) + A. indica"):
        current_product = "H. acida + A. indica"
        current_unit = "g/kg"
        continue

    if line.startswith("L. lanceolata (g/kg)"):
        current_product = "L. lanceolata"
        current_unit = "g/kg"
        continue

    if line.startswith("H. acida (g/kg)"):
        current_product = "H. acida"
        current_unit = "g/kg"
        continue

    if line.startswith("A. Indica (ml/kg)"):
        current_product = "A. indica"
        current_unit = "ml/kg"
        continue

    if current_product is None:
        continue

    m = re.match(r"^(0|0\.4|2|4|6|20|40)\s+", line)

    if not m:
        continue

    vals = PM.findall(line)

    if len(vals) < 4:
        continue

    dose = float(m.group(1))
    mean, se = vals[3]

    arm = (
        "NEGATIVE_CONTROL"
        if dose == 0
        else "NATURAL_TREATMENT"
    )

    add_record(
        records, "SZ_00424", 2, r["title"],
        current_product,
        dose,
        current_unit,
        336,
        mean,
        se,
        "SE",
        arm
    )


# ==========================================================
# SZ_00802 TABLE 1
#
# IMPORTANTE:
# columnas = cuatro plantas.
# El script anterior tomaba solo la última.
# ==========================================================

r = get_table(df, "SZ_00802", 1)

plants = [
    "Azadirachta indica",
    "Plectranthus glandulosus",
    "Steganotaenia araliacea",
    "Annona senegalensis",
]

for raw in str(r["table_text"]).splitlines():

    line = re.sub(r"\s+", " ", raw).strip()

    m = re.match(r"^(0|5|10|20|40)\s+", line)

    if not m:
        continue

    dose = float(m.group(1))
    vals = PM.findall(line)

    if len(vals) != 4:
        continue

    for plant, (mean, se) in zip(plants, vals):

        arm = (
            "NEGATIVE_CONTROL"
            if dose == 0
            else "NATURAL_TREATMENT"
        )

        add_record(
            records, "SZ_00802", 1, r["title"],
            plant,
            dose,
            "g/kg",
            336,
            mean,
            se,
            "SE",
            arm,
            formulation="powder"
        )


# ==========================================================
# CREAR DATASET
# ==========================================================

out = pd.DataFrame(records)

out = out.drop_duplicates().copy()

out["valid_range"] = (
    out["mortality_mean"].between(0, 100) &
    out["dispersion_value"].between(0, 100)
)

out["analytic_candidate"] = (
    out["valid_range"] &
    (out["arm_type"] != "SYNTHETIC_POSITIVE_CONTROL")
)


# ==========================================================
# IDS
# ==========================================================

out.insert(
    0,
    "effect_record_id",
    [
        f"MORT_{i:04d}"
        for i in range(1, len(out) + 1)
    ]
)


# ==========================================================
# GUARDAR
# ==========================================================

out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

summary = (
    out.groupby("study_record_id")
    .agg(
        n_rows=("effect_record_id", "size"),
        natural_rows=(
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
        treatments=("treatment", "nunique"),
        times=("time_h", "nunique")
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
print("RESULTADO CORREGIDO")
print("==========================================\n")

print("Filas:", len(out))
print("Estudios:", out["study_record_id"].nunique())

print("\nTipo de brazo:")
print(out["arm_type"].value_counts().to_string())

print("\nTipo de dispersión:")
print(out["dispersion_type"].value_counts().to_string())

print("\nRangos inválidos:", (~out["valid_range"]).sum())

print("\n==========================================")
print("RESUMEN")
print("==========================================\n")

print(summary.to_string(index=False))

print("\n==========================================")
print("CONTROL POR TRATAMIENTO")
print("==========================================\n")

check = (
    out[
        out["arm_type"] == "NATURAL_TREATMENT"
    ]
    .groupby(
        [
            "study_record_id",
            "table_number",
            "treatment",
            "formulation"
        ],
        dropna=False
    )
    .agg(
        n=("effect_record_id", "size"),
        min_dose=("dose", "min"),
        max_dose=("dose", "max"),
        min_mortality=("mortality_mean", "min"),
        max_mortality=("mortality_mean", "max")
    )
    .reset_index()
)

print(check.to_string(index=False))

print(f"\nDataset:\n{OUTPUT}")
print(f"\nResumen:\n{SUMMARY}")
