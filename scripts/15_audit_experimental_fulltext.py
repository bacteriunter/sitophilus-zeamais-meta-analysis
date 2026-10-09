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
    "fulltext_extraction_log.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "experimental_audit"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTDIR /
    "experimental_audit_all.csv"
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


def count_matches(text, pattern):

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

species_pattern = (
    r"\bsitophilus\s+zeamais\b"
)

maize_pattern = (
    r"\b("
    r"maize|corn|zea\s+mays|"
    r"maiz|maíz"
    r")\b"
)

control_pattern = (
    r"\b("
    r"untreated control|"
    r"negative control|"
    r"control treatment|"
    r"control group|"
    r"control sample|"
    r"control grains|"
    r"control grain|"
    r"untreated grain|"
    r"untreated grains|"
    r"untreated maize|"
    r"without treatment|"
    r"without application|"
    r"control"
    r")\b"
)

replication_pattern = (
    r"\b("
    r"replicate|replicates|"
    r"replicated|replication|"
    r"triplicate|triplicates|"
    r"completely randomized|"
    r"completely randomised|"
    r"randomized design|"
    r"randomised design|"
    r"experimental design"
    r")\b"
)

sample_size_pattern = (
    r"\b("
    r"n\s*=\s*\d+|"
    r"\d+\s+replicates|"
    r"\d+\s+replications|"
    r"\d+\s+insects|"
    r"\d+\s+adults|"
    r"\d+\s+weevils|"
    r"\d+\s+grains|"
    r"\d+\s+seeds"
    r")\b"
)

dose_pattern = (
    r"("
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:mg|g|kg|ml|µl|ul)"
    r"\s*(?:/|per\s+)"
    r"(?:g|kg|ml|l)\b"
    r"|"
    r"\b\d+(?:\.\d+)?\s*%"
    r"|"
    r"\bconcentration(?:s)?\b"
    r"|"
    r"\bdose(?:s)?\b"
    r"|"
    r"\bdosage\b"
    r")"
)

temperature_pattern = (
    r"("
    r"\btemperature(?:s)?\b|"
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:°\s*c|º\s*c|degrees?\s+c)"
    r")"
)

humidity_pattern = (
    r"("
    r"\brelative humidity\b|"
    r"\bhumidity\b|"
    r"\bRH\b|"
    r"\b\d+(?:\.\d+)?\s*%\s*RH\b"
    r")"
)

time_pattern = (
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:"
    r"hour|hours|h|"
    r"day|days|d|"
    r"week|weeks|"
    r"month|months"
    r")\b"
)


# ==========================================================
# OUTCOMES
# ==========================================================

outcome_patterns = {

    "mortality":
        r"\b("
        r"mortality|adult mortality|"
        r"percent mortality|"
        r"percentage mortality"
        r")\b",

    "progeny":
        r"\b("
        r"progeny|offspring|"
        r"adult emergence|"
        r"f1 emergence|"
        r"f1 progeny"
        r")\b",

    "damage":
        r"\b("
        r"grain damage|"
        r"kernel damage|"
        r"damaged grains|"
        r"damaged grain"
        r")\b",

    "weight_loss":
        r"\b("
        r"weight loss|"
        r"mass loss|"
        r"grain weight loss"
        r")\b",

    "germination":
        r"\b("
        r"germination|"
        r"germination percentage|"
        r"seed viability"
        r")\b",

    "infestation":
        r"\b("
        r"infestation|"
        r"infested grains|"
        r"infestation rate"
        r")\b",

    "repellency":
        r"\b("
        r"repellency|"
        r"repellent activity|"
        r"repellent effect"
        r")\b",

    "oviposition":
        r"\b("
        r"oviposition|"
        r"eggs laid|"
        r"number of eggs"
        r")\b"
}


# ==========================================================
# SEÑALES ESTADÍSTICAS
# ==========================================================

mean_pattern = (
    r"\b("
    r"mean|means|average"
    r")\b"
)

dispersion_pattern = (
    r"("
    r"\bstandard deviation\b|"
    r"\bstandard error\b|"
    r"\bmean\s*[±\+\-]\s*|"
    r"\bSD\b|"
    r"\bSEM\b"
    r")"
)

