#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# ARCHIVOS
# ============================================================

ROOT = Path.home() / "sitophilus_meta"

INCLUDE = ROOT / "05_extraction/scope_eligibility/INCLUDE.csv"
MASTER = ROOT / "02_deduplication/master_unique.csv"
BIO = ROOT / "07_meta_analysis/biological_synthesis/mortality_biological_master.csv"

OUTDIR = ROOT / "07_meta_analysis/biological_synthesis"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUT = OUTDIR / "Tabla_S1_estudios_referencias.csv"


# ============================================================
# ESTUDIOS UTILIZADOS EN EL ANÁLISIS DE MORTALIDAD
# ============================================================

MORTALITY_STUDIES = {
    "SZ_00071",
    "SZ_00124",
    "SZ_00288",
    "SZ_00401",
    "SZ_00424",
    "SZ_00549",
    "SZ_00600",
    "SZ_00668",
    "SZ_00802",
}


# ============================================================
# CARGAR DATOS
# ============================================================

inc = pd.read_csv(INCLUDE)
master = pd.read_csv(MASTER)
bio = pd.read_csv(BIO)

print("\n============================================")
print("TABLA DE REFERENCIAS DE ESTUDIOS")
print("============================================")
print("Estudios incluidos:", len(inc))


# ============================================================
# NORMALIZAR ID
# ============================================================

for df in [inc, master, bio]:
    df["study_record_id"] = df["study_record_id"].astype(str).str.strip()


# ============================================================
# METADATOS BIBLIOGRÁFICOS
# ============================================================

meta_cols = [
    "study_record_id",
    "authors",
    "year",
    "title",
    "journal",
    "doi",
]

meta = master[meta_cols].copy()

# Por seguridad: una fila por ID
meta = meta.drop_duplicates(subset="study_record_id", keep="first")


# ============================================================
# BASE DE LOS 58 ESTUDIOS
# ============================================================

tab = inc[
    ["study_record_id", "title", "doi"]
].copy()

tab = tab.merge(
    meta,
    on="study_record_id",
    how="left",
    suffixes=("_include", "_master")
)

# Priorizar título y DOI de INCLUDE; completar desde master
tab["Título"] = (
    tab["title_include"]
    .fillna(tab["title_master"])
)

tab["DOI"] = (
    tab["doi_include"]
    .fillna(tab["doi_master"])
)

tab["Autores"] = tab["authors"]
tab["Año"] = tab["year"]
tab["Revista"] = tab["journal"]


# ============================================================
# TRATAMIENTOS/MATERIALES DE LOS 9 ESTUDIOS CUANTITATIVOS
# ============================================================

def clean_values(series):
    vals = (
        series.dropna()
        .astype(str)
        .str.strip()
    )

    vals = vals[
        ~vals.str.lower().isin(
            ["", "nan", "na", "nr", "none"]
        )
    ]

    return "; ".join(sorted(vals.unique()))


# Intentar usar species_material, que es nuestra variable biológica final
if "species_material" in bio.columns:

    materials = (
        bio.groupby("study_record_id")["species_material"]
        .apply(clean_values)
        .reset_index(name="Tratamiento/material")
    )

else:

    materials = (
        bio.groupby("study_record_id")["treatment"]
        .apply(clean_values)
        .reset_index(name="Tratamiento/material")
    )

tab = tab.merge(
    materials,
    on="study_record_id",
    how="left"
)


# ============================================================
# ESTADO DE INCLUSIÓN
# ============================================================

tab["Revisión sistemática"] = "Sí"

tab["Análisis de mortalidad"] = np.where(
    tab["study_record_id"].isin(MORTALITY_STUDIES),
    "Sí",
    "No"
)

tab["Tipo de evidencia"] = np.where(
    tab["study_record_id"].isin(MORTALITY_STUDIES),
    "Cuantitativa – mortalidad",
    "Sistemática/descriptiva"
)


# ============================================================
# PARA LOS ESTUDIOS NO CUANTITATIVOS
# ============================================================

tab["Tratamiento/material"] = tab["Tratamiento/material"].fillna(
    "No incorporado en la síntesis cuantitativa de mortalidad"
)


# ============================================================
# TABLA FINAL
# ============================================================

final = tab[
    [
        "study_record_id",
        "Autores",
        "Año",
        "Título",
        "Revista",
        "DOI",
        "Tratamiento/material",
        "Revisión sistemática",
        "Análisis de mortalidad",
        "Tipo de evidencia",
    ]
].copy()

final = final.rename(
    columns={"study_record_id": "ID"}
)

final = final.sort_values("ID").reset_index(drop=True)


# ============================================================
# GUARDAR
# ============================================================

final.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# CONTROL
# ============================================================

print("\nEstudios en Tabla S1:", len(final))

print(
    "Incluidos en análisis de mortalidad:",
    (final["Análisis de mortalidad"] == "Sí").sum()
)

print(
    "Solo revisión sistemática/descriptiva:",
    (final["Análisis de mortalidad"] == "No").sum()
)

print("\nMetadatos faltantes:")
for c in ["Autores", "Año", "Título", "Revista", "DOI"]:
    print(f"{c}: {final[c].isna().sum()}")

print("\nEstudios cuantitativos:")
print(
    final.loc[
        final["Análisis de mortalidad"] == "Sí",
        [
            "ID",
            "Autores",
            "Año",
            "Título",
            "Tratamiento/material"
        ]
    ].to_string(index=False)
)

print("\nArchivo creado:")
print(OUT)

