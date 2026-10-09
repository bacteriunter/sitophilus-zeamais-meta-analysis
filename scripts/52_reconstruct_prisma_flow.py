#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

OUTDIR = PROJECT / "07_meta_analysis" / "final_summary"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUT_RECORDS = OUTDIR / "prisma_record_flow.csv"
OUT_COUNTS = OUTDIR / "prisma_flow_counts.csv"
OUT_TXT = OUTDIR / "prisma_flow_audit.txt"


# ==========================================================
# ARCHIVOS
# ==========================================================

FILES = {
    "primary":
        "03_screening/final_candidates/primary_candidates_final.csv",

    "meta_high":
        "03_screening/meta_eligibility/META_HIGH.csv",

    "meta_possible":
        "03_screening/meta_eligibility/META_POSSIBLE.csv",

    "review_only":
        "03_screening/meta_eligibility/REVIEW_ONLY.csv",

    "fulltext":
        "05_extraction/fulltext_extraction_log.csv",

    "experimental":
        "05_extraction/experimental_audit/experimental_audit_all.csv",

    "extract_high":
        "05_extraction/experimental_audit/EXTRACT_HIGH.csv",

    "extract_possible":
        "05_extraction/experimental_audit/EXTRACT_POSSIBLE.csv",

    "manual":
        "05_extraction/experimental_audit/MANUAL_CHECK.csv",

    "numeric_high":
        "05_extraction/numeric_audit/NUMERIC_HIGH.csv",

    "scope_include":
        "05_extraction/scope_eligibility/INCLUDE.csv",

    "scope_review":
        "05_extraction/scope_eligibility/REVIEW.csv",

    "scope_exclude":
        "05_extraction/scope_eligibility/EXCLUDE_AUTO.csv",

    "mortality_meta":
        "07_meta_analysis/mortality_meta_dataset.csv",
}


def load(name):
    path = PROJECT / FILES[name]

    if not path.exists():
        raise FileNotFoundError(
            f"No existe: {path}"
        )

    return pd.read_csv(path)


dfs = {
    name: load(name)
    for name in FILES
}


# ==========================================================
# IDENTIFICAR COLUMNA ID
# ==========================================================

ID_CANDIDATES = [
    "study_record_id",
    "record_id",
    "study_id",
    "id"
]


def find_id_column(df, label):

    for c in ID_CANDIDATES:
        if c in df.columns:
            return c

    raise ValueError(
        f"No encuentro columna ID en {label}. "
        f"Columnas: {list(df.columns)}"
    )


idcols = {}

for name, df in dfs.items():

    idcols[name] = find_id_column(
        df,
        name
    )


print("\n==========================================")
print("COLUMNAS ID")
print("==========================================\n")

for name in FILES:
    print(
        f"{name}: {idcols[name]}"
    )


# ==========================================================
# NORMALIZAR ID
# ==========================================================

def ids(name):

    df = dfs[name]
    col = idcols[name]

    return set(
        df[col]
        .dropna()
        .astype(str)
        .str.strip()
    )


sets = {
    name: ids(name)
    for name in FILES
}


# ==========================================================
# UNIVERSO: 483 CANDIDATOS FINALES
# ==========================================================

primary = dfs["primary"].copy()
primary_id = idcols["primary"]

primary[primary_id] = (
    primary[primary_id]
    .astype(str)
    .str.strip()
)

primary = primary.drop_duplicates(
    subset=[primary_id]
).copy()

flow = pd.DataFrame({
    "study_record_id":
        primary[primary_id]
})


# ==========================================================
# MEMBRESÍA EN CADA ETAPA
# ==========================================================

for name in [
    "meta_high",
    "meta_possible",
    "review_only",
    "fulltext",
    "experimental",
    "extract_high",
    "extract_possible",
    "manual",
    "numeric_high",
    "scope_include",
    "scope_review",
    "scope_exclude",
    "mortality_meta",
]:

    flow[name] = (
        flow["study_record_id"]
        .isin(sets[name])
    )


# ==========================================================
# META-ELIGIBILITY
# ==========================================================

def meta_status(r):

    flags = []

    if r["meta_high"]:
        flags.append("META_HIGH")

    if r["meta_possible"]:
        flags.append("META_POSSIBLE")

    if r["review_only"]:
        flags.append("REVIEW_ONLY")

    if len(flags) == 0:
        return "NOT_CLASSIFIED"

    if len(flags) > 1:
        return "MULTIPLE"

    return flags[0]


