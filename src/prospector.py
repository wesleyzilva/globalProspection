"""
Prospector orchestrator — coordinates Hunter + Apollo to build prospect list.

Strategy (credit-efficient):
  1. Apollo search: find recruiter names + LinkedIn by company — NO email credit used
  2. Hunter domain search: get emails from domain — 1 credit per domain
  3. Cross-reference: match Apollo names with Hunter emails when possible
  4. Write to CSV
"""

import os
from config.companies import COMPANIES, RECRUITER_TITLES
from src.hunter_client import HunterClient
from src.apollo_client import ApolloClient
from src.csv_exporter import write_prospects


def _is_recruiter(position: str, titles: list[str]) -> bool:
    pos = position.lower()
    keywords = [t.lower() for t in titles] + [
        "recruiter", "talent", "hiring", "people", "rh", "hr"
    ]
    return any(k in pos for k in keywords)


def run_hunter_only(
    output_path: str,
    verticals: list[str] | None = None,
    max_companies: int | None = None,
) -> int:
    """
    Use Hunter.io only (Tier 1, 25 free/month).
    Searches each company domain and filters for recruiter-like roles.
    """
    client = HunterClient()
    try:
        credits = client.check_credits()
        print(f"[Hunter] Credits — used: {credits['used']} / available: {credits['available']}")
    except Exception:
        pass

    targets = _filter_companies(verticals, max_companies)
    all_prospects: list[dict] = []

    for company in targets:
        print(f"  → Hunter: {company['name']} ({company['domain']})")
        contacts = client.domain_search(company["domain"], limit=20)

        # Keep everyone — recruiter filter is a best-effort
        recruiters = [c for c in contacts if _is_recruiter(c.get("position", ""), RECRUITER_TITLES)]
        if not recruiters:
            recruiters = contacts[:5]  # fallback: take first 5 if no title match

        for c in recruiters:
            c["company"] = company["name"]
            c["domain"] = company["domain"]
            c["vertical"] = company["vertical"]

        all_prospects.extend(recruiters)
        print(f"     → {len(recruiters)} contacts found")

    written = write_prospects(all_prospects, output_path)
    return written


def run_apollo_only(
    output_path: str,
    verticals: list[str] | None = None,
    max_companies: int | None = None,
) -> int:
    """
    Use Apollo.io only (Tier 2, 50 free/month).
    Searches recruiters by title + company name. Does not spend email credits.
    """
    client = ApolloClient()
    targets = _filter_companies(verticals, max_companies)
    all_prospects: list[dict] = []

    for company in targets:
        print(f"  → Apollo: {company['name']}")
        contacts = client.search_people(company["name"], RECRUITER_TITLES, per_page=5)

        for c in contacts:
            if not c.get("company"):
                c["company"] = company["name"]
            c["domain"] = company["domain"]
            c["vertical"] = company["vertical"]

        all_prospects.extend(contacts)
        print(f"     → {len(contacts)} contacts found")

    written = write_prospects(all_prospects, output_path)
    return written


def run_combined(
    output_path: str,
    verticals: list[str] | None = None,
    max_companies: int | None = None,
) -> int:
    """
    Use both Apollo (names) + Hunter (emails), merging results.
    Most accurate but uses credits from both APIs.
    """
    apollo = ApolloClient()
    hunter = HunterClient()
    targets = _filter_companies(verticals, max_companies)
    all_prospects: list[dict] = []

    for company in targets:
        print(f"  → Combined: {company['name']}")

        # Step 1: Apollo → get names + LinkedIn
        apollo_contacts = apollo.search_people(company["name"], RECRUITER_TITLES, per_page=5)

        # Step 2: Hunter → get emails by domain
        hunter_contacts = hunter.domain_search(company["domain"], limit=20)
        hunter_email_map: dict[str, str] = {}
        for hc in hunter_contacts:
            key = f"{hc['first_name'].lower()}_{hc['last_name'].lower()}"
            hunter_email_map[key] = hc.get("email", "")

        # Step 3: Merge
        merged: list[dict] = []
        for c in apollo_contacts:
            key = f"{c['first_name'].lower()}_{c['last_name'].lower()}"
            if not c.get("email") and key in hunter_email_map:
                c["email"] = hunter_email_map[key]
                c["source"] = "apollo+hunter"
            c["company"] = company["name"]
            c["domain"] = company["domain"]
            c["vertical"] = company["vertical"]
            merged.append(c)

        # Add Hunter-only contacts not found in Apollo
        apollo_names = {
            f"{c['first_name'].lower()}_{c['last_name'].lower()}"
            for c in apollo_contacts
        }
        for hc in hunter_contacts:
            key = f"{hc['first_name'].lower()}_{hc['last_name'].lower()}"
            if key not in apollo_names and _is_recruiter(hc.get("position", ""), RECRUITER_TITLES):
                hc["company"] = company["name"]
                hc["domain"] = company["domain"]
                hc["vertical"] = company["vertical"]
                merged.append(hc)

        all_prospects.extend(merged)
        print(f"     → {len(merged)} contacts")

    written = write_prospects(all_prospects, output_path)
    return written


def _filter_companies(
    verticals: list[str] | None, max_companies: int | None
) -> list[dict]:
    companies = COMPANIES
    if verticals:
        companies = [c for c in companies if c["vertical"] in verticals]
    if max_companies:
        companies = companies[:max_companies]
    return companies
