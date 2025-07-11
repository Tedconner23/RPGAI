"""Chat manager for communicating with the OpenAI API and tracking history."""

from openai import OpenAI

from .game import GameState


class ChatManager:
    """Manage chat communication with OpenAI and keep conversation history."""

    def __init__(self, openai_client: OpenAI, game_state: GameState) -> None:
        self.client = openai_client
        self.game_state = game_state
        self.history: list[dict[str, str]] = []

    def send_message(self, message: str) -> str:
        """Send a message to the AI and return the response text."""
        self.history.append({"role": "user", "content": message})

        system_prompt = {"role": "system", "content": self.game_state.describe_world()}
        messages = [system_prompt] + self.history

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        answer = response.choices[0].message.content.strip()

        self.history.append({"role": "assistant", "content": answer})
        return answer
