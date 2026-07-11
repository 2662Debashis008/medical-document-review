import base64
import io
import time
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, UnidentifiedImageError

from config.settings import settings


class MedGemmaProvider:
    MAX_IMAGE_BYTES = 1_500_000
    MAX_IMAGE_SIDE = 1600

    def __init__(self):
        self.api_url = settings.MEDGEMMA_API_URL
        self.api_key = settings.MEDGEMMA_API_KEY
        self.model_name = settings.MODEL_NAME
        self.timeout = 90

    def _build_payload(self, prompt: str, input_paths: list[str], text_content: str | None):
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

        if text_content:
            content.append({"type": "text", "text": text_content})

        for input_path in input_paths:
            path = Path(input_path)
            if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                image_bytes, mime_type = self._image_payload(path)
                encoded = base64.b64encode(image_bytes).decode("ascii")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
                })

        return {
            "model": self.model_name,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
        }

    def infer(
        self,
        prompt: str,
        input_paths: list[str],
        text_content: str | None = None,
        max_retries: int = 2,
    ) -> tuple[str, dict[str, Any]]:
        payload = self._build_payload(prompt, input_paths, text_content)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        started = time.perf_counter()
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(self.api_url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    latency = time.perf_counter() - started
                    return self._extract_text(data), {
                        "latency": latency,
                        "model": data.get("model", self.model_name),
                        "attempts": attempt + 1,
                    }
            except Exception as exc:
                last_error = exc
                if attempt == max_retries:
                    break
                time.sleep(0.75 * (attempt + 1))

        raise RuntimeError(f"MedGemma request failed: {last_error}")

    @staticmethod
    def _mime_type(path: Path) -> str:
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            return "image/jpeg"
        return "image/png"

    @classmethod
    def _image_payload(cls, path: Path) -> tuple[bytes, str]:
        image_bytes = path.read_bytes()
        if len(image_bytes) <= cls.MAX_IMAGE_BYTES and path.suffix.lower() in {".jpg", ".jpeg"}:
            return image_bytes, "image/jpeg"

        try:
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((cls.MAX_IMAGE_SIDE, cls.MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
                quality = 82
                while True:
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=quality, optimize=True)
                    compressed = buffer.getvalue()
                    if len(compressed) <= cls.MAX_IMAGE_BYTES or quality <= 52:
                        return compressed, "image/jpeg"
                    quality -= 10
        except (UnidentifiedImageError, OSError):
            return image_bytes, cls._mime_type(path)

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(
                    item.get("text", "") for item in content if isinstance(item, dict)
                )
        return data.get("output_text") or data.get("text") or str(data)
