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
            "inventory": []  # NEW: empty list for PortableItems
        }

        self.ship = {
            "name": ship_name,
            "rooms": self._load_ship_rooms()
        }

        # Player always starts in quarters after waking up
        self.current_location = self.ship["rooms"]["crew quarters"]

    def _load_ship_rooms(self) -> dict:
        """Load ship room data from JSON and return a dict keyed by room ID."""
        with open("data/ship_rooms.json", "r") as f:
            rooms_data = json.load(f)

        rooms = {}
        for room_data in rooms_data:
            room_id = room_data["id"]

            # Convert raw "objects" list into Interactable instances
            objects = []
            for obj_data in room_data.get("objects", []):
                obj_type = obj_data.get("type", "portable")  # Default to portable if missing

                # IMPORTANT: We remove the "type" key before passing to the dataclass.
                # "type" is just control metadata in JSON telling us which class to use.
                # It is NOT a field the PortableItem or FixedObject classes expect.
                # If we pass it, Python will raise TypeError: unexpected keyword argument 'type'.
                # So we create a clean copy without "type".
                obj_kwargs = {k: v for k, v in obj_data.items() if k != "type"}

                if obj_type == "portable":
                    obj = PortableItem(**obj_kwargs)
                elif obj_type == "fixed":
                    obj = FixedObject(**obj_kwargs)
                else:
                    print(f"Warning: Unknown object type '{obj_type}' in room {room_id}")
                    continue

                objects.append(obj)

            room_data["objects"] = objects  # Replace raw list with instantiated objects
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

    # NEW: Inventory helpers
    def add_to_inventory(self, item: PortableItem) -> None:
        """Add a takeable item to the player's inventory."""
        if isinstance(item, PortableItem) and item.takeable:
            self.player["inventory"].append(item)
        else:
            print(f"Warning: Tried to add non-takeable item {item.id} to inventory")

    def remove_from_inventory(self, item_id: str) -> bool:
        """Remove an item from inventory by ID. Returns True if successful."""
        for i, item in enumerate(self.player["inventory"]):
            if item.id == item_id:
                self.player["inventory"].pop(i)
                return True
        return False