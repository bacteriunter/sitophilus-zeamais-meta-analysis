#!/usr/bin/env python3

from Bio import Entrez
import pandas as pd
from pathlib import Path
import time

# ==========================================
# CONFIGURACIÓN
# ==========================================

Entrez.email = "bacteriunter@gmail.com"

PROJECT = Path.home() / "sitophilus_meta"
OUTDIR = PROJECT / "01_search"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# BÚSQUEDAS
# ==========================================

queries = {

    "general":
        '"Sitophilus zeamais"[Title/Abstract] AND '
        '(maize[Title/Abstract] OR corn[Title/Abstract] OR '
        '"Zea mays"[Title/Abstract])',

    "botanicals":
        '"Sitophilus zeamais"[Title/Abstract] AND '
        '(botanical*[Title/Abstract] OR plant*[Title/Abstract] OR '
        'extract*[Title/Abstract] OR powder*[Title/Abstract] OR '
        '"essential oil"[Title/Abstract] OR '
        '"essential oils"[Title/Abstract])',

    "natural_materials":
        '"Sitophilus zeamais"[Title/Abstract] AND '
        '(ash[Title/Abstract] OR ashes[Title/Abstract] OR '
        '"diatomaceous earth"[Title/Abstract] OR '
        'clay[Title/Abstract])',

    "temperature":
        '"Sitophilus zeamais"[Title/Abstract] AND '
        '(temperature[Title/Abstract] OR thermal[Title/Abstract] OR '
        'heat[Title/Abstract] OR cold[Title/Abstract])',

    "storage":
        '"Sitophilus zeamais"[Title/Abstract] AND '
        '(storage[Title/Abstract] OR stored[Title/Abstract] OR '
        'hermetic[Title/Abstract])',

    "maize_origin":
        '"Sitophilus zeamais"[Title/Abstract] AND '
        '("native maize"[Title/Abstract] OR '
        '"local maize"[Title/Abstract] OR '
        '"maize variety"[Title/Abstract] OR '
        '"maize varieties"[Title/Abstract] OR '
        'landrace*[Title/Abstract])'
}

# ==========================================
# FUNCIÓN DE BÚSQUEDA
# ==========================================

def search_pubmed(query):

    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=10000
    )

    record = Entrez.read(handle)
    handle.close()

    return record["IdList"]


def fetch_articles(ids, category):

    records = []

    if not ids:
        return records

    # Recuperación por bloques
    for start in range(0, len(ids), 200):

        batch = ids[start:start + 200]

        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(batch),
            rettype="medline",
            retmode="text"
        )

        from Bio import Medline

        articles = Medline.parse(handle)

        for article in articles:

            records.append({

                "source": "PubMed",

                "search_category": category,

                "pmid": article.get("PMID", ""),

                "doi": next(
                    (
                        x
                        for x in article.get("AID", [])
                        if "[doi]" in x
                    ),
                    ""
                ).replace(" [doi]", ""),

                "title": article.get("TI", ""),

                "abstract": article.get("AB", ""),

                "authors": "; ".join(
                    article.get("AU", [])
                ),

                "journal": article.get("JT", ""),

                "year": article.get("DP", "")[:4],

                "language": "; ".join(
                    article.get("LA", [])
                )
            })

        handle.close()

        time.sleep(0.4)

    return records


# ==========================================
# EJECUCIÓN
# ==========================================

all_records = []

print("\n==========================================")
print("SITOPHILUS ZEAMAIS — PUBMED SEARCH")
print("==========================================\n")

for category, query in queries.items():

    print(f"Buscando: {category}")

    ids = search_pubmed(query)

    print(f"  Registros encontrados: {len(ids)}")

    records = fetch_articles(ids, category)

    all_records.extend(records)

    time.sleep(0.5)


# ==========================================
# GUARDAR RESULTADOS
# ==========================================

df = pd.DataFrame(all_records)

outfile = OUTDIR / "pubmed_raw.csv"

df.to_csv(
    outfile,
    index=False,
    encoding="utf-8"
)

print("\n==========================================")
print("RESULTADO")
print("==========================================")

print(f"Registros totales: {len(df)}")

if len(df) > 0:

    print(
        f"PMID únicos: "
        f"{df['pmid'].nunique()}"
    )

    print("\nRegistros por búsqueda:")

    print(
        df.groupby("search_category")
        .size()
        .sort_values(ascending=False)
    )

print(f"\nArchivo: {outfile}")
