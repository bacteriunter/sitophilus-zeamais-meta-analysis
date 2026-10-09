#!/usr/bin/env python3

import re
import subprocess
import pandas as pd
import xml.etree.ElementTree as ET

from pathlib import Path


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

PROJECT = Path.home() / "sitophilus_meta"

LOG = (
    PROJECT /
    "04_pdfs" /
    "logs" /
    "download_log.csv"
)

TEXT_DIR = (
    PROJECT /
    "05_extraction" /
    "fulltext"
)

TEXT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    PROJECT /
    "05_extraction" /
    "fulltext_extraction_log.csv"
)


# ==========================================================
# LIMPIEZA DE TEXTO
# ==========================================================

def clean_text(text):

    text = text.replace(
        "\x00",
        " "
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# ==========================================================
# XML -> TEXTO
# ==========================================================

def extract_xml(path):

    try:

        tree = ET.parse(path)

        root = tree.getroot()

        parts = []

        for elem in root.iter():

            tag = elem.tag.split("}")[-1]

            if tag in [
                "article-title",
                "title",
                "p",
                "th",
                "td",
                "caption"
            ]:

                text = " ".join(
                    elem.itertext()
                )

                text = clean_text(
                    text
                )

                if text:
                    parts.append(
                        text
                    )

        fulltext = "\n\n".join(
            parts
        )

        return fulltext, None

    except Exception as e:

        return "", str(e)


# ==========================================================
# PDF -> TEXTO
# ==========================================================

def extract_pdf(path):

    try:

        result = subprocess.run(
            [
                "pdftotext",
                "-layout",
                str(path),
                "-"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:

            return (
                "",
                result.stderr.strip()
            )

        text = clean_text(
            result.stdout
        )

        return text, None

    except Exception as e:

        return "", str(e)


# ==========================================================
# LEER LOG
# ==========================================================

df = pd.read_csv(LOG)

df = df[
    df["download_success"] == True
].copy()


print("\n==========================================")
print("EXTRACCIÓN DE TEXTO")
print("==========================================\n")

print(
    f"Archivos descargados: {len(df)}"
)


# ==========================================================
# EXTRAER
# ==========================================================

records = []

total = len(df)


for n, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

    study_id = str(
        row["study_record_id"]
    )

    filepath = Path(
        str(row["filepath"])
    )

    suffix = (
        filepath
        .suffix
        .lower()
    )

    text = ""
    error = None
    source_format = None


    if suffix == ".xml":

        source_format = "XML"

        text, error = extract_xml(
            filepath
        )


    elif suffix == ".pdf":

        source_format = "PDF"

        text, error = extract_pdf(
            filepath
        )


    else:

        source_format = "UNKNOWN"

        error = (
            f"unsupported_format_{suffix}"
        )


    # ------------------------------------------------------
    # CONTROL DE CALIDAD
    # ------------------------------------------------------

    char_count = len(text)

    word_count = len(
        text.split()
    )

    if char_count >= 10000:

        extraction_quality = "GOOD"

    elif char_count >= 3000:

        extraction_quality = "PARTIAL"

    elif char_count > 0:

        extraction_quality = "POOR"

    else:

        extraction_quality = "FAILED"


    # ------------------------------------------------------
    # GUARDAR TEXTO
    # ------------------------------------------------------

    text_path = None

    if text:

        text_path = (
            TEXT_DIR /
            f"{study_id}.txt"
        )

        text_path.write_text(
            text,
            encoding="utf-8"
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
            source_format,

        "source_file":
            str(filepath),

        "text_file":
            (
                str(text_path)
                if text_path
                else None
            ),

        "char_count":
            char_count,

        "word_count":
            word_count,

        "extraction_quality":
            extraction_quality,

        "error":
            error
    })


    if (
        n % 20 == 0
        or n == total
    ):

        print(
            f"Procesados: "
            f"{n}/{total}"
        )


# ==========================================================
# GUARDAR LOG
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
# RESUMEN
# ==========================================================

print("\n==========================================")
print("RESULTADO DE EXTRACCIÓN")
print("==========================================\n")

print(
    f"Intentados: {len(out)}"
)

print("\nCalidad:")

for category in [
    "GOOD",
    "PARTIAL",
    "POOR",
    "FAILED"
]:

    n = (
        out["extraction_quality"]
        == category
    ).sum()

    print(
        f"{category:10s} {n}"
    )


print("\nPor formato:")

print(
    pd.crosstab(
        out["source_format"],
        out["extraction_quality"]
    ).to_string()
)


print("\nLongitud del texto:")

print(
    f"Mediana palabras: "
    f"{out['word_count'].median():.0f}"
)

print(
    f"Media palabras:   "
    f"{out['word_count'].mean():.0f}"
)

print(
    f"Máximo palabras:  "
    f"{out['word_count'].max():.0f}"
)


print(
    f"\nTextos generados: "
    f"{len(list(TEXT_DIR.glob('*.txt')))}"
)

print(
    f"\nLog:\n{OUTPUT}"
)
