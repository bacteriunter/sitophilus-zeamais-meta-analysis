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
    "numeric_audit" /
    "numeric_audit.csv"
)

OUTPUT_DIR = (
    PROJECT /
    "05_extraction" /
    "scope_eligibility"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTPUT_DIR /
    "scope_eligibility_all.csv"
)


# ==========================================================
# FUNCIONES
# ==========================================================

def has(text, pattern):

    return bool(
        re.search(
            pattern,
            text,
            flags=re.I
        )
    )


def count(text, pattern):

    return len(
        re.findall(
            pattern,
            text,
            flags=re.I
        )
    )


# ==========================================================
# PATRONES
# ==========================================================

zeamais = (
    r"\bsitophilus\s+zeamais\b"
)

maize = (
    r"\b("
    r"maize|corn|zea\s+mays|"
    r"maiz|maíz"
    r")\b"
)

other_grains = (
    r"\b("
    r"sorghum|wheat|rice|"
    r"barley|cowpea|bean|beans"
    r")\b"
)

botanical = (
    r"\b("
    r"essential oils?|"
    r"plant oils?|"
    r"vegetable oils?|"
    r"plant powders?|"
    r"leaf powders?|"
    r"seed powders?|"
    r"plant extracts?|"
    r"leaf extracts?|"
    r"seed extracts?|"
    r"botanical(?:s)?|"
    r"medicinal plants?"
    r")\b"
)

natural_material = (
    r"\b("
    r"wood ash|"
    r"cow dung ash|"
    r"rice husk ash|"
    r"ash|ashes|"
    r"diatomaceous earth|"
    r"inert dusts?|"
    r"clay|"
    r"sand"
    r")\b"
)

hermetic = (
    r"\b("
    r"hermetic storage|"
    r"hermetic bag|"
    r"hermetic bags|"
    r"airtight storage"
    r")\b"
)

