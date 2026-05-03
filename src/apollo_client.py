"""
Apollo.io client — Tier 2 (FREE: 50 credits/month)
Docs: https://apolloio.github.io/apollo-api-docs/

What it does:
  - People search: find recruiters/HR by job title + company name/domain
  - Returns: name, email (when available), LinkedIn URL, title, company

Free plan: 50 export credits/month. Search itself is free; email reveal costs 1 credit.
Strategy: search without email reveal first → use Hunter to find email by name+domain.
"""

from __future__ import annotations

import os
import time
import requests


APOLLO_BASE = "https://api.apollo.io/v1"
_RATE_LIMIT_DELAY = 1.5  # seconds between requests


class RateLimitError(Exception):
    """Raised when the Apollo.io API returns HTTP 429 (quota exhausted)."""
    pass


class ApolloClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("APOLLO_API_KEY", "")
        if not self.api_key or self.api_key == "your_apollo_api_key_here":
            raise ValueError(
                "APOLLO_API_KEY not set. Get a free key at https://developer.apollo.io/keys/"
            )

    def search_people(
        self,
        company_name: str,
        titles: list[str],
        per_page: int = 10,
    ) -> list[dict]:
        """
        Search for people in Apollo's database by title + company name.
        Uses api/v1/people/search (searches Apollo's full public database).
        Returns list of contacts with: name, title, linkedin, company.
        """
        url = f"{APOLLO_BASE}/people/search"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,   # Apollo v1 requires key in header
        }
        params = {}
        payload = {
            "q_organization_name": company_name,
            "person_titles": titles,
            "page": 1,
            "per_page": per_page,
        }
        try:
            resp = requests.post(
                url, params=params, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            people = data.get("people") or data.get("contacts") or []
            if not people:
                # log raw keys to help diagnose unexpected response shapes
                print(f"  [Apollo] Response keys for {company_name}: {list(data.keys())}")

            contacts = []
            for p in people:
                org = (p.get("organization") or p.get("account") or {})
                contacts.append({
                    "first_name": p.get("first_name", ""),
                    "last_name": p.get("last_name", ""),
                    "email": p.get("email", ""),
                    "position": p.get("title", ""),
                    "linkedin": p.get("linkedin_url", ""),
                    "company": org.get("name", company_name),
                    "company_domain": org.get("domain", org.get("primary_domain", "")),
                    "source": "apollo_contacts_search",
                })
            time.sleep(_RATE_LIMIT_DELAY)
            return contacts
        except requests.HTTPError as e:
            if resp.status_code == 429:
                raise RateLimitError(
                    f"Apollo.io rate limit reached for {company_name}")
            elif resp.status_code == 401:
                raise ValueError("APOLLO_API_KEY is invalid or expired")
            elif resp.status_code == 403:
                body = {}
                try:
                    body = resp.json()
                except Exception:
                    pass
                if body.get("error_code") == "API_INACCESSIBLE":
                    raise ValueError(
                        "Apollo free plan nao inclui people/search. "
                        "Use Snov.io (SNOV_API_KEY) ou faca upgrade em https://app.apollo.io/"
                    )
                print(f"  [Apollo] HTTP 403 Forbidden para {company_name}: {body.get('error', e)}")
            else:
                print(f"  [Apollo] HTTP error for {company_name}: {e}")
            return []
        except Exception as e:
            print(f"  [Apollo] Error for {company_name}: {e}")
            return []

    def reveal_email(self, person_id: str) -> str:
        """
        Reveal email for a specific Apollo person ID.
        Costs 1 export credit. Use sparingly on the free plan.
        """
        url = f"{APOLLO_BASE}/people/match"
        headers = {"X-Api-Key": self.api_key,
                   "Content-Type": "application/json"}
        payload = {"id": person_id, "reveal_personal_emails": False}
        try:
            resp = requests.post(
                url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json().get("person", {}).get("email", "")
        except Exception as e:
            print(f"  [Apollo] Email reveal error for {person_id}: {e}")
            return ""
