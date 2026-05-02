"""
Logger — structured logging to both console and campaign log file.
Also provides report generation (text + JSON).
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path


def get_logger(name: str, log_path: str | None = None) -> logging.Logger:
    """
    Returns a logger that writes to stdout AND optionally to a file.
    Format: [HH:MM:SS] [LEVEL] message
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler (if path given)
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# ── Report generator ────────────────────────────────────────────────────────


def generate_report(campaign_meta: dict, output_dir: str) -> str:
    """
    Generate a text + JSON report for a campaign.
    Returns path to the text report file.
    """
    stats = campaign_meta.get("stats", {})
    name = campaign_meta.get("name", "unknown")
    source = campaign_meta.get("source", "?")
    verticals = campaign_meta.get("verticals") or ["ALL"]
    created = campaign_meta.get("created_at", "?")
    updated = campaign_meta.get("updated_at", "?")

    lines = [
        "=" * 60,
        f"  CAMPAIGN REPORT — {name}",
        "=" * 60,
        f"  Source       : {source}",
        f"  Verticals    : {', '.join(verticals)}",
        f"  Started      : {created}",
        f"  Last run     : {updated}",
        "-" * 60,
        f"  Companies processed  : {stats.get('companies_processed', 0)}",
        f"  Contacts found       : {stats.get('contacts_found', 0)}",
        f"  Contacts skipped     : {stats.get('contacts_skipped_dedup', 0)}  (duplicates removed)",
        f"  Contacts written     : {stats.get('contacts_written', 0)}",
        "-" * 60,
        f"  Hunter.io calls      : {stats.get('hunter_calls', 0)}",
        f"  Apollo.io calls      : {stats.get('apollo_calls', 0)}",
        f"  API fallbacks used   : {stats.get('api_fallbacks', 0)}",
        f"  Errors               : {stats.get('errors', 0)}",
        "=" * 60,
    ]

    report_txt = "\n".join(lines)
    txt_path = os.path.join(output_dir, "report.txt")
    json_path = os.path.join(output_dir, "report.json")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(report_txt + "\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(campaign_meta, f, indent=2, ensure_ascii=False)

    return txt_path


def generate_global_summary(campaigns_dir: str = "output/campaigns") -> str:
    """
    Summarize all campaigns in a single report printed to console.
    Returns formatted string.
    """
    if not os.path.isdir(campaigns_dir):
        return "No campaigns found."

    rows = []
    total_written = 0
    total_skipped = 0

    for name in sorted(os.listdir(campaigns_dir)):
        meta_path = os.path.join(campaigns_dir, name, "campaign.json")
        if not os.path.isfile(meta_path):
            continue
        try:
            with open(meta_path, encoding="utf-8") as f:
                m = json.load(f)
            s = m.get("stats", {})
            written = s.get("contacts_written", 0)
            skipped = s.get("contacts_skipped_dedup", 0)
            total_written += written
            total_skipped += skipped
            rows.append(
                f"  {m['name']:<30} source={m['source']:<10} "
                f"written={written:<5} skipped={skipped:<5} "
                f"errors={s.get('errors', 0)}"
            )
        except Exception:
            pass

    lines = [
        "=" * 70,
        "  GLOBAL PROSPECTION SUMMARY",
        "=" * 70,
        *rows,
        "-" * 70,
        f"  TOTAL contacts written : {total_written}",
        f"  TOTAL duplicates skipped: {total_skipped}",
        "=" * 70,
    ]
    return "\n".join(lines)
