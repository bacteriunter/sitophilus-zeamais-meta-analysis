#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

PROJECT = Path.home() / "sitophilus_meta"

INPUT = (
    PROJECT / "03_screening" /
    "final_candidates" /
    "primary_candidates.csv"
)

OUTPUT = (
    PROJECT / "03_screening" /
    "final_candidates" /
    "primary_candidates_final.csv"
)

REMOVED = (
    PROJECT / "03_screening" /
    "final_candidates" /
    "duplicates_removed.csv"
)

df = pd.read_csv(INPUT)

# ==========================================================
# PARES QUE SÍ SON DUPLICADOS
# ==========================================================

duplicate_pairs = [
    ("SZ_00658", "SZ_00695"),
    ("SZ_01732", "SZ_00550")
]


def completeness(row):

    score = 0

    doi = str(row.get("doi", ""))
    abstract = str(row.get("abstract", ""))
    journal = str(row.get("journal", ""))
    year = str(row.get("year", ""))

    if doi not in ["", "nan", "None"]:
        score += 5

    if abstract not in ["", "nan", "None"]:
        score += 3
        score += min(len(abstract) / 1000, 2)

    if journal not in ["", "nan", "None"]:
        score += 1

    if year not in ["", "nan", "None"]:
        score += 1

    return score


remove_ids = []
decision_records = []

for id1, id2 in duplicate_pairs:

    r1 = df[
        df["study_record_id"] == id1
    ]

    r2 = df[
        df["study_record_id"] == id2
    ]

    if len(r1) != 1 or len(r2) != 1:

        print(
            f"ADVERTENCIA: no se encontró "
            f"correctamente {id1} / {id2}"
        )

        continue

    r1 = r1.iloc[0]
    r2 = r2.iloc[0]

    s1 = completeness(r1)
    s2 = completeness(r2)

    if s1 >= s2:
        keep = id1
        remove = id2
    else:
        keep = id2
        remove = id1

    remove_ids.append(remove)

    decision_records.append({
        "kept_id": keep,
        "removed_id": remove,
        "score_kept": max(s1, s2),
        "score_removed": min(s1, s2),
        "reason": "duplicate bibliographic record"
    })


# ==========================================================
# GUARDAR
# ==========================================================

removed_df = df[
    df["study_record_id"].isin(remove_ids)
].copy()

final = df[
    ~df["study_record_id"].isin(remove_ids)
].copy()

final.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

removed_df.to_csv(
    REMOVED,
    index=False,
    encoding="utf-8"
)

decision_df = pd.DataFrame(decision_records)

decision_df.to_csv(
    PROJECT /
    "03_screening" /
    "final_candidates" /
    "duplicate_decisions.csv",
    index=False,
    encoding="utf-8"
)


print("\n==========================================")
print("RESOLUCIÓN DE DUPLICADOS")
print("==========================================\n")

for d in decision_records:

    print(
        f"Conservar: {d['kept_id']} | "
        f"Eliminar: {d['removed_id']}"
    )

print(
    "\nSZ_00147 y SZ_00108 se conservan "
    "(outcomes/publicaciones diferentes)."
)

print(f"\nRegistros iniciales: {len(df)}")
print(f"Duplicados eliminados: {len(remove_ids)}")
print(f"Registros finales: {len(final)}")

print(f"\nArchivo final:\n{OUTPUT}")
