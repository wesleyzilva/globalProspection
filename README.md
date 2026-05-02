# Global Prospection — Recruiter & Company Finder

> Python app that searches recruiters at funded tech startups and exports a ready-to-use CSV for outreach management.
> Uses free API tiers first — **Hunter.io (25/month)** → **Apollo.io (50/month)** → paid sources later.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/wesleyzilva/globalProspection.git
cd globalProspection

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API keys
cp .env.example .env
# Edit .env and add your keys (start with Hunter.io — it's the easiest free tier)

# 4. Run
python run.py --source hunter                          # Tier 1: Hunter.io only
python run.py --source apollo                          # Tier 2: Apollo.io only
python run.py --source combined                        # Both merged
python run.py --source hunter --verticals Fintech TradeTech --max 5   # filtered
```

Output is saved to `output/prospects.csv` — open in Excel, Google Sheets, or import to any CRM.

---

## API Sources — Free Tier Ranking

| # | Source | Free quota | What it returns | Get key |
|---|--------|-----------|-----------------|---------|
| 1 | **Hunter.io** | 25 searches/month | Emails by company domain + name + role | [hunter.io/api-keys](https://hunter.io/api-keys) |
| 2 | **Apollo.io** | 50 credits/month | Recruiter names + LinkedIn by title + company | [developer.apollo.io](https://developer.apollo.io/keys/) |
| 3 | **RocketReach** | 5 lookups/month | Email + phone verified | [rocketreach.co/api](https://rocketreach.co/api) |
| 4 | **Clearbit** | Paid | Full company + person enrichment | [clearbit.com/api](https://dashboard.clearbit.com/api) |

> Start with Hunter (best free/quality ratio). Add Apollo for name-first search. Combine both for highest coverage.

---

## Project Structure

```
globalProspection/
├── run.py                    ← CLI entry point
├── .env.example              ← API keys template (copy to .env)
├── requirements.txt
├── config/
│   └── companies.py          ← target companies list (edit freely)
├── src/
│   ├── hunter_client.py      ← Hunter.io domain search + email finder
│   ├── apollo_client.py      ← Apollo.io people search
│   ├── prospector.py         ← orchestrator (hunter / apollo / combined)
│   └── csv_exporter.py       ← CSV writer
└── output/
    └── prospects.csv         ← generated output (gitignored)
