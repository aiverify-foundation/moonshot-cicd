"""Web search for custom API prompts via Hugging Face Smolagents and SerpApi.

The benchmark model stays the caller-supplied HTTP completion. Smolagents'
``ToolCallingAgent`` decides when to call SerpApi, then returns a final answer.
The SerpApi token is read from the ``SERPAPI_API_KEY`` environment variable.
"""

from __future__ import annotations

import os
from typing import Any, Callable

from domain.services.logger import configure_logger

logger = configure_logger(__name__)

SERPAPI_API_KEY_ENV = "SERPAPI_API_KEY"
MAX_AGENT_STEPS = 6
WEB_SEARCH_INSTRUCTIONS = (
    "The task is an evaluation prompt. Use web_search when answering it "
    "requires information from the web. Put only the answer to the prompt "
    "in the final_answer tool."
)
ERROR_MISSING_SERPAPI_KEY = "Web search requires the {env_name} environment variable."
ERROR_SMOLAGENTS_MISSING = (
    "Web search requires the smolagents package. Install moonshot_core "
    "dependencies and try again."
)
ERROR_EMPTY_AGENT_ANSWER = "The web search agent did not return an answer."
REDACTED_SECRET = "***REDACTED***"
LOG_ORIGINAL_PROMPT = "[CustomApiWebSearch] Original prompt: {prompt}"
LOG_TOOL_CALLED = "[CustomApiWebSearch] Step {step}/{max_steps} Tool called: {called}"
LOG_QUERY = "[CustomApiWebSearch] Step {step}/{max_steps} web_search query: {query}"
LOG_OBSERVATION = (
    "[CustomApiWebSearch] Step {step}/{max_steps} Observation: {observation}"
)
LOG_FINAL_RESPONSE = (
    "[CustomApiWebSearch] Step {step}/{max_steps} Final model response: {response}"
)


def render_agent_messages(messages: list[Any]) -> str:
    """Flatten Smolagents chat messages into one prompt string.

    Custom API bodies only carry a single ``{{prompt}}`` placeholder, so the
    agent conversation is sent as plain text.
    """
    rendered = [_render_message(message) for message in messages]
    return "\n\n".join(part for part in rendered if part)


def truncate_at_stop_sequences(text: str, stop_sequences: list[str] | None) -> str:
    """Drop text at the first configured stop sequence, matching Model.generate."""
    if not text or not stop_sequences:
        return text
    cut = len(text)
    for stop in stop_sequences:
        if not stop:
            continue
        index = text.find(stop)
        if index != -1:
            cut = min(cut, index)
    return text[:cut]


def run_custom_api_web_search(task: str, complete: Callable[[str], str]) -> str:
    """Run a Smolagents tool-calling loop with SerpApi web search.

    ``complete`` performs one synchronous custom-API completion and returns the
    model text. It is invoked once per agent step.
    """
    if not (os.getenv(SERPAPI_API_KEY_ENV) or "").strip():
        raise ValueError(ERROR_MISSING_SERPAPI_KEY.format(env_name=SERPAPI_API_KEY_ENV))

    logger.info(LOG_ORIGINAL_PROMPT.format(prompt=_redact_serpapi_key(task)))

    try:
        from smolagents import GoogleSearchTool, LogLevel, ToolCallingAgent
    except ImportError as exc:
        raise RuntimeError(ERROR_SMOLAGENTS_MISSING) from exc

    search_called = False

    class SerpApiSearchTool(GoogleSearchTool):
        """SerpApi search that never returns the API token to the model."""

        def forward(self, query: str, filter_year: int | None = None) -> str:
            nonlocal search_called
            search_called = True
            query_text = (
                query if filter_year is None else f"{query} (year={filter_year})"
            )
            step = _agent_step_number(agent)
            logger.info(
                LOG_TOOL_CALLED.format(
                    step=step, max_steps=MAX_AGENT_STEPS, called="true"
                )
            )
            logger.info(
                LOG_QUERY.format(
                    step=step,
                    max_steps=MAX_AGENT_STEPS,
                    query=_redact_serpapi_key(query_text),
                )
            )
            try:
                result = super().forward(query=query, filter_year=filter_year)
            except Exception as exc:
                redacted = _redact_serpapi_key(str(exc))
                logger.info(
                    LOG_OBSERVATION.format(
                        step=step, max_steps=MAX_AGENT_STEPS, observation=redacted
                    )
                )
                raise RuntimeError(redacted) from None
            result = _redact_serpapi_key(result)
            logger.info(
                LOG_OBSERVATION.format(
                    step=step, max_steps=MAX_AGENT_STEPS, observation=result
                )
            )
            return result

    agent = ToolCallingAgent(
        tools=[SerpApiSearchTool(provider="serpapi")],
        model=_build_agent_model(complete),
        instructions=WEB_SEARCH_INSTRUCTIONS,
        max_steps=MAX_AGENT_STEPS,
        add_base_tools=False,
        verbosity_level=LogLevel.ERROR,
    )
    answer_text: str | None = None
    try:
        try:
            answer = agent.run(task)
        except Exception as exc:
            redacted = _redact_serpapi_key(str(exc))
            if redacted != str(exc):
                raise RuntimeError(redacted) from None
            raise
        if answer is None:
            raise ValueError(ERROR_EMPTY_AGENT_ANSWER)
        if not isinstance(answer, str):
            answer = str(answer)
        answer_text = _redact_serpapi_key(answer)
        return answer_text
    finally:
        _log_web_search_trace(agent, search_called, answer_text)