statistical_pattern = (
    r"\b("
    r"anova|analysis of variance|"
    r"tukey|duncan|lsd|"
    r"student.?s t|"
    r"t-test|"
    r"significant difference|"
    r"significantly different"
    r")\b"
)

pvalue_pattern = (
    r"\bp\s*[<=>]\s*0?\.\d+"
)


# ==========================================================
# LEER LOG
# ==========================================================

df = pd.read_csv(INPUT)

records = []


print("\n==========================================")
print("AUDITORÍA EXPERIMENTAL FULL TEXT")
print("==========================================\n")

print(
    f"Textos a evaluar: {len(df)}"
)


# ==========================================================
# ANALIZAR
# ==========================================================

for _, row in df.iterrows():

    study_id = str(
        row["study_record_id"]
    )

    text_file = row.get(
        "text_file"
    )

    if pd.isna(text_file):

        continue

    path = Path(
        str(text_file)
    )

    if not path.exists():

        continue

    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    # ------------------------------------------------------
    # SEÑALES GENERALES
    # ------------------------------------------------------

    has_species = detect(
        text,
        species_pattern
    )

    has_maize = detect(
        text,
        maize_pattern
    )

    has_control = detect(
        text,
        control_pattern
    )

    has_replication = detect(
        text,
        replication_pattern
    )

    has_sample_size = detect(
        text,
        sample_size_pattern
    )

    has_dose = detect(
        text,
        dose_pattern
    )

    has_temperature = detect(
        text,
        temperature_pattern
    )

    has_humidity = detect(
        text,
        humidity_pattern
    )

    has_time = detect(
        text,
        time_pattern
    )

    has_mean = detect(
        text,
        mean_pattern
    )

    has_dispersion = detect(
        text,
        dispersion_pattern
    )

    has_statistics = detect(
        text,
        statistical_pattern
    )

    has_pvalue = detect(
        text,
        pvalue_pattern
    )


    # ------------------------------------------------------
    # OUTCOMES
    # ------------------------------------------------------

    detected_outcomes = []

    for name, pattern in (
        outcome_patterns.items()
    ):

        if detect(
            text,
            pattern
        ):

            detected_outcomes.append(
                name
            )


    n_outcomes = len(
        detected_outcomes
    )


    # ------------------------------------------------------
    # SCORE DE EXTRACCIÓN
    # ------------------------------------------------------

    score = 0

    if has_species:
        score += 1

    if has_maize:
        score += 1

    if has_control:
        score += 3

    if has_replication:
        score += 2

    if has_sample_size:
        score += 2

    if has_dose:
        score += 1

    if n_outcomes > 0:
        score += 3

    if has_mean:
        score += 1

    if has_dispersion:
        score += 3

    if has_statistics:
        score += 1

    if has_pvalue:
        score += 1


    # ------------------------------------------------------
    # CLASIFICACIÓN
    # ------------------------------------------------------

    if (
        has_control
        and n_outcomes > 0
        and has_dispersion
        and (
            has_replication
            or has_sample_size
        )
    ):

        extraction_priority = (
            "EXTRACT_HIGH"
        )

    elif (
        has_control
        and n_outcomes > 0
        and (
            has_replication
            or has_sample_size
            or has_mean
        )
    ):

        extraction_priority = (
            "EXTRACT_POSSIBLE"
        )

    else:

        extraction_priority = (
            "MANUAL_CHECK"
        )


    records.append({

        "study_record_id":
            study_id,

        "meta_priority":
            row.get(
                "meta_priority"
            ),

        "title":
            row.get(
                "title"
            ),

        "doi":
            row.get(
                "doi"
            ),

        "source_format":
            row.get(
                "source_format"
            ),

        "extraction_quality":
            row.get(
                "extraction_quality"
            ),

        "has_species":
            has_species,

        "has_maize":
            has_maize,

        "has_control":
            has_control,

        "has_replication":
            has_replication,

        "has_sample_size":
            has_sample_size,

        "has_dose":
            has_dose,

        "has_temperature":
            has_temperature,

        "has_humidity":
            has_humidity,

        "has_time":
            has_time,

        "has_mean":
            has_mean,

        "has_dispersion":
            has_dispersion,

        "has_statistics":
            has_statistics,

        "has_pvalue":
            has_pvalue,

        "n_outcomes":
            n_outcomes,

        "outcomes":
            ";".join(
                detected_outcomes
            ),

        "extraction_score":
            score,

        "extraction_priority":
            extraction_priority,

        "text_file":
            str(path)
    })


