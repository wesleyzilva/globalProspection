from __future__ import annotations

"""
Exportador CSV para prospecção local (Lecto.com.br).
Salva em output/local/{cidade}_{keyword}_{data}.csv
"""

import csv
import os
import re
import unicodedata
from datetime import date


FIELDNAMES = [
    "nome_empresa",
    "segmento",
    "cidade_estado",
    "ddd",
    "telefone_fixo",
    "celular",
    "whatsapp",          # 55{ddd}{celular} — pronto para link wa.me/
    "email",
    "site",
    "endereco",
    "descricao",
    "url_lecto",
    "fonte",
    "data_coleta",
    "status_contato",    # para controle: novo / contatado / respondeu / sem_interesse
    "data_contato",
    "notas",
]


def _safe_filename(text: str) -> str:
    """Remove acentos e caracteres especiais para usar em nomes de arquivo."""
    normalized = unicodedata.normalize("NFD", text.lower())
    ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")


def write_local(
    contacts: list[dict],
    cidade: str,
    keyword: str,
    output_dir: str = "output/local",
) -> str:
    """
    Grava contacts em CSV. Retorna o caminho do arquivo gerado.
    Se o arquivo já existir, SUBSTITUI (dados frescos de cada scrape).
    """
    os.makedirs(output_dir, exist_ok=True)

    today     = date.today().strftime("%Y%m%d")
    city_slug = _safe_filename(cidade)
    kw_slug   = _safe_filename(keyword)
    filename  = f"{city_slug}_{kw_slug}_{today}.csv"
    filepath  = os.path.join(output_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for c in contacts:
            row = {k: c.get(k, "") for k in FIELDNAMES}
            row.setdefault("status_contato", "novo")
            writer.writerow(row)

    return filepath


def write_local_final(
    contacts: list[dict],
    output_dir: str = "output/local",
    filename: str = "prospects_local_final.csv",
) -> str:
    """
    Grava/atualiza o arquivo final consolidado de prospecção local.
    Faz merge com dados existentes (dedup por nome_empresa+cidade).
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # carrega existentes
    existing: dict[str, dict] = {}
    if os.path.isfile(filepath):
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                key = f"{row.get('nome_empresa','').lower()}|{row.get('cidade_estado','').lower()}"
                existing[key] = row

    # merge novos
    for c in contacts:
        key = f"{c.get('nome_empresa','').lower()}|{c.get('cidade_estado','').lower()}"
        if key not in existing:
            existing[key] = {k: c.get(k, "") for k in FIELDNAMES}
            existing[key].setdefault("status_contato", "novo")

    rows = sorted(
        existing.values(),
        key=lambda r: (r.get("cidade_estado", ""), r.get("nome_empresa", "")),
    )

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return filepath
