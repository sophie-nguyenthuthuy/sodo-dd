"""Render a PDF due-diligence report."""

from __future__ import annotations

import hashlib
import io
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _kv_table(rows: list[tuple[str, str]]) -> Table:
    t = Table(rows, colWidths=[5 * cm, 11 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f4f6fa")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd2dc")),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#cbd2dc")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def render(
    *,
    job_id: str,
    organization_name: str,
    parsed: dict[str, Any],
    risk_score: int,
    risk_level: str,
    red_flags: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> tuple[bytes, str]:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        title=f"Sổ Đỏ DD Report — {job_id}",
    )
    s = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>BÁO CÁO THẨM ĐỊNH SỔ ĐỎ</b>", s["Title"]))
    story.append(Paragraph(f"Due Diligence Report — {organization_name}", s["Heading4"]))
    story.append(Paragraph(f"Mã báo cáo: <b>{job_id}</b>", s["BodyText"]))
    story.append(
        Paragraph(
            f"Phát hành: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
            s["BodyText"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    risk_color = {
        "low": "#2e7d32",
        "medium": "#f9a825",
        "high": "#e65100",
        "critical": "#c62828",
    }.get(risk_level, "#37474f")
    story.append(
        Paragraph(
            f"<b>Mức rủi ro: <font color='{risk_color}'>{risk_level.upper()}</font> "
            f"(điểm: {risk_score}/100)</b>",
            s["Heading3"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("<b>1. Thông tin GCN (trích xuất OCR)</b>", s["Heading4"]))
    story.append(
        _kv_table(
            [
                ("Loại mẫu", parsed.get("form", "")),
                ("Số seri", parsed.get("serial_number", "") or "—"),
                ("Số vào sổ", parsed.get("book_number", "") or "—"),
                ("Chủ sử dụng", parsed.get("owner_name", "") or "—"),
                ("CCCD/CMND", parsed.get("owner_id", "") or "—"),
                ("Thửa đất số", parsed.get("parcel_number", "") or "—"),
                ("Tờ bản đồ số", parsed.get("sheet_number", "") or "—"),
                ("Diện tích (m²)", str(parsed.get("area_sqm") or "—")),
                ("Mục đích SD", parsed.get("land_use_purpose", "") or "—"),
                ("Thời hạn", parsed.get("land_use_term", "") or "—"),
                ("Địa chỉ", parsed.get("address", "") or "—"),
                ("Cấp bởi", parsed.get("issued_by", "") or "—"),
                ("Ngày cấp", parsed.get("issued_at", "") or "—"),
            ]
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("<b>2. Cảnh báo (Red flags)</b>", s["Heading4"]))
    if not red_flags:
        story.append(Paragraph("Không phát hiện cảnh báo.", s["BodyText"]))
    else:
        rows = [["#", "Mã", "Mức", "Mô tả", "Nguồn"]]
        for i, f in enumerate(red_flags, 1):
            rows.append(
                [
                    str(i),
                    f.get("code", ""),
                    f.get("severity", ""),
                    Paragraph(f.get("description", ""), s["BodyText"]),
                    f.get("source", ""),
                ]
            )
        t = Table(rows, colWidths=[0.8 * cm, 3.5 * cm, 1.6 * cm, 8 * cm, 2.5 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#cbd2dc")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("<b>3. Nguồn đối chiếu</b>", s["Heading4"]))
    src_rows = [["Nguồn", "Trạng thái", "Thời điểm", "SHA-256"]]
    for src in sources:
        src_rows.append(
            [
                src.get("name", ""),
                src.get("status", ""),
                src.get("queried_at", ""),
                (src.get("response_hash", "") or "")[:16] + "…",
            ]
        )
    t = Table(src_rows, colWidths=[5 * cm, 2.5 * cm, 4.5 * cm, 4.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#cbd2dc")),
            ]
        )
    )
    story.append(t)

    story.append(Spacer(1, 0.6 * cm))
    story.append(
        Paragraph(
            "<i>Báo cáo được tạo tự động. Tài liệu này không thay thế ý kiến pháp lý "
            "chính thức và cần được công chứng/luật sư có thẩm quyền xác nhận trước "
            "khi sử dụng cho mục đích pháp lý hoặc tài chính.</i>",
            s["Italic"],
        )
    )

    doc.build(story)
    pdf = buf.getvalue()
    return pdf, hashlib.sha256(pdf).hexdigest()
