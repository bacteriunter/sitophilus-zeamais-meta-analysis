#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

OUTDIR = PROJECT / "07_meta_analysis" / "final_summary"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUTDIR / "project_flow_summary.csv"
OUT_TXT = OUTDIR / "project_flow_summary.txt"


# ==========================================================
# FUNCIONES
# ==========================================================

def read_csv(relpath):
    path = PROJECT / relpath

    if not path.exists():
        print(f"WARNING: no existe {path}")
        return None

    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"WARNING: no se pudo leer {path}: {e}")
        return None


def nrows(df):
    return 0 if df is None else len(df)


def nunique(df, column="study_record_id"):
    if df is None:
        return 0

    if column not in df.columns:
        return 0

    return df[column].dropna().nunique()


records = []


def add(stage, category, n, unit, note=""):
    records.append({
        "stage": stage,
        "category": category,
        "n": int(n),
        "unit": unit,
        "note": note
    })


# ==========================================================
# 1. BÚSQUEDA
# ==========================================================

pubmed_raw = read_csv(
    "01_search/pubmed_raw.csv"
)

openalex_raw = read_csv(
    "01_search/openalex_raw.csv"
)

pubmed_unique = read_csv(
    "02_deduplication/pubmed_unique.csv"
)

master_unique = read_csv(
    "02_deduplication/master_unique.csv"
)

add(
    "SEARCH",
    "PubMed raw",
    nrows(pubmed_raw),
    "records"
)

add(
    "SEARCH",
    "OpenAlex raw",
    nrows(openalex_raw),
    "records"
)

add(
    "DEDUPLICATION",
    "PubMed unique",
    nrows(pubmed_unique),
    "records"
)

add(
    "DEDUPLICATION",
    "Master unique",
    nrows(master_unique),
    "records"
)


# ==========================================================
# 2. SCREENING
# ==========================================================

screening = read_csv(
    "03_screening/screening_scored.csv"
)

high = read_csv(
    "03_screening/high_priority.csv"
)

medium = read_csv(
    "03_screening/medium_priority.csv"
)

no_abs = read_csv(
    "03_screening/no_abstract.csv"
)

refined = read_csv(
    "03_screening/refined/refined_candidates.csv"
)

primary = read_csv(
    "03_screening/final_candidates/primary_candidates_final.csv"
)

meta_high = read_csv(
    "03_screening/meta_eligibility/META_HIGH.csv"
)

meta_possible = read_csv(
    "03_screening/meta_eligibility/META_POSSIBLE.csv"
)

review_only = read_csv(
    "03_screening/meta_eligibility/REVIEW_ONLY.csv"
)

add(
    "SCREENING",
    "Screened/scored",
    nrows(screening),
    "records"
)

add(
    "SCREENING",
    "HIGH",
    nrows(high),
    "records"
)

add(
    "SCREENING",
    "MEDIUM",
    nrows(medium),
    "records"
)

add(
    "SCREENING",
    "NO_ABSTRACT",
    nrows(no_abs),
    "records"
)

add(
    "SCREENING_REFINED",
    "Refined candidates",
    nrows(refined),
    "records"
)

add(
    "SCREENING_FINAL",
    "Primary candidates final",
    nrows(primary),
    "records"
)

add(
    "META_ELIGIBILITY",
    "META_HIGH",
    nrows(meta_high),
    "records"
)

add(
    "META_ELIGIBILITY",
    "META_POSSIBLE",
    nrows(meta_possible),
    "records"
)

add(
    "META_ELIGIBILITY",
    "REVIEW_ONLY",
    nrows(review_only),
    "records"
)


# ==========================================================
# 3. TEXTO COMPLETO
# ==========================================================

fulltext = read_csv(
    "05_extraction/fulltext_extraction_log.csv"
)

experimental = read_csv(
    "05_extraction/experimental_audit/experimental_audit_all.csv"
)

extract_high = read_csv(
    "05_extraction/experimental_audit/EXTRACT_HIGH.csv"
)

extract_possible = read_csv(
    "05_extraction/experimental_audit/EXTRACT_POSSIBLE.csv"
)

manual = read_csv(
    "05_extraction/experimental_audit/MANUAL_CHECK.csv"
)

numeric = read_csv(
    "05_extraction/numeric_audit/numeric_audit.csv"
)

numeric_high = read_csv(
    "05_extraction/numeric_audit/NUMERIC_HIGH.csv"
)

scope = read_csv(
    "05_extraction/scope_eligibility/scope_eligibility_all.csv"
)

scope_include = read_csv(
    "05_extraction/scope_eligibility/INCLUDE.csv"
)

