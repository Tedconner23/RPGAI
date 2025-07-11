from __future__ import annotations
from pathlib import Path
from typing import List, Iterable

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
            content = path.read_text()
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
