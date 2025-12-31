# game_manager.py
import json
from constants import STARTING_ROOM, PLAYER_NAME, SHIP_NAME
from models.interactable import PortableItem, FixedObject  # Import the new interactable classes
from models.security_panel import SecurityPanel  # NEW: Import the SecurityPanel class


class GameManager:
    """Central coordinator for game state.

    Holds player, ship, current location and provides methods to create a new game.
    """

    def __init__(self):
        self.player = None
        self.ship = None
        self.current_location = None
        self.items = {}  # id -> full item dict from objects.json

        self._load_items()  # Load global item registry
        self._load_door_status()  # NEW: Load door status

        # Mass tracking for player inventory
        self.player_carry_mass = 0.0
        self.player_max_carry_mass = 10.0

        self.security_panels = {}  # NEW: panel_id -> SecurityPanel
        self._load_security_panels()  # NEW: Load panels at startup


    def _load_items(self):
        """Load all item definitions from objects.json into self.items."""
        try:
            with open("data/objects.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.items = {item["id"]: item for item in data}
        except Exception as e:
            print(f"Failed to load objects.json: {e}")
            self.items = {}

    def create_new_game(self, player_name=PLAYER_NAME, ship_name=SHIP_NAME, skills=None):
        """
        Loads ship rooms from JSON and places the player in their quarters.
        'skills' parameter is included for future background selection.
        """
        # Use fixed skills for now (will come from background choice later)
        if skills is None:
            skills = [
                "Freighter Pilot License",
                "Space Systems Engineering",
                "EVA Certification",
                "Computer Systems Specialist",
                "Basic Trade Negotiation",
                "Zero-G Repair"
            ]

        self.player = {
            "name": player_name,
            "skills": skills,
            "inventory": []  # list of item IDs (strings)
        }

        self.ship = {
            "name": ship_name,
            "rooms": self._load_ship_rooms(),
            "cargo_by_room": {  # NEW
                "storage room": [],  # Personal/small storage
                "cargo bay": []  # Large/trade cargo
            }
        }

        # Player always starts in quarters after waking up
        self.current_location = self.ship["rooms"][STARTING_ROOM]

    def _load_ship_rooms(self) -> dict:
        """
        Load ship room data from JSON and instantiate Room objects.
        Preserves exact current behavior — no new functionality added.
        """
        from models.room import Room

        with open("data/ship_rooms.json", "r", encoding="utf-8") as f:
            rooms_data = json.load(f)

        rooms = {}

        # Temporary storage for raw object IDs
        raw_object_ids = {}

        # First pass: create Room instances
        for room_data in rooms_data:
            room_id = room_data["id"]
            raw_object_ids[room_id] = room_data.get("objects", [])

            room = Room(
                room_id=room_id,
                name=room_data["name"],
                description=room_data["description"],
                background=room_data["background"],
                exits=room_data["exits"]
            )
            rooms[room.id] = room

        # Second pass: instantiate objects using the saved raw IDs
        for room in rooms.values():
            for obj_id in raw_object_ids[room.id]:
                obj_data = self.items.get(obj_id)
                if obj_data:
                    if obj_data["type"] == "portable":
                        obj_instance = PortableItem(
                            **{k: v for k, v in obj_data.items() if k != "type"}
                        )
                    else:
                        obj_instance = FixedObject(
                            **{k: v for k, v in obj_data.items() if k != "type"}
                        )
                    room.add_object(obj_instance)

        return rooms

    def _load_door_status(self):
        """Load door status from door_status.json."""
        try:
            with open("data/door_status.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.door_status = data["connections"]
        except Exception as e:
            print(f"Failed to load door_status.json: {e}")
            self.door_status = []

    def _load_security_panels(self):
        """Load and instantiate SecurityPanel instances from door_status.json."""
        self.security_panels = {}

        try:
            with open("data/door_status.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                connections = data["connections"]

            for door in connections:
                door_id = door["id"]
                panel_ids = door.get("panel_ids", [])
                security_level = door["security_level"]
                door_pin = door.get("pin") if security_level == 3 else None

                for panel_data in panel_ids:
                    panel_id = panel_data["id"]
                    side = panel_data["side"]

                    # NEW: Load damage fields if present
                    damaged = panel_data.get("damaged", False)
                    repair_progress = panel_data.get("repair_progress", 0.0)

                    panel = SecurityPanel(
                        panel_id=panel_id,
                        door_id=door_id,
                        security_level=security_level,
                        side=side,
                        pin=door_pin,
                        damaged=damaged,  # NEW
                        repair_progress=repair_progress  # NEW
                    )
                    self.security_panels[panel_id] = panel

        except Exception as e:
            print(f"Failed to load security panels: {e}")
            self.security_panels = {}

    def get_current_location(self) -> dict:
        """Return the current location data."""
        return self.current_location

    def set_current_location(self, room_id: str) -> None:
        """Set the current location by room ID. Single source of truth for game state."""
        if room_id in self.ship["rooms"]:
            self.current_location = self.ship["rooms"][room_id]
        else:
            raise ValueError(f"Invalid room ID: {room_id}")

    # Inventory helpers (updated to use IDs and mass)
    def add_to_inventory(self, item_id: str) -> tuple[bool, str]:
        """Add a portable item by ID to player inventory, checking mass."""
        item_data = self.items.get(item_id)
        if not item_data or item_data["type"] != "portable":
            return False, "You can't take that."

        mass = item_data.get("mass", 0.0)
        if self.player_carry_mass + mass > self.player_max_carry_mass:
            return False, f"Too heavy! You can carry {self.player_max_carry_mass - self.player_carry_mass:.1f} kg more."

        self.player["inventory"].append(item_id)
        self.player_carry_mass += mass
        return True, f"You take the {item_data['name']}."

    def remove_from_inventory(self, item_id: str) -> bool:
        """Remove an item by ID from inventory and update mass."""
        if item_id in self.player["inventory"]:
            item_data = self.items.get(item_id)
            if item_data:
                self.player_carry_mass -= item_data.get("mass", 0.0)
            self.player["inventory"].remove(item_id)
            return True
        return False

    def add_to_cargo(self, item: PortableItem, room_id: str) -> bool:
        """Add item to the cargo list for the specified room."""
        if isinstance(item, PortableItem) and room_id in self.ship["cargo_by_room"]:
            self.ship["cargo_by_room"][room_id].append(item)
            return True
        return False

    def remove_from_cargo(self, item_id: str, room_id: str) -> bool:
        """Remove item from the cargo list for the specified room by ID."""
        if room_id in self.ship["cargo_by_room"]:
            cargo_list = self.ship["cargo_by_room"][room_id]
            for i, item in enumerate(cargo_list):
                if item.id == item_id:
                    cargo_list.pop(i)
                    return True
        return False

    def get_cargo_for_room(self, room_id: str) -> list:
        """Get cargo list for a specific room."""
        return self.ship["cargo_by_room"].get(room_id, [])

    def get_player_inventory(self) -> list:
        """Return the player's personal inventory list (of item IDs)."""
        return self.player["inventory"]