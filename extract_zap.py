"""
extract_zap.py — Extrai números de WhatsApp de screenshots e gera CSV para disparo.

Uso:
  python extract_zap.py                    # Tesseract local (padrão)
  python extract_zap.py --engine openai    # OpenAI Vision API (mais preciso)
  python extract_zap.py --input minha_pasta --output minha_lista.csv

Instalar dependências:
  Tesseract: pip install pytesseract Pillow
  OpenAI:    pip install openai Pillow python-dotenv
  Tesseract binário (Windows): https://github.com/UB-Mannheim/tesseract/wiki
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Phone extraction — Brazilian formats
# ---------------------------------------------------------------------------

PHONE_RE = re.compile(
    r"""
    (?:\+?55[\s\-.]?)?          # country code optional: +55 or 55
    \(?(\d{2})\)?               # DDD (2 digits), parentheses optional
    [\s\-.]?
    (9\d{4})                    # 5-digit prefix (mobile always starts with 9)
    [\s\-.]?
    (\d{4})                     # last 4 digits
    |
    (?:\+?55[\s\-.]?)?
    \(?(\d{2})\)?
    [\s\-.]?
    (\d{4})                     # 4-digit prefix (landline)
    [\s\-.]?
    (\d{4})
    """,
    re.VERBOSE,
)

NAME_RE = re.compile(r"^[A-ZÀ-Ú][a-zA-ZÀ-úÇç'\s]{2,40}$")


def normalize_phone(match) -> str | None:
    """Return E.164-ish string: 5511999998888 or None if invalid."""
    if match.group(1):  # mobile path
        ddd, prefix, suffix = match.group(1), match.group(2), match.group(3)
        return f"55{ddd}{prefix}{suffix}"
    elif match.group(4):  # landline path
        ddd, prefix, suffix = match.group(4), match.group(5), match.group(6)
        if prefix and suffix:
            return f"55{ddd}{prefix}{suffix}"
    return None


def extract_phones_and_names(text: str) -> list[dict]:
    """
    Extract ALL (nome, telefone) pairs from raw OCR text.

    WhatsApp group lists typically render as:
        João Silva          ← name line (above phone)
        +55 11 99999-8888
        Maria Santos
        +55 21 98888-7777

    Also handles:
        - Name and phone on the same line: "João Silva +55 11 99999-8888"
        - Name appearing BELOW the phone (some layouts)
        - Inline chat messages containing numbers
    """
    lines = text.splitlines()
    results = []
    seen = set()

    for i, line in enumerate(lines):
        for match in PHONE_RE.finditer(line):
            phone = normalize_phone(match)
            if not phone or phone in seen:
                continue
            ddd = int(phone[2:4])
            if not (11 <= ddd <= 99):
                continue
            seen.add(phone)

            nome = ""

            # 1. Same line: extract text BEFORE the phone number on this line
            prefix = line[: match.start()].strip().rstrip(":,-")
            if NAME_RE.match(prefix) and len(prefix) > 3:
                nome = prefix

            # 2. Look at up to 5 lines BEFORE (WhatsApp list: name is above number)
            if not nome:
                for j in range(i - 1, max(i - 6, -1), -1):
                    candidate = lines[j].strip()
                    if not candidate:
                        continue
                    # Stop if this line itself contains a phone (different contact block)
                    if PHONE_RE.search(candidate):
                        break
                    if NAME_RE.match(candidate) and len(candidate) > 3:
                        nome = candidate
                        break

            # 3. Look at up to 2 lines AFTER (some layouts show number then name)
            if not nome:
                for j in range(i + 1, min(i + 3, len(lines))):
                    candidate = lines[j].strip()
                    if not candidate:
                        continue
                    if PHONE_RE.search(candidate):
                        break
                    if NAME_RE.match(candidate) and len(candidate) > 3:
                        nome = candidate
                        break

            results.append({"nome": nome, "telefone": phone})

    return results


# ---------------------------------------------------------------------------
# Engine A — Tesseract (local, free)
# ---------------------------------------------------------------------------

def ocr_tesseract(image_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        print("ERROR: Install with:  pip install pytesseract Pillow")
        print("       Then install Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)

    # Common Windows install path
    tess_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tess_path):
        pytesseract.pytesseract.tesseract_cmd = tess_path

    img = Image.open(image_path)
    return pytesseract.image_to_string(img, lang="por+eng")


# ---------------------------------------------------------------------------
# Engine B — OpenAI Vision (paid, more accurate)
# ---------------------------------------------------------------------------

def ocr_openai(image_path: str) -> str:
    try:
        import base64
        from openai import OpenAI
        from dotenv import load_dotenv
    except ImportError:
        print("ERROR: Install with:  pip install openai python-dotenv Pillow")
        sys.exit(1)

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    ext = Path(image_path).suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "This is a WhatsApp screenshot with MULTIPLE contacts. "
                            "Extract ALL phone numbers and their associated names. "
                            "Return one contact per line using this exact format: NAME | PHONE. "
                            "If a name is not visible for a number, write: SEM NOME | PHONE. "
                            "Include ALL contacts visible — do not skip any. "
                            "Preserve Brazilian phone format with country code +55 when present."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"},
                    },
                ],
            }
        ],
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


def parse_openai_output(text: str) -> list[dict]:
    """Parse OpenAI-structured output (NAME | PHONE) and also fallback to regex."""
    results = []
    seen = set()

    for line in text.splitlines():
        line = line.strip()
        if "|" in line:
            parts = line.split("|", 1)
            nome = parts[0].strip()
            raw_phone = parts[1].strip()
        else:
            nome = ""
            raw_phone = line

        # Find phone via regex on the raw_phone segment
        for match in PHONE_RE.finditer(raw_phone):
            phone = normalize_phone(match)
            if not phone or phone in seen:
                continue
            ddd = int(phone[2:4])
            if not (11 <= ddd <= 99):
                continue
            seen.add(phone)
            results.append({"nome": nome, "telefone": phone})

    # Fallback: also run generic extraction on full block
    for entry in extract_phones_and_names(text):
        if entry["telefone"] not in seen:
            seen.add(entry["telefone"])
            results.append(entry)

    return results


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "nome",
    "telefone",
    "whatsapp_link",
    "fonte",
    "data_coleta",
    "status",
    "notas",
]


def write_csv(rows: list[dict], output_path: str) -> None:
    exists = Path(output_path).exists()
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def main():
    parser = argparse.ArgumentParser(
        description="Extract WhatsApp contacts from screenshots → CSV")
    parser.add_argument("--input", default="inputImages",
                        help="Folder with screenshots (default: inputImages)")
    parser.add_argument(
        "--output", default="output/zap_contacts.csv", help="Output CSV path")
    parser.add_argument(
        "--engine", choices=["tesseract", "openai"], default="tesseract", help="OCR engine")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"ERROR: Folder '{args.input}' not found.")
        sys.exit(1)

    images = [f for f in sorted(input_dir.iterdir())
              if f.suffix.lower() in IMAGE_EXTS]
    if not images:
        print(f"No images found in '{args.input}'. Supported: {IMAGE_EXTS}")
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    total_found = 0
    total_dupes = 0
    all_seen = set()

    print(
        f"Engine: {args.engine} | Images: {len(images)} | Output: {args.output}\n")

    for img_path in images:
        print(f"  Processing: {img_path.name} ...", end=" ", flush=True)

        try:
            if args.engine == "tesseract":
                text = ocr_tesseract(str(img_path))
                contacts = extract_phones_and_names(text)
            else:
                text = ocr_openai(str(img_path))
                contacts = parse_openai_output(text)
        except Exception as e:
            print(f"SKIP ({e})")
            continue

        now = datetime.now().strftime("%Y-%m-%d")
        rows = []
        dupes = 0

        for c in contacts:
            phone = c["telefone"]
            if phone in all_seen:
                dupes += 1
                continue
            all_seen.add(phone)
            rows.append({
                "nome": c["nome"],
                "telefone": phone,
                "whatsapp_link": f"https://wa.me/{phone}",
                "fonte": img_path.name,
                "data_coleta": now,
                "status": "novo",
                "notas": "",
            })

        if rows:
            write_csv(rows, args.output)

        total_found += len(rows)
        total_dupes += dupes
        print(f"{len(rows)} novos, {dupes} duplicados")

    print(
        f"\nDone. Total: {total_found} contatos → {args.output} | {total_dupes} duplicados ignorados")


if __name__ == "__main__":
    main()
