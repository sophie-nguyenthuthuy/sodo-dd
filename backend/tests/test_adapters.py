from app.services.adapters import (
    LandPortalAdapter,
    TransactionHistoryAdapter,
    ZoningAdapter,
)


def test_land_portal_mock_match():
    a = LandPortalAdapter(mode="mock")
    r = a.query(serial_number="BU837192", owner_name="NGUYỄN VĂN A",
                parcel_number="142", sheet_number="27", area_sqm=78.5)
    assert r.status == "ok"
    assert r.payload["match"] == "full"
    assert r.response_hash != ""


def test_land_portal_mock_not_found():
    a = LandPortalAdapter(mode="mock")
    r = a.query(serial_number="XX000000")  # ends with 0000
    assert r.status == "no_data"


def test_land_portal_mock_owner_mismatch():
    a = LandPortalAdapter(mode="mock")
    r = a.query(serial_number="ZZ009999", owner_name="A")
    assert r.payload["match"] == "partial"


def test_zoning_mock_conflict():
    a = ZoningAdapter(mode="mock")
    r = a.query(parcel_number="71")
    assert r.payload["conflict"] is True
    r2 = a.query(parcel_number="42")
    assert r2.payload["conflict"] is False


def test_history_mock_mortgage_and_dispute():
    a = TransactionHistoryAdapter(mode="mock")
    r = a.query(serial_number="AA868686")
    assert any(e["type"] == "mortgage" for e in r.payload["encumbrances"])
    assert r.payload["disputes"]