flow["meta_eligibility_status"] = flow.apply(
    meta_status,
    axis=1
)


# ==========================================================
# EXPERIMENTAL AUDIT STATUS
# ==========================================================

def experimental_status(r):

    flags = []

    if r["extract_high"]:
        flags.append("EXTRACT_HIGH")

    if r["extract_possible"]:
        flags.append("EXTRACT_POSSIBLE")

    if r["manual"]:
        flags.append("MANUAL_CHECK")

    if not r["fulltext"]:
        return "NO_FULLTEXT_RECORD"

    if len(flags) == 0:
        return "FULLTEXT_NOT_CLASSIFIED"

    if len(flags) > 1:
        return "MULTIPLE"

    return flags[0]


flow["experimental_status"] = flow.apply(
    experimental_status,
    axis=1
)


# ==========================================================
# SCOPE STATUS
# ==========================================================

def scope_status(r):

    flags = []

    if r["scope_include"]:
        flags.append("INCLUDE")

    if r["scope_review"]:
        flags.append("REVIEW")

    if r["scope_exclude"]:
        flags.append("EXCLUDE_AUTO")

    if len(flags) == 0:
        return "NOT_SCOPE_AUDITED"

    if len(flags) > 1:
        return "MULTIPLE"

    return flags[0]


flow["scope_status"] = flow.apply(
    scope_status,
    axis=1
)


# ==========================================================
# RUTA FINAL
# ==========================================================

def final_path(r):

    if not r["fulltext"]:
        return "NO_FULLTEXT_IN_EXTRACTION_LOG"

    if r["experimental_status"] == "EXTRACT_POSSIBLE":
        return "FULLTEXT_EXTRACT_POSSIBLE"

    if r["experimental_status"] == "MANUAL_CHECK":
        return "FULLTEXT_MANUAL_CHECK"

    if r["experimental_status"] == "FULLTEXT_NOT_CLASSIFIED":
        return "FULLTEXT_NOT_CLASSIFIED"

    if r["experimental_status"] == "MULTIPLE":
        return "EXPERIMENTAL_MULTIPLE_STATUS"

    if r["experimental_status"] == "EXTRACT_HIGH":

        if not r["numeric_high"]:
            return "EXTRACT_HIGH_NOT_NUMERIC_HIGH"

        if r["scope_status"] == "INCLUDE":

            if r["mortality_meta"]:
                return "INCLUDED_MORTALITY_META"

            return "SCOPE_INCLUDE_NOT_MORTALITY_META"

        if r["scope_status"] == "REVIEW":
            return "SCOPE_REVIEW"

        if r["scope_status"] == "EXCLUDE_AUTO":
            return "SCOPE_EXCLUDE_AUTO"

        if r["scope_status"] == "MULTIPLE":
            return "SCOPE_MULTIPLE_STATUS"

        return "NUMERIC_HIGH_NOT_SCOPE_CLASSIFIED"

    return "OTHER"


flow["final_path"] = flow.apply(
    final_path,
    axis=1
)


# ==========================================================
# CONTROLES DE CONSISTENCIA
# ==========================================================

issues = []


# Meta categorías deberían sumar 483
meta_multiple = (
    flow["meta_eligibility_status"] == "MULTIPLE"
).sum()

meta_unclassified = (
    flow["meta_eligibility_status"] == "NOT_CLASSIFIED"
).sum()

if meta_multiple:
    issues.append(
        f"{meta_multiple} registros aparecen en múltiples "
        "categorías meta-eligibility."
    )

if meta_unclassified:
    issues.append(
        f"{meta_unclassified} registros no aparecen en ninguna "
        "categoría meta-eligibility."
    )


# Todo registro experimental debería tener fulltext
bad_exp = flow[
    flow["experimental"]
    &
    ~flow["fulltext"]
]

if len(bad_exp):
    issues.append(
        f"{len(bad_exp)} registros aparecen en experimental_audit "
        "pero no en fulltext log."
    )


# Todo mortality_meta debería ser scope include
bad_meta = flow[
    flow["mortality_meta"]
    &
    ~flow["scope_include"]
]

