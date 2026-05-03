from __future__ import annotations

"""
Merge all campaign CSVs into a single deduplicated output/prospects_final.csv.
Called automatically after every campaign run.
"""

import csv
import os
from datetime import datetime

from src.csv_exporter import FIELDNAMES

CAMPAIGNS_DIR = "output/campaigns"
FINAL_PATH    = "output/prospects_final.csv"


def _fingerprint(row: dict) -> str:
    email   = (row.get("email")    or "").strip().lower()
    linkedin = (row.get("linkedin") or "").strip().lower()
    nome    = f"{row.get('primeiro_nome','').lower()}_{row.get('ultimo_nome','').lower()}_{row.get('dominio','').lower()}"
    if email:    return f"email:{email}"
    if linkedin: return f"li:{linkedin}"
    return f"name:{nome}"


def merge_all_campaigns() -> int:
    """
    Read every prospects.csv inside output/campaigns/*/,
    deduplicate by fingerprint, sort by empresa+vertical,
    write output/prospects_final.csv.
    Returns total rows written.
    """
    seen:    set[str]   = set()
    rows:    list[dict] = []

    if not os.path.isdir(CAMPAIGNS_DIR):
        return 0

    for campaign in sorted(os.listdir(CAMPAIGNS_DIR)):
        csv_path = os.path.join(CAMPAIGNS_DIR, campaign, "prospects.csv")
        if not os.path.isfile(csv_path):
            continue
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                fp = _fingerprint(row)
                if fp not in seen:
                    seen.add(fp)
                    rows.append(row)

    # ordenar por vertical > empresa > sobrenome
    rows.sort(key=lambda r: (
        r.get("vertical", ""),
        r.get("empresa", ""),
        r.get("ultimo_nome", ""),
    ))

    os.makedirs("output", exist_ok=True)
    with open(FINAL_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)
