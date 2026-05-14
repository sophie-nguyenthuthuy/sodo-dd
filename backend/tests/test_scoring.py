from app.models.report import RiskLevel
from app.services.scoring import score


def _parsed(**overrides):
    base = {
        "serial_number": "BU837192",
        "parcel_number": "142",
        "sheet_number": "27",
    }
    base.update(overrides)
    return base


def test_low_risk():
    s, level, _flags = score(
        parsed=_parsed(),
        ocr_confidence=0.92,
        portal={"status": "ok", "payload": {"match": "full", "status": "active"}},
        zoning={"status": "ok", "payload": {"conflict": False}},
        history={"status": "ok", "payload": {"transfers": [], "encumbrances": [], "disputes": []}},
    )
    assert level == RiskLevel.LOW
    assert s < 30


def test_critical_when_portal_missing():
    s, level, _ = score(
        parsed=_parsed(),
        ocr_confidence=0.4,
        portal={"status": "no_data"},
        zoning=None,
        history=None,
    )
    assert level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert s >= 60


def test_owner_mismatch_raises_flag():
    _, _, flags = score(
        parsed=_parsed(),
        ocr_confidence=0.9,
        portal={
            "status": "ok",
            "payload": {
                "match": "partial",
                "registered_owner": "B",
                "input_owner": "A",
                "status": "active",
            },
        },
        zoning=None,
        history=None,
    )
    assert any(f["code"] == "owner_mismatch" for f in flags)


def test_dispute_flag():
    _, _, flags = score(
        parsed=_parsed(),
        ocr_confidence=0.9,
        portal=None,
        zoning=None,
        history={
            "status": "ok",
            "payload": {"transfers": [], "encumbrances": [], "disputes": [{"type": "boundary"}]},
        },
    )
    assert any(f["code"] == "active_dispute" for f in flags)
