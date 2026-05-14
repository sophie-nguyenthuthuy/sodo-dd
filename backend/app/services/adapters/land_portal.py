"""Đối chiếu với Cổng dịch vụ công đất đai / Hệ thống thông tin đất đai quốc gia.

In production this uses signed B2B endpoints negotiated bilaterally with the
General Department of Land Administration (Tổng cục Quản lý đất đai) or
provincial Văn phòng Đăng ký Đất đai (VPĐKĐĐ).
"""
from __future__ import annotations

from typing import Any

from app.services.adapters.base import AdapterResponse, BaseAdapter


class LandPortalAdapter(BaseAdapter):
    name = "land_portal"
    base_url = "https://dichvucong.gov.vn"

    def _live(
        self,
        *,
        serial_number: str | None = None,
        book_number: str | None = None,
        parcel_number: str | None = None,
        sheet_number: str | None = None,
        province: str | None = None,
        **_: Any,
    ) -> AdapterResponse:
        if not (serial_number or book_number or (parcel_number and sheet_number)):
            return self._error("insufficient identifiers")
        url = f"{self.base_url}/api/land-certificates/lookup"
        try:
            resp = self._http_get(
                url,
                params={
                    "serial": serial_number,
                    "book": book_number,
                    "parcel": parcel_number,
                    "sheet": sheet_number,
                    "province": province,
                },
            )
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return self._error(str(exc), url=url)
        if not data.get("found"):
            return self._no_data(url=url)
        return self._ok(data, url=url)

    def _mock(
        self,
        *,
        serial_number: str | None = None,
        owner_name: str | None = None,
        parcel_number: str | None = None,
        sheet_number: str | None = None,
        area_sqm: float | None = None,
        **_: Any,
    ) -> AdapterResponse:
        # Deterministic mock: anything ending in "0000" simulates "not found",
        # ending in "9999" simulates "owner mismatch", else "match".
        suffix = (serial_number or "")[-4:]
        if suffix == "0000":
            return self._no_data(url=f"{self.base_url}/mock")
        if suffix == "9999":
            return self._ok(
                {
                    "found": True,
                    "match": "partial",
                    "registered_owner": "TRẦN VĂN B",
                    "input_owner": owner_name,
                    "parcel_number": parcel_number,
                    "sheet_number": sheet_number,
                    "area_sqm": area_sqm,
                    "encumbrances": [],
                    "status": "active",
                },
                url=f"{self.base_url}/mock",
            )
        return self._ok(
            {
                "found": True,
                "match": "full",
                "registered_owner": owner_name,
                "parcel_number": parcel_number,
                "sheet_number": sheet_number,
                "area_sqm": area_sqm,
                "encumbrances": [],
                "status": "active",
            },
            url=f"{self.base_url}/mock",
        )
