"""Chat manager for communicating with the OpenAI API and tracking history."""

import time
from openai import OpenAI

from .game import GameState


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
        self.assistant = self.client.beta.assistants.create(
            model="gpt-4o",
            instructions=self.game_state.describe_world(),
            tools=tools,
            file_ids=file_ids or [],
        )
        self.thread = self.client.beta.threads.create()

    def send_message(self, message: str) -> str:
        """Send a message to the assistant and return the response text."""
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
        return answer