```

---

## CSV Output Columns

| Column | Description |
|--------|-------------|
| `empresa` | Company name |
| `vertical` | Niche (Fintech, TradeTech, HealthTech...) |
| `primeiro_nome` | First name |
| `ultimo_nome` | Last name |
| `cargo` | Job title |
| `email` | Email (when available) |
| `linkedin` | LinkedIn profile URL |
| `dominio` | Company domain |
| `confianca_email` | Hunter confidence score (0–100) |
| `fonte` | Source API (hunter_domain / apollo_search / apollo+hunter) |
| `data_coleta` | Date collected |
| `status` | Novo / Ativo / Avançando / Entrevista / Oferta / Recusado / Cold |
| `template_usado` | A / B / C (fill manually after contact) |
| `data_contato` | Date of first contact |
| `resposta` | Response received |
| `notas` | Free notes |

---

## Target Verticals

`Fintech` · `TradeTech` · `HealthTech` · `CXTech` · `SalesTech` · `LegalTech` · `AIGovernance` · `Cybersecurity` · `Platform`

Edit `config/companies.py` to add/remove companies or change domains.

---

## Git — Commit & Push

```bash
cd /c/repositorio/repositorio_particular/globalProspection
git remote set-url origin https://wesleyzilva@github.com/wesleyzilva/globalProspection.git
git add .
git commit -m "feat: initial prospection app"
git push origin main
```

---

## Outreach Playbook

See [recruitmentTech/readme-nearshore.md](https://github.com/wesleyzilva/recruitmenttech/blob/main/readme-nearshore.md) for:
- Message templates A / B / C
- Outreach cadence (Day 1 → Day 20)
- Target company list by vertical
- Wesley's differentiators

---

*Last updated: 02/05/2026 — Wesley Silva*

---

# Nearshore Outreach — Global IT Manager Prospecting Playbook

> Target: **funded startups and scale-ups** (Series A–C / unicorns) hiring Brazil-based engineering leads for **global** remote roles.
> Profile: Wesley Silva — IT Manager · UTC-3 · C1 English · AI-First · 14+ years leading nearshore squads.
> Portfolio: [wesleyzilva.github.io](https://wesleyzilva.github.io/portfolioNearshoreWesIA/)

---

## 1. Target Company Types

> **Primary focus: funded startups and scale-ups with proven investment runway (Series A+).** These companies have budget, move fast, and actively need delivery-oriented IT Managers who can operate globally from UTC-3.

---

### Fintech & Payments

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Nubank** | NYSE: NU — unicorn | Global engineering squads led from BR |
| **Ebanx** | BR — unicorn | Cross-border payments, delivery leads |
| **Creditas** | BR — Series F ~$550M | Fintech scale-up, distributed teams |
| **Pismo** | Acquired by Visa | Core banking platform, global clients |
| **Dock** | BR — Series B+ | Fintech infrastructure, multi-country |
| **Celcoin** | BR — Series B | Open finance, scaling fast |
| **Matera** | BR — growth stage | Core banking SaaS, US/EU clients |
| **dLocal** | NASDAQ | Emerging markets payments, LATAM hubs |
| **Nuvei** | NASDAQ | Payments, Brazil hub |
| **Kushki** | LATAM — Series B | Payments infrastructure, multi-country |
| **Pomelo** | LATAM — Series B | Fintech cards infrastructure |
| **Belvo** | LATAM — Series A | Open banking API |

---

### Trade Tech — Trading Robots & Financial Automation

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Anka** | BR — Series A | Algorithmic trading platform for retail investors |
| **Warren** | BR — Series C | Automated investment platform |
| **Órama** | BR — growth | Digital investment distributor, automation-heavy |
| **Clear / XP Inc** | NYSE: XP | Brokerage, heavy fintech engineering |
| **modalmais** | BR — acquired by XP | Trading platform, engineering org |
| **TradersClub** | BR — Series B | Social investing + automation |
| **Alpaca** | US — Series B | API-first brokerage, algo trading infra |
| **Interactive Brokers (IBKR)** | NASDAQ | Global brokerage, LATAM expansion |
| **QuantConnect** | US — Series A | Open-source algo trading platform |
| **Databricks** | US — pre-IPO $43B | Data + AI for quant/financial models |

---

### Health Tech

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Nilo Saúde** | BR — Series B | Digital primary care, distributed squads |
| **Alice** | BR — Series C ~$127M | Corporate health insurance, tech-first |
| **Sami** | BR — Series B | Health plan SaaS, engineering-led |
| **Axur** | BR — Series C | Cyber + health data monitoring |
| **Hims & Hers** | NYSE | Telehealth, LATAM engineering expansion |
| **Clipboard Health** | US — Series C | Healthcare marketplace, remote-first |
| **Sword Health** | US — unicorn | Digital physical therapy, LATAM squads |
| **Dock Health** | US — Series B | Task management for healthcare teams |
| **Omada Health** | US — IPO track | Chronic disease digital care |

---

### Customer Service Tech, Self-Service & Autoatendimento

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Zendesk** | US — private (~$10B) | CX platform, nearshore dev teams |
| **Movidesk** | BR — acquired by Zenvia | CRM/helpdesk, BR engineering |
| **Zenvia** | NASDAQ: ZVIA | Omnichannel CX, LATAM platform |
| **Take Blip** | BR — unicorn | Conversational AI, chatbots, CX automation |
| **Botmaker** | LATAM — Series B | WhatsApp + chatbot automation |
| **Freshworks** | NASDAQ | CRM + CX, LATAM hiring |
| **Intercom** | US — Series D | AI-first customer support |
| **Kustomer** | Acquired by Meta | CX CRM, global delivery |
| **NICE inContact** | NASDAQ | Contact center tech, nearshore delivery |
| **Twilio** | NYSE | Communications API, BR PMs/EMs |

---

### Prospecting, Sales Tech & Revenue Automation

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Exact Sales** | BR — Series B | Sales cadence + lead qualification |
| **Meetime** | BR — growth | Inside sales platform, BR teams |
| **RD Station** | BR — acquired by Totvs | Marketing automation, large BR engineering |
| **Ramper** | BR — Series A | Outbound prospecting automation |
| **Salesforce (BR)** | NYSE | CRM global leader, BR delivery hub |
| **HubSpot** | NYSE | CRM + sales automation, LATAM squad |
| **Apollo.io** | US — Series D ~$1.6B | Sales intelligence, global remote |
| **Outreach** | US — unicorn | Sales engagement platform |
| **Gong** | US — unicorn $7.5B | Revenue intelligence AI |
| **Salesloft** | US — unicorn | Sales engagement, LATAM hiring |

---

### Legal Tech & Jurídico

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Jurídico Certo** | BR — Series A | Legal platform for SMBs |
| **Contraktor** | BR — growth | Contract management, automation |
| **Docket** | BR — Series B | Legal document search + AI |
| **Assertiva** | BR — growth | Legal data intelligence |
| **Clio** | Canada — unicorn | Legal practice management SaaS |
| **Ironclad** | US — Series D $100M+ | Contract lifecycle management AI |
| **Veritone** | NASDAQ | AI-powered legal + compliance platform |
| **Harvey** | US — Series B $100M+ | AI for law firms, engineering-heavy |
| **EvenUp** | US — Series C | AI for legal demand letters |
| **Relativity** | US — $3.4B valuation | Legal tech, e-discovery, global teams |

---

### AI Governance & Responsible AI

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Weights & Biases** | US — Series C $200M | MLOps + model monitoring, AI governance |
| **Arthur AI** | US — Series B | AI monitoring, fairness, explainability |
| **Fiddler AI** | US — Series C | Model performance + bias monitoring |
| **Scale AI** | US — $14B valuation | AI data + governance, LATAM hiring |
| **Patronus AI** | US — Series A | LLM evaluation and compliance |
| **Credo AI** | US — Series A | AI governance platform |
| **Holistic AI** | UK — Series A | EU AI Act compliance automation |
| **Truera** | Acquired by Snowflake | AI quality + trust platform |
| **DataRobot** | US — Series G $1B+ | AutoML + AI governance, global delivery |

---

### Cybersecurity

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Axur** | BR — Series C | Digital risk monitoring, LATAM leader |
| **BugHunt** | BR — Series A | Bug bounty platform, BR engineering |
| **Tempest Security** | BR — acquired by Embratel | Managed security services |
| **Crowdstrike** | NASDAQ | EDR/XDR, LATAM delivery presence |
| **SentinelOne** | NYSE | AI-native cybersecurity, remote-first |
| **Wiz** | US — $12B acquisition by Google | Cloud security, fast-growing teams |
| **Lacework** | US — unicorn | Cloud + data security |
| **Orca Security** | US — Series C $550M | Cloud security platform |
| **Snyk** | US — unicorn $8.6B | Developer-first security, DevSecOps |
| **GitGuardian** | France — Series B | Secrets detection, DevSecOps |

---

### Product Sustentação & SRE / Platform Engineering

| Company | HQ / Stage | Why fit |
|---------|-----------|---------|
| **Instana (IBM)** | US/DE | APM + AIOps, product sustentação |
| **PagerDuty** | NYSE | Incident management, LATAM expansion |
| **Grafana Labs** | US — unicorn $6B | Observability platform, remote squads |
| **Datadog** | NASDAQ | Monitoring + sustentação at scale |
| **Honeycomb** | US — Series D | Observability for distributed systems |
| **Chronosphere** | US — Series C | Cloud-native monitoring |
| **Cortex** | US — Series B | Internal developer portal, platform eng |
| **OpsLevel** | US — Series B | Service catalog + software sustentação |
| **Backstage (Spotify)** | Open source / Roadie SaaS | Developer portal, platform sustentação |

---

### Where to Find Funded Startups

- [Crunchbase](https://crunchbase.com) — filter: Brazil, Series A+, fintech/SaaS/security
- [StartSe](https://startse.com) — Brazilian startup ecosystem map
- [Distrito](https://distrito.me) — BR startup intelligence + funding radar
- [Wellfound](https://wellfound.com) — remote roles at funded startups
- [arc.dev](https://arc.dev) — vetted nearshore engineering roles
- [Y Combinator](https://ycombinator.com/companies) — filter by domain + hiring

---

## 2. LinkedIn Search Strings

Use these in LinkedIn search (People or Jobs):

```
"IT Manager" Brazil remote
"Delivery Manager" nearshore Brazil
"Engineering Manager" UTC-3 OR Brazil
"Technical Program Manager" Brazil remote
"Head of Engineering" LATAM nearshore
"Product Owner" Brazil remote fintech
site:linkedin.com/jobs "IT Manager" "nearshore" "Brazil"
```

### Recruiter filter (People search):
```
title:"Technical Recruiter" OR "TA Manager" company:Globant OR CI&T OR Stefanini OR Encora OR EPAM
```

---

## 3. Message Templates

### Template A — Published Job Opening

```
Hi [Name],

