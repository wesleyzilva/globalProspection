#!/usr/bin/env python3
"""
Global Prospection — CLI entry point

Run a campaign:
  python run.py --campaign fintech_q2 --source hunter --verticals Fintech --max 5
  python run.py --campaign cybersec_may --source apollo --verticals Cybersecurity
  python run.py --campaign full_combined --source combined

Show reports:
  python run.py --report                   # summary of all campaigns
  python run.py --report --campaign fintech_q2   # report for one campaign
"""

import argparse
import os
from datetime import datetime
from dotenv import load_dotenv
from src.prospector import run_campaign
from src.campaign_manager import list_campaigns, load_campaign_meta
from src.logger import generate_report, generate_global_summary

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
        "--campaign",
        default=None,
        help=(
            "Campaign name (creates output/campaigns/<name>/). "
            "Auto-generated if not provided (e.g. hunter_20260502_1430). "
            "Also used with --report to view a specific campaign."
        ),
    )
    parser.add_argument(
        "--source",
        choices=VALID_SOURCES,
        default="hunter",
        help=(
            "API source:\n"
            "  hunter   — Hunter.io (FREE: 25/month)\n"
            "  apollo   — Apollo.io (FREE: 50/month)\n"
            "  combined — Apollo names + Hunter emails merged"
        ),
    )
    parser.add_argument(
        "--verticals",
        nargs="+",
        choices=VALID_VERTICALS,
        default=None,
        help="Filter by vertical (e.g. --verticals Fintech TradeTech)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Max companies to process (saves free API credits)",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Optional description for this campaign",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Disable automatic API fallback on rate limit",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Show campaign report(s) and exit without running a new search",
    )

    args = parser.parse_args()

    # ── Report mode ───────────────────────────────────────────────────────
    if args.report:
        if args.campaign:
            meta = load_campaign_meta(args.campaign)
            if not meta:
                print(f"Campaign '{args.campaign}' not found.")
                raise SystemExit(1)
            campaign_dir = os.path.join("output/campaigns", args.campaign)
            report_path = generate_report(meta, campaign_dir)
            with open(report_path, encoding="utf-8") as f:
                print(f.read())
        else:
            print(generate_global_summary())
        return

    # ── Run campaign ──────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    campaign_name = args.campaign or f"{args.source}_{ts}"

    print(f"\n=== Global Prospection ===")
    print(f"Campaign : {campaign_name}")
    print(f"Source   : {args.source}")
    print(f"Verticals: {args.verticals or 'ALL'}")
    print(f"Max cos  : {args.max or 'ALL'}")
    print(f"Fallback : {'disabled' if args.no_fallback else 'enabled'}")
    print()

    try:
        stats = run_campaign(
            campaign_name=campaign_name,
            source=args.source,
            verticals=args.verticals,
            max_companies=args.max,
            description=args.description,
            fallback=not args.no_fallback,
        )
        print(
            f"\n✓ Done — {stats.get('contacts_written', 0)} new contacts written.")
        print(f"  CSV: output/campaigns/{campaign_name}/prospects.csv")
        print(f"  Log: output/campaigns/{campaign_name}/run.log")

    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("  Copy .env.example to .env and fill in your API keys.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
