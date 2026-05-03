"""
Hunter.io client — Tier 1 (FREE: 25 searches/month)
Docs: https://hunter.io/api-documentation/v2

What it does:
  - Domain search: given a company domain, returns all known emails + names + roles
  - Email finder: given first/last name + domain, returns the most likely email

Free plan: 25 requests/month (domain search counts as 1 request)
"""

from __future__ import annotations

import os
import time
import requests


HUNTER_BASE = "https://api.hunter.io/v2"
_RATE_LIMIT_DELAY = 1.2  # seconds between requests (safe for free tier)


class RateLimitError(Exception):
    """Raised when the Hunter.io API returns HTTP 429 (quota exhausted)."""
    pass


class HunterClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("HUNTER_API_KEY", "")
        if not self.api_key or self.api_key == "your_hunter_api_key_here":
            raise ValueError(
                "HUNTER_API_KEY not set. Get a free key at https://hunter.io/api-keys"
            )

    def domain_search(self, domain: str, limit: int = 10) -> list[dict]:
        """
        Search all known emails for a given domain.
        Returns a list of contacts with: first, last, email, position, linkedin
        """
        url = f"{HUNTER_BASE}/domain-search"
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "limit": limit,
            # personal emails only (not generic like info@)
            "type": "personal",
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            emails = data.get("data", {}).get("emails", [])
            contacts = []
            for e in emails:
                contacts.append({
                    "first_name": e.get("first_name", ""),
                    "last_name": e.get("last_name", ""),
                    "email": e.get("value", ""),
                    "position": e.get("position", ""),
                    "linkedin": e.get("linkedin", ""),
                    "confidence": e.get("confidence", 0),
                    "source": "hunter_domain",
                })
            time.sleep(_RATE_LIMIT_DELAY)
            return contacts
        except requests.HTTPError as e:
            if resp.status_code == 429:
                raise RateLimitError(
                    f"Hunter.io rate limit reached for domain {domain}")
            elif resp.status_code == 401:
                raise ValueError("HUNTER_API_KEY is invalid or expired")
            else:
                print(f"  [Hunter] HTTP error for {domain}: {e}")
            return []
        except Exception as e:
            print(f"  [Hunter] Error for {domain}: {e}")
            return []

    def email_finder(self, domain: str, first_name: str, last_name: str) -> dict | None:
        """
        Find the most likely email for a specific person at a domain.
        Uses 1 credit. Returns contact dict or None.
        """
        url = f"{HUNTER_BASE}/email-finder"
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": self.api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if not data.get("email"):
                return None
            time.sleep(_RATE_LIMIT_DELAY)
            return {
                "first_name": first_name,
                "last_name": last_name,
                "email": data.get("email", ""),
                "position": data.get("position", ""),
                "linkedin": data.get("linkedin", ""),
                "confidence": data.get("score", 0),
                "source": "hunter_finder",
            }
        except Exception as e:
            print(
                f"  [Hunter] Finder error for {first_name} {last_name} @ {domain}: {e}")
            return None

    def check_credits(self) -> dict:
        """Check remaining credits on the free plan."""
        url = f"{HUNTER_BASE}/account"
        resp = requests.get(url, params={"api_key": self.api_key}, timeout=10)
        resp.raise_for_status()
        plan = resp.json().get("data", {}).get("requests", {})
        return {
            "used": plan.get("searches", {}).get("used", "?"),
            "available": plan.get("searches", {}).get("available", "?"),
        }
