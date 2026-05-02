#!/usr/bin/env python3
"""
Global Prospection — CLI entry point
Usage:
  python run.py --source hunter
  python run.py --source apollo
  python run.py --source combined
  python run.py --source hunter --verticals Fintech TradeTech --max 5
"""

import argparse
import os
from dotenv import load_dotenv
from src.prospector import run_hunter_only, run_apollo_only, run_combined

load_dotenv()

VALID_SOURCES = ["hunter", "apollo", "combined"]
VALID_VERTICALS = [
    "Fintech", "TradeTech", "HealthTech", "CXTech",
    "SalesTech", "LegalTech", "AIGovernance", "Cybersecurity", "Platform",
]


def main():
    parser = argparse.ArgumentParser(
        description="Global Prospection — find recruiters at funded tech startups"
    )
    parser.add_argument(
        "--source",
        choices=VALID_SOURCES,
        default="hunter",
        help=(
            "API source to use:\n"
            "  hunter   — Hunter.io (FREE: 25/month, email discovery by domain)\n"
            "  apollo   — Apollo.io (FREE: 50/month, people search by title)\n"
            "  combined — Apollo names + Hunter emails merged (uses both APIs)"
        ),
    )
    parser.add_argument(
        "--verticals",
        nargs="+",
        choices=VALID_VERTICALS,
        default=None,
        help="Filter to specific verticals (e.g. --verticals Fintech TradeTech)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Max number of companies to process (useful to save free credits)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.getenv("OUTPUT_DIR", "output"), os.getenv("OUTPUT_FILE", "prospects.csv")),
        help="Path to output CSV file (default: output/prospects.csv)",
    )

    args = parser.parse_args()

    print(f"\n=== Global Prospection ===")
    print(f"Source   : {args.source}")
    print(f"Verticals: {args.verticals or 'ALL'}")
    print(f"Max cos  : {args.max or 'ALL'}")
    print(f"Output   : {args.output}")
    print()

    try:
        if args.source == "hunter":
            total = run_hunter_only(args.output, args.verticals, args.max)
        elif args.source == "apollo":
            total = run_apollo_only(args.output, args.verticals, args.max)
        else:
            total = run_combined(args.output, args.verticals, args.max)

        print(f"\n✓ Done — {total} prospects written to {args.output}")
        print(f"  Open in Excel/Sheets or import into your CRM.")

    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("  Copy .env.example to .env and fill in your API keys.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
