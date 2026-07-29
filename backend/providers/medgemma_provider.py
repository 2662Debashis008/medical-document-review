import base64
import io
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from PIL import Image, UnidentifiedImageError

from config.settings import settings


class MedGemmaConfigurationError(RuntimeError):
    """Raised when the configured inference endpoint cannot be used."""


class MedGemmaProvider:
    MAX_IMAGE_BYTES = 1_500_000
    # Vision inference is the dominant cost on a local 4B model. Limiting the
    # longest edge retains document layout while avoiding oversized image tokens.
    MAX_IMAGE_SIDE = 512

    def __init__(self):
        self.api_url = settings.MEDGEMMA_API_URL
        self.model_name = settings.MODEL_NAME
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=settings.MEDGEMMA_READ_TIMEOUT_SECONDS,
            write=30.0,
            pool=10.0,
        )
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        parsed = urlparse(self.api_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise MedGemmaConfigurationError(
                "MEDGEMMA_API_URL must be a full HTTP(S) URL, for example "
                "http://localhost:11434/v1/chat/completions."
            )
        if parsed.scheme == "https" and parsed.hostname in {"localhost", "127.0.0.1"} and parsed.port == 11434:
            raise MedGemmaConfigurationError(
                "Ollama on port 11434 uses HTTP, not HTTPS. Set MEDGEMMA_API_URL to "
                "http://localhost:11434/v1/chat/completions."
            )
        if not self.model_name.strip():
            raise MedGemmaConfigurationError("MODEL_NAME must not be empty.")

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
            # A bounded response keeps local inference predictable while leaving
            # enough room for the structured extraction schemas.
            "max_tokens": settings.MEDGEMMA_MAX_TOKENS,
            "keep_alive": "1h",
            "options": {
                "num_thread": 6,
                "num_ctx": 4096,
            },
        }

    def infer(
        self,
        prompt: str,
        input_paths: list[str],
        text_content: str | None = None,
        max_retries: int = 2,
    ) -> tuple[str, dict[str, Any]]:
        payload = self._build_payload(prompt, input_paths, text_content)
        headers = {"Content-Type": "application/json"}

        started = time.perf_counter()
        last_error: Exception | None = None
        attempts_made = 0

        # Keep one connection for all retry attempts. This avoids repeated TCP/TLS
        # handshakes, which is particularly noticeable while processing PDF pages.
        with httpx.Client(timeout=self.timeout) as client:
            for attempt in range(max_retries + 1):
                attempts_made = attempt + 1
                try:
                    response = client.post(self.api_url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    if not isinstance(data, dict):
                        raise RuntimeError("MedGemma returned a non-object JSON response.")
                    latency = time.perf_counter() - started
                    return self._extract_text(data), {
                        "latency": latency,
                        "model": data.get("model", self.model_name),
                        "attempts": attempt + 1,
                    }
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    # Retrying client-side validation errors only adds delay. Server
                    # failures and rate limits can be transient, so retry those.
                    if exc.response.status_code < 500 and exc.response.status_code != 429:
                        break
                except httpx.TimeoutException as exc:
                    # A completed request that exceeded its deadline will not become
                    # faster by being immediately submitted again.
                    last_error = exc
                    break
                except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                    last_error = exc
                if attempt == max_retries:
                    break
                time.sleep(0.5 * (attempt + 1))

        raise RuntimeError(
            f"MedGemma request failed after {attempts_made} attempt(s): {last_error}"
        )

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
