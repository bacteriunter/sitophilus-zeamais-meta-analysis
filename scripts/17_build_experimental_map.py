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
    "experimental_audit" /
    "EXTRACT_HIGH.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "experimental_map"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTDIR /
    "experimental_map.csv"
)


# ==========================================================
# FUNCIONES
# ==========================================================

def detect(text, pattern):

    return bool(
        re.search(
            pattern,
            text,
            flags=re.I
        )
    )


def unique_matches(text, pattern):

    matches = re.findall(
        pattern,
        text,
        flags=re.I
    )

    values = []

    for m in matches:

        if isinstance(m, tuple):
            m = m[0]

        m = str(m).strip()

        if m and m not in values:
            values.append(m)

    return values


def clean(text):

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ==========================================================
# INTERVENCIONES
# ==========================================================

botanical_pattern = (
    r"\b("
    r"essential oils?|"
    r"plant powders?|"
    r"leaf powders?|"
    r"seed powders?|"
    r"plant extracts?|"
    r"leaf extracts?|"
    r"seed extracts?|"
    r"vegetable oils?|"
    r"botanical pesticides?|"
    r"botanicals?"
    r")\b"
)

ash_pattern = (
    r"\b("
    r"wood ash|"
    r"rice husk ash|"
    r"cow dung ash|"
    r"ashes?|"
    r"diatomaceous earth|"
    r"inert dusts?|"
    r"clay|"
    r"river sand|"
    r"charcoal"
    r")\b"
)

physical_pattern = (
    r"\b("
    r"microwave|"
    r"microwave energy|"
    r"hermetic storage|"
    r"hermetic|"
    r"solar heating|"
    r"heat treatment|"
    r"cold treatment|"
    r"controlled atmosphere|"
    r"modified atmosphere"
    r")\b"
)

synthetic_pattern = (
    r"\b("
    r"deltamethrin|"
    r"permethrin|"
    r"cypermethrin|"
    r"malathion|"
    r"pirimiphos|"
    r"phosphine|"
    r"synthetic insecticide|"
    r"chemical insecticide"
    r")\b"
)


# ==========================================================
# TEMPERATURA
# ==========================================================

temp_value_pattern = (
    r"(\d{1,2}(?:\.\d+)?)\s*"
    r"(?:°\s*c|º\s*c|degrees?\s*c)"
)

temp_range_pattern = (
    r"(\d{1,2}(?:\.\d+)?)\s*"
    r"(?:-|–|to)\s*"
    r"(\d{1,2}(?:\.\d+)?)\s*"
    r"(?:°\s*c|º\s*c|degrees?\s*c)"
)

temp_factor_pattern = (
    r"\b("
    r"different temperatures|"
    r"various temperatures|"
    r"temperature treatments|"
    r"temperature levels|"
    r"temperatures of|"
    r"effect of temperature|"
    r"effects of temperature|"
    r"at temperatures|"
    r"under different temperatures"
    r")\b"
)


# ==========================================================
# HUMEDAD
# ==========================================================

rh_value_pattern = (
    r"(\d{1,3}(?:\.\d+)?)\s*%\s*"
    r"(?:RH|relative humidity)"
)

rh_factor_pattern = (
    r"\b("
    r"different relative humidities|"
    r"relative humidity levels|"
    r"humidity treatments|"
    r"different humidities|"
    r"effect of relative humidity|"
    r"effect of humidity"
    r")\b"
)


# ==========================================================
# DOSIS
# ==========================================================

dose_numeric_pattern = (
    r"(\d+(?:\.\d+)?\s*"
    r"(?:mg|g|kg|ml|µl|ul)"
    r"\s*(?:/|per\s+)"
    r"(?:g|kg|ml|l))"
)

percent_pattern = (
    r"(\d+(?:\.\d+)?\s*%)"
)


# ==========================================================
# TIEMPO
# ==========================================================

time_pattern = (
    r"(\d+(?:\.\d+)?\s*"
    r"(?:hours?|hrs?|days?|weeks?|months?))"
)


# ==========================================================
# DISEÑO / REPLICACIÓN
# ==========================================================

rep_pattern = (
    r"(\d+)\s+"
    r"(?:replicates|replications)"
)

insect_n_pattern = (
    r"(\d+)\s+"
    r"(?:adult insects|adults|"
    r"insects|weevils)"
)

grain_n_pattern = (
    r"(\d+)\s+"
    r"(?:grains|seeds)"
)


# ==========================================================
# LEER
# ==========================================================

df = pd.read_csv(INPUT)

records = []


print("\n==========================================")
print("MAPA EXPERIMENTAL")
print("==========================================\n")

print(
    f"Artículos: {len(df)}"
)


# ==========================================================
# PROCESAR
# ==========================================================

