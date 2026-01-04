# models/ship.py
"""
Ship class — encapsulates the entire ship structure.
Replaces the raw self.ship dict in GameManager.
Loads rooms, objects, doors, and panels exactly as current code does.
"""

from typing import Dict, List, Tuple
from models.room import Room
from models.door import Door
from models.interactable import PortableItem, FixedObject
from models.security_panel import SecurityPanel

import json


class Ship:
    """
    Owns all rooms, doors, and cargo.
    Centralizes loading and provides clean access/query methods.
    """

    def __init__(self, name: str):
        self.name = name
        self.rooms: Dict[str, Room] = {}                    # room_id → Room
        self.doors: List[Door] = []                         # All doors
        self.cargo_by_room: Dict[str, List[PortableItem]] = {}  # room_id → [PortableItem]

    @classmethod
    def load_from_json(cls, name: str, items: Dict[str, dict]) -> 'Ship':
        """
        Load full ship state from JSON files.
        Mirrors GameManager._load_ship_rooms() and _load_doors() exactly.
        """
        ship = cls(name)

        # === Load rooms and instantiate objects ===
        with open("data/ship_rooms.json", "r", encoding="utf-8") as f:
            rooms_data = json.load(f)

        raw_object_ids: Dict[str, List[str]] = {}

        for room_data in rooms_data:
            room_id = room_data["id"]
            raw_object_ids[room_id] = room_data.get("fixed_objects", [])

            room = Room(
                room_id=room_id,
                name=room_data["name"],
                description=room_data["description"],
                background=room_data["background"],
                exits=room_data["exits"]
            )
            ship.rooms[room_id] = room

        # Instantiate objects
        for room in ship.rooms.values():
            for obj_id in raw_object_ids[room.id]:
                obj_data = items.get(obj_id)
                if not obj_data:
                    continue
                # Filter out 'type' — matches current behavior exactly
                filtered_data = {k: v for k, v in obj_data.items() if k != "type"}
                if obj_data["type"] == "portable":
                    obj_instance = PortableItem(**filtered_data)
                else:
                    obj_instance = FixedObject(**filtered_data)
                room.add_object(obj_instance)

        # === Load doors and panels (exact replica of _load_doors) ===
        try:
            with open("data/door_status.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                connections = data["connections"]
        except Exception as e:
            print(f"Failed to load door_status.json in Ship: {e}")
            connections = []

        door_by_pair: Dict[frozenset[str], Door] = {}

        for conn in connections:
            door_id = conn["id"]
            room_ids = conn["rooms"]
            if len(room_ids) != 2:
                print(f"Warning: Door {door_id} does not connect exactly two rooms")
                continue

            room_a = ship.rooms.get(room_ids[0])
            room_b = ship.rooms.get(room_ids[1])
            if not room_a or not room_b:
                print(f"Warning: Missing room for door {door_id}")
                continue

            pair_key = frozenset([room_a.id, room_b.id])

            if pair_key in door_by_pair:
                door = door_by_pair[pair_key]
            else:
                door = Door(
                    door_id=door_id,
                    room_a=room_a,
                    room_b=room_b,
                    locked=conn.get("locked", False),
                    security_level=conn["security_level"],
                    pin=conn.get("pin"),
                    images={
                        "open": conn.get("open_image", "resources/images/image_missing.png"),
                        "locked": conn.get("locked_image", "resources/images/image_missing.png"),
                        "panel": conn.get("panel_image", "resources/images/image_missing.png"),
                        "panel_damaged": conn.get("panel_image_damaged", "resources/images/image_missing.png"),
                    },
                )
                door_by_pair[pair_key] = door
                ship.doors.append(door)

            # Attach panels — preserving all debug prints
            for panel_data in conn.get("panel_ids", []):
                panel_id = panel_data["id"]
                side_room_id = panel_data["side"]
                damaged = panel_data.get("damaged", False)
                repair_progress = panel_data.get("repair_progress", 0.0)

                print("START------------------------------")
                print(panel_data)
                print(f"DEBUG: damaged = {damaged}")

                panel = SecurityPanel(
                    panel_id=panel_id,
                    door_id=door_id,
                    security_level=door.security_level,
                    side=side_room_id,
                    pin=door.pin,
                    damaged=damaged,
                    repair_progress=repair_progress,
                )

                print(f"panel is broken : {panel.is_broken}")

                door.panels[side_room_id] = panel
                print(f"ATTACHED PANEL: side={side_room_id}, panel_id={panel_id}, is_broken={panel.is_broken}")
                print("END ---------------------")

                side_room = room_a if side_room_id == room_a.id else room_b
                side_room.panels[door_id] = panel

        # Patch exits with door references (critical step)
        for door in ship.doors:
            room_a, room_b = door.rooms

            exit_key_a = next((k for k, v in room_a.exits.items() if v.get("target") == room_b.id), None)
            exit_key_b = next((k for k, v in room_b.exits.items() if v.get("target") == room_a.id), None)

            if exit_key_a and exit_key_b:
                for room, exit_key in [(room_a, exit_key_a), (room_b, exit_key_b)]:
                    original_exit = room.exits[exit_key].copy()
                    original_exit["door"] = door
                    room.exits[exit_key] = original_exit
            else:
                print(f"Warning: Missing bidirectional exit for door {door.id}")

        # Initialize cargo
        ship.cargo_by_room = {
            "storage room": [],
            "cargo bay": []
        }

        return ship

    # === Useful query helpers (safe, minimal, no behavior change) ===

    def find_door_from_room(self, room: Room, target_exit: str) -> Door | None:
        """Return the Door matching an exit label/shortcut FROM THE GIVEN ROOM ONLY."""
        if not target_exit:
            return None

        target = target_exit.strip().lower()
        for exit_key, ed in room.exits.items():
            if "door" not in ed:
                continue  # Only consider secured exits

            door = ed["door"]
            other_room = door.get_other_room(room)

            # Match on exit key, shortcuts, or other room ID
            if (target == exit_key.lower() or
                target in [s.lower() for s in ed.get("shortcuts", [])] or
                target == other_room.id.lower()):
                return door

        return None

    def get_broken_panels_in_room(self, room: Room) -> List[Tuple[SecurityPanel, str, Door]]:
        broken = []
        for door in self.doors:
            panel = door.get_panel_for_room(room)
            if panel and panel.is_broken:
                other_room = door.get_other_room(room)
                exit_label = next(
                    (ed.get("label", other_room.name) for ed in room.exits.values() if ed.get("target") == other_room.id),
                    other_room.name
                )
                broken.append((panel, exit_label, door))
        return broken

    # === Cargo helpers (exact copies from GameManager) ===

    def add_to_cargo(self, item: PortableItem, room_id: str) -> bool:
        if isinstance(item, PortableItem) and room_id in self.cargo_by_room:
            self.cargo_by_room[room_id].append(item)
            return True
        return False

    def remove_from_cargo(self, item_id: str, room_id: str) -> bool:
        if room_id in self.cargo_by_room:
            cargo_list = self.cargo_by_room[room_id]
            for i, item in enumerate(cargo_list):
                if item.id == item_id:
                    cargo_list.pop(i)
                    return True
        return False

    def get_cargo_for_room(self, room_id: str) -> List[PortableItem]:
        return self.cargo_by_room.get(room_id, [])