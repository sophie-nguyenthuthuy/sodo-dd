"""Quy hoạch (zoning / land-use plan) check.

Provider matrix:
  hanoi  -> https://quyhoach.hanoi.vn  (open data + signed API)
  hcmc   -> https://thongtinquyhoach.tphcm.gov.vn
  danang -> https://gis.danang.gov.vn
  others -> Bộ TNMT national portal
"""

from __future__ import annotations

from typing import Any

from app.services.adapters.base import AdapterResponse, BaseAdapter


class ZoningAdapter(BaseAdapter):
    name = "zoning"
    base_url = "https://quyhoach.gov.vn"

    def _live(
        self,
        *,
        parcel_number: str | None = None,
        sheet_number: str | None = None,
        province: str | None = None,
        **_: Any,
    ) -> AdapterResponse:
        if not (parcel_number and sheet_number and province):
            return self._error("parcel_number, sheet_number, province required")
        url = f"{self.base_url}/api/v1/parcel/zoning"
        try:
            resp = self._http_get(
                url,
                params={"parcel": parcel_number, "sheet": sheet_number, "province": province},
            )
            return self._ok(resp.json(), url=url)
        except Exception as exc:
            return self._error(str(exc), url=url)

    def _mock(
        self,
        *,
        parcel_number: str | None = None,
        land_use_purpose: str | None = None,
        **_: Any,
    ) -> AdapterResponse:
        # 90% of parcels match. Anything containing '7' simulates "earmarked for
        # public infrastructure", which is the most common red flag at appraisal.
        if parcel_number and "7" in parcel_number:
            return self._ok(
                {
                    "planned_use": "Đất giao thông (quy hoạch mở rộng đường)",
                    "current_use": land_use_purpose or "Đất ở đô thị",
                    "conflict": True,
                    "plan_period": "2021-2030",
                    "decision_no": "QĐ-1234/UBND",
                },
                url=f"{self.base_url}/mock",
            )
        return self._ok(
            {
                "planned_use": land_use_purpose or "Đất ở đô thị",
                "current_use": land_use_purpose or "Đất ở đô thị",
                "conflict": False,
                "plan_period": "2021-2030",
                "decision_no": "QĐ-0420/UBND",
            },
            url=f"{self.base_url}/mock",
        )
