import json
from typing import Any, Dict, Optional

import httpx
from app.core.config import settings


class OllamaClient:
    def __init__(self, model: str | None = None, base_url: str | None = None):
        model = model or getattr(settings, "OLLAMA_MODEL", "llama3.1")
        base_url = base_url or getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate_json(self, prompt: str, timeout: float = 8.0) -> Optional[Dict[str, Any]]:
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "format": "json",
                    "keep_alive": "10m",
                    "options": {
                        "temperature": 0,
                        "num_predict": 256,
                    },
                },
                timeout=timeout,
            )
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "")
            return json.loads(content)
        except Exception as exc:
            print(f"Ollama unavailable or returned invalid JSON: {exc}")
            return None
