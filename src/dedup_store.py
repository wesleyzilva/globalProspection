from __future__ import annotations

"""
Deduplication store — tracks what we've already found to avoid repeating contacts.

Stores a persistent JSON file at output/.seen.json with:
  - seen_contacts: set of fingerprints (email OR linkedin OR name+domain)
  - searched_domains: set of domains already searched by Hunter
  - searched_companies: set of company names already searched by Apollo
"""

import json
import os
from pathlib import Path


SEEN_FILE = "output/.seen.json"


class DedupStore:
    def __init__(self, path: str = SEEN_FILE):
        self.path = path
        self._data: dict = self._load()

    def _load(self) -> dict:
        if os.path.isfile(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    raw = json.load(f)
                    return {
                        "contacts": set(raw.get("contacts", [])),
                        "hunter_domains": set(raw.get("hunter_domains", [])),
                        "apollo_companies": set(raw.get("apollo_companies", [])),
                    }
            except Exception:
                pass
        return {"contacts": set(), "hunter_domains": set(), "apollo_companies": set()}

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "contacts": sorted(self._data["contacts"]),
                    "hunter_domains": sorted(self._data["hunter_domains"]),
                    "apollo_companies": sorted(self._data["apollo_companies"]),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    # ── Contact deduplication ──────────────────────────────────────────────

    def _fingerprint(self, contact: dict) -> str:
        """
        Primary key priority: email > linkedin > first+last+domain.
        Lowercased and stripped.
        """
        email = (contact.get("email") or "").strip().lower()
        linkedin = (contact.get("linkedin") or "").strip().lower().rstrip("/")
        name = f"{contact.get('first_name', '').lower()}_{contact.get('last_name', '').lower()}"
        domain = (contact.get("domain") or contact.get(
            "company_domain") or "").lower()

        if email:
            return f"email:{email}"
        if linkedin:
            return f"li:{linkedin}"
        if name.strip("_"):
            return f"name:{name}@{domain}"
        return ""

    def is_new_contact(self, contact: dict) -> bool:
        fp = self._fingerprint(contact)
        return bool(fp) and fp not in self._data["contacts"]

    def mark_contact(self, contact: dict) -> None:
        fp = self._fingerprint(contact)
        if fp:
            self._data["contacts"].add(fp)

    def filter_new(self, contacts: list[dict]) -> tuple[list[dict], int]:
        """Returns (new_contacts, skipped_count)."""
        new, skipped = [], 0
        for c in contacts:
            if self.is_new_contact(c):
                new.append(c)
                self.mark_contact(c)
            else:
                skipped += 1
        return new, skipped

    # ── Source deduplication ───────────────────────────────────────────────

    def already_searched_hunter(self, domain: str) -> bool:
        return domain.lower() in self._data["hunter_domains"]

    def mark_hunter_domain(self, domain: str) -> None:
        self._data["hunter_domains"].add(domain.lower())

    def already_searched_apollo(self, company: str) -> bool:
        return company.lower() in self._data["apollo_companies"]

    def mark_apollo_company(self, company: str) -> None:
        self._data["apollo_companies"].add(company.lower())

    # ── Stats ──────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "total_contacts_seen": len(self._data["contacts"]),
            "hunter_domains_searched": len(self._data["hunter_domains"]),
            "apollo_companies_searched": len(self._data["apollo_companies"]),
        }