# ==========================================================
# DATAFRAME
# ==========================================================

out = pd.DataFrame(
    records
)

out = out.sort_values(
    [
        "extraction_priority",
        "extraction_score"
    ],
    ascending=[
        True,
        False
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


for category in [
    "EXTRACT_HIGH",
    "EXTRACT_POSSIBLE",
    "MANUAL_CHECK"
]:

    subset = out[
        out["extraction_priority"]
        == category
    ]

    subset.to_csv(
        OUTDIR /
        f"{category}.csv",
        index=False,
        encoding="utf-8"
    )


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("RESULTADO DE AUDITORÍA")
print("==========================================\n")

print(
    f"Artículos evaluados: {len(out)}"
)

print("\nPrioridad:")

for category in [
    "EXTRACT_HIGH",
    "EXTRACT_POSSIBLE",
    "MANUAL_CHECK"
]:

    n = (
        out["extraction_priority"]
        == category
    ).sum()

    print(
        f"{category:20s} {n}"
    )


print("\nComponentes experimentales:")

variables = [
    ("Control", "has_control"),
    ("Replicación", "has_replication"),
    ("Tamaño muestra", "has_sample_size"),
    ("Dosis", "has_dose"),
    ("Temperatura", "has_temperature"),
    ("Humedad", "has_humidity"),
    ("Tiempo", "has_time"),
    ("Media", "has_mean"),
    ("Dispersión", "has_dispersion"),
    ("Estadística", "has_statistics"),
    ("p-value", "has_pvalue")
]

for label, column in variables:

    print(
        f"{label:18s} "
        f"{out[column].sum()}"
    )


print("\nOutcomes:")

for name in outcome_patterns:

    n = (
        out["outcomes"]
        .fillna("")
        .str.contains(
            rf"(^|;){name}(;|$)",
            regex=True
        )
        .sum()
    )

    print(
        f"{name:18s} {n}"
    )


# ==========================================================
# CRUCES IMPORTANTES
# ==========================================================

print("\nCandidatos con:")

print(
    "Control + outcome:       ",
    (
        out["has_control"]
        &
        (out["n_outcomes"] > 0)
    ).sum()
)

print(
    "Control + outcome + n:   ",
    (
        out["has_control"]
        &
        (out["n_outcomes"] > 0)
        &
        (
            out["has_replication"]
            |
            out["has_sample_size"]
        )
    ).sum()
)

print(
    "Control + outcome + SD:  ",
    (
        out["has_control"]
        &
        (out["n_outcomes"] > 0)
        &
        out["has_dispersion"]
    ).sum()
)


# ==========================================================
# EJEMPLOS
# ==========================================================

print("\n==========================================")
print("15 EJEMPLOS EXTRACT_HIGH")
print("==========================================\n")

examples = (
    out[
        out["extraction_priority"]
        == "EXTRACT_HIGH"
    ]
    .sort_values(
        "extraction_score",
        ascending=False
    )
    .head(15)
)

for _, row in examples.iterrows():

    print(
        f"[{row['extraction_score']}] "
        f"{row['title']}"
    )

    print(
        f"    Outcomes: "
        f"{row['outcomes']}"
    )

    mods = []

    if row["has_temperature"]:
        mods.append(
            "temperatura"
        )

    if row["has_humidity"]:
        mods.append(
            "humedad"
        )

    if row["has_dose"]:
        mods.append(
            "dosis"
        )

    if row["has_time"]:
        mods.append(
            "tiempo"
        )

    if mods:

        print(
            "    Variables: "
            + ", ".join(mods)
        )

    print()


print(
    f"Archivo principal:\n"
    f"{OUTPUT}"
)