I saw [Company] is hiring an IT Manager / Delivery Manager for global delivery.

I'm Wesley, based in São Paulo (UTC-3), C1 English, 14+ years leading nearshore squads across Brazil, India, South Africa, the US, Costa Rica, and London.

I specialize in: distributed team delivery, DevSecOps, Data Engineering at scale (80M+ tx/day), and building high-performance teams with DORA metrics.

Would love to explore if there's a fit.
Full context: https://wesleyzilva.github.io/portfolioNearshoreWesIA/

Best,
Wesley
```

---

### Template B — Cold Outreach (no open role)

```
Hi [Name],

I came across [Company] and noticed you build distributed teams with Brazil-based engineers.

I'm Wesley — IT Manager in São Paulo, UTC-3, C1 English, 14+ years in nearshore delivery (fintech, utilities, payments).

I'm exploring selective engagements for 2026. Thought it might be worth a quick chat if your team is scaling its LATAM delivery capacity.

Portfolio: https://wesleyzilva.github.io/portfolioNearshoreWesIA/

Is there someone I should connect with?
```

---

### Template C — Short InMail (recruiter)

```
Hi [Name],

Brazil-based IT Manager here — UTC-3, C1 English, 14+ years nearshore leadership (fintech / enterprise / data).

Do you work with LATAM profiles for global IT Manager or Delivery Manager roles?

