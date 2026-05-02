"""
CSV exporter — writes prospect list to output/prospects.csv
Appends to existing file or creates new one.
"""

import csv
import os
from datetime import date

FIELDNAMES = [
    "empresa",
    "vertical",
    "primeiro_nome",
    "ultimo_nome",
    "cargo",
    "email",
    "linkedin",
    "dominio",
    "confianca_email",
    "fonte",
    "data_coleta",
    "status",
    "template_usado",
    "data_contato",
    "resposta",
    "notas",
]


def write_prospects(prospects: list[dict], output_path: str) -> int:
    """
    Write prospects to CSV. Appends if file exists, creates with header if not.
    Returns number of rows written.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.isfile(output_path)
    today = date.today().strftime("%d/%m/%Y")

    written = 0
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=FIELDNAMES, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        for p in prospects:
            row = {
                "empresa": p.get("company", ""),
                "vertical": p.get("vertical", ""),
                "primeiro_nome": p.get("first_name", ""),
                "ultimo_nome": p.get("last_name", ""),
                "cargo": p.get("position", ""),
                "email": p.get("email", ""),
                "linkedin": p.get("linkedin", ""),
                "dominio": p.get("domain", ""),
                "confianca_email": p.get("confidence", ""),
                "fonte": p.get("source", ""),
                "data_coleta": today,
                "status": "Novo",
                "template_usado": "",
                "data_contato": "",
                "resposta": "",
                "notas": "",
            }
            writer.writerow(row)
            written += 1
    return written
