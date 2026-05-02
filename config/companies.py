"""
Target companies with their web domains and vertical.
Add or remove entries freely — the prospector uses this list.
"""

COMPANIES = [
    # ── Fintech & Payments
    {"name": "Nubank",          "domain": "nubank.com.br",      "vertical": "Fintech"},
    {"name": "Ebanx",           "domain": "ebanx.com",          "vertical": "Fintech"},
    {"name": "Creditas",        "domain": "creditas.com",        "vertical": "Fintech"},
    {"name": "Pismo",           "domain": "pismo.io",            "vertical": "Fintech"},
    {"name": "Dock",            "domain": "dock.tech",           "vertical": "Fintech"},
    {"name": "Celcoin",         "domain": "celcoin.com.br",      "vertical": "Fintech"},
    {"name": "Matera",          "domain": "matera.com",          "vertical": "Fintech"},
    {"name": "dLocal",          "domain": "dlocal.com",          "vertical": "Fintech"},
    {"name": "Nuvei",           "domain": "nuvei.com",           "vertical": "Fintech"},
    {"name": "Kushki",          "domain": "kushki.com",          "vertical": "Fintech"},
    {"name": "Pomelo",          "domain": "pomelo.la",           "vertical": "Fintech"},
    {"name": "Belvo",           "domain": "belvo.com",           "vertical": "Fintech"},

    # ── Trade Tech
    {"name": "Warren",          "domain": "warren.com.br",
        "vertical": "TradeTech"},
    {"name": "Alpaca",          "domain": "alpaca.markets",
        "vertical": "TradeTech"},
    {"name": "TradersClub",     "domain": "tradersclub.com.br",  "vertical": "TradeTech"},
    {"name": "QuantConnect",    "domain": "quantconnect.com",    "vertical": "TradeTech"},

    # ── Health Tech
    {"name": "Alice",           "domain": "alice.com.br",
        "vertical": "HealthTech"},
    {"name": "Sami",            "domain": "sami.com.br",
        "vertical": "HealthTech"},
    {"name": "Sword Health",    "domain": "swordhealth.com",
        "vertical": "HealthTech"},
    {"name": "Clipboard Health", "domain": "clipboardhealth.com",
        "vertical": "HealthTech"},
    {"name": "Omada Health",    "domain": "omadahealth.com",
        "vertical": "HealthTech"},

    # ── Customer Service / CX
    {"name": "Take Blip",       "domain": "take.net",            "vertical": "CXTech"},
    {"name": "Zenvia",          "domain": "zenvia.com",          "vertical": "CXTech"},
    {"name": "Botmaker",        "domain": "botmaker.com",        "vertical": "CXTech"},
    {"name": "Intercom",        "domain": "intercom.com",        "vertical": "CXTech"},
    {"name": "Freshworks",      "domain": "freshworks.com",      "vertical": "CXTech"},
    {"name": "Twilio",          "domain": "twilio.com",          "vertical": "CXTech"},

    # ── Sales Tech
    {"name": "Exact Sales",     "domain": "exactsales.com.br",   "vertical": "SalesTech"},
    {"name": "Ramper",          "domain": "ramper.com.br",
        "vertical": "SalesTech"},
    {"name": "Apollo.io",       "domain": "apollo.io",
        "vertical": "SalesTech"},
    {"name": "Outreach",        "domain": "outreach.io",
        "vertical": "SalesTech"},
    {"name": "Gong",            "domain": "gong.io",
        "vertical": "SalesTech"},
    {"name": "Salesloft",       "domain": "salesloft.com",
        "vertical": "SalesTech"},

    # ── Legal Tech
    {"name": "Ironclad",        "domain": "ironcladapp.com",
        "vertical": "LegalTech"},
    {"name": "Harvey",          "domain": "harvey.ai",
        "vertical": "LegalTech"},
    {"name": "Clio",            "domain": "clio.com",
        "vertical": "LegalTech"},
    {"name": "EvenUp",          "domain": "evenuplaw.com",
        "vertical": "LegalTech"},
    {"name": "Relativity",      "domain": "relativity.com",
        "vertical": "LegalTech"},

    # ── AI Governance
    {"name": "Weights & Biases", "domain": "wandb.ai",
        "vertical": "AIGovernance"},
    {"name": "Scale AI",        "domain": "scale.com",
        "vertical": "AIGovernance"},
    {"name": "DataRobot",       "domain": "datarobot.com",
        "vertical": "AIGovernance"},
    {"name": "Patronus AI",     "domain": "patronus.ai",
        "vertical": "AIGovernance"},
    {"name": "Credo AI",        "domain": "credo.ai",
        "vertical": "AIGovernance"},

    # ── Cybersecurity
    {"name": "Axur",            "domain": "axur.com",
        "vertical": "Cybersecurity"},
    {"name": "Snyk",            "domain": "snyk.io",
        "vertical": "Cybersecurity"},
    {"name": "Wiz",             "domain": "wiz.io",
        "vertical": "Cybersecurity"},
    {"name": "SentinelOne",     "domain": "sentinelone.com",
        "vertical": "Cybersecurity"},
    {"name": "GitGuardian",     "domain": "gitguardian.com",
        "vertical": "Cybersecurity"},

    # ── Platform / SRE
    {"name": "PagerDuty",       "domain": "pagerduty.com",       "vertical": "Platform"},
    {"name": "Grafana Labs",    "domain": "grafana.com",         "vertical": "Platform"},
    {"name": "Datadog",         "domain": "datadoghq.com",       "vertical": "Platform"},
    {"name": "Honeycomb",       "domain": "honeycomb.io",        "vertical": "Platform"},
]

# Job titles to search for in Apollo
RECRUITER_TITLES = [
    "Technical Recruiter",
    "Senior Technical Recruiter",
    "Talent Acquisition",
    "TA Manager",
    "Head of Talent",
    "Engineering Recruiter",
    "Global Recruiter",
    "LATAM Recruiter",
]
