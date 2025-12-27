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
            "pick up": self._handle_take,   # alias, spaces are stripped
            "store": self._handle_store,
            "cargo": self._handle_ship_cargo,     # Restricted to terminals
            "debug cargo": self._handle_debug_cargo,  # TEMPORARY: for testing without terminal
            # NEW: Examine command
            "examine": self._handle_examine,
            "x": self._handle_examine,  # shortcut
            "drop": self._handle_drop,
            "retrieve": self._handle_retrieve,
            "lock": self._handle_lock,
            "unlock": self._handle_unlock,
            # Future commands will be added here, e.g.:
            # "look": self._handle_look,
            # "examine": self._handle_examine,
        }

    def process(self, cmd: str) -> str:
        """Process a single command string and return the response."""
        cmd = cmd.strip().lower()
        if not cmd:
            return ""

        # Split into words
        words = cmd.split()

        # Check for two-word verbs first (e.g., "pick up")
        if len(words) >= 2:
            two_word_verb = f"{words[0]} {words[1]}"
            if two_word_verb in self.commands:
                # Use the two-word verb as key, args = rest of command
                verb = two_word_verb
                args = " ".join(words[2:]) if len(words) > 2 else ""
            else:
                verb = words[0]
                args = " ".join(words[1:]) if len(words) > 1 else ""
        else:
            verb = words[0] if words else ""
            args = ""

        print(f"cmd is {cmd}")
        print(f"verb is {verb} : args is {args}")

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
        if normalized_cmd in current_location["exits"]:
            exit_data = current_location["exits"][normalized_cmd]
            next_id = exit_data["target"]
            exit_label = exit_data.get("label", current_location["name"])
        else:
            for exit_key, ed in current_location["exits"].items():
                if "direction" in ed and normalized_cmd == ed["direction"].lower():
                    exit_data = ed
                    next_id = ed["target"]
                    exit_label = ed.get("label", current_location["name"])
                    break
                if "shortcuts" in ed and normalized_cmd in [s.lower() for s in ed["shortcuts"]]:
                    exit_data = ed
                    next_id = ed["target"]
                    exit_label = ed.get("label", current_location["name"])
                    break

        if not next_id:
            return "You can't go that way."

        # NEW: Check door status from door_status.json
        current_room_id = current_location["id"]
        for door in self.game_manager.door_status:
            if set(door["rooms"]) == {current_room_id, next_id}:
                if door["locked"]:
                    # Show locked door image
                    image_path = door.get("locked_image", "resources/images/locked_door_default.png")
                    self.ship_view.drawing.set_background_image(image_path)

                    # Find the correct panel ID for this side
                    panel_id = None
                    for panel_data in door.get("panel_ids", []):
                        if panel_data["side"] == current_room_id:
                            panel_id = panel_data["id"]
                            break

                    if panel_id:
                        # Set as active immediately so use panel works right now
                        self.game_manager.last_attempted_panel_id = panel_id
                        self.game_manager.last_attempted_door_id = door["id"]
                    else:
                        print("DEBUG: No panel found for current side — this shouldn't happen")

                    return door["locked_description"]
                break  # door found and not locked, proceed

        # Move normally
        self.ship_view.change_location(next_id)
        display_name = exit_label if exit_label else self.game_manager.get_current_location()["name"]
        return f"You enter {display_name}."

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

    def _handle_debug_cargo(self, args: str) -> str:
        """TEMP: Force access to ship cargo for testing."""
        current_location = self.game_manager.get_current_location()
        room_id = current_location["id"]

        # Get cargo for the current room
        cargo_items = self.game_manager.get_cargo_for_room(room_id)

        # The rest stays the same - open the view
        cargo_view = InventoryView(self.game_manager, is_player=False)
        cargo_view.previous_view = self.ship_view
        self.ship_view.window.show_view(cargo_view)

        # Optional: Show room-specific info in the response
        room_name = current_location["name"]
        return f"DEBUG: Opening {room_name} cargo manifest (terminal bypass)...\nItems: {len(cargo_items)}"

    # NEW: Take from room → player inventory
    def _handle_take(self, args: str) -> str:
        """Take a portable item from the current room to player inventory."""
        if not args:
            return "Take what?"

        target_name = args.strip().lower()
        current_location = self.game_manager.get_current_location()
        object_instances = current_location.get("objects", [])

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

    # NEW: Store from player → ship cargo
    def _handle_store(self, args: str) -> str:
        """Store an item from player inventory to ship cargo."""
        if not args:
            return "Store what?"

        target_name = args.strip().lower()

        # NEW: Get current room and check if valid for storage
        current_location = self.game_manager.get_current_location()
        room_id = current_location["id"]
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
                    room_name = current_location["name"].lower()  # e.g., "storage room" or "cargo bay"
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
        room_id = current_location["id"]
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
                        f"You retrieve the {obj.name} from the {current_location['name'].lower()}.",
                        f"You take the {obj.name} from the {current_location['name'].lower()}.",
                        f"You pick up the {obj.name} from the {current_location['name'].lower()}.",
                        f"The {obj.name} is now in your hands."
                    ]
                    return random.choice(success_messages)
                else:
                    return message  # e.g., "Too heavy!"

        return f"There's nothing like '{args}' in the {current_location['name'].lower()}."

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

    def _handle_unlock(self, args: str) -> str:
        """Unlock a door by targeting the room or direction it leads to.
        Example: 'unlock cargo bay' or 'unlock cargo'.
        """
        if not args:
            return "Unlock what? Try 'unlock cargo bay' or 'unlock [direction]'."

        target = args.strip().lower()
        current_location = self.game_manager.get_current_location()
        current_room_id = current_location["id"]

        # Find the target exit/door
        next_id = None
        exit_label = None
        exit_data = None
        for exit_key, ed in current_location["exits"].items():
            if target == exit_key.lower() or target in [s.lower() for s in ed.get("shortcuts", [])]:
                exit_data = ed
                next_id = ed["target"]
                exit_label = ed.get("label", current_location["name"])
                break

        if not next_id:
            return f"No door leads to '{target}'. Try a valid room or direction."

        # Find the matching door connection
        matching_door = None
        for door in self.game_manager.door_status:
            if set(door["rooms"]) == {current_room_id, next_id}:
                matching_door = door
                break

        if not matching_door:
            return "No matching door found."

        if not matching_door["locked"]:
            return "That hatch is already unlocked."

        # Find the panel on the current side
        panel_id = None
        for panel_data in matching_door.get("panel_ids", []):
            if panel_data["side"] == current_room_id:
                panel_id = panel_data["id"]
                break

        if not panel_id:
            return "No panel on this side of the door."

        panel = self.game_manager.security_panels.get(panel_id)
        if not panel:
            return f"Panel '{panel_id}' not found."

        # Attempt to unlock
        success, message = panel.attempt_unlock(self.game_manager.get_player_inventory())

        if success:
            # Unlock the door
            matching_door["locked"] = False
            # Show open hatch image
            image_path = matching_door.get("open_image", "resources/images/open_hatch.png")
            self.ship_view.drawing.set_background_image(image_path)
            # TODO: Save door_status.json if persistent (in-memory for now)

            return f"{message} The hatch to {exit_label or next_id} is now unlocked."
        else:
            return message

    def _handle_lock(self, args: str) -> str:
        """Lock a door by targeting the room or direction it leads to.
        Example: 'lock cargo bay' or 'lock cargo'.
        """
        if not args:
            return "Lock what? Try 'lock cargo bay' or 'lock [direction]'."

        target = args.strip().lower()
        current_location = self.game_manager.get_current_location()
        current_room_id = current_location["id"]

        # Find the target exit/door
        next_id = None
        exit_label = None
        exit_data = None
        for exit_key, ed in current_location["exits"].items():
            if target == exit_key.lower() or target in [s.lower() for s in ed.get("shortcuts", [])]:
                exit_data = ed
                next_id = ed["target"]
                exit_label = ed.get("label", current_location["name"])
                break

        if not next_id:
            return f"No door leads to '{target}'. Try a valid room or direction."

        # Find the matching door connection
        matching_door = None
        for door in self.game_manager.door_status:
            if set(door["rooms"]) == {current_room_id, next_id}:
                matching_door = door
                break

        if not matching_door:
            return "No matching door found."

        if matching_door["locked"]:
            return "That hatch is already locked."

        # Find the panel on the current side
        panel_id = None
        for panel_data in matching_door.get("panel_ids", []):
            if panel_data["side"] == current_room_id:
                panel_id = panel_data["id"]
                break

        if not panel_id:
            return "No panel on this side of the door."

        panel = self.game_manager.security_panels.get(panel_id)
        if not panel:
            return f"Panel '{panel_id}' not found."

        # Attempt to lock (same security check as unlock for now)
        success, message = panel.attempt_lock(self.game_manager.get_player_inventory())

        if success:
            # Lock the door
            matching_door["locked"] = True
            # Show locked hatch image
            image_path = matching_door.get("locked_image", "resources/images/closed_hatch.png")
            self.ship_view.drawing.set_background_image(image_path)
            # TODO: Save door_status.json if persistent (in-memory for now)

            return f"{message} The hatch to {exit_label or next_id} is now locked."
        else:
            return message