# command_processor.py
from ui.inventory_view import InventoryView
from models.interactable import PortableItem, FixedObject
import random

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
            # NEW: Inventory & cargo commands
            "inventory": self._handle_player_inventory,
            "i": self._handle_player_inventory,  # shortcut
            "take": self._handle_take,
            "pick_up": self._handle_take,   # alias, spaces are stripped
            "store": self._handle_store,
            "cargo": self._handle_ship_cargo,     # Restricted to terminals
            "debug_cargo": self._handle_debug_cargo,  # TEMPORARY: for testing without terminal
            # NEW: Examine command
            "examine": self._handle_examine,
            "x": self._handle_examine,  # shortcut
            "drop": self._handle_drop,
            # Future commands will be added here, e.g.:
            # "look": self._handle_look,
            # "examine": self._handle_examine,
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
        exit_label = None  # NEW: to store the label for the response
        if normalized_cmd in current_location["exits"]:
            exit_data = current_location["exits"][normalized_cmd]
            next_id = exit_data["target"]
            exit_label = exit_data.get("label", current_location["name"])  # Use label if present
        else:
            # Try direction alias (e.g., "forward")
            for exit_key, exit_data in current_location["exits"].items():
                if "direction" in exit_data and normalized_cmd == exit_data["direction"].lower():
                    next_id = exit_data["target"]
                    exit_label = exit_data.get("label", current_location["name"])  # Use label if present
                    break

            # NEW: Try shortcuts (e.g., "H2", "sub corridor")
            if next_id is None:
                for exit_key, exit_data in current_location["exits"].items():
                    if "shortcuts" in exit_data:
                        if normalized_cmd in [s.lower() for s in exit_data["shortcuts"]]:
                            next_id = exit_data["target"]
                            exit_label = exit_data.get("label", current_location["name"])
                            break

        if next_id:
            self.ship_view.change_location(next_id)
            # NEW: Use label for immersive response (fallback to room name if no label)
            display_name = exit_label if exit_label else self.game_manager.get_current_location()["name"]
            return f"You enter {display_name}."

        # Movement attempt failed
        return "You can't go that way."

    # NEW: Player inventory
    def _handle_player_inventory(self, args: str) -> str:
        """Show player's personal carried inventory."""
        inventory_view = InventoryView(self.game_manager, is_player=True)
        inventory_view.previous_view = self.ship_view
        self.ship_view.window.show_view(inventory_view)
        return "Opening personal inventory..."

    # NEW: Ship cargo (restricted)
    def _handle_ship_cargo(self, args: str) -> str:
        """Attempt to show ship cargo manifest (normally terminal-only)."""
        if not self._can_access_ship_cargo():
            return "Ship cargo manifest is only accessible from a terminal."
        cargo_view = InventoryView(self.game_manager, is_player=False)
        cargo_view.previous_view = self.ship_view
        self.ship_view.window.show_view(cargo_view)
        return "Opening ship cargo manifest..."

    # TEMPORARY debug command
    def _handle_debug_cargo(self, args: str) -> str:
        """TEMP: Force access to ship cargo for testing."""
        cargo_view = InventoryView(self.game_manager, is_player=False)
        cargo_view.previous_view = self.ship_view
        self.ship_view.window.show_view(cargo_view)
        return "DEBUG: Opening ship cargo manifest (terminal bypass)..."

    # NEW: Take from room → player inventory
    def _handle_take(self, args: str) -> str:
        """Take a portable item from the current room to player inventory."""
        if not args:
            return "Take what?"

        target_name = args.strip().lower()
        current_location = self.game_manager.get_current_location()
        object_instances = current_location.get("objects", [])

        for obj in object_instances[:]:  # copy to avoid modification during iteration
            if obj.matches(target_name) and isinstance(obj, PortableItem):
                item_id = obj.id  # Use the item's ID
                success, message = self.game_manager.add_to_inventory(item_id)
                if success:
                    object_instances.remove(obj)  # Remove from room
                    self.ship_view._rebuild_description()  # Refresh description immediately
                    success_messages = [
                        f"You take the {obj.name}.",
                        f"You grab the {obj.name}.",
                        f"You pick up the {obj.name}.",
                        f"The {obj.name} is now in your hands."
                    ]
                    return random.choice(success_messages)
                else:
                    return message  # e.g., "Too heavy!"

        return "There's nothing like that here to take."

    # NEW: Store from player → ship cargo
    def _handle_store(self, args: str) -> str:
        """Store an item from player inventory to ship cargo."""
        if not args:
            return "Store what?"

        target_name = args.strip().lower()
        inventory = self.game_manager.get_player_inventory()

        for obj in inventory[:]:
            if obj.matches(target_name) and isinstance(obj, PortableItem):
                if self.game_manager.add_to_cargo(obj):
                    inventory.remove(obj)
                    self.ship_view._rebuild_description()  # Refresh description immediately
                    return f"You store the {obj.name} in the cargo hold."
                else:
                    return "Failed to store item (cargo full?)."

        return f"You don't have a '{args}' in your inventory."

    def _handle_drop(self, args: str) -> str:
        """Drop an item from player inventory back to the current room."""
        if not args:
            return "Drop what?"

        target_name = args.strip().lower()
        inventory_ids = self.game_manager.get_player_inventory()

        for item_id in inventory_ids[:]:
            obj_data = self.game_manager.items.get(item_id)
            if obj_data and (target_name == obj_data["name"].lower() or target_name in obj_data.get("keywords", [])):
                if self.game_manager.remove_from_inventory(item_id):
                    current_location = self.game_manager.get_current_location()
                    # Re-instantiate the object for the room
                    obj_type = obj_data["type"]
                    obj_kwargs = {k: v for k, v in obj_data.items() if k != "type"}
                    if obj_type == "portable":
                        obj = PortableItem(**obj_kwargs)
                    else:
                        obj = FixedObject(**obj_kwargs)
                    current_location["objects"].append(obj)
                    self.ship_view._rebuild_description()  # Refresh immediately
                    drop_messages = [
                        f"You drop the {obj_data['name']}.",
                        f"You put down the {obj_data['name']}.",
                        f"You leave the {obj_data['name']}.",
                        f"The {obj_data['name']} is now on the floor."
                    ]
                    return random.choice(drop_messages)
        return f"You don't have a '{args}' to drop."

    def _handle_examine(self, args: str) -> str:
        """Examine an object in the current room or inventory."""
        if not args:
            return "Examine what?"

        target_name = args.strip().lower()
        current_location = self.game_manager.get_current_location()
        object_instances = current_location.get("objects", [])

        # Check room objects
        for obj in object_instances:
            if obj.matches(target_name):
                return obj.on_examine() if hasattr(obj,
                                                   "on_examine") else f"You see nothing special about the {obj.name}."

        # Check player inventory
        for item_id in self.game_manager.get_player_inventory_ids():
            obj_data = self.game_manager.items.get(item_id)
            if obj_data and (target_name == obj_data["name"].lower() or target_name in obj_data.get("keywords", [])):
                return obj_data.get("examine_text", f"You see nothing special about the {obj_data['name']}.")

        return f"There's nothing called '{args}' here to examine."

    # Helper for access control (expand later with terminal check)
    def _can_access_ship_cargo(self) -> bool:
        """Check if player can access ship cargo (for now, always False)."""
        # Later: check if current room has a terminal or terminal is "unlocked"
        return False