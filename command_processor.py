# command_processor.py
from ui.inventory_view import InventoryView
from models.interactable import PortableItem, FixedObject, StorageUnit  # Added StorageUnit
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
            # Storage unit commands — grouped for clarity (multi-word verbs work due to longest-match logic)
            "open": self._handle_open,
            "close": self._handle_close,
            "look in": self._handle_look_in,
            "take from": self._handle_take_from,
            "put in": self._handle_put_in,

            # Core movement and interaction
            "quit": self._handle_quit,
            "exit": self._handle_quit,
            "go": self._handle_move,
            "enter": self._handle_move,
            "move": self._handle_move,
            "look": self._handle_look,
            "l": self._handle_look,

            # Inventory and object manipulation
            "inventory": self._handle_player_inventory,
            "i": self._handle_player_inventory,
            "take": self._handle_take,
            "pick up": self._handle_take,
            "drop": self._handle_drop,
            "examine": self._handle_examine,
            "x": self._handle_examine,

            # Door and repair
            "lock": lambda args: self._handle_door_action("lock", args),
            "unlock": lambda args: self._handle_door_action("unlock", args),
            "repair door panel": self._handle_repair_door_panel,
            "repair door access panel": self._handle_repair_door_panel,
            "repair access panel": self._handle_repair_door_panel,
            "repair door": self._handle_repair_door_panel,

            # Equip commands
            "wear": self._handle_wear,
            "put on": self._handle_wear,
            "equip": self._handle_wear,
            "remove": self._handle_unequip,
            "take off": self._handle_unequip,
            "unequip": self._handle_unequip,
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

        # Special handling for preposition-based container commands
        if " from " in cmd and cmd.startswith("take "):
            # 'take wrench from locker'
            parts = cmd.split(" from ", 1)
            item_part = parts[0][5:].strip()  # remove "take "
            container_part = parts[1].strip()
            return self._handle_take_from(f"{item_part} from {container_part}")

        if " in " in cmd and cmd.startswith("put "):
            # 'put wrench in locker'
            parts = cmd.split(" in ", 1)
            item_part = parts[0][4:].strip()  # remove "put "
            container_part = parts[1].strip()
            return self._handle_put_in(f"{item_part} in {container_part}")

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
        return "Quit"

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
        inventory_view = InventoryView(self.game_manager)
        inventory_view.previous_view = self.ship_view
        self.ship_view.window.show_view(inventory_view)
        return "Opening personal inventory..."

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
                    success, message = self.game_manager.add_to_inventory(obj)
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

    def _handle_drop(self, args: str) -> str:
        """Drop an item from player inventory back to the current room."""
        if not args:
            return "Drop what?"

        target_name = args.strip().lower()
        inventory = self.game_manager.get_player_inventory()

        for item in inventory[:]:
            if item.matches(target_name):
                if self.game_manager.remove_from_inventory(item):
                    current_location = self.game_manager.get_current_location()
                    current_location.objects.append(item)
                    self.ship_view.description_renderer.rebuild_description()  # Refresh immediately
                    self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
                    drop_messages = [
                        f"You drop the {item.name}.",
                        f"You put down the {item.name}.",
                        f"You leave the {item.name}.",
                        f"The {item.name} is now on the floor."
                    ]
                    return random.choice(drop_messages)
        return f"You don't have a '{args}' to drop."

    def _handle_wear(self, args: str) -> str:
        """Wear/equip an item from inventory."""
        if not args:
            return "Wear/equip what? (e.g., 'wear eva suit')"

        target_name = args.strip().lower()
        inventory = self.game_manager.get_player_inventory()

        for item in inventory:
            if item.matches(target_name):
                if not hasattr(item, "equip_slot") or not item.equip_slot:
                    return f"You can't wear the {item.name}."

                success, message = self.game_manager.player.equip(item)
                if success:
                    # Optional: refresh description if equipped items will be shown there later
                    self.ship_view.description_renderer.rebuild_description()
                    self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
                return message

        return f"You don't have a '{args}' to wear."

    def _handle_unequip(self, args: str) -> str:
        """Remove/unequip item from a slot."""
        if not args:
            return "Remove/unequip what? (e.g., 'remove eva suit' or 'unequip head')"

        target = args.strip().lower()
        player = self.game_manager.player
        current_location = self.game_manager.get_current_location()

        # Try to match by item name first (most common)
        for slot_name, item in [
            ("head", self.game_manager.player.head_slot),
            ("body", self.game_manager.player.body_slot),
            ("torso", self.game_manager.player.torso_slot),
            ("waist", self.game_manager.player.waist_slot),
            ("feet", self.game_manager.player.feet_slot),
        ]:
            if item and item.matches(target):
                success, message = player.unequip(slot_name, current_room=current_location)
                if success:
                    # Refresh room description (item now on floor)
                    self.ship_view.description_renderer.rebuild_description()
                    self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
                return message

        return f"Nothing matching '{args}' is currently equipped."

    def _handle_examine(self, args: str) -> str:
        """Examine an object in the current room or inventory."""
        if not args:
            return "Examine what?"

        target_name = args.strip().lower()
        current_location = self.game_manager.get_current_location()

        # Check room objects
        for obj in current_location.objects:
            if obj.matches(target_name):
                return obj.on_examine()

        # Check player inventory (now live instances)
        for item in self.game_manager.get_player_inventory():
            if item.matches(target_name):
                return item.on_examine()

        return f"There's nothing called '{args}' here to examine."

    def _find_storage_unit(self, target_name: str):
        """Helper: find a StorageUnit in current room by keyword match."""
        current_location = self.game_manager.get_current_location()
        for obj in current_location.objects:
            if isinstance(obj, StorageUnit) and obj.matches(target_name):
                return obj
        return None

    def _handle_open(self, args: str) -> str:
        """Open a storage unit and automatically reveal its contents."""
        if not args:
            return "Open what?"

        target_name = args.strip().lower()
        unit = self._find_storage_unit(target_name)
        if not unit:
            return f"There's no {args} here to open."

        lines = []

        if unit.is_open:
            lines.append(f"The {unit.name.lower()} is already open.")
        else:
            unit.is_open = True
            lines.append(f"You open the {unit.name.lower()}.")
            if hasattr(unit, "open_description") and unit.open_description:
                lines.append(unit.open_description)

        # Refresh UI
        self.ship_view.description_renderer.rebuild_description()
        self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()

        return "\n".join(lines)

    def _handle_close(self, args: str) -> str:
        """Close a storage unit."""
        if not args:
            return "Close what?"

        target_name = args.strip().lower()
        unit = self._find_storage_unit(target_name)
        if not unit:
            return f"There's no {args} here to close."

        if not unit.is_open:
            return f"The {unit.name.lower()} is already closed."

        unit.is_open = False
        self.ship_view.description_renderer.rebuild_description()
        self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
        return f"You close the {unit.name.lower()}."

    def _handle_look_in(self, args: str) -> str:
        """Look inside an open storage unit."""
        if not args:
            return "Look in what?"

        target_name = args.strip().lower()
        unit = self._find_storage_unit(target_name)
        if not unit:
            return f"There's no {args} here to look in."

        if not unit.is_open:
            return f"The {unit.name.lower()} is closed."

        if not unit.contents:
            return f"The {unit.name.lower()} is empty."

        response = f"Inside the {unit.name.lower()} you see:\n"
        for item in unit.contents:
            response += f"• {item.name}\n"
        return response.strip()

    def _handle_take_from(self, args: str) -> str:
        """Take an item from a storage unit: 'take wrench from locker'"""
        if not args:
            return "Take what from where?"

        parts = args.lower().split(" from ")
        if len(parts) != 2:
            return "Take what from where? Try 'take [item] from [locker]'."

        item_name = parts[0].strip()
        container_name = parts[1].strip()
        unit = self._find_storage_unit(container_name)
        if not unit:
            return f"There's no {container_name} here."

        if not unit.is_open:
            return f"The {unit.name.lower()} is closed."

        target_item = None
        for item in unit.contents:
            if item.matches(item_name):
                target_item = item
                break

        if not target_item:
            return f"There's no {item_name} in the {unit.name.lower()}."

        success, message = self.game_manager.add_to_inventory(target_item)
        if success:
            unit.remove_item(target_item)
            self.ship_view.description_renderer.rebuild_description()
            self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
            return f"You take the {target_item.name} from the {unit.name.lower()}."
        else:
            return message  # e.g., too heavy

    def _handle_put_in(self, args: str) -> str:
        """Put an item into a storage unit: 'put wrench in locker'"""
        if not args:
            return "Put what in where?"

        parts = args.lower().split(" in ")
        if len(parts) != 2:
            return "Put what in where? Try 'put [item] in [locker]'."

        item_name = parts[0].strip()
        container_name = parts[1].strip()

        unit = self._find_storage_unit(container_name)
        if not unit:
            return f"There's no {container_name} here."

        if not unit.is_open:
            return f"The {unit.name.lower()} is closed."

        inventory = self.game_manager.get_player_inventory()
        target_item = None
        for item in inventory:
            if item.matches(item_name):
                target_item = item
                break

        if not target_item:
            return f"You don't have a {item_name}."

        if not unit.add_item(target_item):
            return f"The {unit.name.lower()} is too full to hold the {target_item.name}."

        self.game_manager.remove_from_inventory(target_item)
        self.ship_view.description_renderer.rebuild_description()
        self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
        return f"You put the {target_item.name} in the {unit.name.lower()}."

    def _handle_door_action(self, action: str, args: str) -> str:
        """Delegate door lock/unlock to the dedicated handler."""
        door_handler = DoorHandler(self.ship_view)
        return door_handler.handle_door_action(action, args)

    def _handle_repair_door_panel(self, args: str) -> str:
        """Delegate repair of door panels to dedicated handler."""
        repair_handler = RepairHandler(self.ship_view)
        return repair_handler.handle_repair_door_panel(args)

    def _handle_look(self, args: str) -> str:
        """Survey the current room — reset background and give flavor text.
        Ignores any arguments for a more natural, forgiving feel."""
        current_location = self.game_manager.get_current_location()
        background_image = current_location.background or "resources/images/image_missing.png"
        self.ship_view.drawing.set_background_image(background_image)

        # Refresh description to ensure consistency
        self.ship_view.description_renderer.rebuild_description()
        self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()

        messages = [
            "You survey your surroundings.",
            "You take a moment to look around.",
            "You scan the room carefully.",
            "You observe your environment."
        ]
        message = random.choice(messages)

        return message