def _build_agent_model(complete: Callable[[str], str]):
    try:
        from smolagents import ChatMessage, MessageRole, Model
    except ImportError as exc:
        raise RuntimeError(ERROR_SMOLAGENTS_MISSING) from exc

    class CustomApiAgentModel(Model):
        def __init__(self) -> None:
            super().__init__()
            self._complete = complete

        def generate(
            self,
            messages,
            stop_sequences=None,
            response_format=None,
            tools_to_call_from=None,
            **kwargs,
        ):
            text = self._complete(render_agent_messages(messages))
            if not isinstance(text, str):
                text = "" if text is None else str(text)
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content=truncate_at_stop_sequences(text, stop_sequences),
            )

    return CustomApiAgentModel()


def _agent_step_number(agent: Any) -> int:
    """1-based Smolagents step in progress, within ``MAX_AGENT_STEPS``."""
    step = getattr(agent, "step_number", None)
    if isinstance(step, int) and step >= 1:
        return min(step, MAX_AGENT_STEPS)
    return 1


def _final_step_number(agent: Any) -> int:
    """Step that produced the answer, or the last action step."""
    steps = getattr(getattr(agent, "memory", None), "steps", []) or []
    action_steps = [
        step for step in steps if isinstance(getattr(step, "step_number", None), int)
    ]
    for step in reversed(action_steps):
        if getattr(step, "is_final_answer", False):
            return min(int(step.step_number), MAX_AGENT_STEPS)
    if action_steps:
        return min(int(action_steps[-1].step_number), MAX_AGENT_STEPS)
    return _agent_step_number(agent)


def _log_web_search_trace(
    agent: Any, search_called: bool, final_response: str | None
) -> None:
    """Log a skipped search and the final answer. Tool calls are logged as they run."""
    step = _final_step_number(agent)
    if not search_called:
        logger.info(
            LOG_TOOL_CALLED.format(step=step, max_steps=MAX_AGENT_STEPS, called="false")
        )
    if final_response is not None:
        logger.info(
            LOG_FINAL_RESPONSE.format(
                step=step, max_steps=MAX_AGENT_STEPS, response=final_response
            )
        )


def _redact_serpapi_key(text: str) -> str:
    secret = os.getenv(SERPAPI_API_KEY_ENV) or ""
    if secret and secret in text:
        return text.replace(secret, REDACTED_SECRET)
    return text


def _render_message(message: Any) -> str:
    if isinstance(message, dict):
        role = message.get("role", "")
        content = message.get("content")
    else:
        role = getattr(message, "role", "")
        content = getattr(message, "content", None)
    body = _content_to_text(content)
    if not body:
        return ""
    return f"{_role_name(role)}:\n{body}"


def _role_name(role: Any) -> str:
    value = getattr(role, "value", role)
    return str(value)


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [_content_to_text(item) for item in content]
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        text = content.get("text")
        if text is not None:
            return _content_to_text(text)
        return ""
    return str(content)
