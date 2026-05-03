from __future__ import annotations

"""
Snov.io client — FREE plan: 1000 credits/month
Uses OAuth2 client_credentials + v2 async API (start -> poll result).

Credit cost per domain search:
  - 1 credit per /prospects/start request
  - 1 credit per email found via search-emails

Get credentials at: https://app.snov.io/account/api
"""

import os
import time
import requests


_BASE_URL   = "https://api.snov.io"
_TOKEN_URL  = f"{_BASE_URL}/v1/oauth/access_token"
_POLL_MAX   = 30   # seconds to wait for each async task
_RATE_DELAY = 1.0  # seconds between domain requests


class RateLimitError(Exception):
    """Raised when Snov.io returns HTTP 429 (quota exhausted)."""
    pass


class SnovClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.client_id     = client_id     or os.getenv("SNOV_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SNOV_CLIENT_SECRET", "")
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "SNOV_CLIENT_ID e SNOV_CLIENT_SECRET nao configurados. "
                "Obtenha em https://app.snov.io/account/api"
            )
        self._token: str | None = None

    # ── OAuth token ─────────────────────────────────────────────────────────

    def _get_token(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            _TOKEN_URL,
            data={
                "grant_type":    "client_credentials",
                "client_id":     self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=15,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    # ── Polling helper ───────────────────────────────────────────────────────

    def _poll(self, url: str, max_wait: int = _POLL_MAX) -> dict:
        """GET url until status == 'completed' or timeout. Returns response dict."""
        deadline = time.time() + max_wait
        while time.time() < deadline:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "completed":
                return data
            time.sleep(2)
        return {}

    # ── Per-prospect email fetch ─────────────────────────────────────────────

    def _fetch_email(self, search_emails_start_url: str) -> str:
        """
        POST to the search_emails_start URL from a prospect result, then poll.
        Returns best email found or "" if none. Costs 1 credit if email found.
        """
        try:
            resp = requests.post(
                search_emails_start_url,
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            result_url = resp.json().get("links", {}).get("result", "")
            if not result_url:
                return ""
            result = self._poll(result_url, max_wait=20)
            emails = result.get("data", {}).get("emails", [])
            if emails:
                for e in emails:
                    if e.get("smtp_status") == "valid":
                        return e["email"]
                return emails[0]["email"]
        except Exception:
            pass
        return ""

    # ── Domain search ────────────────────────────────────────────────────────

    def domain_search(
        self,
        domain: str,
        titles: list[str] | None = None,
        limit: int = 20,
        fetch_emails: bool = True,
    ) -> list[dict]:
        """
        Find recruiter profiles at *domain* using the v2 async API.
          1. POST /v2/domain-search/prospects/start  (positions[] server-side filter)
          2. Poll  /v2/domain-search/prospects/result/{task_hash}
          3. For each prospect, POST search_emails_start URL + poll result

        Returns contacts compatible with the pipeline.
        """
        # Positions filter — max 10 per API call
        positions = (titles or [
            "Recruiter", "Talent Acquisition", "HR Manager",
            "Head of Talent", "People Operations",
        ])[:10]

        # Build form-encoded data with positions[] array
        form_data: list[tuple[str, str]] = [("domain", domain)]
        for pos in positions:
            form_data.append(("positions[]", pos))

        try:
            resp = requests.post(
                f"{_BASE_URL}/v2/domain-search/prospects/start",
                headers=self._headers(),
                data=form_data,
                timeout=15,
            )
            if resp.status_code == 429:
                raise RateLimitError(f"Snov.io quota esgotada para {domain}")
            if resp.status_code in (401, 403):
                raise ValueError(
                    "SNOV_CLIENT_ID ou SNOV_CLIENT_SECRET invalido, "
                    "ou plano gratuito sem acesso API. "
                    "Agende uma demo em https://snov.io para liberar acesso."
                )
            resp.raise_for_status()

            payload    = resp.json()
            result_url = payload.get("links", {}).get("result", "")
            if not result_url:
                print(f"  [Snov] Sem result URL para {domain}")
                return []

            # Poll until prospects are ready
            result    = self._poll(result_url)
            prospects = result.get("data", [])

            if not prospects:
                status = result.get("status", "timeout/sem dados")
                print(f"  [Snov] 0 prospects para {domain} (status={status})")
                return []

            contacts = []
            for p in prospects[:limit]:
                email = ""
                if fetch_emails and p.get("search_emails_start"):
                    email = self._fetch_email(p["search_emails_start"])
                    time.sleep(0.5)

                contacts.append({
                    "first_name":     p.get("first_name", ""),
                    "last_name":      p.get("last_name",  ""),
                    "email":          email,
                    "position":       p.get("position",   ""),
                    "linkedin":       p.get("source_page", ""),
                    "company":        "",   # filled by prospector
                    "company_domain": domain,
                    "source":         "snov",
                })

            time.sleep(_RATE_DELAY)
            return contacts

        except (RateLimitError, ValueError):
            raise
        except requests.HTTPError as exc:
            print(f"  [Snov] HTTP error para {domain}: {exc}")
            return []
        except Exception as exc:
            print(f"  [Snov] Erro para {domain}: {exc}")
            return []

    # ── Balance check ────────────────────────────────────────────────────────

    def check_balance(self) -> dict:
        """
        Returns {balance, limit_resets_in, expires_in} or {}.
        Free to call (no credit cost).
        """
        try:
            resp = requests.get(
                f"{_BASE_URL}/v1/get-balance",
                params={"access_token": self._get_token()},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("data", {})
        except Exception:
            return {}
