"""Risk scoring rules.

Outputs (risk_score 0-100, list[red_flag]). Higher score = higher risk.
Tuned with conservative weights — adjust after real-world calibration.
"""
from __future__ import annotations

from typing import Any

from app.models.report import RiskLevel


def _flag(code: str, severity: str, description: str, source: str) -> dict[str, Any]:
    return {"code": code, "severity": severity, "description": description, "source": source}


def score(
    *,
    parsed: dict[str, Any],
    ocr_confidence: float,
    portal: dict[str, Any] | None,
    zoning: dict[str, Any] | None,
    history: dict[str, Any] | None,
) -> tuple[int, RiskLevel, list[dict[str, Any]]]:
    flags: list[dict[str, Any]] = []
    score_pts = 0

    # OCR confidence
    if ocr_confidence < 0.55:
        score_pts += 25
        flags.append(_flag("ocr_low_confidence", "high",
                           f"OCR confidence {ocr_confidence:.2f} below threshold", "ocr"))
    elif ocr_confidence < 0.75:
        score_pts += 8
        flags.append(_flag("ocr_medium_confidence", "warn",
                           f"OCR confidence {ocr_confidence:.2f} — manual review recommended", "ocr"))

    # Required field presence
    for required in ("serial_number", "parcel_number", "sheet_number"):
        if not parsed.get(required):
            score_pts += 6
            flags.append(_flag(f"missing_{required}", "warn",
                               f"Field '{required}' could not be parsed", "ocr"))

    # Portal verification
    if portal is not None:
        if portal.get("status") == "no_data":
            score_pts += 35
            flags.append(_flag("portal_not_found", "critical",
                               "Land portal returned no record for this certificate",
                               "land_portal"))
        elif portal.get("status") == "error":
            score_pts += 10
            flags.append(_flag("portal_error", "warn",
                               f"Land portal lookup failed: {portal.get('error')}",
                               "land_portal"))
        else:
            data = portal.get("payload", {})
            if data.get("match") == "partial":
                score_pts += 25
                flags.append(_flag("owner_mismatch", "high",
                                   f"Registered owner '{data.get('registered_owner')}' differs from "
                                   f"certificate owner '{data.get('input_owner')}'",
                                   "land_portal"))
            if data.get("status") and data.get("status") != "active":
                score_pts += 30
                flags.append(_flag("certificate_inactive", "critical",
                                   f"Certificate status in portal: {data.get('status')}",
                                   "land_portal"))

    # Zoning
    if zoning is not None and zoning.get("status") == "ok":
        data = zoning.get("payload", {})
        if data.get("conflict"):
            score_pts += 22
            flags.append(_flag("planning_conflict", "high",
                               f"Parcel zoned for '{data.get('planned_use')}' but current use is "
                               f"'{data.get('current_use')}' (decision {data.get('decision_no')})",
                               "zoning"))

    # Transaction history
    if history is not None and history.get("status") == "ok":
        data = history.get("payload", {})
        if data.get("disputes"):
            score_pts += 30
            flags.append(_flag("active_dispute", "critical",
                               f"{len(data['disputes'])} active dispute(s) recorded", "transaction_history"))
        if data.get("encumbrances"):
            score_pts += 15
            for enc in data["encumbrances"]:
                flags.append(_flag(
                    "encumbrance",
                    "high",
                    f"Active {enc.get('type')} — {enc.get('lender', '')} ({enc.get('registered_at', '')})".strip(),
                    "transaction_history",
                ))
        if data.get("pending_changes"):
            score_pts += 10
            flags.append(_flag("pending_change", "warn",
                               f"{len(data['pending_changes'])} pending change(s) at VPĐKĐĐ",
                               "transaction_history"))

    score_pts = min(score_pts, 100)
    level = (
        RiskLevel.LOW if score_pts < 30
        else RiskLevel.MEDIUM if score_pts < 60
        else RiskLevel.HIGH if score_pts < 80
        else RiskLevel.CRITICAL
    )
    return score_pts, level, flags
