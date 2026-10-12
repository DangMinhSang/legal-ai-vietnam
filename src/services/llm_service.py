"""
LLM Service module for Legal AI Vietnam.

Provides unified LiteLLM client with automatic retry (tenacity), model fallback
(Claude 3.5 Sonnet -> GPT-4o-mini), structured JSON output enforcement, token usage
and cost tracking, and legal entity extraction.
"""

from __future__ import annotations

import json
import os
from typing import Any

import litellm
import regex
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

# Avoid parameter incompatibility warnings across model providers
litellm.drop_params = True


def _log_retry_attempt(retry_state: Any) -> None:
    """Log retry attempt information using loguru."""
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception() if retry_state.outcome else "Unknown error"
    logger.warning(
        f"LLM call failed (attempt {attempt}/3): {exc}. Retrying with exponential backoff..."
    )


class LLMService:
    """Production-ready LLM service with retry, fallback, and structured outputs."""

    def __init__(
        self,
        primary_model: str = "claude-3-5-sonnet-20241022",
        fallback_model: str = "gpt-4o-mini",
        max_tokens: int = 4096,
        timeout: int = 60,
        settings: Any | None = None,
    ) -> None:
        """Initialize LLM service with primary model, fallback model, and timeout.

        Args:
            primary_model: Default model identifier (LiteLLM format).
            fallback_model: Secondary model identifier if primary fails.
            max_tokens: Maximum tokens allowed in response.
            timeout: Timeout in seconds per API request (default 60s).
            settings: Optional application settings instance.
        """
        if settings is not None and hasattr(settings, "llm"):
            llm_cfg = settings.llm
            self.primary_model = getattr(llm_cfg, "llm_primary_model", primary_model)
            self.fallback_model = getattr(llm_cfg, "llm_fallback_model", fallback_model)
            self.max_tokens = getattr(llm_cfg, "llm_max_tokens", max_tokens)
            anthropic_key = getattr(llm_cfg, "anthropic_api_key", None)
            if anthropic_key and not os.environ.get("ANTHROPIC_API_KEY"):
                os.environ["ANTHROPIC_API_KEY"] = str(anthropic_key)
            openai_key = getattr(llm_cfg, "openai_api_key", None)
            if openai_key and not os.environ.get("OPENAI_API_KEY"):
                os.environ["OPENAI_API_KEY"] = str(openai_key)
        else:
            self.primary_model = primary_model
            self.fallback_model = fallback_model
            self.max_tokens = max_tokens

        self.timeout = timeout
        logger.info(
            f"LLMService initialized. Primary: '{self.primary_model}', "
            f"Fallback: '{self.fallback_model}', Timeout: {self.timeout}s"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=_log_retry_attempt,
        reraise=True,
    )
    def _call_model(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> Any:
        """Call litellm completion with retry logic.

        Args:
            model: LiteLLM model string.
            messages: Formatted chat messages list.
            temperature: Sampling temperature.

        Returns:
            LiteLLM completion response object.
        """
        logger.debug(f"Sending completion request to {model} (timeout={self.timeout}s)...")
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
        )
        return response

    def _log_usage_and_cost(self, response: Any, model: str) -> None:
        """Log token usage and estimated cost for a completion response."""
        usage = getattr(response, "usage", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)
            total_tokens = getattr(usage, "total_tokens", 0)
            logger.info(
                f"[{model}] Token usage - Prompt: {prompt_tokens}, "
                f"Completion: {completion_tokens}, Total: {total_tokens}"
            )
        else:
            logger.info(f"[{model}] Token usage information not available in response.")

        try:
            cost = litellm.completion_cost(completion_response=response)
            if cost is not None:
                logger.info(f"[{model}] Estimated cost: ${cost:.6f}")
        except Exception as cost_err:
            logger.debug(f"[{model}] Estimated cost could not be calculated: {cost_err}")

    def _completion_with_fallback(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> Any:
        """Execute request against primary model; fallback to secondary on failure.

        Args:
            messages: List of chat messages.
            temperature: Sampling temperature.

        Returns:
            LiteLLM completion response.
        """
        try:
            logger.debug(f"Executing request with primary model: {self.primary_model}")
            response = self._call_model(
                model=self.primary_model,
                messages=messages,
                temperature=temperature,
            )
            self._log_usage_and_cost(response, self.primary_model)
            return response
        except Exception as exc:
            logger.warning(
                f"Primary model '{self.primary_model}' failed after retries: {exc}. "
                f"Switching to fallback model '{self.fallback_model}'..."
            )
            try:
                response = self._call_model(
                    model=self.fallback_model,
                    messages=messages,
                    temperature=temperature,
                )
                self._log_usage_and_cost(response, self.fallback_model)
                return response
            except Exception as fallback_exc:
                logger.error(
                    f"Fallback model '{self.fallback_model}' also failed: {fallback_exc}"
                )
                raise fallback_exc

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.1,
    ) -> str:
        """Generate a text completion for the given prompt.

        Args:
            prompt: User prompt text.
            system: Optional system prompt text.
            temperature: Sampling temperature (default 0.1).

        Returns:
            LLM response text content.
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._completion_with_fallback(
            messages=messages,
            temperature=temperature,
        )
        text = response.choices[0].message.content
        return text if text is not None else ""

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Parse JSON from LLM response handling code fences and malformed syntax.

        Args:
            text: Raw text string from LLM response.

        Returns:
            Parsed dictionary or empty dictionary on unrecoverable parse failure.
        """
        if not text or not text.strip():
            logger.warning("Empty response received when parsing JSON.")
            return {}

        cleaned = text.strip()

        # 1. Direct parse attempt
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {"items": data}
            return {"result": data}
        except json.JSONDecodeError:
            pass

        # 2. Extract from markdown code fence (```json ... ``` or ``` ... ```)
        json_fence_match = regex.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if json_fence_match:
            fence_content = json_fence_match.group(1).strip()
            try:
                data = json.loads(fence_content)
                if isinstance(data, dict):
                    return data
                if isinstance(data, list):
                    return {"items": data}
                return {"result": data}
            except json.JSONDecodeError:
                pass

        # 3. Extract outermost curly braces {...}
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = cleaned[first_brace : last_brace + 1]
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass

        logger.error(
            f"Failed to parse JSON response gracefully. Response snippet: {cleaned[:200]}..."
        )
        return {"error": "Failed to parse JSON response", "raw_content": cleaned}

    def complete_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        system: str | None = None,
    ) -> dict[str, Any]:
        """Generate a structured response adhering to a JSON schema.

        Uses prompt engineering to enforce JSON compliance:
        - System: "Always respond with valid JSON matching the schema provided."
        - User: f"Schema: {json.dumps(schema)}\\n\\nTask: {prompt}"

        Args:
            prompt: User task prompt.
            response_schema: Dict describing expected output structure.
            system: Optional additional system instructions.

        Returns:
            Parsed JSON output as a dictionary.
        """
        base_system = "Always respond with valid JSON matching the schema provided."
        system_instruction = f"{system}\n{base_system}" if system else base_system

        schema_json = json.dumps(response_schema, ensure_ascii=False, indent=2)
        user_prompt = f"Schema: {schema_json}\n\nTask: {prompt}"

        text = self.complete(
            prompt=user_prompt,
            system=system_instruction,
            temperature=0.1,
        )
        return self._parse_json_response(text)

    def extract_entities(
        self,
        text: str,
        entity_types: list[str],
    ) -> dict[str, list[str]]:
        """Extract specified legal entity types from Vietnamese text.

        Args:
            text: Input Vietnamese legal text.
            entity_types: List of entity types to extract (e.g. ['court', 'crime', 'statute']).

        Returns:
            Dictionary mapping each entity_type to a list of found entity strings.
        """
        if not text or not entity_types:
            return {etype: [] for etype in entity_types}

        schema = {etype: ["string"] for etype in entity_types}
        types_str = ", ".join(entity_types)

        prompt = (
            f"Trích xuất tất cả thực thể thuộc các loại sau từ văn bản pháp lý tiếng Việt:\n"
            f"Danh sách loại thực thể cần trích xuất: {types_str}.\n\n"
            f"Văn bản:\n\"\"\"\n{text}\n\"\"\"\n\n"
            f"Hướng dẫn:\n"
            f"- Trả về đối tượng JSON với mỗi khóa là một loại thực thể trong danh sách trên.\n"
            f"- Giá trị là danh sách chuỗi các thực thể tương ứng tìm thấy trong văn bản.\n"
            f"- Nếu không có thực thể nào cho một loại, giá trị phải là danh sách rỗng []."
        )

        system = (
            "Bạn là chuyên gia trích xuất thực thể pháp lý tiếng Việt (Vietnamese Legal NER). "
            "Trích xuất chính xác, trung thực theo nội dung văn bản."
        )

        raw_result = self.complete_structured(
            prompt=prompt,
            response_schema=schema,
            system=system,
        )

        extracted: dict[str, list[str]] = {}
        for etype in entity_types:
            val = raw_result.get(etype)
            if isinstance(val, list):
                extracted[etype] = [
                    str(item).strip()
                    for item in val
                    if item is not None and str(item).strip()
                ]
            elif isinstance(val, str) and val.strip():
                extracted[etype] = [val.strip()]
            else:
                extracted[etype] = []

        return extracted

    async def ping(self) -> bool:
        """Check whether the LLM service can respond."""
        try:
            res = self.complete(prompt="ping", temperature=0.0)
            return bool(res)
        except Exception:
            return False

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Async convenience alias for complete."""
        temp = kwargs.get("temperature", 0.1)
        sys = kwargs.get("system", None)
        return self.complete(prompt=prompt, system=sys, temperature=temp)
