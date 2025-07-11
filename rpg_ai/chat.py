"""Chat manager for communicating with the OpenAI API and tracking history."""

import logging
import time
from openai import OpenAI

from .game import GameState


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

        tools = [{"type": "retrieval"}] if file_ids else []

        try:
            # Older versions of the OpenAI client accept ``file_ids`` directly
            # when creating the assistant.
            self.assistant = self.client.beta.assistants.create(
                model="gpt-4o",
                instructions=self.game_state.describe_world(),
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
                    instructions=self.game_state.describe_world(),
                    tools=tools,
                    tool_resources=tool_resources,
                )
            else:
                # If files are provided but we cannot attach them, create the
                # assistant without retrieval capabilities so at least the
                # application continues to function.
                self.assistant = self.client.beta.assistants.create(
                    model="gpt-4o",
                    instructions=self.game_state.describe_world(),
                )
        self.thread = self.client.beta.threads.create()
        logger.info("ChatManager initialized (files: %s)", file_ids)

    def send_message(self, message: str) -> str:
        """Send a message to the assistant and return the response text."""
        logger.info("User: %s", message)
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=message,
        )

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

        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": answer})
        logger.info("Assistant: %s", answer)
        return answer
