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
    "experimental_audit" /
    "EXTRACT_HIGH.csv"
)

OUTDIR = (
    PROJECT /
    "05_extraction" /
    "evidence_windows"
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = (
    OUTDIR /
    "evidence_windows.csv"
)


# ==========================================================
# CONCEPTOS
# ==========================================================

patterns = {

    "control": (
        r"\b("
        r"untreated control|negative control|"
        r"control treatment|control group|"
        r"control grains?|untreated grains?|"
        r"untreated maize|without treatment|"
        r"control"
        r")\b"
    ),

    "replication": (
        r"\b("
        r"replicate|replicates|replicated|"
        r"replication|triplicate|"
        r"completely randomized|"
        r"completely randomised|"
        r"experimental design"
        r")\b"
    ),

    "sample_size": (
        r"\b("
        r"n\s*=\s*\d+|"
        r"\d+\s+replicates|"
        r"\d+\s+insects|"
        r"\d+\s+adults|"
        r"\d+\s+weevils|"
        r"\d+\s+grains|"
        r"\d+\s+seeds"
        r")\b"
    ),

    "dose": (
        r"("
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:mg|g|kg|ml|µl|ul)"
        r"\s*(?:/|per\s+)"
        r"(?:g|kg|ml|l)\b"
        r"|"
        r"\b\d+(?:\.\d+)?\s*%"
        r"|"
        r"\bdose(?:s)?\b|"
        r"\bconcentration(?:s)?\b"
        r")"
    ),

    "temperature": (
        r"("
        r"\btemperature(?:s)?\b|"
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:°\s*c|º\s*c|degrees?\s+c)"
        r")"
    ),

    "humidity": (
        r"("
        r"\brelative humidity\b|"
        r"\bhumidity\b|"
        r"\b\d+(?:\.\d+)?\s*%\s*RH\b"
        r")"
    ),

    "mortality": (
        r"\b("
        r"mortality|adult mortality|"
        r"percentage mortality|"
        r"percent mortality"
        r")\b"
    ),

    "progeny": (
        r"\b("
        r"progeny|offspring|"
        r"adult emergence|"
        r"f1 emergence|f1 progeny"
        r")\b"
    ),

    "damage": (
        r"\b("
        r"grain damage|kernel damage|"
        r"damaged grains?"
        r")\b"
    ),

    "weight_loss": (
        r"\b("
        r"weight loss|mass loss|"
        r"grain weight loss"
        r")\b"
    ),

    "germination": (
        r"\b("
        r"germination|seed viability"
        r")\b"
    ),

    "repellency": (
        r"\b("
        r"repellency|repellent activity|"
        r"repellent effect"
        r")\b"
    ),

    "oviposition": (
        r"\b("
        r"oviposition|eggs laid|"
        r"number of eggs"
        r")\b"
    )
}


# ==========================================================
# LIMPIAR FRAGMENTO
# ==========================================================

def clean_fragment(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================================
# GENERAR VENTANAS
# ==========================================================

def get_windows(
    text,
    pattern,
    radius=600,
    max_windows=8
):

    matches = list(
        re.finditer(
            pattern,
            text,
            flags=re.I
        )
    )

    windows = []

    used_ranges = []

    for match in matches:

        start = max(
            0,
            match.start() - radius
        )

        end = min(
            len(text),
            match.end() + radius
        )

        # Evitar ventanas casi idénticas
        overlap = False

        for old_start, old_end in used_ranges:

            intersection = max(
                0,
                min(end, old_end)
                - max(start, old_start)
            )

            smaller = min(
                end - start,
                old_end - old_start
            )

            if (
                smaller > 0
                and intersection / smaller > 0.70
            ):

                overlap = True
                break

        if overlap:
            continue

        fragment = clean_fragment(
            text[start:end]
        )

        windows.append(
            fragment
        )

        used_ranges.append(
            (start, end)
        )

        if len(windows) >= max_windows:
            break

    return windows


# ==========================================================
# LEER CANDIDATOS
# ==========================================================

df = pd.read_csv(INPUT)

records = []


print("\n==========================================")
print("EXTRACCIÓN DE VENTANAS DE EVIDENCIA")
print("==========================================\n")

print(
    f"Artículos EXTRACT_HIGH: {len(df)}"
)


# ==========================================================
# PROCESAR
# ==========================================================

for n, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

    study_id = str(
        row["study_record_id"]
    )

    text_file = Path(
        str(row["text_file"])
    )

    if not text_file.exists():
        continue

    text = text_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    for concept, pattern in patterns.items():

        windows = get_windows(
            text,
            pattern
        )

        for number, fragment in enumerate(
            windows,
            start=1
        ):

            records.append({

                "study_record_id":
                    study_id,

                "title":
                    row["title"],

                "doi":
                    row.get("doi"),

                "concept":
                    concept,

                "window_number":
                    number,

                "evidence_text":
                    fragment
            })


    if (
        n % 10 == 0
        or n == len(df)
    ):

        print(
            f"Procesados: "
            f"{n}/{len(df)}"
        )


# ==========================================================
# GUARDAR
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
print("RESULTADO")
print("==========================================\n")

print(
    f"Artículos procesados: "
    f"{out['study_record_id'].nunique()}"
)

print(
    f"Ventanas generadas: "
    f"{len(out)}"
)


print("\nArtículos con evidencia por concepto:")

summary = (
    out.groupby("concept")
    ["study_record_id"]
    .nunique()
    .sort_values(
        ascending=False
    )
)

print(
    summary.to_string()
)


print("\nVentanas por concepto:")

counts = (
    out["concept"]
    .value_counts()
)

print(
    counts.to_string()
)


print(
    f"\nArchivo:\n{OUTPUT}"
)