Happy to share my deck: https://wesleyzilva.github.io/portfolioNearshoreWesIA/
```

---

## 4. Outreach Cadence

| Day | Action |
|-----|--------|
| Day 1 | Send connection request + short note (Template C) |
| Day 5 | If connected, send full message (A or B) |
| Day 12 | Single follow-up: "Just checking in — happy to share more context if useful." |
| Day 20+ | Move to "Cold — revisit in 60 days" column in tracker |

---

## 5. Job Boards — Where to Search

| Platform | URL | Best for |
|----------|-----|---------|
| arc.dev | https://arc.dev | Remote senior engineers / leads |
| Toptal | https://www.toptal.com | Vetted nearshore talent marketplace |
| Wellfound | https://wellfound.com | Startups hiring global/remote |
| remote.com | https://remote.com | Full-remote companies |
| LinkedIn Jobs | linkedin.com/jobs | Everything, filter: Remote + LATAM |
| Glassdoor | glassdoor.com | Company research + salary benchmarks |
| Himalayas | himalayas.app | Remote-only job board, good filters |
| WeWorkRemotely | weworkremotely.com | Dev/engineering roles, global remote |
| Remotive | remotive.com | Curated remote tech jobs |

---

## 6. Prospect Tracker

Use this in a spreadsheet (`outreach/prospect_tracker.csv`):

```csv
Empresa,Recruiter/Contato,LinkedIn URL,Cargo alvo,Data contato,Template usado,Resposta,Follow-up agendado,Status,Notas
Globant,John Smith,https://linkedin.com/in/...,IT Manager,02/05/2026,B,Sem resposta,07/05/2026,Ativo,CTO de squad US
CI&T,Ana Souza,https://linkedin.com/in/...,Delivery Manager,02/05/2026,A,Respondeu,Reuniao 10/05,Avançando,Posição remota conf.
```

**Status values:** `Ativo` · `Avançando` · `Entrevista` · `Oferta` · `Recusado` · `Cold`

---

## 7. Wesley's Differentiators to Highlight

- **UTC-3** → real-time overlap US East + West + Western Europe + UK
- **C1 English** → fluent async and sync communication
- **14+ years nearshore** → 6 countries: Brazil, India, South Africa, US, Costa Rica, London
- **80M+ transactions/day** → data engineering at scale
- **90% vulnerability reduction** → DevSecOps track record
- **DORA Metrics** → engineering performance measurement
- **High Performance Team building** → not just delivery, but team creation and scaling
- **AI-First operating model** → AI-assisted backlog, automated pipelines, agentic workflows
- **Industry domains**: Payments · Billing · Sales · CX · Legal · HR · Regulatory

---

## 8. Rate & Engagement Terms

| Term | Preference |
|------|------------|
| Rate | USD /month |
| Contract | 12/24/36 months preferential; quarterly SOW negotiable |
| Model | Part-time or full-time, SOW-based |
| Payment | Wire transfer; BTC · USDT · USDC · ETH · SOL accepted |
| Working model | Remote-first UTC-3 |
| Exclusivity | One client. Multiple projects. |

---

## 9. Portfolio URLs

| Page | Link |
|------|------|
| Portfolio | [wesleyzilva.github.io](https://wesleyzilva.github.io/portfolioNearshoreWesIA/) |
| About / Quick snapshot | [about](https://wesleyzilva.github.io/portfolioNearshoreWesIA/about) |
| Location & timezone | [location](https://wesleyzilva.github.io/portfolioNearshoreWesIA/location) |

---

## 10. Git — Run, Commit & Push (wesleyzilva account)

```bash
# 1. Navigate to the repo
cd /c/repositorio/repositorio_particular/recruitmentTech

# 2. Check remote (should point to wesleyzilva)
git remote -v
# Expected:
# origin  https://github.com/wesleyzilva/recruitmenttech.git (fetch)
# origin  https://github.com/wesleyzilva/recruitmenttech.git (push)

# 3. If remote is wrong, fix it:
git remote set-url origin https://wesleyzilva@github.com/wesleyzilva/recruitmenttech.git

# 4. Stage changes
git add .

# 5. Commit
git commit -m "feat(nearshore): update playbook with funded startup targets"

# 6. Push to main
git push origin main
```

> If prompted for credentials, use GitHub token (not password).
> Generate at: https://github.com/settings/tokens → Personal access tokens → repo scope.

---

## 11. Last Updated

`02/05/2026` — Wesley Silva · wesley.silva@br.experian.com · [linkedin.com/in/wesleyzilva](https://linkedin.com/in/wesleyzilva)
