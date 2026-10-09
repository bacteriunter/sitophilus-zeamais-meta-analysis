#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
import re

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT / "03_screening" /
    "final_candidates" /
    "primary_candidates_final.csv"
)

OUTDIR = (
    PROJECT / "03_screening" /
    "meta_eligibility"
)

OUTDIR.mkdir(parents=True, exist_ok=True)


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


# ==========================================================
# LEER
# ==========================================================

df = pd.read_csv(INPUT)

df["title"] = (
    df["title"]
    .fillna("")
    .astype(str)
)

df["abstract"] = (
    df["abstract"]
    .fillna("")
    .astype(str)
)

df["text"] = (
    df["title"] +
    " " +
    df["abstract"]
).str.lower()

df["has_abstract"] = (
    df["abstract"]
    .str.strip()
    .str.len() > 0
)


# ==========================================================
# COMPARADOR / CONTROL
# ==========================================================

control_pattern = (
    r"\b("
    r"control|controls|"
    r"untreated|untreated control|"
    r"negative control|"
    r"positive control|"
    r"control group|"
    r"control treatment|"
    r"without treatment|"
    r"without application|"
    r"comparison|compared with|"
    r"compared to"
    r")\b"
)

df["has_control_signal"] = df["text"].apply(
    lambda x: detect(x, control_pattern)
)


# ==========================================================
# REPLICACIÓN / DISEÑO
# ==========================================================

replication_pattern = (
    r"\b("
    r"replicate|replicates|"
    r"replicated|replication|"
    r"completely randomized|"
    r"randomized design|"
    r"experimental design|"
    r"three times|"
    r"four times|"
    r"triplicate|triplicates"
    r")\b"
)

df["has_replication_signal"] = df["text"].apply(
    lambda x: detect(
        x,
        replication_pattern
    )
)


# ==========================================================
# DATOS CUANTITATIVOS
# ==========================================================

quantitative_pattern = (
    r"("
    r"\d+(\.\d+)?\s*%|"
    r"\d+(\.\d+)?\s*(mg|g|kg|ml|µl|ul)|"
    r"\bmean\b|"
    r"\bmeans\b|"
    r"\bstandard deviation\b|"
    r"\bsd\b|"
    r"\bstandard error\b|"
    r"\bse\b|"
    r"\bp\s*[<=>]\s*0?\.\d+|"
    r"\bpercent mortality\b|"
    r"\bpercentage mortality\b|"
    r"\bweight loss\b|"
    r"\bpercentage weight loss\b"
    r")"
)

df["has_quantitative_signal"] = (
    df["text"].apply(
        lambda x: detect(
            x,
            quantitative_pattern
        )
    )
)


# ==========================================================
# OUTCOMES ESPECÍFICOS
# ==========================================================

outcomes = {

    "mortality":
        r"\b(mortality|dead adults|adult mortality)\b",

    "survival":
        r"\b(survival|survivorship|surviving adults)\b",

    "progeny":
        r"\b(progeny|offspring|f1|adult emergence|emergence)\b",

    "damage":
        r"\b(grain damage|kernel damage|damaged grain|damaged grains)\b",

    "weight_loss":
        r"\b(weight loss|mass loss)\b",

    "germination":
        r"\b(germination|seed viability|grain viability)\b",

    "infestation":
        r"\b(infestation|infestation rate|infested grains)\b",

    "repellency":
        r"\b(repellency|repellent activity|repellent effect)\b",

    "oviposition":
        r"\b(oviposition|eggs laid|egg laying)\b"
}


for name, pattern in outcomes.items():

    df[f"out_{name}"] = (
        df["text"].apply(
            lambda x: detect(
                x,
                pattern
            )
        )
    )


out_cols = [
    f"out_{x}"
    for x in outcomes
]

df["n_outcomes_detected"] = (
    df[out_cols]
    .sum(axis=1)
)


# ==========================================================
# TIPO DE INFORMACIÓN EXPERIMENTAL
# ==========================================================

dose_pattern = (
    r"\b("
    r"dose|doses|"
    r"concentration|concentrations|"
    r"dosage|"
    r"g/kg|g kg|"
    r"ml/kg|ml kg|"
    r"mg/l|mg l"
    r")\b"
)