scope_review = read_csv(
    "05_extraction/scope_eligibility/REVIEW.csv"
)

scope_exclude = read_csv(
    "05_extraction/scope_eligibility/EXCLUDE_AUTO.csv"
)

add(
    "FULLTEXT",
    "Full-text extraction log",
    nrows(fulltext),
    "studies"
)

add(
    "EXPERIMENTAL_AUDIT",
    "All audited",
    nrows(experimental),
    "studies"
)

add(
    "EXPERIMENTAL_AUDIT",
    "EXTRACT_HIGH",
    nrows(extract_high),
    "studies"
)

add(
    "EXPERIMENTAL_AUDIT",
    "EXTRACT_POSSIBLE",
    nrows(extract_possible),
    "studies"
)

add(
    "EXPERIMENTAL_AUDIT",
    "MANUAL_CHECK",
    nrows(manual),
    "studies"
)

add(
    "NUMERIC_AUDIT",
    "All numeric audit",
    nrows(numeric),
    "studies"
)

add(
    "NUMERIC_AUDIT",
    "NUMERIC_HIGH",
    nrows(numeric_high),
    "studies"
)

add(
    "SCOPE",
    "Scope audited",
    nrows(scope),
    "studies"
)

add(
    "SCOPE",
    "INCLUDE",
    nrows(scope_include),
    "studies"
)

add(
    "SCOPE",
    "REVIEW",
    nrows(scope_review),
    "studies"
)

add(
    "SCOPE",
    "EXCLUDE_AUTO",
    nrows(scope_exclude),
    "studies"
)


# ==========================================================
# 4. MORTALIDAD
# ==========================================================

mortality_tables = read_csv(
    "05_extraction/mortality/tables/mortality_tables.csv"
)

selected_mortality = read_csv(
    "05_extraction/mortality/selected_tables/selected_mortality_tables.csv"
)

mortality_values = read_csv(
    "05_extraction/mortality/values/mortality_values_raw.csv"
)

mortality_expanded = read_csv(
    "05_extraction/mortality/analytic/mortality_analytic_expanded.csv"
)

comparison_final = read_csv(
    "06_effect_sizes/mortality_comparison_map_final.csv"
)

variance_ready = read_csv(
    "06_effect_sizes/mortality_variance_ready.csv"
)

meta = read_csv(
    "07_meta_analysis/mortality_meta_dataset.csv"
)

add(
    "MORTALITY",
    "Detected mortality tables",
    nrows(mortality_tables),
    "tables"
)

add(
    "MORTALITY",
    "Selected mortality tables",
    nrows(selected_mortality),
    "tables"
)

add(
    "MORTALITY",
    "Candidate mortality values",
    nrows(mortality_values),
    "rows"
)

add(
    "MORTALITY",
    "Expanded analytic dataset",
    nrows(mortality_expanded),
    "observations"
)

add(
    "MORTALITY",
    "Final comparison map",
    nrows(comparison_final),
    "comparisons"
)

add(
    "MORTALITY",
    "Variance-ready",
    nrows(variance_ready),
    "comparisons"
)

add(
    "MORTALITY_META",
    "Final meta dataset",
    nrows(meta),
    "observations"
)

add(
    "MORTALITY_META",
    "Studies in final meta dataset",
    nunique(meta),
    "studies"
)


# ==========================================================
# 5. RESULTADOS DEL MODELO
# ==========================================================

model = read_csv(
    "07_meta_analysis/multilevel_mortality_results.csv"
)

partition = read_csv(
    "07_meta_analysis/mortality_variance_partition.csv"
)

if model is not None:
    add(
        "MODEL",
        "Multilevel model result rows",
        len(model),
        "rows",
        "PRIMARY_ALL + sensitivity analyses"
    )

if partition is not None:
    add(
        "MODEL",
        "Variance partition components",
        len(partition),
        "components"
    )


# ==========================================================
# 6. OUTCOMES SECUNDARIOS
# ==========================================================

secondary = read_csv(
    "05_extraction/secondary_outcomes/secondary_outcome_audit.csv"
)

if secondary is not None and {
    "outcome",
    "extractability"
}.issubset(secondary.columns):

    for outcome in [
        "PROGENY_F1",
        "WEIGHT_LOSS",
        "GERMINATION"
    ]:

        x = secondary[
            secondary["outcome"] == outcome
        ]

        add(
            "SECONDARY_OUTCOMES",
            f"{outcome} detected",
            len(x),
            "studies"
        )

        add(
            "SECONDARY_OUTCOMES",
            f"{outcome} HIGH",
            (
                x["extractability"] == "HIGH"
            ).sum(),
            "studies"
        )


# ==========================================================
# F1 VALIDATION
# ==========================================================

