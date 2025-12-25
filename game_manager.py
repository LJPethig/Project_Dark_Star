# game_manager.py
import json
from models.interactable import PortableItem, FixedObject  # Import the new interactable classes


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

        # Mass tracking for player inventory
        self.player_carry_mass = 0.0
        self.player_max_carry_mass = 10.0

    def _load_items(self):
        """Load all item definitions from objects.json into self.items."""
        try:
            with open("data/objects.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.items = {item["id"]: item for item in data}
        except Exception as e:
            print(f"Failed to load objects.json: {e}")
            self.items = {}

    def create_new_game(self, player_name="Jack Harrow", ship_name="Tempus Fugit", skills=None):
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
            "cargo": []  # NEW: ship cargo hold (list of PortableItems)
        }

        # Player always starts in quarters after waking up
        self.current_location = self.ship["rooms"]["crew quarters"]

    def _load_ship_rooms(self) -> dict:
        """Load ship room data from JSON and instantiate objects from self.items."""
        with open("data/ship_rooms.json", "r") as f:
            rooms_data = json.load(f)

        rooms = {}
        for room_data in rooms_data:
            room_id = room_data["id"]

            # Convert raw "objects" list of IDs into instantiated Interactable objects
            objects = []
            for obj_id in room_data.get("objects", []):
                item_data = self.items.get(obj_id)
                if not item_data:
                    print(f"Warning: Item ID '{obj_id}' not found in objects.json")
                    continue

                obj_type = item_data.get("type", "portable")

                # Remove 'type' key (it's not expected by the dataclasses)
                obj_kwargs = {k: v for k, v in item_data.items() if k != "type"}

                if obj_type == "portable":
                    obj = PortableItem(**obj_kwargs)
                elif obj_type == "fixed":
                    obj = FixedObject(**obj_kwargs)
                else:
                    print(f"Warning: Unknown object type '{obj_type}' for {obj_id}")
                    continue

                objects.append(obj)

            room_data["objects"] = objects  # Replace ID list with instantiated objects
            rooms[room_id] = room_data

        return rooms

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

    def add_to_cargo(self, item: PortableItem) -> bool:
        """Add item to ship cargo hold."""
        if isinstance(item, PortableItem):
            self.ship["cargo"].append(item)
            return True
        return False

    def remove_from_cargo(self, item_id: str) -> bool:
        """Remove from ship cargo by ID."""
        for i, item in enumerate(self.ship["cargo"]):
            if item.id == item_id:
                self.ship["cargo"].pop(i)
                return True
        return False

    def get_ship_cargo(self) -> list:
        """Return the ship's cargo list."""
        return self.ship["cargo"]

    def get_player_inventory(self) -> list:
        """Return the player's personal inventory list (of item IDs)."""
        return self.player["inventory"]