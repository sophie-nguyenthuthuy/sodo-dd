from __future__ import annotations

import io

import numpy as np
import pytesseract
from PIL import Image

from app.config import settings
from app.services.ocr.base import OCRResult


class TesseractEngine:
    name = "tesseract"

    def extract(self, image_bytes: bytes, *, mime_type: str) -> OCRResult:
        images = list(self._open_pages(image_bytes, mime_type=mime_type))
        if not images:
            return OCRResult(text="", confidence=0.0, engine=self.name, page_count=0)

        full_text: list[str] = []
        confidences: list[float] = []
        for img in images:
            img = self._preprocess(img)
            data = pytesseract.image_to_data(
                img,
                lang=settings.tesseract_lang,
                config=f"--oem 1 --psm 6 --dpi {settings.ocr_dpi}",
                output_type=pytesseract.Output.DICT,
            )
            page_text = " ".join(t for t in data.get("text", []) if t.strip())
            conf = [float(c) for c in data.get("conf", []) if c not in ("", "-1")]
            if conf:
                confidences.append(sum(conf) / len(conf) / 100.0)
            full_text.append(page_text)

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return OCRResult(
            text="\n\n".join(full_text),
            confidence=round(avg_conf, 4),
            engine=self.name,
            page_count=len(images),
        )

    # ─── helpers
    @staticmethod
    def _open_pages(blob: bytes, *, mime_type: str):
        if mime_type == "application/pdf":
            try:
                from pdf2image import convert_from_bytes

                yield from convert_from_bytes(blob, dpi=settings.ocr_dpi)
                return
            except Exception:
                return
        yield Image.open(io.BytesIO(blob))

    @staticmethod
    def _preprocess(img: Image.Image) -> Image.Image:
        # Basic adaptive thresholding via OpenCV gives a meaningful lift on
        # photographed (rather than scanned) Sổ Đỏ images.
        try:
            import cv2  # type: ignore[import-untyped]
        except ImportError:
            return img.convert("L")

        arr = np.array(img.convert("RGB"))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        gray = cv2.fastNlMeansDenoising(gray, h=10)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 11
        )
        return Image.fromarray(thresh)
