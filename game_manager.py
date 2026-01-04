# game_manager.py
import json
import random
from constants import STARTING_ROOM, PLAYER_NAME, SHIP_NAME
from models.interactable import PortableItem, FixedObject
from models.ship import Ship
from models.chronometer import Chronometer

class GameManager:
    """Central coordinator for game state.

    Manages player data and delegates all ship-related state to the Ship class.
    """

    def __init__(self):
        self.player = None
        self.ship = None
        self.current_location = None
        self.items = {}  # id -> full item dict from objects.json

        self._load_items()

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

    def create_new_game(self, player_name=PLAYER_NAME, ship_name=SHIP_NAME):
        """Create a new game by loading the ship and placing the player."""
        self.player = {
            "name": player_name,
            "inventory": []  # list of item IDs (strings)
        }

        self.ship = Ship.load_from_json(name=ship_name, items=self.items)
        self.current_location = self.ship.rooms[STARTING_ROOM]

        # NEW: Place portable items procedurally
        self._place_portable_items()

        # NEW: Initialize ship chronometer
        self.chronometer = Chronometer()

    def get_current_location(self):
        """Return the current Room instance."""
        return self.current_location

    def set_current_location(self, room_id: str) -> None:
        """Set the current location by room ID."""
        if room_id in self.ship.rooms:
            self.current_location = self.ship.rooms[room_id]
        else:
            raise ValueError(f"Invalid room ID: {room_id}")

    # Inventory helpers
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

    # Cargo helpers — delegated to Ship
    def add_to_cargo(self, item: PortableItem, room_id: str) -> bool:
        """Add item to the cargo list for the specified room."""
        return self.ship.add_to_cargo(item, room_id)

    def remove_from_cargo(self, item_id: str, room_id: str) -> bool:
        """Remove item from the cargo list for the specified room by ID."""
        return self.ship.remove_from_cargo(item_id, room_id)

    def get_cargo_for_room(self, room_id: str) -> list:
        """Get cargo list for a specific room."""
        return self.ship.get_cargo_for_room(room_id)

    def get_player_inventory(self) -> list:
        """Return the player's personal inventory list (of item IDs)."""
        return self.player["inventory"]

    def _place_portable_items(self) -> None:
        """Procedurally place all portable items at game start with required guarantees."""
        if not self.ship or not self.items:
            return

        random.seed()  # Ensure fresh randomness each new game

        # Room references
        crew_quarters = self.ship.rooms["crew quarters"]
        storage_room = self.ship.rooms["storage room"]
        engineering = self.ship.rooms["engineering"]
        cargo_bay = self.ship.rooms["cargo bay"]

        scatter_rooms = [storage_room, engineering, cargo_bay]

        # === 1. Guaranteed undamaged high-sec card (critical progression item) ===
        high_sec_data = self.items["id_card_high_sec"]
        high_sec_item = PortableItem(**{k: v for k, v in high_sec_data.items() if k != "type"})
        random.choice(scatter_rooms).add_object(high_sec_item)

        # === 2. One random ID card in each required room ===
        id_card_ids = ["id_card_low_sec", "id_card_high_sec", "id_card_high_sec_damaged"]
        for room in [crew_quarters, engineering, storage_room]:
            card_id = random.choice(id_card_ids)
            card_data = self.items[card_id]
            card = PortableItem(**{k: v for k, v in card_data.items() if k != "type"})
            room.add_object(card)

        # === 3. All other portable items (tools, wires, wearables, scan tool, etc.) ===
        # Includes EVA suit and tool belt automatically via "type": "portable"
        portable_ids = [
            item_id for item_id, data in self.items.items()
            if data.get("type") == "portable" and not item_id.startswith("id_card")
        ]

        # Uniques: appear exactly once
        uniques = {"scan_tool", "eva_suit"}  # tool_belt can be common if desired
        normal_items = [pid for pid in portable_ids if pid not in uniques]
        unique_items = [pid for pid in portable_ids if pid in uniques]

        # Place uniques once
        for unique_id in unique_items:
            item_data = self.items[unique_id]
            item = PortableItem(**{k: v for k, v in item_data.items() if k != "type"})
            random.choice(scatter_rooms).add_object(item)

        # Place all remaining tools/wires/wearables
        random.shuffle(normal_items)
        for item_id in normal_items:
            item_data = self.items[item_id]
            item = PortableItem(**{k: v for k, v in item_data.items() if k != "type"})
            random.choice(scatter_rooms).add_object(item)