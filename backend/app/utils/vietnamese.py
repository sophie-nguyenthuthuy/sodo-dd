"""Vietnamese text normalization helpers used by the OCR parser."""
from __future__ import annotations

import re
import unicodedata

# Hand-curated abbreviations seen on Vietnamese land certificates
ABBREV = {
    r"\bUBND\b": "Ủy ban nhân dân",
    r"\bSởTNMT\b": "Sở Tài nguyên và Môi trường",
    r"\bGCN\b": "Giấy chứng nhận",
    r"\bQSDĐ\b": "Quyền sử dụng đất",
    r"\bQSH\b": "Quyền sở hữu",
    r"\bTP\.?": "Thành phố",
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def expand_abbreviations(s: str) -> str:
    for pat, rep in ABBREV.items():
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    return s


def is_cccd(s: str) -> bool:
    """12-digit citizen ID (CCCD) or legacy 9-digit CMND."""
    s = s.strip()
    return bool(re.fullmatch(r"\d{9}|\d{12}", s))


def parse_area_sqm(s: str) -> float | None:
    """Parses area string like '123,4 m²' or '1.234,50 m2' → 123.4 / 1234.5."""
    m = re.search(r"([\d.,]+)\s*m[2²]?", s)
    if not m:
        return None
    raw = m.group(1)
    # Vietnamese decimal: '.' as thousand sep, ',' as decimal — but OCR is messy, try both
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None
