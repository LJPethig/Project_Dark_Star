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
        dimensions_m: dict, # Expected shape: {"length": float, "width": float, "height": float}
        target_temperature: float = 20.0,  # resolved numeric °C
    ):
        self.id = room_id
        self.name = name
        self.description = description
        self.background = background
        self.exits = exits  # Raw exit dicts — unchanged until Door arrives
        # Validate and compute volume
        self.dimensions_m, self.volume_m3 = self._validate_and_compute_volume(
            dimensions_m, room_id
        )
        # List of instantiated interactables (PortableItem / FixedObject)
        self.objects: List[PortableItem | FixedObject] = []

        # Placeholder for per-side security panels (filled later by Door loading)
        self.panels: Dict[str, Any] = {}  # door_id → SecurityPanel

        self.target_temperature = target_temperature
        self.current_temperature = target_temperature


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

    @staticmethod
    def _validate_and_compute_volume(dimensions_m: dict, room_id: str) -> tuple[dict, float]:
        if not isinstance(dimensions_m, dict):
            raise ValueError(f"Room '{room_id}': dimensions_m must be a dict")

        expected = {"length", "width", "height"}
        if set(dimensions_m) != expected:
            missing = expected - set(dimensions_m)
            extra = set(dimensions_m) - expected
            raise ValueError(
                f"Room '{room_id}': dimensions_m wrong keys. "
                f"Missing: {missing}, Extra: {extra}"
            )

        try:
            length = float(dimensions_m["length"])
            width = float(dimensions_m["width"])
            height = float(dimensions_m["height"])
        except (TypeError, ValueError):
            raise ValueError(f"Room '{room_id}': dimensions_m values must be numbers")

        if length <= 0 or width <= 0 or height <= 0:
            raise ValueError(f"Room '{room_id}': all dimensions must be positive")

        volume = length * width * height
        return dimensions_m, volume

    def __repr__(self) -> str:
        return f"<Room '{self.id}' vol={self.volume_m3:.2f} m³>"