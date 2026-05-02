"""
Prospector orchestrator — coordinates Hunter + Apollo with:
  - Per-campaign output (output/campaigns/<name>/)
  - Global deduplication (output/.seen.json)
  - API fallback: when Hunter hits limit → auto-switch to Apollo and vice-versa
  - Full logging per run
"""

import json
import os
from config.companies import COMPANIES, RECRUITER_TITLES
from src.hunter_client import HunterClient, RateLimitError
from src.apollo_client import ApolloClient, RateLimitError as ApolloRateLimitError
from src.csv_exporter import write_prospects
from src.dedup_store import DedupStore
from src.campaign_manager import Campaign
from src.logger import get_logger, generate_report


def _is_recruiter(position: str, titles: list[str]) -> bool:
    pos = position.lower()
    keywords = [t.lower() for t in titles] + [
        "recruiter", "talent", "hiring", "people", "rh", "hr",
    ]
    return any(k in pos for k in keywords)


def _filter_companies(
    verticals: list[str] | None, max_companies: int | None
) -> list[dict]:
    companies = COMPANIES
    if verticals:
        companies = [c for c in companies if c["vertical"] in verticals]
    if max_companies:
        companies = companies[:max_companies]
    return companies


def run_campaign(
    campaign_name: str,
    source: str,
    verticals: list[str] | None = None,
    max_companies: int | None = None,
    description: str = "",
    fallback: bool = True,
) -> dict:
    """
    Run a named prospection campaign. Returns campaign stats dict.
    Output: output/campaigns/<campaign_name>/prospects.csv

    source: "hunter" | "apollo" | "combined"
    fallback: auto-switch API when rate limit is hit
    """
    campaign = Campaign(
        name=campaign_name,
        source=source,
        verticals=verticals,
        description=description,
    )
    log = get_logger(campaign_name, campaign.log_path)
    dedup = DedupStore()

    log.info(
        f"Campaign '{campaign_name}' started | source={source} | verticals={verticals or 'ALL'}")
    log.info(f"Dedup state: {dedup.stats()}")

    targets = _filter_companies(verticals, max_companies)
    log.info(f"Target companies: {len(targets)}")

    all_new: list[dict] = []
    active_source = source

    for company in targets:
        log.info(f"Processing: {company['name']} [{company['vertical']}]")
        campaign.update_stats(companies_processed=1)
        contacts: list[dict] = []

        # ── Hunter ────────────────────────────────────────────────────────
        if active_source in ("hunter", "combined"):
            if dedup.already_searched_hunter(company["domain"]):
                log.debug(
                    f"  [Hunter] Skipping {company['domain']} — already searched")
            else:
                try:
                    hunter = HunterClient()
                    raw = hunter.domain_search(company["domain"], limit=20)
                    dedup.mark_hunter_domain(company["domain"])
                    campaign.update_stats(hunter_calls=1)
                    log.debug(
                        f"  [Hunter] {len(raw)} raw contacts for {company['domain']}")
                    for c in raw:
                        c["company"] = company["name"]
                        c["domain"] = company["domain"]
                        c["vertical"] = company["vertical"]
                    contacts.extend(raw)

                except RateLimitError:
                    log.warning(
                        f"  [Hunter] Rate limit hit for {company['name']}")
                    if fallback and active_source == "hunter":
                        log.warning(
                            "  → Falling back to Apollo for remaining companies")
                        active_source = "apollo"
                        campaign.update_stats(api_fallbacks=1)
                    else:
                        log.error("  No fallback — stopping")
                        break

                except ValueError as e:
                    log.error(f"  [Hunter] Config error: {e}")
                    if fallback:
                        active_source = "apollo"
                        campaign.update_stats(api_fallbacks=1)

        # ── Apollo ────────────────────────────────────────────────────────
        if active_source in ("apollo", "combined"):
            if dedup.already_searched_apollo(company["name"]):
                log.debug(
                    f"  [Apollo] Skipping {company['name']} — already searched")
            else:
                try:
                    apollo = ApolloClient()
                    raw = apollo.search_people(
                        company["name"], RECRUITER_TITLES, per_page=5)
                    dedup.mark_apollo_company(company["name"])
                    campaign.update_stats(apollo_calls=1)
                    log.debug(
                        f"  [Apollo] {len(raw)} raw contacts for {company['name']}")
                    for c in raw:
                        if not c.get("company"):
                            c["company"] = company["name"]
                        c["domain"] = company["domain"]
                        c["vertical"] = company["vertical"]

                    if active_source == "combined":
                        hunter_names = {
                            f"{c['first_name'].lower()}_{c['last_name'].lower()}"
                            for c in contacts
                        }
                        raw = [
                            c for c in raw
                            if f"{c['first_name'].lower()}_{c['last_name'].lower()}"
                            not in hunter_names
                        ]
                    contacts.extend(raw)

                except ApolloRateLimitError:
                    log.warning(
                        f"  [Apollo] Rate limit hit for {company['name']}")
                    if fallback and active_source == "apollo":
                        log.warning(
                            "  → Falling back to Hunter for remaining companies")
                        active_source = "hunter"
                        campaign.update_stats(api_fallbacks=1)
                    else:
                        log.error("  No fallback — stopping")
                        break

                except ValueError as e:
                    log.error(
                        f"  [Apollo] Config error: {e} — skipping company")
                    campaign.update_stats(errors=1)

        # ── Dedup filter ──────────────────────────────────────────────────
        campaign.update_stats(contacts_found=len(contacts))
        new_contacts, skipped = dedup.filter_new(contacts)
        campaign.update_stats(contacts_skipped_dedup=skipped)

        if skipped:
            log.info(
                f"  → {len(new_contacts)} new / {skipped} duplicates removed")
        else:
            log.info(f"  → {len(new_contacts)} new contacts")

        all_new.extend(new_contacts)

    # ── Write CSV ─────────────────────────────────────────────────────────
    written = write_prospects(all_new, campaign.prospects_path)
    campaign.set_stats(contacts_written=written)
    dedup.save()

    # ── Report ────────────────────────────────────────────────────────────
    with open(campaign.meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    report_path = generate_report(meta, campaign.dir)
    log.info(f"Report saved: {report_path}")
    with open(report_path, encoding="utf-8") as f:
        print(f.read())

    log.info(f"Done — {written} contacts written to {campaign.prospects_path}")
    return campaign.stats


# ── Legacy shortcuts (kept for backward compat) ───────────────────────────────

def run_hunter_only(output_path: str, verticals=None, max_companies=None) -> int:
    name = f"hunter_{_ts()}"
    stats = run_campaign(name, "hunter", verticals, max_companies)
    return stats.get("contacts_written", 0)


def run_apollo_only(output_path: str, verticals=None, max_companies=None) -> int:
    name = f"apollo_{_ts()}"
    stats = run_campaign(name, "apollo", verticals, max_companies)
    return stats.get("contacts_written", 0)


def run_combined(output_path: str, verticals=None, max_companies=None) -> int:
    name = f"combined_{_ts()}"
    stats = run_campaign(name, "combined", verticals, max_companies)
    return stats.get("contacts_written", 0)


def _ts() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")


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
        print(
            f"[Hunter] Credits — used: {credits['used']} / available: {credits['available']}")
    except Exception:
        pass

    targets = _filter_companies(verticals, max_companies)
    all_prospects: list[dict] = []

    for company in targets:
        print(f"  → Hunter: {company['name']} ({company['domain']})")
        contacts = client.domain_search(company["domain"], limit=20)

        # Keep everyone — recruiter filter is a best-effort
        recruiters = [c for c in contacts if _is_recruiter(
            c.get("position", ""), RECRUITER_TITLES)]
        if not recruiters:
            # fallback: take first 5 if no title match
            recruiters = contacts[:5]

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
        contacts = client.search_people(
            company["name"], RECRUITER_TITLES, per_page=5)

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
        apollo_contacts = apollo.search_people(
            company["name"], RECRUITER_TITLES, per_page=5)

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
