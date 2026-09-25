"""
Smart LLM Manager - ReqCraft AI
====================================
Provides a unified `generate()` interface with an automatic fallback chain:

    1. Google Gemini      (PRIMARY)   - free tier, fast
    2. HuggingFace        (FALLBACK)  - used when Gemini fails / quota reached
    3. Ollama (local)     (BACKUP)    - final offline backup

If a provider fails (quota exhausted, network error, missing key) the manager
automatically moves to the next provider so the app keeps working.
"""
import time
import logging
import requests

from google import genai
from google.genai import types

from config import Config

logger = logging.getLogger(__name__)


class LLMResult:
    """Container for a generation result + which provider produced it."""

    def __init__(self, text: str, provider: str, success: bool = True, error: str = ""):
        self.text = text
        self.provider = provider
        self.success = success
        self.error = error

    def to_dict(self):
        return {
            "text": self.text,
            "provider": self.provider,
            "success": self.success,
            "error": self.error,
        }


class SmartLLMManager:
    """Multi-provider LLM manager with automatic fallback + simple caching."""

    def __init__(self):
        self._cache = {}                # prompt-hash -> LLMResult  (basic cost saver)
        self._gemini_client = None
        self._init_gemini()

    # ------------------------------------------------------------------ setup
    def _init_gemini(self):
        if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your-gemini-api-key-here":
            try:
                self._gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
                logger.info("Gemini configured (model=%s)", Config.GEMINI_MODEL)
            except Exception as e:  # noqa: BLE001
                logger.warning("Gemini init failed: %s", e)
        else:
            logger.warning("GEMINI_API_KEY not set - Gemini disabled")

    # --------------------------------------------------------------- providers
    def _call_gemini(self, prompt: str, temperature: float) -> LLMResult:
        if not self._gemini_client:
            return LLMResult("", "gemini", False, "Gemini not configured")
        try:
            resp = self._gemini_client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature),
            )
            text = (resp.text or "").strip()
            if not text:
                return LLMResult("", "gemini", False, "Empty response")
            return LLMResult(text, "gemini")
        except Exception as e:  # noqa: BLE001
            logger.warning("Gemini call failed: %s", e)
            return LLMResult("", "gemini", False, str(e))

    def _call_huggingface(self, prompt: str, temperature: float) -> LLMResult:
        key = Config.HUGGINGFACE_API_KEY
        if not key or key == "your-huggingface-token-here":
            return LLMResult("", "huggingface", False, "HF token not configured")
        try:
            # OpenAI-compatible router endpoint (stable for instruct/chat models)
            url = "https://router.huggingface.co/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {
                "model": Config.HUGGINGFACE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 2048,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=90)
            if r.status_code != 200:
                return LLMResult("", "huggingface", False, f"HTTP {r.status_code}: {r.text[:200]}")
            data = r.json()
            text = data["choices"][0]["message"]["content"].strip()
            return LLMResult(text, "huggingface") if text else LLMResult(
                "", "huggingface", False, "Empty response"
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("HuggingFace call failed: %s", e)
            return LLMResult("", "huggingface", False, str(e))

    def _call_ollama(self, prompt: str, temperature: float) -> LLMResult:
        try:
            url = f"{Config.OLLAMA_BASE_URL}/api/generate"
            payload = {
                "model": Config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            }
            r = requests.post(url, json=payload, timeout=120)
            if r.status_code != 200:
                return LLMResult("", "ollama", False, f"HTTP {r.status_code}")
            text = r.json().get("response", "").strip()
            return LLMResult(text, "ollama") if text else LLMResult(
                "", "ollama", False, "Empty response"
            )
        except Exception as e:  # noqa: BLE001
            logger.info("Ollama not available: %s", e)
            return LLMResult("", "ollama", False, str(e))

    # ------------------------------------------------------------------- public
    def generate(self, prompt: str, temperature: float = 0.4, use_cache: bool = True) -> LLMResult:
        """Run the fallback chain and return the first successful result."""
        cache_key = (hash(prompt), round(temperature, 2))
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            return LLMResult(cached.text, cached.provider + " (cached)", True)

        chain = [self._call_gemini, self._call_huggingface, self._call_ollama]
        last_error = ""
        for provider_call in chain:
            result = provider_call(prompt, temperature)
            if result.success:
                if use_cache:
                    self._cache[cache_key] = result
                logger.info("Generated via %s", result.provider)
                return result
            last_error = f"{result.provider}: {result.error}"
            time.sleep(0.2)  # tiny backoff before next provider

        return LLMResult(
            "", "none", False,
            f"All providers failed. Last error -> {last_error}",
        )

    def provider_status(self) -> dict:
        """Lightweight status for the dashboard (no API calls)."""
        hf = bool(Config.HUGGINGFACE_API_KEY) and \
            Config.HUGGINGFACE_API_KEY != "your-huggingface-token-here"
        return {
            "gemini": self._gemini_client is not None,
            "huggingface": hf,
            "ollama": True,  # assumed reachable if running locally; checked at call time
        }


# Singleton used across the app
llm_manager = SmartLLMManager()
