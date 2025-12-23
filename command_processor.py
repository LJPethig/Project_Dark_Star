# command_processor.py

class CommandProcessor:
    """Command processor that handles player input using a registry pattern."""

    def __init__(self, ship_view):
        self.ship_view = ship_view
        self.game_manager = ship_view.game_manager

        # Command registry: verb → handler function
        # Handlers receive the full remaining args (after the verb)
        self.commands = {
            "quit": self._handle_quit,
            "exit": self._handle_quit,  # alias for quit
            "go": self._handle_move,
            "enter": self._handle_move,  # alias
            "move": self._handle_move,   # alias
            # Future commands will be added here, e.g.:
            # "look": self._handle_look,
            # "inventory": self._handle_inventory,
            # "take": self._handle_take,
        }

    def process(self, cmd: str) -> str:
        """Process a single command string and return the response."""
        cmd = cmd.strip().lower()
        if not cmd:
            return ""

        # Split into verb + arguments
        parts = cmd.split(maxsplit=1)
        verb = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        # Look up and execute handler
        handler = self.commands.get(verb)
        if handler:
            return handler(args)

        # No matching command → unknown
        return f"I don't understand '{cmd}'. Try 'help' for available commands."

    def _handle_quit(self, args: str) -> str:
        """Handle quit/exit commands."""
        return "Thanks for playing Project Dark Star. Goodbye!"

    def _handle_move(self, args: str) -> str:
        """Handle movement commands (go, enter, move) with natural language support."""
        # Get the raw argument string
        raw_args = args.strip().lower()

        # Remove common prefixes like "to", "the", "to the"
        # This makes "go to galley", "go to the galley", "enter the galley" all normalize to "galley"
        prefixes = ["to the ", "to ", "the "]
        normalized_cmd = raw_args
        for prefix in prefixes:
            if normalized_cmd.startswith(prefix):
                normalized_cmd = normalized_cmd[len(prefix):].strip()
                break  # Only remove the first matching prefix

        # If nothing left after stripping (e.g., "go to"), treat as invalid
        if not normalized_cmd:
            return "Where do you want to go? Try 'go to [place]'."

        # Now use the normalized command for matching
        current_location = self.game_manager.get_current_location()

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
            return f"You enter the {self.game_manager.get_current_location()['name']}."

        # Movement attempt failed
        return "You can't go that way."