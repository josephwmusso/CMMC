"""
src/agents/llm_client.py

Unified LLM interface — works with Claude API (dev) or vLLM/OpenAI-compatible (prod).
Swap with one config change in configs/settings.py.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ComplianceLLM:
    """Unified LLM interface for CMMC platform.

    Usage:
        # Dev (Claude API):
        llm = ComplianceLLM(provider="anthropic", api_key="sk-...", model="claude-sonnet-4-20250514")

        # Prod (vLLM):
        llm = ComplianceLLM(provider="openai_compatible", base_url="http://localhost:8000/v1",
                            model="meta-llama/Llama-3.3-70B-Instruct")
    """

    def __init__(
        self,
        provider: str = "anthropic",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.provider = provider
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self.model = model or "claude-sonnet-4-20250514"
        elif provider == "openai_compatible":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key or "not-needed",
                base_url=base_url or "http://localhost:8000/v1",
            )
            self.model = model or "meta-llama/Llama-3.3-70B-Instruct"
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'anthropic' or 'openai_compatible'.")

        logger.info(f"LLM initialized: provider={provider}, model={self.model}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """Generate a completion with retry logic.

        Args:
            system_prompt: System-level instructions.
            user_prompt: The user message / task.
            max_tokens: Max tokens in response.
            temperature: 0.0-1.0, lower = more deterministic.

        Returns:
            The generated text.
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if self.provider == "anthropic":
                    return self._call_anthropic(system_prompt, user_prompt, max_tokens, temperature)
                else:
                    return self._call_openai(system_prompt, user_prompt, max_tokens, temperature)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = self.retry_delay * attempt
                    logger.warning(f"LLM call failed (attempt {attempt}/{self.max_retries}): {e}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"LLM call failed after {self.max_retries} attempts: {e}")

        raise RuntimeError(f"LLM generation failed after {self.max_retries} attempts: {last_error}")

    def _call_anthropic(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    def _call_openai(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content


def get_llm() -> ComplianceLLM:
    """Factory: build a ComplianceLLM from configs/settings.py values."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from configs.settings import LLM_PROVIDER, LLM_API_KEY, LLM_MODEL

    kwargs = {"provider": LLM_PROVIDER, "api_key": LLM_API_KEY, "model": LLM_MODEL}

    # Only pass base_url for openai_compatible
    if LLM_PROVIDER == "openai_compatible":
        from configs.settings import LLM_BASE_URL
        kwargs["base_url"] = LLM_BASE_URL

    return ComplianceLLM(**kwargs)
