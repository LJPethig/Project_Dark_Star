# models/door.py
from typing import Dict
from models.security_panel import SecurityPanel
from models.room import Room


class Door:
    """
    Represents a bi-directional door connection between two rooms.
    Replaces raw connection dicts from door_status.json.
    Holds shared state and per-side panels.
    """

    def __init__(
        self,
        door_id: str,
        room_a: Room,
        room_b: Room,
        locked: bool,
        security_level: int,
        pin: str | None,
        images: Dict[str, str],
    ):
        self.id = door_id
        self.rooms = (room_a, room_b)  # Tuple for symmetry — order irrelevant
        self.locked = locked
        self.security_level = security_level
        self.pin = pin
        self.images = images

        # Per-side panels: room.id → SecurityPanel instance
        self.panels: Dict[str, SecurityPanel] = {}

    def get_other_room(self, current_room: Room) -> Room:
        """Return the room on the opposite side of this door."""
        if current_room is self.rooms[0]:
            return self.rooms[1]
        elif current_room is self.rooms[1]:
            return self.rooms[0]
        else:
            raise ValueError(f"Room {current_room.id} is not connected to door {self.id}")

    def get_panel_for_room(self, room: Room) -> SecurityPanel | None:
        """Return the SecurityPanel instance on the given room's side."""
        return self.panels.get(room.id)

    def set_locked(self, locked: bool):
        """Central place to change locked state (future: events, auto-shut)."""
        self.locked = locked