for n, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

    path = Path(
        str(row["text_file"])
    )

    if not path.exists():
        continue

    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    text = clean(text)


    # ------------------------------------------------------
    # INTERVENCIÓN
    # ------------------------------------------------------

    botanical = detect(
        text,
        botanical_pattern
    )

    natural_material = detect(
        text,
        ash_pattern
    )

    physical = detect(
        text,
        physical_pattern
    )

    synthetic = detect(
        text,
        synthetic_pattern
    )


    intervention_types = []

    if botanical:
        intervention_types.append(
            "BOTANICAL"
        )

    if natural_material:
        intervention_types.append(
            "NATURAL_MATERIAL"
        )

    if physical:
        intervention_types.append(
            "PHYSICAL"
        )

    if synthetic:
        intervention_types.append(
            "SYNTHETIC_PRESENT"
        )

    if not intervention_types:
        intervention_types.append(
            "OTHER"
        )


    # ------------------------------------------------------
    # TEMPERATURA
    # ------------------------------------------------------

    temp_values = unique_matches(
        text,
        temp_value_pattern
    )

    temp_factor_signal = detect(
        text,
        temp_factor_pattern
    )

    if (
        temp_factor_signal
        and len(temp_values) >= 2
    ):

        temperature_role = (
            "TESTED_FACTOR"
        )

    elif len(temp_values) >= 1:

        temperature_role = (
            "CONDITION"
        )

    else:

        temperature_role = (
            "UNKNOWN"
        )


    # ------------------------------------------------------
    # HUMEDAD
    # ------------------------------------------------------

    rh_values = unique_matches(
        text,
        rh_value_pattern
    )

    rh_factor_signal = detect(
        text,
        rh_factor_pattern
    )

    if (
        rh_factor_signal
        and len(rh_values) >= 2
    ):

        humidity_role = (
            "TESTED_FACTOR"
        )

    elif len(rh_values) >= 1:

        humidity_role = (
            "CONDITION"
        )

    else:

        humidity_role = (
            "UNKNOWN"
        )


    # ------------------------------------------------------
    # DOSIS
    # ------------------------------------------------------

    doses = unique_matches(
        text,
        dose_numeric_pattern
    )

    percentages = unique_matches(
        text,
        percent_pattern
    )


    # ------------------------------------------------------
    # TIEMPOS
    # ------------------------------------------------------

    times = unique_matches(
        text,
        time_pattern
    )


    # ------------------------------------------------------
    # REPLICACIÓN
    # ------------------------------------------------------

    replicates = unique_matches(
        text,
        rep_pattern
    )

    insect_numbers = unique_matches(
        text,
        insect_n_pattern
    )

    grain_numbers = unique_matches(
        text,
        grain_n_pattern
    )


    # ------------------------------------------------------
    # OUTCOMES
    # ------------------------------------------------------

    outcomes = str(
        row.get(
            "outcomes",
            ""
        )
    )


    # ------------------------------------------------------
    # REGISTRO
    # ------------------------------------------------------

    records.append({

        "study_record_id":
            row["study_record_id"],

        "title":
            row["title"],

        "doi":
            row.get("doi"),

        "intervention_types":
            ";".join(
                intervention_types
            ),

        "botanical":
            botanical,

        "natural_material":
            natural_material,

        "physical":
            physical,

        "synthetic_present":
            synthetic,

        "temperature_role":
            temperature_role,

        "temperature_values_C":
            ";".join(
                temp_values[:20]
            ),

        "humidity_role":
            humidity_role,

        "humidity_values_RH":
            ";".join(
                rh_values[:20]
            ),

        "dose_values":
            ";".join(
                doses[:30]
            ),

        "percentage_values":
            ";".join(
                percentages[:30]
            ),

        "time_values":
            ";".join(
                times[:30]
            ),

        "replicate_values":
            ";".join(
                replicates[:10]
            ),

        "insect_n_values":
            ";".join(
                insect_numbers[:10]
            ),

        "grain_n_values":
            ";".join(
                grain_numbers[:10]
            ),

        "outcomes":
            outcomes,

        "text_file":
            str(path)
    })


    if (
        n % 10 == 0
        or n == len(df)
    ):

        print(
            f"Procesados: "
            f"{n}/{len(df)}"
        )


# ==========================================================
# DATAFRAME
# ==========================================================

out = pd.DataFrame(
    records
)

out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("RESULTADO DEL MAPA")
print("==========================================\n")

print(
    f"Estudios procesados: {len(out)}"
)


print("\nTipo de intervención:")

for column in [
    "botanical",
    "natural_material",
    "physical",
    "synthetic_present"
]:

    print(
        f"{column:20s} "
        f"{out[column].sum()}"
    )


print("\nRol de temperatura:")

print(
    out[
        "temperature_role"
    ]
    .value_counts()
    .to_string()
)


print("\nRol de humedad:")

print(
    out[
        "humidity_role"
    ]
    .value_counts()
    .to_string()
)


print("\nInformación experimental:")

print(
    "Con dosis numérica:      ",
    (
        out["dose_values"]
        .fillna("")
        .str.len() > 0
    ).sum()
)

print(
    "Con réplicas numéricas:  ",
    (
        out["replicate_values"]
        .fillna("")
        .str.len() > 0
    ).sum()
)

print(
    "Con número de insectos:  ",
    (
        out["insect_n_values"]
        .fillna("")
        .str.len() > 0
    ).sum()
)

print(
    "Con número de granos:    ",
    (
        out["grain_n_values"]
        .fillna("")
        .str.len() > 0
    ).sum()
)


print("\n==========================================")
print("POSIBLES ESTUDIOS DE TEMPERATURA")
print("==========================================\n")

temp_test = out[
    out["temperature_role"]
    == "TESTED_FACTOR"
]

print(
    f"Total: {len(temp_test)}\n"
)

for _, row in temp_test.iterrows():

    print(
        row["study_record_id"],
        "|",
        row["temperature_values_C"],
        "|",
        row["title"]
    )


print(
    f"\nArchivo:\n{OUTPUT}"
)