time_pattern = (
    r"\b("
    r"hours|hour|"
    r"days|day|"
    r"weeks|week|"
    r"months|month|"
    r"exposure time|"
    r"storage period|"
    r"storage time"
    r")\b"
)

df["has_dose_signal"] = (
    df["text"].apply(
        lambda x: detect(
            x,
            dose_pattern
        )
    )
)

df["has_time_signal"] = (
    df["text"].apply(
        lambda x: detect(
            x,
            time_pattern
        )
    )
)


# ==========================================================
# SCORE META-ANALÍTICO
# ==========================================================

df["meta_score"] = 0

df.loc[
    df["has_control_signal"],
    "meta_score"
] += 3

df.loc[
    df["has_replication_signal"],
    "meta_score"
] += 2

df.loc[
    df["has_quantitative_signal"],
    "meta_score"
] += 3

df.loc[
    df["n_outcomes_detected"] > 0,
    "meta_score"
] += 3

df.loc[
    df["has_dose_signal"],
    "meta_score"
] += 1

df.loc[
    df["has_time_signal"],
    "meta_score"
] += 1


# ==========================================================
# CLASIFICACIÓN
# ==========================================================

def classify(row):

    if not row["has_abstract"]:
        return "NO_ABSTRACT"

    if (
        row["has_control_signal"]
        and row["has_quantitative_signal"]
        and row["n_outcomes_detected"] > 0
    ):
        return "META_HIGH"

    if (
        row["n_outcomes_detected"] > 0
        and row["meta_score"] >= 5
    ):
        return "META_POSSIBLE"

    return "REVIEW_ONLY"


df["meta_priority"] = (
    df.apply(
        classify,
        axis=1
    )
)


# ==========================================================
# OUTCOME RESUMIDO
# ==========================================================

def outcome_names(row):

    found = []

    for name in outcomes:

        if row[f"out_{name}"]:
            found.append(name)

    return ";".join(found)


df["outcomes_detected"] = (
    df.apply(
        outcome_names,
        axis=1
    )
)


# ==========================================================
# GUARDAR
# ==========================================================

OUTPUT_ALL = (
    OUTDIR /
    "meta_eligibility_all.csv"
)

df.to_csv(
    OUTPUT_ALL,
    index=False,
    encoding="utf-8"
)


for group in [
    "META_HIGH",
    "META_POSSIBLE",
    "REVIEW_ONLY",
    "NO_ABSTRACT"
]:

    df[
        df["meta_priority"] == group
    ].to_csv(
        OUTDIR / f"{group}.csv",
        index=False,
        encoding="utf-8"
    )


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("ELEGIBILIDAD META-ANALÍTICA")
print("==========================================\n")

print(
    f"Registros evaluados: {len(df)}"
)

print("\nClasificación:")

counts = (
    df["meta_priority"]
    .value_counts()
)

for group in [
    "META_HIGH",
    "META_POSSIBLE",
    "REVIEW_ONLY",
    "NO_ABSTRACT"
]:

    print(
        f"{group:18s} "
        f"{counts.get(group, 0)}"
    )


print("\nSeñales experimentales:")

print(
    f"Control/comparador:    "
    f"{df['has_control_signal'].sum()}"
)

print(
    f"Replicación:           "
    f"{df['has_replication_signal'].sum()}"
)

print(
    f"Datos cuantitativos:   "
    f"{df['has_quantitative_signal'].sum()}"
)

print(
    f"Dosis:                 "
    f"{df['has_dose_signal'].sum()}"
)

print(
    f"Tiempo:                "
    f"{df['has_time_signal'].sum()}"
)


print("\nOutcomes detectados:")

for name in outcomes:

    print(
        f"{name:18s} "
        f"{df[f'out_{name}'].sum()}"
    )


print("\n==========================================")
print("15 EJEMPLOS META_HIGH")
print("==========================================\n")

examples = (
    df[
        df["meta_priority"]
        == "META_HIGH"
    ]
    .sort_values(
        "meta_score",
        ascending=False
    )
    .head(15)
)

for _, row in examples.iterrows():

    print(
        f"[{row['meta_score']}] "
        f"{row['title']}"
    )

    print(
        f"    Outcomes: "
        f"{row['outcomes_detected']}"
    )

    print()


print(
    f"Archivo principal:\n"
    f"{OUTPUT_ALL}"
)
