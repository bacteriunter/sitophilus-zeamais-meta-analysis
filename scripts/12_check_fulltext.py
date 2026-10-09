#!/usr/bin/env python3

import os
import time
import requests
import pandas as pd

from pathlib import Path
from urllib.parse import quote


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "03_screening" /
    "meta_eligibility" /
    "meta_eligibility_all.csv"
)

OUTDIR = (
    PROJECT /
    "04_pdfs" /
    "availability"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTDIR /
    "fulltext_availability.csv"
)

EMAIL = os.environ.get(
    "UNPAYWALL_EMAIL"
)

if not EMAIL:
    raise RuntimeError(
        "\nNo se encontró UNPAYWALL_EMAIL.\n"
        "Ejecuta antes:\n\n"
        'export UNPAYWALL_EMAIL="tu_correo@dominio.com"\n'
    )


# ==========================================================
# FUNCIONES
# ==========================================================

def clean_doi(value):

    if pd.isna(value):
        return None

    doi = str(value).strip()

    if not doi:
        return None

    doi = doi.replace(
        "https://doi.org/",
        ""
    )

    doi = doi.replace(
        "http://doi.org/",
        ""
    )

    doi = doi.replace(
        "doi:",
        ""
    )

    doi = doi.strip()

    if not doi.startswith("10."):
        return None

    return doi


def unpaywall_lookup(doi):

    url = (
        "https://api.unpaywall.org/v2/"
        + quote(doi, safe="")
    )

    try:

        r = requests.get(
            url,
            params={
                "email": EMAIL
            },
            timeout=30
        )

        if r.status_code == 404:

            return {
                "unpaywall_found": False,
                "is_oa": False,
                "oa_status": None,
                "pdf_url": None,
                "landing_url": None,
                "host_type": None,
                "version": None
            }

        r.raise_for_status()

        data = r.json()

        best = (
            data.get(
                "best_oa_location"
            )
            or {}
        )

        return {
            "unpaywall_found": True,

            "is_oa":
                bool(
                    data.get("is_oa")
                ),

            "oa_status":
                data.get(
                    "oa_status"
                ),

            "pdf_url":
                best.get(
                    "url_for_pdf"
                ),

            "landing_url":
                best.get(
                    "url"
                ),

            "host_type":
                best.get(
                    "host_type"
                ),

            "version":
                best.get(
                    "version"
                )
        }

    except Exception as e:

        return {
            "unpaywall_found": False,
            "is_oa": False,
            "oa_status": None,
            "pdf_url": None,
            "landing_url": None,
            "host_type": None,
            "version": None,
            "error": str(e)
        }


def europepmc_lookup(doi):

    if not doi:

        return {
            "epmc_found": False,
            "pmcid": None,
            "epmc_open_access": False
        }

    url = (
        "https://www.ebi.ac.uk/"
        "europepmc/webservices/rest/search"
    )

    query = f'DOI:"{doi}"'

    try:

        r = requests.get(
            url,
            params={
                "query": query,
                "format": "json",
                "pageSize": 5
            },
            timeout=30
        )

        r.raise_for_status()

        data = r.json()

        results = (
            data
            .get("resultList", {})
            .get("result", [])
        )

        if not results:

            return {
                "epmc_found": False,
                "pmcid": None,
                "epmc_open_access": False
            }

        record = results[0]

        pmcid = record.get(
            "pmcid"
        )

        is_oa = (
            record.get(
                "isOpenAccess"
            )
            == "Y"
        )

        return {
            "epmc_found": True,
            "pmcid": pmcid,
            "epmc_open_access":
                bool(
                    pmcid and is_oa
                )
        }

    except Exception as e:

        return {
            "epmc_found": False,
            "pmcid": None,
            "epmc_open_access": False,
            "epmc_error": str(e)
        }


# ==========================================================
# LEER CANDIDATOS
# ==========================================================

df = pd.read_csv(INPUT)

df = df[
    df["meta_priority"].isin(
        [
            "META_HIGH",
            "META_POSSIBLE"
        ]
    )
].copy()