synthetic = (
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

clearly_outside = (
    r"\b("
    r"x-ray irradiation|"
    r"x ray irradiation|"
    r"gamma irradiation|"
    r"ionizing radiation|"
    r"ionising radiation"
    r")\b"
)

control = (
    r"\b("
    r"control|"
    r"untreated|"
    r"without treatment|"
    r"negative control"
    r")\b"
)


# ==========================================================
# LEER DATOS
# ==========================================================

df = pd.read_csv(INPUT)

records = []


print("\n==========================================")
print("AUDITORÍA DE ELEGIBILIDAD")
print("==========================================\n")

print(
    f"Estudios: {len(df)}"
)


# ==========================================================
# PROCESAR
# ==========================================================

for _, row in df.iterrows():

    path = Path(
        str(row["text_file"])
    )

    if not path.exists():
        continue

    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    title = str(
        row["title"]
    )

    title_text = title.lower()

    species_ok = has(
        text,
        zeamais
    )

    maize_text = has(
        text,
        maize
    )

    maize_title = has(
        title,
        maize
    )

    botanical_present = has(
        text,
        botanical
    )

    natural_material_present = has(
        text,
        natural_material
    )

    hermetic_present = has(
        text,
        hermetic
    )

    synthetic_present = has(
        text,
        synthetic
    )

    outside_present = has(
        title,
        clearly_outside
    )

    control_present = has(
        text,
        control
    )

    other_grain_title = has(
        title,
        other_grains
    )


    natural_intervention = (
        botanical_present
        or natural_material_present
        or hermetic_present
    )


    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    reasons = []


    if not species_ok:

        status = "EXCLUDE_AUTO"

        reasons.append(
            "NO_S_ZEAMAIS"
        )


    elif outside_present:

        status = "EXCLUDE_AUTO"

        reasons.append(
            "OUTSIDE_INTERVENTION"
        )


    elif (
        other_grain_title
        and not maize_title
    ):

        status = "REVIEW"

        reasons.append(
            "OTHER_GRAIN_IN_TITLE"
        )


    elif not maize_text:

        status = "REVIEW"

        reasons.append(
            "MAIZE_NOT_CONFIRMED"
        )


    elif not natural_intervention:

        status = "REVIEW"

        reasons.append(
            "NATURAL_INTERVENTION_NOT_CONFIRMED"
        )


    elif not control_present:

        status = "REVIEW"

        reasons.append(
            "CONTROL_NOT_CONFIRMED"
        )


    else:

        status = "INCLUDE"


    # ------------------------------------------------------
    # BANDERAS ADICIONALES
    # ------------------------------------------------------

    if synthetic_present:

        reasons.append(
            "SYNTHETIC_ARM_PRESENT"
        )

    if other_grain_title:

        reasons.append(
            "OTHER_GRAIN_PRESENT"
        )


    # ======================================================
    # REGISTRO
    # ======================================================

    records.append({

        "study_record_id":
            row["study_record_id"],

        "title":
            title,

        "doi":
            row.get("doi"),

        "species_confirmed":
            species_ok,

        "maize_in_text":
            maize_text,

        "maize_in_title":
            maize_title,

        "botanical":
            botanical_present,

        "natural_material":
            natural_material_present,

        "hermetic":
            hermetic_present,

        "natural_intervention":
            natural_intervention,

        "synthetic_present":
            synthetic_present,

        "other_grain_title":
            other_grain_title,

        "control_present":
            control_present,

        "scope_status":
            status,

        "scope_flags":
            ";".join(
                reasons
            ),

        "numeric_priority":
            row["numeric_priority"],

        "mortality_numeric_windows":
            row["mortality_numeric_windows"],

        "progeny_numeric_windows":
            row["progeny_numeric_windows"],

        "weight_loss_numeric_windows":
            row["weight_loss_numeric_windows"],

        "damage_numeric_windows":
            row["damage_numeric_windows"],

        "germination_numeric_windows":
            row["germination_numeric_windows"],

        "text_file":
            str(path)
    })


# ==========================================================
# GUARDAR
# ==========================================================

out = pd.DataFrame(
    records
)

out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


for status in [
    "INCLUDE",
    "REVIEW",
    "EXCLUDE_AUTO"
]:

    out[
        out["scope_status"]
        == status
    ].to_csv(
        OUTPUT_DIR /
        f"{status}.csv",
        index=False,
        encoding="utf-8"
    )


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("RESULTADO DE ELEGIBILIDAD")
print("==========================================\n")

print(
    out[
        "scope_status"
    ]
    .value_counts()
    .to_string()
)


print("\nIntervenciones:")

print(
    "Botánicos:           ",
    out["botanical"].sum()
)

print(
    "Materiales naturales:",
    out["natural_material"].sum()
)

print(
    "Herméticos:          ",
    out["hermetic"].sum()
)

print(
    "Sintético presente:  ",
    out["synthetic_present"].sum()
)


print("\nINCLUDE con outcome numérico:")

included = out[
    out["scope_status"]
    == "INCLUDE"
]

for outcome in [
    "mortality",
    "progeny",
    "weight_loss",
    "damage",
    "germination"
]:

    column = (
        f"{outcome}_numeric_windows"
    )

    print(
        f"{outcome:15s}",
        (
            included[column] > 0
        ).sum()
    )


# ==========================================================
# MOSTRAR REVIEW
# ==========================================================

review = out[
    out["scope_status"]
    == "REVIEW"
]

print("\n==========================================")
print("ESTUDIOS PARA REVISAR")
print("==========================================\n")

print(
    f"Total: {len(review)}\n"
)

for _, row in review.iterrows():

    print(
        row["study_record_id"],
        "|",
        row["scope_flags"],
        "|",
        row["title"]
    )


# ==========================================================
# EXCLUSIONES
# ==========================================================

excluded = out[
    out["scope_status"]
    == "EXCLUDE_AUTO"
]

print("\n==========================================")
print("EXCLUSIONES AUTOMÁTICAS")
print("==========================================\n")

print(
    f"Total: {len(excluded)}\n"
)

for _, row in excluded.iterrows():

    print(
        row["study_record_id"],
        "|",
        row["scope_flags"],
        "|",
        row["title"]
    )


print(
    f"\nArchivo:\n{OUTPUT}"
)