if len(bad_meta):
    issues.append(
        f"{len(bad_meta)} estudios del mortality meta dataset "
        "no aparecen como scope INCLUDE."
    )


# ==========================================================
# CONTEOS
# ==========================================================

counts = []


def add(stage, category, n):
    counts.append({
        "stage": stage,
        "category": category,
        "n": int(n)
    })


add(
    "SCREENING",
    "Primary candidates",
    len(flow)
)

for status, n in (
    flow["meta_eligibility_status"]
    .value_counts()
    .items()
):
    add(
        "META_ELIGIBILITY",
        status,
        n
    )


add(
    "FULLTEXT",
    "In fulltext extraction log",
    flow["fulltext"].sum()
)

add(
    "FULLTEXT",
    "Not in fulltext extraction log",
    (~flow["fulltext"]).sum()
)


for status, n in (
    flow["experimental_status"]
    .value_counts()
    .items()
):
    add(
        "EXPERIMENTAL",
        status,
        n
    )


add(
    "NUMERIC",
    "NUMERIC_HIGH",
    flow["numeric_high"].sum()
)


for status, n in (
    flow["scope_status"]
    .value_counts()
    .items()
):
    add(
        "SCOPE",
        status,
        n
    )


add(
    "QUANTITATIVE",
    "Studies in mortality meta dataset",
    flow["mortality_meta"].sum()
)


for status, n in (
    flow["final_path"]
    .value_counts()
    .items()
):
    add(
        "FINAL_PATH",
        status,
        n
    )


counts_df = pd.DataFrame(counts)


# ==========================================================
# GUARDAR
# ==========================================================

flow.to_csv(
    OUT_RECORDS,
    index=False,
    encoding="utf-8"
)

counts_df.to_csv(
    OUT_COUNTS,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# TXT
# ==========================================================

lines = []

lines.append(
    "PRISMA FLOW AUDIT"
)

lines.append(
    "=" * 75
)

lines.append(
    f"Primary candidate universe: {len(flow)}"
)

lines.append("")

for stage, g in counts_df.groupby(
    "stage",
    sort=False
):

    lines.append(stage)
    lines.append("-" * 75)

    for _, r in g.iterrows():
        lines.append(
            f"{r['category']}: {r['n']}"
        )

    lines.append("")


lines.append("CONSISTENCY CHECKS")
lines.append("-" * 75)

if issues:
    lines.extend(issues)
else:
    lines.append(
        "No structural inconsistencies detected."
    )


lines.append("")
lines.append("IMPORTANT")
lines.append("-" * 75)

lines.append(
    "NO_FULLTEXT_IN_EXTRACTION_LOG means only that the record "
    "does not occur in the full-text extraction log. It must not "
    "automatically be reported as 'full text unavailable' without "
    "verification of the preceding workflow."
)

lines.append(
    "Internal analytical units such as tables, treatment arms, "
    "comparisons, doses and mortality observations are not PRISMA "
    "study counts."
)

OUT_TXT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# ==========================================================
# TERMINAL
# ==========================================================

print("\n==========================================")
print("PRISMA FLOW AUDIT")
print("==========================================\n")

print(
    "Universo de candidatos:",
    len(flow)
)


print("\n==========================================")
print("META ELIGIBILITY")
print("==========================================\n")

print(
    flow["meta_eligibility_status"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("FULL TEXT")
print("==========================================\n")

print(
    "En extraction log:",
    int(flow["fulltext"].sum())
)

print(
    "No presentes en extraction log:",
    int((~flow["fulltext"]).sum())
)


print("\n==========================================")
print("EXPERIMENTAL STATUS")
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
print("RUTA FINAL")
print("==========================================\n")

print(
    flow["final_path"]
    .value_counts()
    .to_string()
)


print("\n==========================================")
print("QUANTITATIVE SYNTHESIS")
print("==========================================\n")

print(
    "Estudios en mortality meta dataset:",
    int(flow["mortality_meta"].sum())
)


print("\n==========================================")
print("CONSISTENCY CHECKS")
print("==========================================\n")

if issues:

    for x in issues:
        print("WARNING:", x)

else:
    print(
        "No structural inconsistencies detected."
    )


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_RECORDS)
print(OUT_COUNTS)
print(OUT_TXT)
