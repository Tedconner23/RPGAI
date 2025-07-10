from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Item:
    """Represent an item in the player's inventory."""
    name: str
    description: str
    image_url: Optional[str] = None

@dataclass
class Player:
    """Simple player model with basic D&D style attributes."""
    name: str
    race: str
    character_class: str
    level: int = 1
    hit_points: int = 10
    inventory: List[Item] = field(default_factory=list)

    def add_item(self, item: Item) -> None:
        self.inventory.append(item)
