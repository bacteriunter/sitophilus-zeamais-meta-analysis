#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

OUTDIR = PROJECT / "07_meta_analysis" / "final_summary"
OUTDIR.mkdir(parents=True, exist_ok=True)

FULLTEXT = PROJECT / "05_extraction/fulltext_extraction_log.csv"

EXP_HIGH = (
    PROJECT /
    "05_extraction/experimental_audit/EXTRACT_HIGH.csv"
)

EXP_POSSIBLE = (
    PROJECT /
    "05_extraction/experimental_audit/EXTRACT_POSSIBLE.csv"
)

MANUAL = (
    PROJECT /
    "05_extraction/experimental_audit/MANUAL_CHECK.csv"
)

NUM_HIGH = (
    PROJECT /
    "05_extraction/numeric_audit/NUMERIC_HIGH.csv"
)

SCOPE_INCLUDE = (
    PROJECT /
    "05_extraction/scope_eligibility/INCLUDE.csv"
)

SCOPE_REVIEW = (
    PROJECT /
    "05_extraction/scope_eligibility/REVIEW.csv"
)

SCOPE_EXCLUDE = (
    PROJECT /
    "05_extraction/scope_eligibility/EXCLUDE_AUTO.csv"
)

META = (
    PROJECT /
    "07_meta_analysis/mortality_meta_dataset.csv"
)

SECONDARY = (
    PROJECT /
    "05_extraction/secondary_outcomes/"
    "secondary_outcome_audit.csv"
)

F1 = (
    PROJECT /
    "05_extraction/secondary_outcomes/progeny/final/"
    "progeny_tables_validated.csv"
)

WEIGHT = (
    PROJECT /
    "05_extraction/secondary_outcomes/weight_loss/"
    "weightloss_table_audit.csv"
)

GERM = (
    PROJECT /
    "05_extraction/secondary_outcomes/germination/"
    "germination_table_audit.csv"
)

OUT_RECORDS = OUTDIR / "review_eligibility_final.csv"
OUT_COUNTS = OUTDIR / "review_eligibility_counts.csv"
OUT_TXT = OUTDIR / "review_eligibility_final.txt"


# ==========================================================
# FUNCIONES
# ==========================================================

ID = "study_record_id"


def load(path):
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    if ID not in df.columns:
        raise ValueError(
            f"{path.name}: no contiene {ID}. "
            f"Columnas = {list(df.columns)}"
        )

    df[ID] = (
        df[ID]
        .astype(str)
        .str.strip()
    )

    return df


def get_ids(df):
    return set(
        df[ID]
        .dropna()
        .astype(str)
        .str.strip()
    )


# ==========================================================
# CARGA
# ==========================================================

fulltext = load(FULLTEXT)
exp_high = load(EXP_HIGH)
exp_possible = load(EXP_POSSIBLE)
manual = load(MANUAL)
num_high = load(NUM_HIGH)

scope_include = load(SCOPE_INCLUDE)
scope_review = load(SCOPE_REVIEW)
scope_exclude = load(SCOPE_EXCLUDE)

meta = load(META)
secondary = load(SECONDARY)
f1 = load(F1)
weight = load(WEIGHT)
germ = load(GERM)


sets = {
    "exp_high": get_ids(exp_high),
    "exp_possible": get_ids(exp_possible),
    "manual": get_ids(manual),
    "num_high": get_ids(num_high),
    "scope_include": get_ids(scope_include),
    "scope_review": get_ids(scope_review),
    "scope_exclude": get_ids(scope_exclude),
    "mortality_meta": get_ids(meta),
}


# ==========================================================
# UNIVERSO = 151 TEXTOS COMPLETOS
# ==========================================================

flow = pd.DataFrame({
    ID: sorted(get_ids(fulltext))
})

for name, ids in sets.items():
    flow[name] = flow[ID].isin(ids)


# ==========================================================
# CLASIFICACIÓN EXPERIMENTAL
# ==========================================================

def experimental_status(r):

    flags = []

    if r["exp_high"]:
        flags.append("EXTRACT_HIGH")

    if r["exp_possible"]:
        flags.append("EXTRACT_POSSIBLE")

    if r["manual"]:
        flags.append("MANUAL_CHECK")

    if len(flags) == 1:
        return flags[0]

    if len(flags) == 0:
        return "UNCLASSIFIED"

    return "MULTIPLE"


flow["experimental_status"] = flow.apply(
    experimental_status,
    axis=1
)


# ==========================================================
# SCOPE
# ==========================================================

