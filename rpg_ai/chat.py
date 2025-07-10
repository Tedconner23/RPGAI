"""Chat manager for communicating with the OpenAI API and tracking history."""

from typing import Any

from .game import GameState


class ChatManager:
    """Manage chat communication with OpenAI and keep conversation history."""

    def __init__(self, openai_client: Any, game_state: GameState) -> None:
        self.client = openai_client
        self.game_state = game_state
        self.history: list[dict[str, str]] = []

    def send_message(self, message: str) -> str:
        """Send a message to the AI and return the response text."""
        self.history.append({"role": "user", "content": message})
        # This is a placeholder call since the OpenAI API requires network access.
        # In a real implementation, you would call the OpenAI API here using
        # ``self.history`` as the message list and ``self.game_state`` to provide
        # additional context.
        # Example:
        # response = self.client.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     messages=self.history,
        # )
        # answer = response.choices[0].message.content

        answer = (
            f"[World] {self.game_state.describe_world()}\n"
            "This is a placeholder response."
        )
        self.history.append({"role": "assistant", "content": answer})
        return answer
