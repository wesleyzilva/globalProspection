from __future__ import annotations

"""
Scraper para Lecto.com.br — lista telefônica local.

Coleta dados de empresas/estabelecimentos de uma cidade para
prospecção local (aquecimento via WhatsApp / email).

URL padrão da busca:
  https://www.lecto.com.br/busca/basica/{cidade}/keyword/{keyword}/{offset}#resultado

Exemplos:
  São Carlos, todas categorias, página 1:
    /busca/basica/sao%20carlos/keyword/todas-as-cidades/1#resultado
  Ribeirão Preto, keyword "advocacia":
    /busca/basica/ribeirao%20preto/keyword/advocacia/1#resultado

Dados extraídos por listing:
  - nome_empresa
  - ddd
  - telefones_fixos   (lista)
  - celulares         (lista — prováveis WhatsApp)
  - whatsapp_principal (55{ddd}{celular} sem formatação — pronto para link)
  - email
  - site
  - endereco
  - cidade_estado
  - url_lecto
  - descricao (primeiros 300 chars)
  - segmento  (keyword usada na busca)
  - data_coleta
"""

import re
import time
import unicodedata
from datetime import date
from urllib.parse import quote

from curl_cffi import requests as cf_requests
from bs4 import BeautifulSoup


_BASE      = "https://www.lecto.com.br"
_DELAY     = 2.0   # delay entre páginas (respeitar servidor)
_PAGE_SIZE = 10    # Lecto retorna 10 resultados por página
_MAX_PAGES = 50    # proteção: máx. 500 resultados por busca

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.7,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# ── Regex de extração ────────────────────────────────────────────────────────

_RE_DDD     = re.compile(r"\((\d{2})\)")
_RE_TEL_HREF = re.compile(r"tel:\+55(\d{2})\s*([\d\s\-]+)$")


def _slug_city(city: str) -> str:
    """'São Carlos' → 'sao%20carlos'"""
    normalized = unicodedata.normalize("NFD", city.lower())
    ascii_city = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return quote(ascii_city)


def _decode_cf_email(cfemail: str) -> str:
    """Decodifica email ofuscado pelo Cloudflare (XOR com primeiro byte como chave)."""
    try:
        enc = bytes.fromhex(cfemail)
        key = enc[0]
        return "".join(chr(b ^ key) for b in enc[1:])
    except Exception:
        return ""


def _clean_phone(raw: str) -> str:
    """Remove prefixos de operadora ('Vivo ', 'Tim ', 'WhatsApp ', etc.)."""
    return re.sub(
        r"^\s*(WhatsApp|Vivo|Tim|Claro|Oi|Nextel)\s+",
        "",
        raw,
        flags=re.I,
    ).strip()


def _format_whatsapp(ddd: str, celular: str) -> str:
    """Formata número para link do WhatsApp: 55 + DDD + celular (só dígitos)."""
    digits = re.sub(r"\D", "", celular)
    return f"55{ddd}{digits}"


# ── Parser de um bloco div.resultbox ────────────────────────────────────────

