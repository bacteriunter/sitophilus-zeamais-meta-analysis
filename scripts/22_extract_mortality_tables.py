#!/usr/bin/env python3

import re
import pandas as pd
from pathlib import Path


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "mortality_study_map.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "mortality" /
    "tables"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTDIR /
    "mortality_tables.csv"
)


# ==========================================================
# PATRONES
# ==========================================================

table_heading = re.compile(
    r"(?im)^"
    r"\s*table\s+"
    r"(\d+[a-z]?)"
    r"[\s\.\:\-]+"
    r"(.{0,300})"
)

mortality_terms = re.compile(
    r"\b("
    r"mortality|"
    r"adult mortality|"
    r"corrected mortality|"
    r"percent mortality|"
    r"percentage mortality|"
    r"dead insects?"
    r")\b",
    flags=re.I
)

numeric_pattern = re.compile(
    r"\d+(?:\.\d+)?"
)

plusminus_pattern = re.compile(
    r"\d+(?:\.\d+)?\s*"
    r"(?:±|\+/-|\+-)\s*"
    r"\d+(?:\.\d+)?"
)

percent_pattern = re.compile(
    r"\d+(?:\.\d+)?\s*%"
)


# ==========================================================
# FUNCIONES
# ==========================================================

def clean_block(text):

    lines = []

    for line in text.splitlines():

        line = line.rstrip()

        if line.strip():
            lines.append(line)

    return "\n".join(lines)


def extract_tables(text):

    matches = list(
        table_heading.finditer(text)
    )

    tables = []

    for i, match in enumerate(matches):

        start = match.start()

        if i + 1 < len(matches):

            end = matches[
                i + 1
            ].start()

        else:

            # máximo 8000 caracteres
            # después del encabezado
            end = min(
                len(text),
                start + 8000
            )

        block = text[
            start:end
        ]

        # evitar capturar enormes
        # secciones del artículo
        if len(block) > 8000:

            block = block[:8000]

        tables.append({

            "table_number":
                match.group(1),

            "table_heading":
                match.group(2).strip(),

            "table_text":
                clean_block(block)
        })

    return tables


# ==========================================================
# PROCESAR
# ==========================================================

df = pd.read_csv(
    INPUT
)

records = []


print("\n==========================================")
print("EXTRACCIÓN DE TABLAS DE MORTALIDAD")
print("==========================================\n")

print(
    f"Estudios: {len(df)}"
)


for i, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

    path = Path(
        str(row["text_file"])
    )

    if not path.exists():
        continue

    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    tables = extract_tables(
        text
    )


    for table in tables:

        combined = (
            table["table_heading"]
            + "\n"
            + table["table_text"]
        )

        if not mortality_terms.search(
            combined
        ):
            continue


        records.append({

            "study_record_id":
                row["study_record_id"],

            "title":
                row["title"],

            "table_number":
                table["table_number"],

            "table_heading":
                table["table_heading"],

            "n_numeric_values":
                len(
                    numeric_pattern.findall(
                        table["table_text"]
                    )
                ),

            "n_plusminus":
                len(
                    plusminus_pattern.findall(
                        table["table_text"]
                    )
                ),

            "n_percent":
                len(
                    percent_pattern.findall(
                        table["table_text"]
                    )
                ),

            "table_text":
                table["table_text"],

            "text_file":
                str(path)
        })


    if (
        i % 10 == 0
        or i == len(df)
    ):

        print(
            f"Procesados: "
            f"{i}/{len(df)}"
        )


# ==========================================================
# GUARDAR
# ==========================================================

out = pd.DataFrame(
    records
)

if len(out) > 0:

    out.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8"
    )


# ==========================================================
# RESUMEN
# ==========================================================

print("\n==========================================")
print("RESULTADO DE TABLAS")
print("==========================================\n")

if len(out) == 0:

    print(
        "No se detectaron tablas "
        "de mortalidad."
    )

else:

    print(
        f"Tablas detectadas: "
        f"{len(out)}"
    )

    print(
        f"Estudios con tabla: "
        f"{out['study_record_id'].nunique()}"
    )

    print(
        "\nCon valores ±:",
        (
            out["n_plusminus"] > 0
        ).sum()
    )

    print(
        "Con porcentajes:",
        (
            out["n_percent"] > 0
        ).sum()
    )


    # ----------------------------------------------
    # CALIDAD APROXIMADA
    # ----------------------------------------------

    out["table_quality"] = "LOW"

    out.loc[
        out["n_numeric_values"] >= 10,
        "table_quality"
    ] = "MEDIUM"

    out.loc[
        (
            out["n_numeric_values"] >= 10
        )
        &
        (
            (
                out["n_plusminus"] > 0
            )
            |
            (
                out["n_percent"] > 0
            )
        ),
        "table_quality"
    ] = "HIGH"


    print(
        "\nCalidad aproximada:"
    )

    print(
        out[
            "table_quality"
        ]
        .value_counts()
        .to_string()
    )


    print(
        "\n=========================================="
    )

    print(
        "PRIMERAS 10 TABLAS"
    )

    print(
        "==========================================\n"
    )


    for _, row in (
        out.head(10).iterrows()
    ):

        print(
            row["study_record_id"],
            "| Table",
            row["table_number"],
            "|",
            row["table_heading"][:150]
        )

        print(
            "   números:",
            row["n_numeric_values"],
            "| ±:",
            row["n_plusminus"],
            "| %:",
            row["n_percent"]
        )

        print()


    # guardar de nuevo
    # incluyendo table_quality

    out.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8"
    )


print(
    f"\nArchivo:\n{OUTPUT}"
)
