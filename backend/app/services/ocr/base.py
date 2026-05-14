from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class OCRResult:
    text: str
    confidence: float        # 0.0 - 1.0
    engine: str
    page_count: int = 1
    extras: dict | None = None


class OcrEngine(Protocol):
    name: str

    def extract(self, image_bytes: bytes, *, mime_type: str) -> OCRResult: ...


def get_engine(name: str) -> OcrEngine:
    name = name.lower()
    if name == "tesseract":
        from app.services.ocr.tesseract import TesseractEngine

        return TesseractEngine()
    raise ValueError(f"unknown OCR engine: {name}")