def scope_status(r):

    flags = []

    if r["scope_include"]:
        flags.append("INCLUDE")

    if r["scope_review"]:
        flags.append("REVIEW")

    if r["scope_exclude"]:
        flags.append("EXCLUDE_AUTO")

    if len(flags) == 1:
        return flags[0]

    if len(flags) == 0:
        return "NOT_SCOPE_AUDITED"

    return "MULTIPLE"


flow["scope_status"] = flow.apply(
    scope_status,
    axis=1
)


# ==========================================================
# OUTCOMES SECUNDARIOS
# ==========================================================

# Señal general de outcomes secundarios
sec_ids = get_ids(secondary)
flow["secondary_outcome_detected"] = (
    flow[ID].isin(sec_ids)
)


# F1 validado
if "final_status" in f1.columns:

    f1_valid = f1[
        f1["final_status"].isin(
            ["VALID", "VALID_STRONG"]
        )
    ].copy()

else:
    f1_valid = f1.iloc[0:0].copy()

# Excluir estudio X-ray ya identificado fuera del scope
f1_valid = f1_valid[
    f1_valid[ID] != "SZ_00213"
]

f1_ids = get_ids(f1_valid)

flow["validated_f1"] = (
    flow[ID].isin(f1_ids)
)


# Weight loss HIGH
if "status" in weight.columns:

    weight_high = weight[
        weight["status"] == "HIGH"
    ].copy()

else:
    weight_high = weight.iloc[0:0].copy()

weight_ids = get_ids(weight_high)

flow["high_weight_loss"] = (
    flow[ID].isin(weight_ids)
)


# Germination HIGH
if "status" in germ.columns:

    germ_high = germ[
        germ["status"] == "HIGH"
    ].copy()

else:
    germ_high = germ.iloc[0:0].copy()

germ_ids = get_ids(germ_high)

flow["high_germination"] = (
    flow[ID].isin(germ_ids)
)


# ==========================================================
# EVIDENCIA UTILIZADA
# ==========================================================

flow["has_any_structured_evidence"] = (
    flow["scope_include"]
    |
    flow["mortality_meta"]
    |
    flow["validated_f1"]
    |
    flow["high_weight_loss"]
    |
    flow["high_germination"]
)


# ==========================================================
# CLASIFICACIÓN FINAL CONSERVADORA
# ==========================================================

def final_class(r):

    # Síntesis cuantitativa primaria
    if r["mortality_meta"]:
        return "INCLUDED_QUANTITATIVE_MORTALITY"

    # Scope INCLUDE pero no mortality meta
    if r["scope_include"]:
        return "INCLUDED_SYSTEMATIC_REVIEW"

    # Pendiente/revisión de alcance
    if r["scope_review"]:
        return "SCOPE_REVIEW_UNRESOLVED"

    # Exclusión explícita
    if r["scope_exclude"]:
        return "EXCLUDED_SCOPE"

    # Extract high pero no pasó a inclusión
    if r["experimental_status"] == "EXTRACT_HIGH":

        if not r["num_high"]:
            return "EXCLUDED_INSUFFICIENT_NUMERIC_EVIDENCE"

        return "EXTRACT_HIGH_NOT_FINAL_INCLUDED"

    # Posibles experimentales
    if r["experimental_status"] == "EXTRACT_POSSIBLE":
        return "EXCLUDED_NOT_HIGH_CONFIDENCE_EXPERIMENTAL"

    # Manual
    if r["experimental_status"] == "MANUAL_CHECK":
        return "MANUAL_CHECK_NOT_INCLUDED"

    return "UNRESOLVED"


flow["final_review_class"] = flow.apply(
    final_class,
    axis=1
)


# ==========================================================
# CONTEOS
# ==========================================================

counts = (
    flow["final_review_class"]
    .value_counts()
    .rename_axis("final_review_class")
    .reset_index(name="n")
)


# ==========================================================
# CONTROLES
# ==========================================================

issues = []

if len(flow) != 151:
    issues.append(
        f"El universo tiene {len(flow)} estudios; "
        "se esperaban 151."
    )

if (
    flow["experimental_status"] == "MULTIPLE"
).any():

    issues.append(
        "Hay estudios en múltiples categorías "
        "del experimental audit."
    )

if (
    flow["experimental_status"] == "UNCLASSIFIED"
).any():

    n = (
        flow["experimental_status"]
        == "UNCLASSIFIED"
    ).sum()

    issues.append(
        f"{n} estudios no tienen clasificación experimental."
    )

if (
    flow["scope_status"] == "MULTIPLE"
).any():

    issues.append(
        "Hay estudios en múltiples categorías de scope."
    )


