# game_manager.py
import json
import random
from typing import List
from constants import STARTING_ROOM, PLAYER_NAME, SHIP_NAME
from models.interactable import PortableItem, FixedObject, StorageUnit  # Added StorageUnit
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
        self.items = {}  # id -> full item dict from objects.json (kept as template source)

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
            "inventory": []  # NOW: list of live PortableItem instances
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

    # Instance-based inventory helpers
    def add_to_inventory(self, item: PortableItem) -> tuple[bool, str]:
        """Add a live PortableItem instance to player inventory, checking mass."""
        if not isinstance(item, PortableItem):
            return False, "You can't take that."

        mass = getattr(item, "mass", 0.0)
        if self.player_carry_mass + mass > self.player_max_carry_mass:
            remaining = self.player_max_carry_mass - self.player_carry_mass
            return False, f"Too heavy! You can carry {remaining:.1f} kg more."

        self.player["inventory"].append(item)
        self.player_carry_mass += mass
        return True, f"You take the {item.name}."

    def remove_from_inventory(self, item: PortableItem) -> bool:
        """Remove a live instance from inventory and update mass."""
        if item in self.player["inventory"]:
            mass = getattr(item, "mass", 0.0)
            self.player["inventory"].remove(item)
            self.player_carry_mass -= mass
            return True
        return False

    def get_player_inventory(self) -> List[PortableItem]:
        """Return the player's personal inventory (list of live instances)."""
        return self.player["inventory"]

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

        # Fixed storage units by current ID
        crew_locker = next((obj for obj in crew_quarters.objects if obj.id == "crew_quarters_cabinet"), None)
        storage_small = next((obj for obj in storage_room.objects if obj.id == "storage_room_small_cabinet"), None)
        storage_large = next((obj for obj in storage_room.objects if obj.id == "storage_room_large_storage_unit"), None)
        eng_tool_cabinet = next((obj for obj in engineering.objects if obj.id == "engineering_tool_storage_cabinet"), None)
        eng_parts_unit = next((obj for obj in engineering.objects if obj.id == "engineering_large_parts_storage_unit"), None)
        eva_locker = next((obj for obj in cargo_bay.objects if obj.id == "cargo_bay_eva_equipment_locker"), None)  # Note: in cargo bay now
        cargo_large = next((obj for obj in cargo_bay.objects if obj.id == "cargo_bay_large_cabinet"), None)

        # === 1. Guaranteed undamaged high-sec card ===
        high_sec_data = self.items["id_card_high_sec"]
        high_sec_item = PortableItem(**{k: v for k, v in high_sec_data.items() if k != "type"})
        if crew_locker and crew_locker.add_item(high_sec_item):
            pass
        else:
            crew_quarters.add_object(high_sec_item)  # fallback

        # === 2. Random ID cards in key locations ===
        id_card_ids = ["id_card_low_sec", "id_card_high_sec", "id_card_high_sec_damaged"]
        for room, container in [
            (crew_quarters, crew_locker),
            (engineering, eng_parts_unit),
            (storage_room, storage_large)
        ]:
            card_id = random.choice(id_card_ids)
            card_data = self.items[card_id]
            card = PortableItem(**{k: v for k, v in card_data.items() if k != "type"})
            if container and container.add_item(card):
                pass
            else:
                room.add_object(card)

        # === 3. Uniques (EVA suit, scan tool) ===
        uniques = {"eva_suit": eva_locker, "scan_tool": eng_tool_cabinet}
        for unique_id, preferred_container in uniques.items():
            item_data = self.items[unique_id]
            item = PortableItem(**{k: v for k, v in item_data.items() if k != "type"})
            if preferred_container and preferred_container.add_item(item):
                continue
            # Fallback scatter
            fallback_room = random.choice([storage_room, engineering, cargo_bay])
            fallback_room.add_object(item)

        # === 4. All other portable tools/wires ===
        portable_ids = [
            item_id for item_id, data in self.items.items()
            if data.get("type") == "portable" and not item_id.startswith("id_card")
            and item_id not in uniques
        ]
        random.shuffle(portable_ids)

        # Weighted placement targets — bias toward thematic containers
        placement_targets = []
        if eng_tool_cabinet:
            placement_targets.extend([eng_tool_cabinet] * 6)     # strong bias: tools go here
        if eng_parts_unit:
            placement_targets.extend([eng_parts_unit] * 3)
        if storage_large:
            placement_targets.extend([storage_large] * 3)
        if cargo_large:
            placement_targets.extend([cargo_large] * 2)
        if storage_small:
            placement_targets.extend([storage_small] * 2)
        if crew_locker:
            placement_targets.append(crew_locker)  # rare personal items

        # Fallback rooms if no containers available (safety)
        fallback_rooms = [storage_room, engineering, cargo_bay]

        for item_id in portable_ids:
            item_data = self.items[item_id]
            item = PortableItem(**{k: v for k, v in item_data.items() if k != "type"})

            if placement_targets:
                target = random.choice(placement_targets)
                if not target.add_item(item):
                    # Full → fall back to loose on floor
                    random.choice(fallback_rooms).add_object(item)
            else:
                # No containers at all → place loose
                random.choice(fallback_rooms).add_object(item)