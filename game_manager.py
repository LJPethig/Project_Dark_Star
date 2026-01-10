# game_manager.py
import json
import random
from typing import List
from constants import STARTING_ROOM, PLAYER_NAME, SHIP_NAME
from models.interactable import PortableItem, FixedObject, StorageUnit  # Added StorageUnit
from models.ship import Ship
from models.player import Player
from models.chronometer import Chronometer


class GameManager:
    """Central coordinator for game state.

    Manages player data and delegates all ship-related state to the Ship class.
    """

    def __init__(self):
        self.player = None
        self.ship = None
        self.current_location = None
        self.items = {}  # id -> full item dict from tools.json (kept as template source)

        self._load_items()


    def _load_items(self):
        """Load all item definitions from multiple JSON files into self.items."""
        self.items = {}

        files_to_load = [
            "data/tools.json",            # Core portable tools (wrench, bit driver, etc.)
            "data/storage_units.json",    # Fixed storage containers (lockers, cabinets)
            "data/terminals.json",        # Fixed terminals
            "data/consumables.json",      # Wires and future repair/consumable items
            "data/wearables.json",        # Equippable items (EVA suit, tool belt, etc.)
            "data/misc_items.json"        # ID cards and future flavor objects
        ]

        for file_path in files_to_load:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if item["id"] in self.items:
                        raise KeyError(f"Duplicate object ID '{item['id']}' in {file_path}")
                    self.items[item["id"]] = item

    def create_new_game(self, player_name=PLAYER_NAME, ship_name=SHIP_NAME):
        """Create a new game by loading the ship and placing the player."""
        self.player = Player(name=player_name)

        self.ship = Ship.load_from_json(name=ship_name, items=self.items)
        self.current_location = self.ship.rooms[STARTING_ROOM]

        # strict placement
        self._place_player_starting_items()

        # Place portable items procedurally
        self._place_portable_items()

        # Initialize ship chronometer
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

    # Inventory helpers - delegated to Player
    def add_to_inventory(self, item: PortableItem) -> tuple[bool, str]:
        return self.player.add_to_inventory(item)

    def remove_from_inventory(self, item: PortableItem) -> bool:
        return self.player.remove_from_inventory(item)

    def get_player_inventory(self) -> List[PortableItem]:
        return self.player.get_inventory()

    # Cargo helpers — delegated to Ship (already instance-based)
    def add_to_cargo(self, item: PortableItem, room_id: str) -> bool:
        """Add item to the cargo list for the specified room."""
        return self.ship.add_to_cargo(item, room_id)

    def remove_from_cargo(self, item_id: str, room_id: str) -> bool:
        """Remove item from the cargo list for the specified room by ID."""
        return self.ship.remove_from_cargo(item_id, room_id)

    def get_cargo_for_room(self, room_id: str) -> list:
        """Get cargo list for a specific room."""
        return self.ship.get_cargo_for_room(room_id)

    def _place_player_starting_items(self) -> None:
        """
        Load player's guaranteed personal starting items from data/starting_items.json.
        Raises exception on any error (missing file, invalid ID, wrong container type, etc.).
        """
        with open("data/starting_items.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        for item_id in config.get("inventory", []):
            item_data = self.items[item_id]
            item = PortableItem(**{k: v for k, v in item_data.items() if k != "type"})
            self.player.add_to_inventory(item)  # <-- use new method

            # Optional: auto-equip stasis garment if it's in starting inventory
            if item_id == "stasis_garment":
                self.player.equip(item)

        for container_id, item_ids in config.get("containers", {}).items():
            container = next(
                obj for room in self.ship.rooms.values()
                for obj in room.objects if obj.id == container_id
            )
            for item_id in item_ids:
                item_data = self.items[item_id]
                item = PortableItem(**{k: v for k, v in item_data.items() if k != "type"})
                container.add_item(item)

    def _place_portable_items(self) -> None:
        """Procedurally place portable items thematically into fixed storage units."""
        if not self.ship or not self.items:
            return

        random.seed()  # Fresh randomness per new game

        # Room references
        crew_quarters = self.ship.rooms["crew quarters"]
        storage_room = self.ship.rooms["storage room"]
        engineering = self.ship.rooms["engineering"]
        cargo_bay = self.ship.rooms["cargo bay"]
        airlock = self.ship.rooms["airlock"]

        # Fixed storage units by current ID (fail fast if missing)
        crew_locker = next(obj for obj in crew_quarters.objects if obj.id == "crew_quarters_cabinet")
        storage_small = next((obj for obj in storage_room.objects if obj.id == "storage_room_small_cabinet"), None)
        storage_large = next((obj for obj in storage_room.objects if obj.id == "storage_room_large_storage_unit"), None)
        eng_tool_cabinet = next((obj for obj in engineering.objects if obj.id == "engineering_tool_storage_cabinet"), None)
        eng_parts_unit = next((obj for obj in engineering.objects if obj.id == "engineering_large_parts_storage_unit"), None)
        eva_locker = next((obj for obj in cargo_bay.objects if obj.id == "cargo_bay_eva_equipment_locker"), None)
        cargo_large = next((obj for obj in cargo_bay.objects if obj.id == "cargo_bay_large_cabinet"), None)

        # === 2. Uniques (EVA suit, scan tool) with preferred containers ===
        uniques = {"eva_suit": eva_locker, "scan_tool": eng_tool_cabinet}
        for unique_id, preferred_container in uniques.items():
            item_data = self.items[unique_id]
            item = PortableItem(**{k: v for k, v in item_data.items() if k != "type"})
            if preferred_container and preferred_container.add_item(item):
                continue
            # Fallback scatter (kept only for uniques — acceptable variability)
            fallback_room = random.choice([storage_room, engineering, cargo_bay])
            fallback_room.add_object(item)

        # === 3. All other portable tools/wires ===
        portable_ids = [
            item_id for item_id, data in self.items.items()
            if data.get("type") == "portable" and not item_id.startswith("id_card")
            and item_id not in uniques
        ]
        random.shuffle(portable_ids)

        # Weighted placement targets
        placement_targets = []
        if eng_tool_cabinet:
            placement_targets.extend([eng_tool_cabinet] * 6)
        if eng_parts_unit:
            placement_targets.extend([eng_parts_unit] * 3)
        if storage_large:
            placement_targets.extend([storage_large] * 3)
        if cargo_large:
            placement_targets.extend([cargo_large] * 2)
        if storage_small:
            placement_targets.extend([storage_small] * 2)
        if crew_locker:
            placement_targets.append(crew_locker)

        # Fallback rooms
        fallback_rooms = [storage_room, engineering, cargo_bay]

        for item_id in portable_ids:
            item_data = self.items[item_id]
            item = PortableItem(**{k: v for k, v in item_data.items() if k != "type"})

            if placement_targets:
                target = random.choice(placement_targets)
                if not target.add_item(item):
                    random.choice(fallback_rooms).add_object(item)
            else:
                random.choice(fallback_rooms).add_object(item)