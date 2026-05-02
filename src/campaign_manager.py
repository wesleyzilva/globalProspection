"""
Campaign manager — each run is a named campaign with its own output file and log.

Campaigns are stored in output/campaigns/<campaign_name>/
  - prospects.csv     ← contacts found in this campaign
  - campaign.json     ← metadata (created, source, verticals, stats)
  - run.log           ← full log for this campaign

Global dedup is shared across all campaigns (output/.seen.json).
This lets you run multiple campaigns (e.g. "fintech_q2", "cybersec_may") without
ever contacting the same person twice.
"""

import json
import os
from datetime import datetime
from pathlib import Path


CAMPAIGNS_DIR = "output/campaigns"


class Campaign:
    def __init__(
        self,
        name: str,
        source: str,
        verticals: list[str] | None = None,
        description: str = "",
    ):
        self.name = name
        self.source = source
        self.verticals = verticals or []
        self.description = description
        self.created_at = datetime.now().isoformat(timespec="seconds")
        self.dir = os.path.join(CAMPAIGNS_DIR, name)
        self.prospects_path = os.path.join(self.dir, "prospects.csv")
        self.log_path = os.path.join(self.dir, "run.log")
        self.meta_path = os.path.join(self.dir, "campaign.json")
        os.makedirs(self.dir, exist_ok=True)
        self._stats: dict = {
            "companies_processed": 0,
            "contacts_found": 0,
            "contacts_skipped_dedup": 0,
            "contacts_written": 0,
            "hunter_calls": 0,
            "apollo_calls": 0,
            "api_fallbacks": 0,
            "errors": 0,
        }
        self._save_meta()

    def _save_meta(self) -> None:
        meta = {
            "name": self.name,
            "source": self.source,
            "verticals": self.verticals,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "stats": self._stats,
        }
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def update_stats(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if k in self._stats:
                self._stats[k] += v
        self._save_meta()

    def set_stats(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if k in self._stats:
                self._stats[k] = v
        self._save_meta()

    @property
    def stats(self) -> dict:
        return self._stats


def list_campaigns() -> list[dict]:
    """Return metadata of all campaigns, sorted by created_at desc."""
    result = []
    if not os.path.isdir(CAMPAIGNS_DIR):
        return result
    for name in sorted(os.listdir(CAMPAIGNS_DIR), reverse=True):
        meta_path = os.path.join(CAMPAIGNS_DIR, name, "campaign.json")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, encoding="utf-8") as f:
                    result.append(json.load(f))
            except Exception:
                pass
    return result


def load_campaign_meta(name: str) -> dict | None:
    meta_path = os.path.join(CAMPAIGNS_DIR, name, "campaign.json")
    if not os.path.isfile(meta_path):
        return None
    with open(meta_path, encoding="utf-8") as f:
        return json.load(f)
