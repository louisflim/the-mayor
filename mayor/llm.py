"""Thin LLM client. Gemini, Groq and OpenAI all speak the OpenAI chat API,
so one client with a different base URL covers all three."""

from dataclasses import dataclass

PROVIDERS = {
    "Gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "secret": "GEMINI_API_KEY",
        "models": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"],
    },
    "Groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "secret": "GROQ_API_KEY",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    },
    "OpenAI": {
        "base_url": None,
        "secret": "OPENAI_API_KEY",
        "models": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-5-mini"],
    },
    "Claude": {
        "base_url": "https://api.anthropic.com/v1/",
        "secret": "ANTHROPIC_API_KEY",
        "models": ["claude-haiku-5-5", "claude-sonnet-5-5"],
    },
    # Any other OpenAI-compatible endpoint (e.g. a key from your teacher):
    # set LLM_API_KEY, LLM_BASE_URL and LLM_MODEL in secrets.
    "Custom": {
        "base_url": None,          # read from LLM_BASE_URL
        "secret": "LLM_API_KEY",
        "models": [],              # read from LLM_MODEL
    },
}


class LLMError(RuntimeError):
    pass


@dataclass
class LLMClient:
    provider: str
    api_key: str
    model: str
    temperature: float = 0.8
    base_url: str | None = None   # overrides the provider's URL (used by "Custom")

    def __post_init__(self):
        from openai import OpenAI  # imported lazily so offline mode needs no API package

        base_url = self.base_url or PROVIDERS[self.provider]["base_url"]
        self._client = OpenAI(api_key=self.api_key, base_url=base_url, timeout=60, max_retries=2)

    def chat(self, system: str, messages: list[dict], *, temperature: float | None = None,
             max_tokens: int = 400) -> str:
        params = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": max_tokens,
        }
        # Newer reasoning models reject max_tokens and custom temperatures. Adapt and retry
        # instead of failing, so any model the class is given just works.
        for _ in range(3):
            try:
                resp = self._client.chat.completions.create(**params)
                break
            except Exception as e:  # network, auth, quota, unsupported parameter
                msg = str(e)
                if "max_tokens" in msg and "max_tokens" in params:
                    params["max_completion_tokens"] = max(2000, params.pop("max_tokens"))
                elif "temperature" in msg and "temperature" in params:
                    params.pop("temperature")
                else:
                    raise LLMError(f"{self.provider} call failed: {e}") from e
        else:
            raise LLMError(f"{self.provider} call failed after adjusting parameters")
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise LLMError(f"{self.provider} returned an empty reply")
        return text
