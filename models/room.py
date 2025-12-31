# models/room.py
from typing import Dict, List, Any
from models.interactable import PortableItem, FixedObject


class Room:
    """
    Minimal Room instance — exact replacement for the current room dict.
    Supports the full existing game loop with zero added behavior.
    Future capabilities (states, environment, dynamics) will be added only when required.
    """

    def __init__(
        self,
        room_id: str,
        name: str,
        description: List[str],
        background: str,
        exits: Dict[str, Dict[str, Any]],
    ):
        self.id = room_id
        self.name = name
        self.description = description
        self.background = background
        self.exits = exits  # Raw exit dicts — unchanged until Door arrives

        # List of instantiated interactables (PortableItem / FixedObject)
        self.objects: List[PortableItem | FixedObject] = []

        # Placeholder for per-side security panels (filled later by Door loading)
        self.panels: Dict[str, Any] = {}  # door_id → SecurityPanel


    def add_object(self, obj: PortableItem | FixedObject) -> None:
        """Add an instantiated object to the room."""
        self.objects.append(obj)


    def remove_object(self, obj_id: str) -> bool:
        """Remove an object by ID during 'take' or 'drop'. Returns success."""
        for i, obj in enumerate(self.objects):
            if obj.id == obj_id:
                self.objects.pop(i)
                return True
        return False