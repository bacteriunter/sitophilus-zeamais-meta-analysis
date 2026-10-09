#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

OUTDIR = PROJECT / "07_meta_analysis" / "final_summary"
OUTDIR.mkdir(parents=True, exist_ok=True)

AVAIL = PROJECT / "04_pdfs/availability/fulltext_availability.csv"
DOWNLOAD = PROJECT / "04_pdfs/logs/download_log.csv"
FULLTEXT = PROJECT / "05_extraction/fulltext_extraction_log.csv"
PRIMARY = PROJECT / "03_screening/final_candidates/primary_candidates_final.csv"

OUT_RECORDS = OUTDIR / "prisma_retrieval_final.csv"
OUT_COUNTS = OUTDIR / "prisma_retrieval_counts.csv"
OUT_TXT = OUTDIR / "prisma_retrieval_final.txt"


# ==========================================================
# CARGA
# ==========================================================

avail = pd.read_csv(AVAIL)
download = pd.read_csv(DOWNLOAD)
fulltext = pd.read_csv(FULLTEXT)
primary = pd.read_csv(PRIMARY)

ID = "study_record_id"

for df in [avail, download, fulltext, primary]:
    df[ID] = (
        df[ID]
        .astype(str)
        .str.strip()
    )


# ==========================================================
# CONTROLES INICIALES
# ==========================================================

print("\n==========================================")
print("ENTRADAS")
print("==========================================\n")

print("Primary candidates:", primary[ID].nunique())
print("Availability assessed:", avail[ID].nunique())
print("Download log records:", download[ID].nunique())
print("Fulltexts processed:", fulltext[ID].nunique())


# ==========================================================
# RESUMIR DOWNLOAD LOG POR ESTUDIO
# ==========================================================

download["download_success"] = (
    download["download_success"]
    .astype(str)
    .str.lower()
    .map({
        "true": True,
        "false": False
    })
)


def collapse_download(g):

    success = (
        g["download_success"]
        .fillna(False)
        .any()
    )

    formats = ";".join(
        sorted(
            set(
                g["format_attempted"]
                .dropna()
                .astype(str)
            )
        )
    )

    messages = ";".join(
        sorted(
            set(
                g["message"]
                .dropna()
                .astype(str)
            )
        )
    )

    paths = ";".join(
        sorted(
            set(
                g["filepath"]
                .dropna()
                .astype(str)
            )
        )
    )

    return pd.Series({
        "download_attempted": True,
        "any_download_success": success,
        "formats_attempted": formats,
        "download_messages": messages,
        "download_paths": paths
    })


download_summary = (
    download
    .groupby(ID, as_index=False)
    .apply(
        collapse_download,
        include_groups=False
    )
    .reset_index()
)

# Compatibilidad entre versiones de pandas
if "level_0" in download_summary.columns:
    download_summary = download_summary.drop(
        columns=["level_0"]
    )

if "index" in download_summary.columns:
    download_summary = download_summary.drop(
        columns=["index"]
    )


# ==========================================================
# UNIVERSO DE 441 REGISTROS ELEGIBLES PARA RETRIEVAL
# ==========================================================

x = avail.copy()

x = x.merge(
    download_summary,
    on=ID,
    how="left"
)

x["download_attempted"] = (
    x["download_attempted"]
    .fillna(False)
    .astype(bool)
)

x["any_download_success"] = (
    x["any_download_success"]
    .fillna(False)
    .astype(bool)
)

fulltext_ids = set(
    fulltext[ID]
    .dropna()
    .astype(str)
)

x["processed_fulltext"] = (
    x[ID].isin(fulltext_ids)
)


# ==========================================================
# VERIFICAR ARCHIVOS FÍSICOS
# ==========================================================

pdf_ids = {
    p.stem
    for p in (PROJECT / "04_pdfs/pdf").glob("SZ_*.pdf")
}

xml_ids = set()

for p in (PROJECT / "04_pdfs/xml").glob("SZ_*.xml"):

    # SZ_00067_PMC....xml -> SZ_00067
    parts = p.stem.split("_")

    if len(parts) >= 2:
        xml_ids.add(
            "_".join(parts[:2])
        )


x["pdf_present"] = x[ID].isin(pdf_ids)
x["xml_present"] = x[ID].isin(xml_ids)

x["file_present"] = (
    x["pdf_present"]
    |
    x["xml_present"]
)


# ==========================================================
# ESTADO FINAL DE RETRIEVAL
# ==========================================================

