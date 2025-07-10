from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .models import Player, Item

@dataclass
class GameState:
    """Track overall game state for the session."""

    player: Player

    def add_item_to_player(self, item: Item) -> None:
        self.player.add_item(item)

    def describe_world(self) -> str:
        """Return a brief description of the game world."""
        return (
            "You find yourself in a sprawling realm full of adventure and danger. "
            "Chat with the AI to explore and interact with this world."
        )
