"""Lịch sử giao dịch — transfers, mortgages, disputes from VPĐKĐĐ.

Production: per-province VPĐKĐĐ APIs (signed). Mock returns plausible records.
"""

from __future__ import annotations

from typing import Any

from app.services.adapters.base import AdapterResponse, BaseAdapter


class TransactionHistoryAdapter(BaseAdapter):
    name = "transaction_history"
    base_url = "https://vpdkdd.gov.vn"

    def _live(
        self,
        *,
        serial_number: str | None = None,
        parcel_number: str | None = None,
        sheet_number: str | None = None,
        province: str | None = None,
        **_: Any,
    ) -> AdapterResponse:
        url = f"{self.base_url}/api/v1/transactions"
        try:
            resp = self._http_get(
                url,
                params={
                    "serial": serial_number,
                    "parcel": parcel_number,
                    "sheet": sheet_number,
                    "province": province,
                },
            )
            return self._ok(resp.json(), url=url)
        except Exception as exc:
            return self._error(str(exc), url=url)

    def _mock(
        self,
        *,
        serial_number: str | None = None,
        **_: Any,
    ) -> AdapterResponse:
        # '8' anywhere in serial → active mortgage at a bank
        # '6' anywhere → dispute flag
        has_mortgage = "8" in (serial_number or "")
        has_dispute = "6" in (serial_number or "")
        transfers = [
            {"date": "2019-03-12", "type": "transfer", "from": "Nguyễn Văn A", "to": "Trần Thị B"},
        ]
        encumbrances: list[dict] = []
        if has_mortgage:
            encumbrances.append(
                {"type": "mortgage", "lender": "Ngân hàng XYZ", "registered_at": "2023-09-04"}
            )
        disputes: list[dict] = []
        if has_dispute:
            disputes.append({"type": "boundary", "filed_at": "2024-07-19", "status": "pending"})

        return self._ok(
            {
                "transfers": transfers,
                "encumbrances": encumbrances,
                "disputes": disputes,
                "pending_changes": [],
            },
            url=f"{self.base_url}/mock",
        )