def _parse_listing(block: "BeautifulSoup", segmento: str) -> dict | None:
    """Extrai todos os campos de um <div class='resultbox'>."""

    # ── Nome
    h1 = block.find("h1", class_="resultboxtitle")
    if not h1:
        return None
    a_nome = h1.find("a")
    if not a_nome:
        return None
    nome = a_nome.get_text(strip=True)
    url_lecto = a_nome.get("href", "")

    # ── Cidade / DDD
    city_div = block.find("div", class_="city")
    cidade_estado = city_div.get_text(strip=True) if city_div else ""
    ddd_m = _RE_DDD.search(cidade_estado)
    ddd = ddd_m.group(1) if ddd_m else ""
    # Remove o DDD entre parênteses do campo cidade: "São Carlos, SP (16)" → "São Carlos, SP"
    cidade_estado = re.sub(r"\s*\(\d{2}\)\s*$", "", cidade_estado).strip()

    # ── WhatsApp direto via wa.me/ (número já formatado 55XXXXXXXXXXX)
    whatsapp = ""
    wa_a = block.find("a", href=re.compile(r"https://wa\.me/\d+"))
    if wa_a:
        m = re.search(r"https://wa\.me/(\d+)", wa_a["href"])
        if m:
            whatsapp = m.group(1)

    # ── Telefones via href tel:
    fixos: list[str] = []
    celulares: list[str] = []
    seen_phones: set[str] = set()

    for tel_a in block.find_all("a", href=_RE_TEL_HREF):
        href = tel_a["href"]
        m = _RE_TEL_HREF.search(href)
        if not m:
            continue
        phone_raw = _clean_phone(m.group(2))
        digits = re.sub(r"\D", "", phone_raw)
        if digits in seen_phones:
            continue
        seen_phones.add(digits)
        if len(digits) == 9:
            celulares.append(f"{digits[:5]}-{digits[5:]}")
        elif len(digits) == 8:
            fixos.append(f"{digits[:4]}-{digits[4:]}")

    # Fallback: pega texto de span.hidden-xs dentro de phone-announce
    if not fixos and not celulares:
        for phone_div in block.find_all("div", class_="phone-announce"):
            for span in phone_div.find_all("span", class_="hidden-xs"):
                text = _clean_phone(span.get_text(strip=True))
                digits = re.sub(r"\D", "", text)
                if digits in seen_phones:
                    continue
                seen_phones.add(digits)
                if len(digits) == 9:
                    celulares.append(f"{digits[:5]}-{digits[5:]}")
                elif len(digits) == 8:
                    fixos.append(f"{digits[:4]}-{digits[4:]}")

    # Se não tem WhatsApp via wa.me mas tem celular, formata
    if not whatsapp and ddd and celulares:
        whatsapp = _format_whatsapp(ddd, celulares[0])

    # ── Endereço (na div.color2 > div.address-announce)
    endereco = ""
    color2 = block.find("div", class_="color2")
    if color2:
        addr_div = color2.find("div", class_="address-announce")
        if addr_div:
            parts = []
            for span in addr_div.find_all("span"):
                t = span.get_text(strip=True)
                if t and not span.find("img") and "MAPA" not in t:
                    parts.append(t)
            endereco = " ".join(parts)[:150]

    # ── Email: Cloudflare ofusca via data-cfemail
    email = ""
    cf_span = block.find("span", class_="__cf_email__")
    if cf_span and cf_span.get("data-cfemail"):
        email = _decode_cf_email(cf_span["data-cfemail"])
    else:
        mailto_a = block.find("a", href=re.compile(r"^mailto:"))
        if mailto_a:
            email = mailto_a["href"].replace("mailto:", "").strip()

    # ── Site: webbox > internet-announce
    site = ""
    webbox = block.find("div", class_="webbox")
    if webbox:
        internet = webbox.find("div", class_="internet-announce")
        if internet:
            for a in internet.find_all("a", href=True):
                href = a["href"]
                if (
                    href.startswith("http")
                    and "lecto.com.br" not in href
                    and "facebook.com" not in href
                    and "whatsapp.com" not in href
                    and "twitter.com" not in href
                    and "instagram.com" not in href
                ):
                    site = href
                    break

    # ── Descrição
    descricao = ""
    kw_div = block.find("div", class_="keywordbox")
    if kw_div:
        descricao = kw_div.get_text(strip=True)[:300]

    return {
        "nome_empresa":  nome,
        "segmento":      segmento,
        "cidade_estado": cidade_estado,
        "ddd":           ddd,
        "telefone_fixo": fixos[0]     if fixos     else "",
        "celular":       celulares[0] if celulares else "",
        "whatsapp":      whatsapp,
        "email":         email,
        "site":          site,
        "endereco":      endereco,
        "descricao":     descricao,
        "url_lecto":     url_lecto,
        "fonte":         "lecto.com.br",
        "data_coleta":   date.today().strftime("%d/%m/%Y"),
    }


# ── Scraper principal ────────────────────────────────────────────────────────

def scrape(
    cidade: str,
    keyword: str = "todas-as-cidades",
    max_results: int = 200,
    verbose: bool = True,
) -> list[dict]:
    """
    Scrapa listagens de *cidade* com *keyword* até *max_results* resultados.
    Retorna lista de dicts.
    """
    city_slug    = _slug_city(cidade)
    kw_slug      = quote(keyword.lower().replace(" ", "-"))
    max_pages    = min(_MAX_PAGES, (max_results // _PAGE_SIZE) + 1)
    all_contacts: list[dict] = []
    session      = cf_requests.Session(impersonate="chrome120")
    session.headers.update(_HEADERS)

    for page_idx in range(max_pages):
        offset = page_idx * _PAGE_SIZE + 1
        url    = f"{_BASE}/busca/basica/{city_slug}/keyword/{kw_slug}/{offset}#resultado"

        if verbose:
            print(f"  [Lecto] Página {page_idx + 1} → {url}")

        # Visita a home na primeira página para obter cookies antes da busca
        if page_idx == 0:
            try:
                session.get(_BASE, timeout=15)
                session.headers.update({"Referer": _BASE + "/"})
                time.sleep(1.0)
            except Exception:
                pass

        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            print(f"  [Lecto] Erro na página {page_idx + 1}: {exc}")
            break

        soup   = BeautifulSoup(resp.text, "lxml")
        blocks = soup.find_all("div", class_="resultbox")

        if not blocks:
            body_text = soup.get_text()
            if "Nenhum resultado" in body_text or "nenhum resultado" in body_text:
                if verbose:
                    print("  [Lecto] Nenhum resultado — encerrando.")
            else:
                if verbose:
                    print(f"  [Lecto] Nenhum bloco encontrado na página {page_idx + 1}")
            break

        page_contacts = [_parse_listing(b, keyword) for b in blocks]
        page_contacts = [c for c in page_contacts if c and c["nome_empresa"]]

        if verbose:
            print(f"  [Lecto] {len(page_contacts)} contatos nesta página")

        all_contacts.extend(page_contacts)

        if len(all_contacts) >= max_results:
            break

        # Verifica fim de paginação pelo total anunciado na página
        total_match = re.search(r"RESULTADOS?\s+\d+\s*[-–]\s*\d+\s+DE\s+(\d+)", resp.text, re.I)
        if total_match:
            total_found = int(total_match.group(1))
            if offset + _PAGE_SIZE > total_found:
                if verbose:
                    print(f"  [Lecto] Fim dos resultados (total anunciado: {total_found})")
                break

        time.sleep(_DELAY)

    # Deduplicação básica pelo nome
    seen, unique = set(), []
    for c in all_contacts:
        key = c["nome_empresa"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique
