from ui.inventory_view import InventoryView
from models.interactable import PortableItem, FixedObject
from door_handler import DoorHandler
from repair_handler import RepairHandler

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
            "pick up": self._handle_take,   # alias, spaces are stripped
            "store": self._handle_store,
            "cargo": self._handle_ship_cargo,     # Restricted to terminals
            "debug cargo": self._handle_debug_cargo,  # TEMPORARY: for testing without terminal
            # NEW: Examine command
            "examine": self._handle_examine,
            "x": self._handle_examine,  # shortcut
            "drop": self._handle_drop,
            "retrieve": self._handle_retrieve,
            # Door actions delegated to DoorHandler for complex flows
            "lock": lambda args: self._handle_door_action("lock", args),
            "unlock": lambda args: self._handle_door_action("unlock", args),
            "repair door panel": self._handle_repair_door_panel,
            "repair door access panel": self._handle_repair_door_panel,
            "repair door": self._handle_repair_door_panel, # shortcut
            # Future commands will be added here, e.g.:
            # "look": self._handle_look,
        }

    def process(self, cmd: str) -> str:
        """Process a single command string and return the response."""
        cmd = cmd.strip().lower()
        if not cmd:
            return ""

        # Special handling for active PIN entry (delegated from DoorHandler)
        if hasattr(self.ship_view, 'pending_pin_callback'):
            pin = cmd.strip()
            self.ship_view.pending_pin_callback(pin)
            return ""  # Response handled inside callback

        # Split into words
        words = cmd.split()

        # Find the longest matching verb from the start of the command
        verb = None
        args = ""
        for i in range(len(words), 0, -1):
            candidate = " ".join(words[:i])
            if candidate in self.commands:
                verb = candidate
                args = " ".join(words[i:])
                break

        if not verb:
            return "I don't understand that command."

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
        prefixes = ["to the ", "to ", "the "]
        normalized_cmd = raw_args
        for prefix in prefixes:
            if normalized_cmd.startswith(prefix):
                normalized_cmd = normalized_cmd[len(prefix):].strip()
                break

        if not normalized_cmd:
            return "Where do you want to go? Try 'go to [place]'."

        current_location = self.game_manager.get_current_location()

        # Find the exit
        next_id = None
        exit_label = None
        matching_exit_data = None
        if normalized_cmd in current_location.exits:
            matching_exit_data = current_location.exits[normalized_cmd]
        else:
            for exit_key, ed in current_location.exits.items():
                if "direction" in ed and normalized_cmd == ed["direction"].lower():
                    matching_exit_data = ed
                    break
                if "shortcuts" in ed and normalized_cmd in [s.lower() for s in ed["shortcuts"]]:
                    matching_exit_data = ed
                    break

        if not matching_exit_data:
            return "You can't go that way."

        # Handle movement — support both secured doors and open archways
        if "door" in matching_exit_data:
            # Secured door — full lock check
            target_door = matching_exit_data["door"]

            if target_door.locked:
                image_path = target_door.images.get("locked", "resources/images/image_missing.png")
                self.ship_view.drawing.set_background_image(image_path)

                panel = target_door.get_panel_for_room(current_location)
                if panel:
                    self.game_manager.last_attempted_panel_id = panel.panel_id
                    self.game_manager.last_attempted_door_id = target_door.id

                return target_door.images.get("locked_description", "The door is locked.")

            # Unlocked door — proceed to move
            target_room = target_door.get_other_room(current_location)
        else:
            # Open archway — no door, no lock check
            target_room_id = matching_exit_data["target"]
            target_room = self.game_manager.ship.rooms[target_room_id]

        next_id = target_room.id
        exit_label = matching_exit_data.get("label", target_room.name)

        # Move normally — refresh UI
        self.ship_view.change_location(next_id)
        display_name = exit_label if exit_label else target_room.name
        return f"You enter {display_name}."

    def _handle_player_inventory(self, args: str) -> str:
        """Show player's personal carried inventory."""
        inventory_view = InventoryView(self.game_manager, is_player=True)
        inventory_view.previous_view = self.ship_view
        self.ship_view.window.show_view(inventory_view)
        return "Opening personal inventory..."

    def _handle_ship_cargo(self, args: str) -> str:
        """Attempt to show ship cargo manifest (normally terminal-only)."""
        if not self._can_access_ship_cargo():
            return "Ship cargo manifest is only accessible from a terminal."
        cargo_view = InventoryView(self.game_manager, is_player=False)
        cargo_view.previous_view = self.ship_view
        self.ship_view.window.show_view(cargo_view)
        return "Opening ship cargo manifest..."

    def _handle_debug_cargo(self, args: str) -> str:
        """TEMP: Force access to ship cargo for testing."""
        current_location = self.game_manager.get_current_location()
        room_id = current_location.id

        # Get cargo for the current room
        cargo_items = self.game_manager.get_cargo_for_room(room_id)

        # The rest stays the same - open the view
        cargo_view = InventoryView(self.game_manager, is_player=False)
        cargo_view.previous_view = self.ship_view
        self.ship_view.window.show_view(cargo_view)

        # Optional: Show room-specific info in the response
        room_name = current_location.name
        return f"DEBUG: Opening {room_name} cargo manifest (terminal bypass)...\nItems: {len(cargo_items)}"

    def _handle_take(self, args: str) -> str:
        """Take a portable item from the current room to player inventory."""
        if not args:
            return "Take what?"

        target_name = args.strip().lower()
        current_location = self.game_manager.get_current_location()
        object_instances = current_location.objects

        for obj in object_instances[:]:  # copy to avoid modification during iteration
            if obj.matches(target_name):
                if isinstance(obj, PortableItem):
                    item_id = obj.id
                    success, message = self.game_manager.add_to_inventory(item_id)
                    if success:
                        object_instances.remove(obj)  # Remove from room
                        self.ship_view.description_renderer.rebuild_description()
                        self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
                        success_messages = [
                            f"You take the {obj.name}.",
                            f"You grab the {obj.name}.",
                            f"You pick up the {obj.name}.",
                            f"The {obj.name} is now in your hands."
                        ]
                        return random.choice(success_messages)
                    else:
                        return message  # e.g., "Too heavy!"
                else:
                    # Fixed object - random failure message
                    failure_messages = [
                        f"The {obj.name} is bolted down. It's not coming loose.",
                        f"It's a part of the bulkhead. You have no luck prying it free.",
                        f"The {obj.name} is an integral part of the ship's systems. Taking it would be a bad idea.",
                        f"You try to lift it, but it's securely mounted. It's not going anywhere.",
                        f"It's fixed in place — you can't take it."
                    ]
                    return random.choice(failure_messages)

        return "There's nothing like that here to take."

    def _handle_store(self, args: str) -> str:
        """Store an item from player inventory to ship cargo."""
        if not args:
            return "Store what?"

        target_name = args.strip().lower()

        # NEW: Get current room and check if valid for storage
        current_location = self.game_manager.get_current_location()
        room_id = current_location.id
        if room_id not in ["storage room", "cargo bay"]:
            return "You can only store items in the storage room or cargo bay."

        inventory_ids = self.game_manager.get_player_inventory()  # list of item IDs (strings)

        for item_id in inventory_ids[:]:
            obj_data = self.game_manager.items.get(item_id)  # lookup full data by ID
            if obj_data and obj_data["type"] == "portable" and (
                target_name == obj_data["name"].lower() or target_name in obj_data.get("keywords", [])
            ):
                # Re-create PortableItem object for cargo (since cargo still expects objects)
                obj_kwargs = {k: v for k, v in obj_data.items() if k != "type"}
                obj = PortableItem(**obj_kwargs)

                # NEW: Pass room_id to add_to_cargo
                if self.game_manager.add_to_cargo(obj, room_id):
                    inventory_ids.remove(item_id)
                    self.ship_view.description_renderer.rebuild_description()
                    self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
                    current_location = self.game_manager.get_current_location()
                    room_name = current_location.name.lower()  # e.g., "storage room" or "cargo bay"
                    return f"You store the {obj_data['name']} in the {room_name}."
                else:
                    return "Failed to store item (cargo full?)."

        return f"You don't have a '{args}' in your inventory."

    def _handle_retrieve(self, args: str) -> str:
        """Retrieve an item from ship cargo to player inventory."""
        if not args:
            return "Retrieve what?"

        # NEW: Check if in a valid storage room
        current_location = self.game_manager.get_current_location()
        room_id = current_location.id
        if room_id not in ["storage room", "cargo bay"]:
            return "You can only retrieve items in the storage room or cargo bay."

        target_name = args.strip().lower()
        cargo_items = self.game_manager.get_cargo_for_room(room_id)

        for obj in cargo_items[:]:
            if obj.matches(target_name) and isinstance(obj, PortableItem):
                item_id = obj.id
                success, message = self.game_manager.add_to_inventory(item_id)
                if success:
                    self.game_manager.remove_from_cargo(item_id, room_id)  # Remove from cargo
                    self.ship_view.description_renderer.rebuild_description()
                    self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
                    success_messages = [
                        f"You retrieve the {obj.name} from the {current_location.name.lower()}.",
                        f"You take the {obj.name} from the {current_location.name.lower()}.",
                        f"You pick up the {obj.name} from the {current_location.name.lower()}.",
                        f"The {obj.name} is now in your hands."
                    ]
                    return random.choice(success_messages)
                else:
                    return message  # e.g., "Too heavy!"

        return f"There's nothing like '{args}' in the {current_location.name.lower()}."

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
                    current_location.objects.append(obj)
                    self.ship_view.description_renderer.rebuild_description()  # Refresh immediately
                    self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()  # NEW: Sync UI texts
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
        object_instances = current_location.objects

        # Check room objects
        for obj in object_instances:
            if obj.matches(target_name):
                return obj.on_examine() if hasattr(obj,
                                                   "on_examine") else f"You see nothing special about the {obj.name}."

        # Check player inventory
        for item_id in self.game_manager.get_player_inventory():
            obj_data = self.game_manager.items.get(item_id)
            if obj_data and (target_name == obj_data["name"].lower() or target_name in obj_data.get("keywords", [])):
                return obj_data.get("examine_text", f"You see nothing special about the {obj_data['name']}.")

        return f"There's nothing called '{args}' here to examine."

    # Helper for access control (expand later with terminal check)
    def _can_access_ship_cargo(self) -> bool:
        """Check if player can access ship cargo (for now, always False)."""
        # Later: check if current room has a terminal or terminal is "unlocked"
        return False

    def _handle_door_action(self, action: str, args: str) -> str:
        """Delegate door lock/unlock to the dedicated handler."""
        door_handler = DoorHandler(self.ship_view)
        return door_handler.handle_door_action(action, args)

    def _handle_repair_door_panel(self, args: str) -> str:
        """Delegate repair of door panels to dedicated handler."""
        repair_handler = RepairHandler(self.ship_view)
        return repair_handler.handle_repair_door_panel(args)