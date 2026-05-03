from __future__ import annotations

"""
Ponto de entrada para prospecção LOCAL via Lecto.com.br.

Uso:
  python run_local.py --cidade "sao carlos" --keyword "todas-as-cidades" --max 100
  python run_local.py --cidade "ribeirão preto" --keyword "advocacia" --max 50
"""

import argparse
import sys

from src.lecto_scraper  import scrape
from src.local_exporter import write_local, write_local_final


def main(cidade: str, keyword: str, max_results: int, verbose: bool = True) -> None:
    print(f"\n{'='*60}")
    print(f"  PROSPECÇÃO LOCAL — Lecto.com.br")
    print(f"  Cidade  : {cidade}")
    print(f"  Keyword : {keyword}")
    print(f"  Máx.    : {max_results} resultados")
    print(f"{'='*60}\n")

    contacts = scrape(cidade=cidade, keyword=keyword, max_results=max_results, verbose=verbose)

    if not contacts:
        print("\n[!] Nenhum contato encontrado. Verifique cidade/keyword.")
        sys.exit(1)

    # Conta por tipo
    com_celular   = sum(1 for c in contacts if c.get("celular"))
    com_email     = sum(1 for c in contacts if c.get("email"))
    com_whatsapp  = sum(1 for c in contacts if c.get("whatsapp"))

    path_batch = write_local(contacts, cidade, keyword)
    path_final = write_local_final(contacts)

    print(f"\n{'='*60}")
    print(f"  Resultado da coleta")
    print(f"  Total coletado      : {len(contacts)}")
    print(f"  Com celular/WhatsApp: {com_whatsapp}")
    print(f"  Com email           : {com_email}")
    print(f"\n  Arquivos gerados:")
    print(f"  → {path_batch}  (apenas esta busca)")
    print(f"  → {path_final}  (consolidado geral)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prospecção local via Lecto.com.br"
    )
    parser.add_argument(
        "--cidade", required=True, help='Cidade para busca. Ex: "sao carlos"'
    )
    parser.add_argument(
        "--keyword",
        default="todas-as-cidades",
        help='Segmento/keyword. Ex: "advocacia", "odontologia", "academia"',
    )
    parser.add_argument(
        "--max",
        type=int,
        default=100,
        dest="max_results",
        help="Número máximo de resultados a coletar (padrão: 100)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Modo silencioso (sem log de progresso)"
    )

    args = parser.parse_args()
    main(
        cidade=args.cidade,
        keyword=args.keyword,
        max_results=args.max_results,
        verbose=not args.quiet,
    )
