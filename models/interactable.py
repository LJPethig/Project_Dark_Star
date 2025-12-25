from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Interactable:
    """Base class for all objects the player can interact with in rooms."""
    id: str
    name: str
    description: str
    examine_text: str = ""  # Optional detailed text shown on "examine"
    keywords: List[str] = None  # Synonyms for player input matching

    def __post_init__(self):
        """Default to name as keyword if none provided."""
        if self.keywords is None:
            self.keywords = [self.name.lower()]

    def matches(self, word: str) -> bool:
        """Check if player input matches this object's keywords."""
        return word.lower() in self.keywords

    def on_examine(self) -> str:
        """Default examine behavior (can be overridden)."""
        return self.examine_text or self.description or "No detailed description."

    def on_use(self) -> str:
        """Default use behavior (can be overridden)."""
        return f"You can't use {self.name}."


@dataclass
class PortableItem(Interactable):
    """Items that can be taken and carried in inventory."""
    takeable: bool = True
    mass: float = 0.0  # NEW: Added this field for mass-based inventory limit


@dataclass
class FixedObject(Interactable):
    """Objects that stay fixed in the room (terminals, panels, doors, etc.)."""
    takeable: bool = False
    # Future: on_use_callback: Optional[Callable] = None