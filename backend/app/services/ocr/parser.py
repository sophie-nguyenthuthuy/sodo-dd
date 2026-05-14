"""Parse OCR text into structured certificate fields.

Strategy:
  - Detect form factor (1993 / 1995 / unified 2009 / unified 2024) via marker phrases.
  - Pull labelled fields using regexes anchored on Vietnamese keywords.
  - Each parse returns confidence per field so downstream scoring can weight risk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.certificate import CertificateForm
from app.utils.vietnamese import normalize_ws, parse_area_sqm


@dataclass(slots=True)
class ParsedCertificate:
    form: CertificateForm = CertificateForm.UNKNOWN
    serial_number: str | None = None
    book_number: str | None = None
    issued_at: str | None = None
    issued_by: str | None = None
    owner_name: str | None = None
    owner_id: str | None = None
    parcel_number: str | None = None
    sheet_number: str | None = None
    area_sqm: float | None = None
    land_use_purpose: str | None = None
    land_use_term: str | None = None
    address: str | None = None
    ward: str | None = None
    district: str | None = None
    province: str | None = None
    field_confidence: dict[str, float] = field(default_factory=dict)


FORM_MARKERS: list[tuple[CertificateForm, list[str]]] = [
    (CertificateForm.UNIFIED_2024, ["quyền sở hữu tài sản gắn liền với đất"]),
    (CertificateForm.UNIFIED_2009, ["quyền sử dụng đất, quyền sở hữu nhà ở"]),
    (CertificateForm.SO_HONG_1995, ["giấy chứng nhận quyền sở hữu nhà ở"]),
    (CertificateForm.SO_DO_1993, ["giấy chứng nhận quyền sử dụng đất"]),
]


def _match(text: str, *patterns: str) -> str | None:
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE | re.UNICODE)
        if m:
            return normalize_ws(m.group(1))
    return None


class CertificateParser:
    def parse(self, raw_text: str) -> ParsedCertificate:
        text = normalize_ws(raw_text)
        result = ParsedCertificate()

        # Form detection
        lower = text.lower()
        for form, markers in FORM_MARKERS:
            if any(m in lower for m in markers):
                result.form = form
                break

        # Serial number, e.g. "Số: AB 123456" or "Số phát hành: BC 654321"
        if v := _match(text, r"S[ốo](?:\s*ph[áa]t\s*h[àa]nh)?[:\s]+([A-Z]{2}\s?\d{6,7})"):
            result.serial_number = v.replace(" ", "")
            result.field_confidence["serial_number"] = 0.9

        # Book number "Số vào sổ cấp GCN: CS12345"
        if v := _match(text, r"S[ốo]\s*v[àa]o\s*s[ổo](?:\s*c[ấa]p\s*GCN)?[:\s]+([A-Z0-9./-]+)"):
            result.book_number = v
            result.field_confidence["book_number"] = 0.85

        # Owner name "Ông/Bà: NGUYỄN VĂN A" or "Họ và tên: ..."
        if v := _match(text, r"(?:Ông|Bà|Họ\s*v[àa]\s*t[êe]n)[:\s]+([^\n,]{3,80})"):
            result.owner_name = v
            result.field_confidence["owner_name"] = 0.8

        # CCCD/CMND
        if v := _match(text, r"(?:CCCD|CMND|CMT|S[ốo]\s*CCCD)[:\s]*([0-9]{12}|[0-9]{9})"):
            result.owner_id = v
            result.field_confidence["owner_id"] = 0.95

        # Parcel number / sheet number
        if v := _match(text, r"Th[ửu]a\s*đ[ấa]t\s*s[ốo][:\s]+(\d{1,6})"):
            result.parcel_number = v
            result.field_confidence["parcel_number"] = 0.9
        if v := _match(text, r"T[ờo]\s*b[ảa]n\s*đ[ồo]\s*s[ốo][:\s]+(\d{1,6})"):
            result.sheet_number = v
            result.field_confidence["sheet_number"] = 0.9

        # Area
        if v := _match(text, r"Di[ệe]n\s*t[íi]ch[:\s]+([\d.,]+\s*m[2²]?)"):
            result.area_sqm = parse_area_sqm(v)
            if result.area_sqm:
                result.field_confidence["area_sqm"] = 0.85

        # Land-use purpose
        if v := _match(text, r"M[ụu]c\s*đ[íi]ch\s*s[ửu]\s*d[ụu]ng[:\s]+([^\n;]{3,120})"):
            result.land_use_purpose = v
            result.field_confidence["land_use_purpose"] = 0.7

        # Term
        if v := _match(text, r"Th[ờo]i\s*h[ạa]n[:\s]+([^\n;]{3,80})"):
            result.land_use_term = v
            result.field_confidence["land_use_term"] = 0.7

        # Issued by / at
        if v := _match(text, r"(?:Cấp\s*b[ởo]i|Cơ\s*quan\s*c[ấa]p)[:\s]+([^\n]{3,120})"):
            result.issued_by = v
            result.field_confidence["issued_by"] = 0.75
        if v := _match(
            text, r"(?:Ng[àa]y\s*c[ấa]p|C[ấa]p\s*ng[àa]y)[:\s]+([0-3]?\d[/-][0-1]?\d[/-]\d{2,4})"
        ):
            result.issued_at = v
            result.field_confidence["issued_at"] = 0.85

        # Address: best-effort, often the line that contains "thuộc"
        if v := _match(text, r"đ[ịi]a\s*ch[ỉi][:\s]+([^\n]{5,200})"):
            result.address = v

        # Province / district / ward — try common preposition cues
        if v := _match(text, r"T[ỉi]nh\s+([A-ZÀ-ỹ][^\s,;]+(?:\s+[A-ZÀ-ỹ][^\s,;]+)*)"):
            result.province = v
        if v := _match(
            text, r"(?:Quận|Huyện|Th[ịi]\s*x[ãa])\s+([A-ZÀ-ỹ][^\s,;]+(?:\s+[A-ZÀ-ỹ][^\s,;]+)*)"
        ):
            result.district = v
        if v := _match(
            text, r"(?:Phường|Xã|Th[ịi]\s*tr[ấa]n)\s+([A-ZÀ-ỹ][^\s,;]+(?:\s+[A-ZÀ-ỹ][^\s,;]+)*)"
        ):
            result.ward = v

        return result