f1 = read_csv(
    "05_extraction/secondary_outcomes/progeny/final/"
    "progeny_tables_validated.csv"
)

if f1 is not None:

    valid_f1 = f1[
        f1["final_status"].isin(
            ["VALID_STRONG", "VALID"]
        )
    ].copy()

    # X-ray study already excluded from scope
    valid_f1 = valid_f1[
        valid_f1["study_record_id"] != "SZ_00213"
    ]

    add(
        "SECONDARY_F1",
        "Validated F1 tables",
        len(valid_f1),
        "tables"
    )

    add(
        "SECONDARY_F1",
        "Studies with validated F1 tables",
        nunique(valid_f1),
        "studies"
    )


# ==========================================================
# WEIGHT LOSS
# ==========================================================

wl = read_csv(
    "05_extraction/secondary_outcomes/weight_loss/"
    "weightloss_table_audit.csv"
)

if wl is not None:

    wl_high = wl[
        wl["status"] == "HIGH"
    ]

    add(
        "SECONDARY_WEIGHT_LOSS",
        "HIGH tables",
        len(wl_high),
        "tables"
    )

    add(
        "SECONDARY_WEIGHT_LOSS",
        "Studies with HIGH tables",
        nunique(wl_high),
        "studies"
    )


# ==========================================================
# GERMINATION
# ==========================================================

germ = read_csv(
    "05_extraction/secondary_outcomes/germination/"
    "germination_table_audit.csv"
)

if germ is not None:

    germ_high = germ[
        germ["status"] == "HIGH"
    ]

    add(
        "SECONDARY_GERMINATION",
        "HIGH tables",
        len(germ_high),
        "tables"
    )

    add(
        "SECONDARY_GERMINATION",
        "Studies with HIGH tables",
        nunique(germ_high),
        "studies"
    )


# ==========================================================
# DATAFRAME FINAL
# ==========================================================

summary = pd.DataFrame(records)

summary.to_csv(
    OUT_CSV,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESUMEN TXT
# ==========================================================

lines = []

lines.append(
    "SYSTEMATIC REVIEW / QUANTITATIVE SYNTHESIS"
)
lines.append(
    "=" * 70
)

for stage, g in summary.groupby(
    "stage",
    sort=False
):

    lines.append("")
    lines.append(stage)
    lines.append("-" * 70)

    for _, r in g.iterrows():

        txt = (
            f"{r['category']}: "
            f"{r['n']} {r['unit']}"
        )

        if r["note"]:
            txt += f" | {r['note']}"

        lines.append(txt)


lines.append("")
lines.append("=" * 70)
lines.append("ANALYTIC DECISIONS")
lines.append("=" * 70)

lines.append(
    "Mortality: primary quantitative outcome."
)

lines.append(
    "Primary mortality synthesis: multilevel hierarchical "
    "model of reported final mortality."
)

lines.append(
    "F1/progeny: systematic/descriptive synthesis; "
    "not pooled quantitatively because reporting structures "
    "and variance information were insufficiently consistent."
)

lines.append(
    "Weight loss: systematic/descriptive synthesis; "
    "only three studies reached the strict HIGH table criterion."
)

lines.append(
    "Germination: systematic/descriptive synthesis; "
    "only three studies reached the strict HIGH table criterion."
)

lines.append(
    "Different secondary outcome scales were not combined."
)

lines.append(
    "Synthetic comparator arms were not treated as natural "
    "interventions in the primary synthesis."
)

lines.append(
    "Temperature/humidity/storage conditions were treated as "
    "experimental conditions or potential moderators rather "
    "than intervention classes."
)


OUT_TXT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# ==========================================================
# TERMINAL
# ==========================================================

print("\n==========================================")
print("CONSOLIDACIÓN FINAL")
print("==========================================\n")

for stage, g in summary.groupby(
    "stage",
    sort=False
):

    print(f"\n--- {stage} ---")

    for _, r in g.iterrows():

        print(
            f"{r['category']}: "
            f"{r['n']} {r['unit']}"
        )


print("\n==========================================")
print("DECISIÓN FINAL POR OUTCOME")
print("==========================================\n")

print(
    "MORTALITY   -> QUANTITATIVE PRIMARY"
)

print(
    "PROGENY_F1  -> SYSTEMATIC / DESCRIPTIVE"
)

print(
    "WEIGHT_LOSS -> SYSTEMATIC / DESCRIPTIVE"
)

print(
    "GERMINATION -> SYSTEMATIC / DESCRIPTIVE"
)


print("\n==========================================")
print("ARCHIVOS")
print("==========================================\n")

print(OUT_CSV)
print(OUT_TXT)
