# game_manager.py
import json

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
            "skills": skills
        }

        self.ship = {
            "name": ship_name,
            "rooms": self._load_ship_rooms()
        }

        # Player always starts in quarters after waking up
        self.current_location = self.ship["rooms"]["quarters"]

    def _load_ship_rooms(self) -> dict:
        """Load ship room data from JSON and return a dict keyed by room ID."""
        with open("data/ship_rooms.json", "r") as f:
            rooms_data = json.load(f)

        rooms = {}
        for room in rooms_data:
            rooms[room["id"]] = room
        return rooms

    def get_current_location(self) -> dict:
        """Return the current location data."""
        return self.current_location