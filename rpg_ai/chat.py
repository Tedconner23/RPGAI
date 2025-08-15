"""Chat manager for communicating with the OpenAI API and tracking history."""

import logging
import time
from pathlib import Path
from openai import OpenAI

from .game import GameState
from .memory import (
    update_conversation_summary,
    update_user_preferences,
)


logger = logging.getLogger(__name__)


class ChatManager:
    """Manage chat communication with OpenAI's Assistants API."""

    def __init__(
        self,
        openai_client: OpenAI,
        game_state: GameState,
        file_ids: list[str] | None = None,
    ) -> None:
        self.client = openai_client
        self.game_state = game_state
        self.history: list[dict[str, str]] = []

        root_dir = Path(__file__).resolve().parent.parent
        self.memory_path = root_dir / "source" / "memory_summary.txt"
        self.prefs_path = root_dir / "source" / "user_prefs.txt"
        self.interaction_count = 0

        instructions = self.game_state.describe_world()
        if self.memory_path.exists():
            instructions += (
                "\n\nConversation summary:\n" +
                self.memory_path.read_text(encoding="utf-8")
            )
        if self.prefs_path.exists():
            instructions += (
                "\n\nUser preferences:\n" +
                self.prefs_path.read_text(encoding="utf-8")
            )

        tools = [{"type": "retrieval"}] if file_ids else []

        try:
            # Older versions of the OpenAI client accept ``file_ids`` directly
            # when creating the assistant.
            self.assistant = self.client.beta.assistants.create(
                model="gpt-4o",
                instructions=instructions,
                tools=tools,
                file_ids=file_ids or [],
            )
        except TypeError:
            # Newer versions require a vector store instead of ``file_ids``.
            if file_ids and hasattr(self.client.beta, "vector_stores"):
                vector_store = self.client.beta.vector_stores.create(
                    name="rpg-ai-source"
                )
                self.client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id,
                    files=file_ids,
                )
                tool_resources = {
                    "file_search": {"vector_store_ids": [vector_store.id]}
                }
                self.assistant = self.client.beta.assistants.create(
                    model="gpt-4o",
                    instructions=instructions,
                    tools=tools,
                    tool_resources=tool_resources,
                )
            else:
                # If files are provided but we cannot attach them, create the
                # assistant without retrieval capabilities so at least the
                # application continues to function.
                self.assistant = self.client.beta.assistants.create(
                    model="gpt-4o",
                    instructions=instructions,
                )
        self.thread = self.client.beta.threads.create()
        logger.info("ChatManager initialized (files: %s)", file_ids)
        self._new_log_file()

    def _new_log_file(self) -> None:
        """Create a new text file for logging conversation history."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        root_dir = Path(__file__).resolve().parent.parent
        self.log_path = root_dir / f"chat_{timestamp}.txt"
        with self.log_path.open("w", encoding="utf-8") as f:
            f.write(f"Chat started {timestamp}\n\n")

    def _append_line(self, role: str, content: str) -> None:
        """Append a formatted line to the current chat log file."""
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"{role}: {content}\n")

    def _update_memory(self) -> None:
        """Update conversation summary and, periodically, preference memory."""
        update_conversation_summary(self.client, self.history, self.memory_path)
        if self.interaction_count % 10 == 0 and self.interaction_count > 0:
            update_user_preferences(self.client, self.history, self.prefs_path)

    def send_message(self, message: str) -> str:
        """Send a message to the assistant and return the response text."""
        logger.info("User: %s", message)
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=message,
        )
        answer = self._run_assistant()

        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": answer})
        self._append_line("You", message)
        self._append_line("AI", answer)
        self.interaction_count += 1
        self._update_memory()
        logger.info("Assistant: %s", answer)
        return answer

    def _run_assistant(self) -> str:
        """Execute the assistant run and return the latest assistant reply."""
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )
        while run.status not in {"completed", "failed", "cancelled"}:
            time.sleep(0.5)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id, run_id=run.id
            )
            logger.debug("Run status: %s", run.status)

        if run.status != "completed":
            raise RuntimeError(f"Run failed: {run.status}")

        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        answer = ""
        for msg in messages.data:
            if msg.role == "assistant":
                answer = msg.content[0].text.value.strip()
                break
        return answer

    def _rebuild_thread(self) -> None:
        """Create a new thread and replay ``history`` messages into it."""
        self.thread = self.client.beta.threads.create()
        for msg in self.history:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=msg["role"],
                content=msg["content"],
            )

    def remove_message(self, index: int) -> None:
        """Remove a message from history and rebuild the thread."""
        if 0 <= index < len(self.history):
            del self.history[index]
            self._rebuild_thread()

    def regenerate_last(self) -> str:
        """Regenerate the assistant's most recent response."""
        if len(self.history) < 2 or self.history[-1]["role"] != "assistant":
            return ""

        # Remove the previous assistant reply and rebuild the thread
        self.history.pop()
        self._rebuild_thread()

        answer = self._run_assistant()
        self.history.append({"role": "assistant", "content": answer})
        self._append_line("AI (regenerated)", answer)
        update_conversation_summary(self.client, self.history, self.memory_path)
        logger.info("Assistant (regenerated): %s", answer)
        return answer

    def edit_and_resend(self, index: int, new_message: str) -> str:
        """Edit a prior user message and resend it for a new response."""
        if not 0 <= index < len(self.history):
            return ""
        if self.history[index]["role"] != "user":
            return ""

        self.history[index]["content"] = new_message
        del self.history[index + 1 :]
        self._rebuild_thread()

        answer = self._run_assistant()
        self.history.append({"role": "assistant", "content": answer})
        self._append_line("You (edited)", new_message)
        self._append_line("AI", answer)
        self.interaction_count += 1
        self._update_memory()
        logger.info("Assistant (edited): %s", answer)
        return answer

    def clear(self) -> None:
        """Clear all messages and start a fresh thread."""
        self.history.clear()
        self.thread = self.client.beta.threads.create()
        self._new_log_file()

    def export_history(self) -> str:
        """Return the conversation history as plain text."""
        parts = []
        for msg in self.history:
            role = "You" if msg["role"] == "user" else "AI"
            parts.append(f"{role}: {msg['content']}")
        return "\n\n".join(parts)
