from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .models import Player, Item

@dataclass
class GameState:
    """Track overall game state for the session."""

    player: Player
    source_text: str = ""
    instructions: str = ""
    rating: str = ""

    def add_item_to_player(self, item: Item) -> None:
        self.player.add_item(item)

    def player_description(self) -> str:
        """Return a text summary of the current player."""
        inv_lines = [f"- {i.name}: {i.description}" for i in self.player.inventory]
        inv = "\n".join(inv_lines) if inv_lines else "None"
        return (
            f"Player Info:\n"
            f"Name: {self.player.name}\n"
            f"Race: {self.player.race}\n"
            f"Class: {self.player.character_class}\n"
            f"Level: {self.player.level}\n"
            f"HP: {self.player.hit_points}\n"
            f"Inventory:\n{inv}"
        )

    def describe_world(self) -> str:
        """Return a brief description of the game world with extra context."""
        parts = []
        if self.instructions:
            parts.append(self.instructions)
        parts.append(
            "You find yourself in a sprawling realm full of adventure and danger. "
            "Chat with the AI to explore and interact with this world."
        )
        if self.rating:
            parts.append(f"Content rating: {self.rating}")
        if self.source_text:
            parts.append(self.source_text)
        parts.append(self.player_description())
        return "\n\n".join(parts)