# ==========================================================
# TOTALES IMPORTANTES
# ==========================================================

n_quant = int(
    flow["mortality_meta"].sum()
)

n_scope_include = int(
    flow["scope_include"].sum()
)

n_systematic_nonmeta = int(
    (
        flow["scope_include"]
        &
        ~flow["mortality_meta"]
    ).sum()
)

n_review = int(
    flow["scope_review"].sum()
)

n_scope_exclude = int(
    flow["scope_exclude"].sum()
)


# ==========================================================
# GUARDAR
# ==========================================================

flow.to_csv(
    OUT_RECORDS,
    index=False,
    encoding="utf-8"
)

counts.to_csv(
    OUT_COUNTS,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# TXT
# ==========================================================

lines = []

lines.append(
    "FINAL REVIEW ELIGIBILITY AUDIT"
)

lines.append(
    "=" * 75
)

lines.append(
    f"Full-text reports assessed: {len(flow)}"
)

lines.append("")

lines.append(
    f"Scope INCLUDE: {n_scope_include}"
)

lines.append(
    f"Included in quantitative mortality synthesis: {n_quant}"
)

lines.append(
    f"Scope INCLUDE but not mortality meta-analysis: "
    f"{n_systematic_nonmeta}"
)

lines.append(
    f"Scope REVIEW unresolved: {n_review}"
)

lines.append(
    f"Scope EXCLUDE_AUTO: {n_scope_exclude}"
)

lines.append("")

lines.append(
    "FINAL CLASSIFICATION"
)

lines.append(
    "-" * 75
)

for _, r in counts.iterrows():
    lines.append(
        f"{r['final_review_class']}: {r['n']}"
    )


lines.append("")
lines.append(
    "SECONDARY OUTCOME SUPPORT"
)

lines.append(
    "-" * 75
)

lines.append(
    f"Validated F1 studies: "
    f"{flow['validated_f1'].sum()}"
)

lines.append(
    f"HIGH weight-loss studies: "
    f"{flow['high_weight_loss'].sum()}"
)

lines.append(
    f"HIGH germination studies: "
    f"{flow['high_germination'].sum()}"
)


lines.append("")
lines.append(
    "CONSISTENCY CHECKS"
)

lines.append(
    "-" * 75
)

if issues:
    lines.extend(issues)
else:
    lines.append(
        "No structural inconsistencies detected."
    )


lines.append("")
lines.append(
    "INTERPRETATION"
)

lines.append(
    "-" * 75
)

lines.append(
    "The 9 studies in the mortality meta dataset represent "
    "the quantitative primary mortality synthesis and must not "
    "be interpreted automatically as the total number of studies "
    "included in the systematic review."
)

lines.append(
    "Scope INCLUDE identifies studies retained after the strict "
    "scope audit. Secondary outcomes are synthesized descriptively "
    "unless explicitly classified for quantitative analysis."
)


OUT_TXT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# ==========================================================
# TERMINAL
# ==========================================================

print("\n==========================================")
print("CIERRE DE ELEGIBILIDAD")
print("==========================================\n")

print(
    "Full-text reports assessed:",
    len(flow)
)


print("\n==========================================")
print("EXPERIMENTAL AUDIT")
print("==========================================\n")

print(
    flow["experimental_status"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("SCOPE")
print("==========================================\n")

print(
    flow["scope_status"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("CLASIFICACIÓN FINAL")
print("==========================================\n")

print(
    flow["final_review_class"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("OUTCOMES SECUNDARIOS")
print("==========================================\n")

print(
    "Validated F1 studies:",
    int(flow["validated_f1"].sum())
)

print(
    "HIGH weight-loss studies:",
    int(flow["high_weight_loss"].sum())
)

print(
    "HIGH germination studies:",
    int(flow["high_germination"].sum())
)


print("\n==========================================")
print("SÍNTESIS")
print("==========================================\n")

print(
    "Scope INCLUDE:",
    n_scope_include
)

print(
    "Quantitative mortality:",
    n_quant
)

print(
    "Scope INCLUDE no mortality meta:",
    n_systematic_nonmeta
)

print(
    "Scope REVIEW:",
    n_review
)

print(
    "Scope EXCLUDE:",
    n_scope_exclude
)


print("\n==========================================")
print("CONSISTENCY CHECKS")
print("==========================================\n")

if issues:

    for issue in issues:
        print("WARNING:", issue)

else:
    print(
        "No structural inconsistencies detected."
    )


print("\n==========================================")
print("SALIDAS")
print("==========================================\n")

print(OUT_RECORDS)
print(OUT_COUNTS)
print(OUT_TXT)
