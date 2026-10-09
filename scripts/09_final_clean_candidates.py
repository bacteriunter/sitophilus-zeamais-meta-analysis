#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
from rapidfuzz.fuzz import ratio
import re
import unicodedata

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT / "03_screening" / "refined" /
    "refined_candidates.csv"
)

OUTDIR = (
    PROJECT / "03_screening" / "final_candidates"
)

OUTDIR.mkdir(parents=True, exist_ok=True)

OUT_ALL = OUTDIR / "candidates_clean.csv"
OUT_PRIMARY = OUTDIR / "primary_candidates.csv"
OUT_SECONDARY = OUTDIR / "secondary_literature.csv"
OUT_DUP = OUTDIR / "possible_duplicates.csv"


# ==========================================================
# NORMALIZAR TÍTULO
# ==========================================================

def normalize_title(text):

    if pd.isna(text):
        return ""

    text = str(text).lower()

    # eliminar prefijo "Data from:"
    text = re.sub(
        r"^\s*data\s+from\s*:\s*",
        "",
        text
    )

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================================
# LEER
# ==========================================================

df = pd.read_csv(INPUT)

df["title"] = df["title"].fillna("").astype(str)
df["abstract"] = df["abstract"].fillna("").astype(str)

df["title_norm"] = df["title"].apply(
    normalize_title
)

print("\n==========================================")
print("LIMPIEZA FINAL DE CANDIDATOS")
print("==========================================\n")

print(f"Registros iniciales: {len(df)}")


# ==========================================================
# SOLO A + C
# ==========================================================

df = df[
    df["refined_priority"].isin(
        ["A_VERY_LIKELY", "C_REVIEW"]
    )
].copy()

print(
    f"A + C considerados: {len(df)}"
)


# ==========================================================
# IDENTIFICAR TIPO DE PUBLICACIÓN
# ==========================================================

secondary_pattern = re.compile(
    r"\b("
    r"review|systematic review|"
    r"meta analysis|meta-analysis|"
    r"overview|bibliometric|"
    r"editorial|commentary|"
    r"correction|corrigendum|erratum"
    r")\b",
    flags=re.I
)

dataset_pattern = re.compile(
    r"^\s*data\s+from\s*:",
    flags=re.I
)

df["is_secondary"] = df["title"].apply(
    lambda x: bool(secondary_pattern.search(x))
)

df["is_dataset_record"] = df["title"].apply(
    lambda x: bool(dataset_pattern.search(x))
)


# ==========================================================
# ELIMINAR DUPLICADOS EXACTOS
# ==========================================================

before = len(df)

df = (
    df.sort_values(
        "refined_priority"
    )
    .drop_duplicates(
        subset=["title_norm"],
        keep="first"
    )
    .copy()
)

exact_removed = before - len(df)

print(
    f"Duplicados exactos por título: "
    f"{exact_removed}"
)


# ==========================================================
# BUSCAR TÍTULOS CASI DUPLICADOS
# ==========================================================

titles = df[
    ["study_record_id", "title", "title_norm"]
].reset_index(drop=True)

possible_duplicates = []

for i in range(len(titles)):

    title_i = titles.loc[i, "title_norm"]

    if len(title_i) < 20:
        continue

    for j in range(i + 1, len(titles)):

        title_j = titles.loc[j, "title_norm"]

        if len(title_j) < 20:
            continue

        # Evitar comparar títulos de longitudes
        # extremadamente diferentes
        length_ratio = (
            min(len(title_i), len(title_j))
            /
            max(len(title_i), len(title_j))
        )

        if length_ratio < 0.75:
            continue

        similarity = ratio(
            title_i,
            title_j
        )

        if similarity >= 92:

            possible_duplicates.append({
                "id_1":
                    titles.loc[i, "study_record_id"],

                "title_1":
                    titles.loc[i, "title"],

                "id_2":
                    titles.loc[j, "study_record_id"],

                "title_2":
                    titles.loc[j, "title"],

                "similarity":
                    similarity
            })


dup_df = pd.DataFrame(possible_duplicates)

dup_df.to_csv(
    OUT_DUP,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# SEPARAR LITERATURA
# ==========================================================

secondary = df[
    df["is_secondary"]
].copy()

primary = df[
    ~df["is_secondary"]
].copy()


# Los dataset records se conservan,
# pero se marcan para revisión

primary["needs_dataset_check"] = (
    primary["is_dataset_record"]
)


# ==========================================================
# GUARDAR
# ==========================================================

df.to_csv(
    OUT_ALL,
    index=False,
    encoding="utf-8"
)

primary.to_csv(
    OUT_PRIMARY,
    index=False,
    encoding="utf-8"
)

secondary.to_csv(
    OUT_SECONDARY,
    index=False,
    encoding="utf-8"
)


# ==========================================================
# RESULTADOS
# ==========================================================

print("\n==========================================")
print("RESULTADO")
print("==========================================")

print(
    f"Candidatos limpios:       {len(df)}"
)

print(
    f"Primarios potenciales:    {len(primary)}"
)

print(
    f"Literatura secundaria:    {len(secondary)}"
)

print(
    f"Registros 'Data from':    "
    f"{df['is_dataset_record'].sum()}"
)

print(
    f"Pares casi duplicados:    "
    f"{len(dup_df)}"
)


print("\nPor prioridad:")

print(
    df["refined_priority"]
    .value_counts()
    .to_string()
)


print("\nIntervenciones en primarios potenciales:")

print(
    f"Botánicos:                "
    f"{primary['botanical_refined'].sum()}"
)

print(
    f"Ceniza/materiales:        "
    f"{primary['natural_refined'].sum()}"
)

print(
    f"Físicas/temperatura:      "
    f"{primary['physical_refined'].sum()}"
)


print("\nModeradores en primarios potenciales:")

print(
    f"Temperatura:              "
    f"{primary['mod_temperature'].sum()}"
)

print(
    f"Humedad:                  "
    f"{primary['mod_moisture'].sum()}"
)

print(
    f"Tiempo almacenamiento:    "
    f"{primary['mod_storage_time'].sum()}"
)

print(
    f"Dosis:                    "
    f"{primary['mod_dose'].sum()}"
)


print("\nArchivos generados:")
print(OUT_PRIMARY)
print(OUT_SECONDARY)
print(OUT_DUP)