df["doi_clean"] = (
    df["doi"]
    .apply(clean_doi)
)


print(
    "\n=========================================="
)

print(
    "BÚSQUEDA DE TEXTO COMPLETO"
)

print(
    "==========================================\n"
)

print(
    f"Candidatos: {len(df)}"
)

print(
    f"Con DOI: {df['doi_clean'].notna().sum()}"
)

print(
    f"Sin DOI: {df['doi_clean'].isna().sum()}"
)


# ==========================================================
# CONSULTAS
# ==========================================================

records = []

total = len(df)


for n, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

    doi = row["doi_clean"]

    result = {
        "study_record_id":
            row["study_record_id"],

        "meta_priority":
            row["meta_priority"],

        "meta_score":
            row["meta_score"],

        "year":
            row["year"],

        "title":
            row["title"],

        "journal":
            row["journal"],

        "doi":
            doi,

        "outcomes_detected":
            row["outcomes_detected"]
    }


    if doi:

        up = unpaywall_lookup(
            doi
        )

        epmc = europepmc_lookup(
            doi
        )

        result.update(up)
        result.update(epmc)

        # Pequeña pausa para ser respetuosos
        # con los servicios públicos.
        time.sleep(0.12)

    else:

        result.update({
            "unpaywall_found": False,
            "is_oa": False,
            "oa_status": None,
            "pdf_url": None,
            "landing_url": None,
            "host_type": None,
            "version": None,
            "epmc_found": False,
            "pmcid": None,
            "epmc_open_access": False
        })


    # --------------------------------------
    # DISPONIBILIDAD
    # --------------------------------------

    if result.get(
        "epmc_open_access"
    ):

        availability = (
            "OA_EUROPE_PMC"
        )

    elif result.get(
        "pdf_url"
    ):

        availability = (
            "OA_DIRECT_PDF"
        )

    elif result.get(
        "is_oa"
    ):

        availability = (
            "OA_LANDING_PAGE"
        )

    elif not doi:

        availability = (
            "NO_DOI"
        )

    else:

        availability = (
            "NO_OA_FOUND"
        )


    result[
        "fulltext_status"
    ] = availability

    records.append(
        result
    )


    if (
        n % 25 == 0
        or n == total
    ):

        print(
            f"Procesados: "
            f"{n}/{total}"
        )


# ==========================================================
# RESULTADOS
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
# ARCHIVOS POR CATEGORÍA
# ==========================================================

for status in [
    "OA_EUROPE_PMC",
    "OA_DIRECT_PDF",
    "OA_LANDING_PAGE",
    "NO_OA_FOUND",
    "NO_DOI"
]:

    subset = out[
        out["fulltext_status"]
        == status
    ]

    subset.to_csv(
        OUTDIR /
        f"{status}.csv",
        index=False,
        encoding="utf-8"
    )


# ==========================================================
# RESUMEN
# ==========================================================

print(
    "\n=========================================="
)

print(
    "DISPONIBILIDAD DE TEXTO COMPLETO"
)

print(
    "==========================================\n"
)

counts = (
    out["fulltext_status"]
    .value_counts()
)

for status in [
    "OA_EUROPE_PMC",
    "OA_DIRECT_PDF",
    "OA_LANDING_PAGE",
    "NO_OA_FOUND",
    "NO_DOI"
]:

    print(
        f"{status:20s} "
        f"{counts.get(status, 0)}"
    )


accessible = out[
    out["fulltext_status"].isin(
        [
            "OA_EUROPE_PMC",
            "OA_DIRECT_PDF",
            "OA_LANDING_PAGE"
        ]
    )
]

print(
    "\nTotal con alguna "
    f"ruta OA: {len(accessible)}"
)

print(
    f"Sin ruta OA automática: "
    f"{len(out) - len(accessible)}"
)


print(
    "\nPor prioridad:"
)

summary = pd.crosstab(
    out["meta_priority"],
    out["fulltext_status"]
)

print(
    summary.to_string()
)


print(
    "\nArchivo principal:"
)

print(
    OUTPUT
)
