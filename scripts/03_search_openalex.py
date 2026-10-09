#!/usr/bin/env python3

import requests
import pandas as pd
from pathlib import Path
import time

PROJECT = Path.home() / "sitophilus_meta"
OUTDIR = PROJECT / "01_search"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "openalex_raw.csv"

# Coloca el mismo correo utilizado anteriormente
EMAIL = "bacteriunter@gmail.com"

queries = {
    "general":
        '"Sitophilus zeamais" maize',

    "botanicals":
        '"Sitophilus zeamais" botanical plant extract powder essential oil maize',

    "natural_materials":
        '"Sitophilus zeamais" ash diatomaceous earth clay maize',

    "temperature":
        '"Sitophilus zeamais" temperature thermal heat cold maize',

    "storage":
        '"Sitophilus zeamais" storage stored hermetic maize',

    "maize_origin":
        '"Sitophilus zeamais" native maize local maize landrace'
}


def reconstruct_abstract(inv_index):

    if not inv_index:
        return ""

    positions = []

    for word, indexes in inv_index.items():
        for pos in indexes:
            positions.append((pos, word))

    positions.sort()

    return " ".join(word for _, word in positions)


def search_openalex(query, category):

    url = "https://api.openalex.org/works"

    cursor = "*"

    records = []

    while cursor:

        params = {
            "search": query,
            "per-page": 200,
            "cursor": cursor,
            "mailto": EMAIL
        }

        response = requests.get(
            url,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        for work in results:

            doi = work.get("doi") or ""

            doi = doi.replace(
                "https://doi.org/",
                ""
            )

            source = ""

            primary_location = work.get(
                "primary_location"
            )

            if primary_location:
                source_info = primary_location.get("source")

                if source_info:
                    source = source_info.get(
                        "display_name",
                        ""
                    ) or ""

            authors = []

            for auth in work.get("authorships", []):

                author_info = auth.get("author")

                if author_info:
                    name = author_info.get(
                        "display_name"
                    )

                    if name:
                        authors.append(name)

            abstract = reconstruct_abstract(
                work.get(
                    "abstract_inverted_index"
                )
            )

            records.append({

                "source": "OpenAlex",

                "search_category": category,

                "openalex_id":
                    work.get("id", ""),

                "doi": doi,

                "title":
                    work.get(
                        "display_name",
                        ""
                    ),

                "abstract": abstract,

                "authors":
                    "; ".join(authors),

                "journal": source,

                "year":
                    work.get(
                        "publication_year",
                        ""
                    ),

                "type":
                    work.get(
                        "type",
                        ""
                    ),

                "cited_by_count":
                    work.get(
                        "cited_by_count",
                        0
                    )
            })

        meta = data.get("meta", {})

        cursor = meta.get("next_cursor")

        print(
            f"    recuperados: {len(records)}",
            end="\r"
        )

        if not results:
            break

        time.sleep(0.15)

    return records


print("\n==========================================")
print("SITOPHILUS ZEAMAIS — OPENALEX SEARCH")
print("==========================================\n")

all_records = []

for category, query in queries.items():

    print(f"\nBuscando: {category}")

    try:

        records = search_openalex(
            query,
            category
        )

        print(
            f"\n  Registros encontrados: "
            f"{len(records)}"
        )

        all_records.extend(records)

    except Exception as e:

        print(
            f"\nERROR en {category}: {e}"
        )


df = pd.DataFrame(all_records)

df.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

print("\n==========================================")
print("RESULTADO")
print("==========================================")

print(f"Registros totales: {len(df)}")

if len(df) > 0:

    print(
        f"OpenAlex ID únicos: "
        f"{df['openalex_id'].nunique()}"
    )

    print(
        f"DOI disponibles: "
        f"{df['doi'].fillna('').ne('').sum()}"
    )

    print(
        f"Con resumen: "
        f"{df['abstract'].fillna('').ne('').sum()}"
    )

    print("\nRegistros por búsqueda:")

    print(
        df.groupby("search_category")
        .size()
        .sort_values(ascending=False)
    )

print(
    f"\nArchivo generado:\n{OUTPUT}"
)
