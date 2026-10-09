#!/usr/bin/env python3

import time
import requests
import pandas as pd

from pathlib import Path


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "04_pdfs" /
    "availability" /
    "fulltext_availability.csv"
)

XML_DIR = (
    PROJECT /
    "04_pdfs" /
    "xml"
)

PDF_DIR = (
    PROJECT /
    "04_pdfs" /
    "pdf"
)

LOG_DIR = (
    PROJECT /
    "04_pdfs" /
    "logs"
)

XML_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PDF_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = (
    LOG_DIR /
    "download_log.csv"
)


# ==========================================================
# SESIÓN HTTP
# ==========================================================

session = requests.Session()

session.headers.update({
    "User-Agent":
        "sitophilus-meta-analysis/1.0 "
        "(academic research)"
})


# ==========================================================
# FUNCIONES
# ==========================================================

def download_epmc_xml(
    study_id,
    pmcid
):

    if pd.isna(pmcid):
        return False, None, "missing_pmcid"

    pmcid = str(pmcid).strip()

    url = (
        "https://www.ebi.ac.uk/"
        "europepmc/webservices/rest/"
        f"{pmcid}/fullTextXML"
    )

    outfile = (
        XML_DIR /
        f"{study_id}_{pmcid}.xml"
    )

    try:

        r = session.get(
            url,
            timeout=60
        )

        if r.status_code != 200:

            return (
                False,
                None,
                f"http_{r.status_code}"
            )

        content = r.content

        # Comprobación mínima:
        # debe parecer XML/JATS
        if (
            b"<article" not in content[:5000]
            and
            b"<?xml" not in content[:500]
        ):

            return (
                False,
                None,
                "not_xml"
            )

        outfile.write_bytes(
            content
        )

        return (
            True,
            str(outfile),
            "ok"
        )

    except Exception as e:

        return (
            False,
            None,
            str(e)
        )


def download_pdf(
    study_id,
    pdf_url
):

    if pd.isna(pdf_url):
        return False, None, "missing_pdf_url"

    pdf_url = str(
        pdf_url
    ).strip()

    if not pdf_url:
        return False, None, "missing_pdf_url"

    outfile = (
        PDF_DIR /
        f"{study_id}.pdf"
    )

    try:

        r = session.get(
            pdf_url,
            timeout=90,
            allow_redirects=True
        )

        if r.status_code != 200:

            return (
                False,
                None,
                f"http_{r.status_code}"
            )

        content = r.content

        content_type = (
            r.headers
            .get(
                "Content-Type",
                ""
            )
            .lower()
        )

        # Verificar PDF real
        is_pdf_header = (
            content[:5]
            == b"%PDF-"
        )

        is_pdf_type = (
            "application/pdf"
            in content_type
        )

        if not (
            is_pdf_header
            or is_pdf_type
        ):

            return (
                False,
                None,
                "not_pdf"
            )

        # Evitar archivos absurdamente pequeños
        if len(content) < 5000:

            return (
                False,
                None,
                "pdf_too_small"
            )

        outfile.write_bytes(
            content
        )

        return (
            True,
            str(outfile),
            "ok"
        )

    except Exception as e:

        return (
            False,
            None,
            str(e)
        )


# ==========================================================
# LEER DISPONIBILIDAD
# ==========================================================

df = pd.read_csv(INPUT)

target = df[
    df["fulltext_status"].isin(
        [
            "OA_EUROPE_PMC",
            "OA_DIRECT_PDF"
        ]
    )
].copy()


print("\n==========================================")
print("DESCARGA DE TEXTO COMPLETO")
print("==========================================\n")

print(
    f"Objetivo total: {len(target)}"
)

print(
    "Europe PMC XML: "
    f"{(target['fulltext_status'] == 'OA_EUROPE_PMC').sum()}"
)

print(
    "PDF directo:    "
    f"{(target['fulltext_status'] == 'OA_DIRECT_PDF').sum()}"
)


# ==========================================================
# DESCARGAR
# ==========================================================

records = []

total = len(target)


for n, (_, row) in enumerate(
    target.iterrows(),
    start=1
):

    study_id = str(
        row["study_record_id"]
    )

    status = str(
        row["fulltext_status"]
    )

    success = False
    filepath = None
    message = None
    format_used = None


    # ------------------------------------------------------
    # EUROPE PMC
    # ------------------------------------------------------

    if status == "OA_EUROPE_PMC":

        success, filepath, message = (
            download_epmc_xml(
                study_id,
                row.get("pmcid")
            )
        )

        format_used = "XML"

        # Si falla XML pero existe URL PDF,
        # intentar PDF como respaldo.

        if (
            not success
            and pd.notna(
                row.get("pdf_url")
            )
        ):

            success, filepath, message = (
                download_pdf(
                    study_id,
                    row.get("pdf_url")
                )
            )

            format_used = "PDF_FALLBACK"


    # ------------------------------------------------------
    # PDF DIRECTO
    # ------------------------------------------------------

    elif status == "OA_DIRECT_PDF":

        success, filepath, message = (
            download_pdf(
                study_id,
                row.get("pdf_url")
            )
        )

        format_used = "PDF"


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

        "source_status":
            status,

        "format_attempted":
            format_used,

        "download_success":
            success,

        "filepath":
            filepath,

        "message":
            message
    })


    if (
        n % 20 == 0
        or n == total
    ):

        successes = sum(
            x["download_success"]
            for x in records
        )

        print(
            f"Procesados: {n}/{total} | "
            f"Descargados: {successes}"
        )


    # pausa pequeña
    time.sleep(0.15)


# ==========================================================
# LOG
# ==========================================================

log = pd.DataFrame(
    records
)

log.to_csv(
    LOG_FILE,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESUMEN
# ==========================================================

success_df = log[
    log["download_success"] == True
]

failed_df = log[
    log["download_success"] == False
]


print("\n==========================================")
print("RESULTADO DE DESCARGA")
print("==========================================\n")

print(
    f"Intentados:      {len(log)}"
)

print(
    f"Descargados:     {len(success_df)}"
)

print(
    f"Fallidos:        {len(failed_df)}"
)


print("\nPor formato:")

if len(success_df) > 0:

    print(
        success_df[
            "format_attempted"
        ]
        .value_counts()
        .to_string()
    )

else:

    print(
        "Ninguna descarga exitosa."
    )


print("\nFallos:")

if len(failed_df) > 0:

    print(
        failed_df[
            "message"
        ]
        .value_counts()
        .head(15)
        .to_string()
    )

else:

    print(
        "Ninguno."
    )


print("\nArchivos físicos:")

print(
    f"XML: "
    f"{len(list(XML_DIR.glob('*.xml')))}"
)

print(
    f"PDF: "
    f"{len(list(PDF_DIR.glob('*.pdf')))}"
)


print(
    f"\nLog:\n{LOG_FILE}"
)
