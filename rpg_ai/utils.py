from __future__ import annotations
from pathlib import Path
from typing import List, Iterable, Tuple

import json

from openai import OpenAI

import PyPDF2


def load_source_files(directory: Path) -> str:
    """Return the combined text from all txt and pdf files in the directory."""
    if not directory.exists():
        return ""

    texts: List[str] = []
    for path in directory.iterdir():
        content = ""
        if path.suffix.lower() == ".txt":
            # Explicitly decode as UTF-8 and ignore any invalid bytes so
            # unexpected encodings do not crash the application.
            content = path.read_text(encoding="utf-8", errors="ignore")
        elif path.suffix.lower() == ".pdf":
            with path.open("rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text() or ""
                    content += text
        if content:
            # Include the file name so the assistant can reference it directly.
            texts.append(f"### File: {path.name}\n{content}")
    return "\n\n".join(texts)


def upload_source_files(client: OpenAI, directory: Path) -> list[str]:
    """Upload txt and pdf files for assistant retrieval and return file IDs."""
    if not directory.exists():
        return []

    file_ids: list[str] = []
    for path in directory.iterdir():
        if path.suffix.lower() not in {".txt", ".pdf"}:
            continue
        with path.open("rb") as f:
            uploaded = client.files.create(file=f, purpose="assistants")
            file_ids.append(uploaded.id)
    return file_ids


def load_system_config(directory: Path) -> Tuple[str, str]:
    """Return custom instructions and a rating string from ``system.json``.

    The file should contain JSON with ``instructions`` and ``rating`` fields.
    Missing fields result in empty strings. If the file does not exist, both
    values are empty.
    """

    config_path = directory / "system.json"
    if not config_path.exists():
        return "", ""

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "", ""

    instructions = data.get("instructions", "") or ""
    rating = data.get("rating", "") or ""
    return instructions, rating