def retrieval_status(r):

    # Evidencia más fuerte:
    # realmente entró a extracción de texto completo
    if r["processed_fulltext"]:
        return "REPORT_RETRIEVED_PROCESSED"

    # Archivo existe aunque no haya sido procesado
    if r["file_present"]:
        return "REPORT_RETRIEVED_NOT_PROCESSED"

    # Log dice descarga exitosa pero archivo no está ahora
    if r["any_download_success"]:
        return "DOWNLOAD_SUCCESS_FILE_NOT_PRESENT"

    # No se localizó OA
    if r["fulltext_status"] == "NO_OA_FOUND":
        return "REPORT_NOT_RETRIEVED_NO_OA"

    # No DOI y no hay otra ruta registrada
    if r["fulltext_status"] == "NO_DOI":
        return "REPORT_NOT_RETRIEVED_NO_DOI"

    # Landing page pero no archivo recuperado
    if r["fulltext_status"] == "OA_LANDING_PAGE":
        return "REPORT_NOT_RETRIEVED_LANDING_ONLY"

    # Se esperaba PDF directo pero falló
    if r["fulltext_status"] == "OA_DIRECT_PDF":
        return "REPORT_NOT_RETRIEVED_DIRECT_PDF_FAILED"

    # Europe PMC esperado pero no quedó archivo
    if r["fulltext_status"] == "OA_EUROPE_PMC":
        return "REPORT_NOT_RETRIEVED_EPMC_FAILED"

    return "UNRESOLVED"


x["retrieval_final"] = x.apply(
    retrieval_status,
    axis=1
)


# ==========================================================
# VALIDACIONES
# ==========================================================

issues = []

if x[ID].nunique() != 441:
    issues.append(
        f"Availability tiene {x[ID].nunique()} IDs únicos, "
        "se esperaban 441."
    )

if x["processed_fulltext"].sum() != 151:
    issues.append(
        f"Se detectaron {x['processed_fulltext'].sum()} textos "
        "procesados dentro de availability; se esperaban 151."
    )


# ¿Hay fulltexts procesados fuera de los 441?
avail_ids = set(x[ID])

outside = (
    fulltext_ids
    -
    avail_ids
)

if outside:
    issues.append(
        f"{len(outside)} fulltexts procesados no aparecen "
        "en fulltext_availability."
    )


# ==========================================================
# CONTEOS
# ==========================================================

counts = (
    x["retrieval_final"]
    .value_counts()
    .rename_axis("retrieval_status")
    .reset_index(name="n")
)

counts["percent_of_441"] = (
    counts["n"]
    / len(x)
    * 100
).round(2)


# ==========================================================
# RESUMEN PRISMA
# ==========================================================

retrieved = (
    x["retrieval_final"]
    .isin([
        "REPORT_RETRIEVED_PROCESSED",
        "REPORT_RETRIEVED_NOT_PROCESSED"
    ])
    .sum()
)

not_retrieved = (
    x["retrieval_final"]
    .str.startswith(
        "REPORT_NOT_RETRIEVED"
    )
    .sum()
)

technical_unresolved = (
    len(x)
    -
    retrieved
    -
    not_retrieved
)


# ==========================================================
# GUARDAR
# ==========================================================

x.to_csv(
    OUT_RECORDS,
    index=False,
    encoding="utf-8"
)

counts.to_csv(
    OUT_COUNTS,
    index=False,
    encoding="utf-8"
)


lines = []

lines.append(
    "FINAL PRISMA RETRIEVAL AUDIT"
)

lines.append(
    "=" * 75
)

lines.append(
    f"Reports sought for retrieval: {len(x)}"
)

lines.append(
    f"Reports retrieved (file/process evidence): {retrieved}"
)

lines.append(
    f"Reports not retrieved: {not_retrieved}"
)

lines.append(
    f"Technical/unresolved states: {technical_unresolved}"
)

lines.append("")

for _, r in counts.iterrows():
    lines.append(
        f"{r['retrieval_status']}: "
        f"{r['n']} ({r['percent_of_441']}%)"
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
lines.append("NOTE")
lines.append("-" * 75)

lines.append(
    "The 42 REVIEW_ONLY records were not part of the "
    "441 reports assessed for automated full-text availability."
)

lines.append(
    "Retrieval status is based on the archived availability "
    "assessment, download log, physical PDF/XML files, and "
    "full-text extraction log."
)

OUT_TXT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# ==========================================================
# TERMINAL
# ==========================================================

print("\n==========================================")
print("ESTADO FINAL DE RECUPERACIÓN")
print("==========================================\n")

print(
    counts.to_string(index=False)
)


print("\n==========================================")
print("RESUMEN")
print("==========================================\n")

print("Reports sought:", len(x))
print("Retrieved:", int(retrieved))
print("Not retrieved:", int(not_retrieved))
print(
    "Technical/unresolved:",
    int(technical_unresolved)
)


print("\n==========================================")
print("ARCHIVOS FÍSICOS")
print("==========================================\n")

print("PDF:", len(pdf_ids))
print("XML:", len(xml_ids))
print(
    "PDF + XML IDs únicos:",
    len(pdf_ids | xml_ids)
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
