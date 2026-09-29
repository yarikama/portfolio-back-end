"""Prompting the autocomplete model and turning its output into a suggestion."""

import json
import math
import time
from dataclasses import dataclass

import httpx
from core import config

MAX_CONTEXT_CHARS = 2000  # about 500 tokens: enough context, fast prefill
MAX_TOKENS = 16  # an upper bound; generation usually stops much earlier
TIMEOUT_SECONDS = 2.0  # past this the author has typed on; give up quietly
SENTENCE_END = (".", "!", "?")


# Tests swap in an httpx.MockTransport.
_transport: httpx.AsyncBaseTransport | None = None


@dataclass
class Prompt:
    text: str
    # Spaces or tabs the author typed after the last word. They are left out
    # of the prompt (see build_prompt) and removed from the suggestion.
    trailing_space: str


@dataclass
class Completion:
    # Everything generated before the model was stopped: the kept tokens,
    # plus the unsure token that ended the suggestion, if any.
    text: str
    tokens: list[tuple[str, float]]
    latency_ms: int


def build_prompt(prefix: str, title: str) -> Prompt:
    """The model continues a Markdown document: the title as a heading, then
    the text before the cursor.

    Trailing spaces are cut. BPE tokenizers attach a word's leading space to
    the word (" was"), so a prompt ending in a space leaves the model to
    produce a token that starts with a second one; ending on the word lets it
    continue naturally. Newlines stay: a new line is a real boundary.
    """
    context = prefix[-MAX_CONTEXT_CHARS:]
    body = context.rstrip(" \t")
    header = f"# {title.strip()}\n\n" if title.strip() else ""
    return Prompt(text=header + body, trailing_space=context[len(body) :])


def keep(token: str, logprob: float, min_prob: float) -> tuple[bool, bool]:
    """Whether a token belongs in the suggestion, and whether it ends it."""
    if math.exp(logprob) < min_prob:
        return False, True
    return True, token.rstrip().endswith(SENTENCE_END)


def shape_suggestion(
    tokens: list[tuple[str, float]], trailing_space: str, min_prob: float
) -> str:
    """Keep the confident start of the completion.

    Tokens are kept while each one's probability stays at or above min_prob,
    and the suggestion ends after a sentence end. If the author already typed
    a space, the completion must start with one (it is dropped); a completion
    that instead continues the last word no longer fits and is discarded.
    """
    text = ""
    for token, logprob in tokens:
        kept, last = keep(token, logprob, min_prob)
        if kept:
            text += token
        if last:
            break
    text = text.rstrip()
    if trailing_space:
        if not text[:1].isspace():
            return ""
        text = text.lstrip(" \t")
    return text


async def complete(prompt: str, min_prob: float) -> Completion:
    """Ask the model to continue prompt, streaming token by token.

    Reading stops at the first token the suggestion would not keep, or after
    a sentence end: leaving the stream closes the connection and vLLM aborts
    the request, instead of generating up to MAX_TOKENS that would be thrown
    away. Raises httpx.HTTPError on failure.
    """
    started = time.perf_counter()
    text, tokens = "", []
    async with (
        httpx.AsyncClient(timeout=TIMEOUT_SECONDS, transport=_transport) as client,
        client.stream(
            "POST",
            f"{config.AUTOCOMPLETE_URL.rstrip('/')}/v1/completions",
            json={
                "model": config.AUTOCOMPLETE_MODEL,
                "prompt": prompt,
                "max_tokens": MAX_TOKENS,
                "temperature": 0,
                "stop": ["\n"],
                # 0: the log-probability of each generated token, no alternatives.
                "logprobs": 0,
                "stream": True,
            },
        ) as response,
    ):
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            if line == "data: [DONE]":
                break
            choice = json.loads(line[len("data: ") :])["choices"][0]
            logprobs = choice.get("logprobs") or {}
            text += choice.get("text", "")
            done = False
            for token, logprob in zip(
                logprobs.get("tokens", []), logprobs.get("token_logprobs", [])
            ):
                tokens.append((token, logprob))
                done = done or keep(token, logprob, min_prob)[1]
            if done:
                break
    return Completion(
        text=text,
        tokens=tokens,
        latency_ms=round((time.perf_counter() - started) * 1000),
    )
