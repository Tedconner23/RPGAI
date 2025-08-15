"""Helpers for maintaining conversation and preference memory files."""
from __future__ import annotations

from pathlib import Path

from openai import OpenAI


def _summarize(client: OpenAI, prompt: str) -> str:
    """Use the OpenAI client to generate a summary string.

    If the API request fails for any reason an empty string is returned so the
    existing memory file can be left unchanged.
    """
    try:
        response = client.responses.create(model="gpt-4o-mini", input=prompt)
        return response.output_text.strip()
    except Exception:
        return ""


def update_conversation_summary(
    client: OpenAI, history: list[dict[str, str]], path: Path
) -> None:
    """Update ``path`` with a brief summary of the conversation so far.

    If an existing summary still applies, it is left unchanged.  When the API
    call fails the file is left untouched.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    prompt = (
        "You maintain a short running summary of a conversation for future context. "
        "Existing summary:\n" + existing + "\n\n"
        "Conversation so far:\n" + convo + "\n\n"
        "Provide an updated summary. If the existing summary is still accurate, "
        "return it unchanged."
    )
    summary = _summarize(client, prompt)
    if summary:
        path.write_text(summary, encoding="utf-8")


def update_user_preferences(
    client: OpenAI, history: list[dict[str, str]], path: Path
) -> None:
    """Update ``path`` with user preferences and AI personality details.

    This is processed less frequently (e.g., every 10 chats).  When the API call
    fails the file remains unchanged.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    prompt = (
        "Extract user preferences, AI personality traits, likes and dislikes from "
        "the conversation. Existing record:\n" + existing + "\n\n"
        "Conversation:\n" + convo + "\n\n"
        "Return an updated record. If nothing new was learned, repeat the "
        "existing record unchanged."
    )
    prefs = _summarize(client, prompt)
    if prefs:
        path.write_text(prefs, encoding="utf-8")
