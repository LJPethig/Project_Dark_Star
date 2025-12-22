# command_processor.py

class CommandProcessor:
    """Minimal command processor that handles movement and quit/exit."""

    def __init__(self, ship_view):
        self.ship_view = ship_view
        self.game_manager = ship_view.game_manager
        # No self.current_location here — we read live from ship_view

    def process(self, cmd: str) -> str:
        """Process a single command string and return the response."""
        cmd = cmd.strip().lower()
        if not cmd:
            return ""

        # Handle quit/exit first
        if cmd in ("quit", "exit"):
            return "Thanks for playing Project Dark Star. Goodbye!"

        # Normalize for movement prefixes
        normalized_cmd = cmd
        if normalized_cmd.startswith(("enter ", "go ", "go to ", "move ")):
            normalized_cmd = normalized_cmd.split(" ", 2)[-1].strip()

        # Get current location live from the view (always up-to-date)
        current_location = self.ship_view.current_location

        # Try direct exit name (e.g., "galley")
        next_id = None
        if normalized_cmd in current_location["exits"]:
            exit_data = current_location["exits"][normalized_cmd]
            next_id = exit_data["target"]
        else:
            # Try direction alias (e.g., "forward")
            for exit_key, exit_data in current_location["exits"].items():
                if "direction" in exit_data and normalized_cmd == exit_data["direction"].lower():
                    next_id = exit_data["target"]
                    break

        if next_id:
            self.ship_view.change_location(next_id)
            # Use live reference for the response
            return f"You enter the {self.ship_view.current_location['name']}."

        # If we got here and it's not quit → movement attempt failed
        if cmd:
            return "You can't go that way."

        return ""