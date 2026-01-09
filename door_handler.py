# door_handler.py
"""
Dedicated handler for all door-related commands and security panel interactions.
Fully extracted from command_processor.py — improves readability and extensibility.
Transient PIN state is managed via ShipView attributes (simple and effective for current scope).
"""

from models.security_panel import SecurityLevel
from models.interactable import PortableItem
from constants import CARD_SWIPE_WAIT


class DoorHandler:
    """
    Handles complex door lock/unlock logic, security panel interactions,
    timed sequences, and PIN entry flows.
    """

    def __init__(self, ship_view):
        self.ship_view = ship_view
        self.game_manager = ship_view.game_manager

    def _set_response(self, text: str):
        """Helper to append text and rebuild response display."""
        self.ship_view.last_response += text + "\n"
        self.ship_view._rebuild_response()

    def handle_door_action(self, action: str, args: str) -> str:
        current_location = self.game_manager.get_current_location()

        matching_door = self.game_manager.ship.find_door_from_room(current_location, args)

        if not matching_door:
            if args.strip():
                target = args.strip().lower()
                for exit_key, exit_data in current_location.exits.items():
                    other_room_id = exit_data["target"]
                    other_room = self.game_manager.ship.rooms[other_room_id]

                    if (target == exit_key.lower() or
                        target == exit_data.get("label", "").lower() or
                        ("direction" in exit_data and target == exit_data["direction"].lower()) or
                        target in [s.lower() for s in exit_data.get("shortcuts", [])] or
                        target == other_room.id.lower()):

                        if "door" not in exit_data:
                            current_name = current_location.name
                            target_name = other_room.name
                            msg = f"There is an open archway between {current_name} and {target_name}, "
                            msg += "there is nothing to unlock." if action == "unlock" else "it has no lock."
                            return msg

                return "There is no such exit."
            return "Which door?"

        if (action == "unlock" and not matching_door.locked) or \
           (action == "lock" and matching_door.locked):
            other_room = matching_door.get_other_room(current_location)
            return f"That door to {other_room.name} is already {action}ed."

        panel = matching_door.get_panel_for_room(current_location)

        if not panel:
            return "No access panel on this side."

        if panel.is_broken:
            damaged_image = matching_door.images.get("panel_damaged", "resources/images/image_missing.png")
            self.ship_view.drawing.set_background_image(damaged_image)
            return "The door access panel on this side is damaged and currently unusable. Repairing it may be possible"

        # early check, does the player have a security card
        player_inv = self.game_manager.get_player_inventory()
        has_any_card = any(
            getattr(item, "id", None) in ("id_card_low_sec", "id_card_high_sec")
            for item in player_inv
        )
        if not has_any_card:
            return "You need an ID card to swipe the door access panel."

        panel_image = matching_door.images.get("panel", "resources/images/image_missing.png")
        self.ship_view.drawing.set_background_image(panel_image)

        other_room = matching_door.get_other_room(current_location)
        exit_label = next(
            (ed.get("label", other_room.name) for ed in current_location.exits.values() if ed.get("target") == other_room.id),
            other_room.name
        )

        def on_delay_complete():
            # Store panel for PIN retry loop (closure alternative possible)
            self.ship_view.last_panel = panel

            attempt_method = panel.attempt_unlock if action == "unlock" else panel.attempt_lock
            success, message = attempt_method(self.game_manager.get_player_inventory())

            if success:
                if panel.security_level == SecurityLevel.KEYCARD_HIGH_PIN:
                    self._start_pin_prompt(action, matching_door, exit_label)
                    finish_callback = self._finish_unlock_with_pin if action == "unlock" else self._finish_lock_with_pin
                    self.ship_view.pending_pin_callback = lambda p: self._handle_pin_input(
                        p, action, matching_door, exit_label, finish_callback
                    )
                else:
                    matching_door.locked = action == "lock"
                    image_key = "open" if action == "unlock" else "locked"
                    image = matching_door.images.get(image_key, "resources/images/image_missing.png")
                    self.ship_view.drawing.set_background_image(image)
                    self._set_response(f"ID accepted, door {action}ed. Access to {exit_label} is now {'open' if action == 'unlock' else 'closed'}.")
            else:
                image_key = "locked" if action == "unlock" else "open"
                image = matching_door.images.get(image_key)
                self.ship_view.drawing.set_background_image(image)
                self._set_response(message)

        self.ship_view.schedule_delayed_action(CARD_SWIPE_WAIT, on_delay_complete)

        return "Swiping door access panel, checking card ID..."

    def _start_pin_prompt(self, action: str, matching_door, exit_label: str) -> None:
        self.ship_view.pin_attempts = 0
        self.ship_view.pin_max_attempts = 3
        prompt = f"Enter PIN to {action} the door to {exit_label} (0/3 attempts)"
        self._set_response(prompt)


    def _handle_pin_input(self, pin: str, action: str, matching_door, exit_label: str, finish_callback) -> None:
        self.ship_view.pin_attempts += 1
        success, message = self.ship_view.last_panel.attempt_pin(pin, self.game_manager.get_player_inventory())

        if success:
            finish_callback(pin, matching_door, exit_label)
            self._cleanup_pin_state()
        else:
            attempts_left = self.ship_view.pin_max_attempts - self.ship_view.pin_attempts
            if attempts_left > 0:
                prompt = f"{message} Attempts left: {attempts_left}/{self.ship_view.pin_max_attempts}"
                self._set_response(prompt)
                self.ship_view.pending_pin_callback = lambda p: self._handle_pin_input(
                    p, action, matching_door, exit_label, finish_callback
                )
            else:
                # === ONLY ON FINAL FAILURE (3 wrong PINs) ===
                image_key = "open" if not matching_door.locked else "locked"
                final_image = matching_door.images.get(image_key, "resources/images/image_missing.png")
                self.ship_view.drawing.set_background_image(final_image)
                self._set_response("Access denied after 3 incorrect PIN attempts. Process terminated.")

                # Invalidate high-sec card
                player_inv = self.game_manager.get_player_inventory()
                high_sec_card = next((item for item in player_inv if item.id == "id_card_high_sec"), None)
                if high_sec_card:
                    self.game_manager.remove_from_inventory(high_sec_card)

                    damaged_template = self.game_manager.items.get("id_card_high_sec_damaged")
                    if damaged_template:
                        damaged_item = PortableItem(**{k: v for k, v in damaged_template.items() if k != "type"})
                        success_add, _ = self.game_manager.add_to_inventory(damaged_item)
                        if success_add:
                            self._set_response("ID card invalidated.")
                            self.ship_view.description_renderer.rebuild_description()

                # Cleanup after final failure
                self._cleanup_pin_state()

    def _cleanup_pin_state(self) -> None:
        for attr in ['pin_attempts', 'pin_max_attempts', 'pending_pin_callback']:
            if hasattr(self.ship_view, attr):
                delattr(self.ship_view, attr)

    def _finish_unlock_with_pin(self, pin: str, matching_door, exit_label: str) -> None:
        matching_door.locked = False
        open_image = matching_door.images.get("open", "resources/images/image_missing.png")
        self.ship_view.drawing.set_background_image(open_image)
        self._set_response(f"PIN accepted. Door unlocked. Access to {exit_label} is now open.")

    def _finish_lock_with_pin(self, pin: str, matching_door, exit_label: str) -> None:
        matching_door.locked = True
        locked_image = matching_door.images.get("locked", "resources/images/image_missing.png")
        self.ship_view.drawing.set_background_image(locked_image)
        self._set_response(f"PIN accepted. Door locked. Access to {exit_label} is now closed.")