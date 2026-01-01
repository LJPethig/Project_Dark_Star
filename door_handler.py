# door_handler.py
"""
Dedicated handler for all door-related commands and security panel interactions.
Fully extracted from command_processor.py — improves readability and extensibility.
Transient PIN state is managed via ShipView attributes (simple and effective for current scope).
"""

from models.security_panel import SecurityLevel


class DoorHandler:
    """
    Handles complex door lock/unlock logic, security panel interactions,
    timed sequences, and PIN entry flows.
    """

    def __init__(self, ship_view):
        self.ship_view = ship_view
        self.game_manager = ship_view.game_manager

    def handle_door_action(self, action: str, args: str) -> str:
        """
        Main entry point for 'lock' and 'unlock' commands targeting a door/exit.
        Returns the initial response text (e.g., "Accessing door panel...").
        All side effects (delays, images, state changes, PIN prompts) are handled internally.
        """
        current_location = self.game_manager.get_current_location()

        # Use shared finder logic — now via Ship.find_door_from_room
        # Find secured door only
        matching_door = self.game_manager.ship.find_door_from_room(current_location, args)

        if not matching_door:
            # If args provided, check if it matches any valid exit (including archways)
            if args.strip():
                target = args.strip().lower()
                for exit_key, exit_data in current_location.exits.items():
                    other_room_id = exit_data["target"]
                    other_room = self.game_manager.ship.rooms[other_room_id]

                    # Match on key, label, direction, shortcuts, or room ID
                    if (target == exit_key.lower() or
                        target == exit_data.get("label", "").lower() or
                        ("direction" in exit_data and target == exit_data["direction"].lower()) or
                        target in [s.lower() for s in exit_data.get("shortcuts", [])] or
                        target == other_room.id.lower()):

                        # Valid exit found — if no door, it's an archway
                        if "door" not in exit_data:
                            current_name = current_location.name
                            target_name = other_room.name
                            if action == "unlock":
                                return f"There is an open archway between {current_name} and {target_name}, there is nothing to unlock."
                            else:  # lock
                                return f"There is an open archway between {current_name} and {target_name}, it has no lock."

                # If we get here: target doesn't match any exit
                return f"There is no such exit."

            # No args → prompt for which door
            return "Which door?"

        # Already correct state?
        if (action == "unlock" and not matching_door.locked) or \
           (action == "lock" and matching_door.locked):
            other_room = matching_door.get_other_room(current_location)
            exit_label = next(
                (ed.get("label", other_room.name) for ed in current_location.exits.values() if ed.get("target") == other_room.id),
                other_room.name
            )
            return f"That door is already {action}ed."

        panel = matching_door.get_panel_for_room(current_location)
        print(
            f"RUNTIME PANEL DEBUG: panel_id={getattr(panel, 'panel_id', 'None')}, side={getattr(panel, 'side', 'None')}, is_broken={panel.is_broken if panel else 'None'}, door_id={getattr(panel, 'door_id', 'None')}")
        print(
            f"DOOR PANELS DICT: { {k: {'panel_id': p.panel_id, 'is_broken': p.is_broken} for k, p in matching_door.panels.items()} }")
        if not panel:
            print("NO PANEL:")
            return "No access panel on this side."

        # Check for damage before proceeding
        if panel.is_broken:
            damaged_image = matching_door.images.get("panel_damaged", "resources/images/image_missing.png")
            self.ship_view.drawing.set_background_image(damaged_image)
            return "The door access panel on this side is damaged and currently unusable. Repairing it may be possible"

        # Check if player has ANY ID card
        player_inv = self.game_manager.get_player_inventory()
        has_any_card = "id_card_low_sec" in player_inv or "id_card_high_sec" in player_inv

        if not has_any_card:
            return "You need an ID card to swipe the door access panel."

        # Has any card → show panel + initial message
        panel_image = matching_door.images.get("panel", "resources/images/image_missing.png")
        self.ship_view.drawing.set_background_image(panel_image)
        self.ship_view.response_text.text = "Swiping door access panel, checking card ID..."

        other_room = matching_door.get_other_room(current_location)
        exit_label = next(
            (ed.get("label", other_room.name) for ed in current_location.exits.values() if ed.get("target") == other_room.id),
            other_room.name
        )

        def on_delay_complete():
            self.ship_view.last_panel = panel
            self.ship_view.last_door = matching_door
            # Choose attempt method based on action
            attempt_method = panel.attempt_unlock if action == "unlock" else panel.attempt_lock
            success, message = attempt_method(self.game_manager.get_player_inventory())

            if success:
                if panel.security_level == SecurityLevel.KEYCARD_HIGH_PIN:
                    self._start_pin_prompt(action, matching_door, exit_label)
                    # Dynamic finish callback based on action
                    finish_callback = self._finish_unlock_with_pin if action == "unlock" else self._finish_lock_with_pin
                    self.ship_view.pending_pin_callback = lambda p: self._handle_pin_input(
                        p, action, matching_door, exit_label, finish_callback
                    )
                else:
                    # Apply immediate state change
                    matching_door.locked = action == "lock"
                    image_key = "open" if action == "unlock" else "locked"
                    image = matching_door.images.get(image_key, "resources/images/image_missing.png")
                    self.ship_view.drawing.set_background_image(image)
                    self.ship_view.response_text.text = f"ID accepted, door {action}ed. Access to {exit_label} is now {'open' if action == 'unlock' else 'closed'}."
            else:
                # Failure image (opposite state)
                image_key = "locked" if action == "unlock" else "open"
                image = matching_door.images.get(image_key)
                self.ship_view.drawing.set_background_image(image)
                self.ship_view.response_text.text = message

        self.ship_view.schedule_delayed_action(5.0, on_delay_complete)

        return "Swiping door access panel, checking card ID..."

    def _start_pin_prompt(self, action: str, matching_door, exit_label: str) -> None:
        """Initiate PIN entry phase with attempt tracking."""
        self.ship_view.pin_attempts = 0
        self.ship_view.pin_max_attempts = 3
        prompt = f"Enter PIN to {action} the door to {exit_label} ({self.ship_view.pin_attempts}/{self.ship_view.pin_max_attempts} attempts)"
        self.ship_view.response_text.text = prompt

    def _handle_pin_input(self, pin: str, action: str, matching_door, exit_label: str, finish_callback) -> None:
        """Shared PIN processing logic with retries."""
        self.ship_view.pin_attempts += 1
        success, message = self.ship_view.last_panel.attempt_pin(pin, self.game_manager.get_player_inventory())

        if success:
            # Success: apply the action
            finish_callback(pin, matching_door, exit_label)
            self._cleanup_pin_state()
        else:
            # Failure: check attempts
            attempts_left = self.ship_view.pin_max_attempts - self.ship_view.pin_attempts
            if attempts_left > 0:
                # Re-prompt with updated message
                prompt = f"{message} Attempts left: {attempts_left}/{self.ship_view.pin_max_attempts}"
                self.ship_view.response_text.text = prompt
                # Keep the same callback
                self.ship_view.pending_pin_callback = lambda p: self._handle_pin_input(
                    p, action, matching_door, exit_label, finish_callback
                )
            else:
                # All attempts used: deny access
                image_key = "open" if not matching_door.locked else "locked"
                final_image = matching_door.images.get(image_key, "resources/images/image_missing.png")
                self.ship_view.drawing.set_background_image(final_image)
                self.ship_view.response_text.text = "Access denied after 3 incorrect PIN attempts. Process terminated."

                # NEW: Invalidate one high-sec card
                inventory_ids = self.game_manager.get_player_inventory()
                if "id_card_high_sec" in inventory_ids:
                    # Remove one high-sec card
                    self.game_manager.remove_from_inventory("id_card_high_sec")

                    # Add damaged version
                    success, msg = self.game_manager.add_to_inventory("id_card_high_sec_damaged")
                    if success:
                        self.ship_view.response_text.text += "\nID card invalidated."

                    # Refresh description UI
                    self.ship_view.description_renderer.rebuild_description()
                    self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()
                else:
                    # Safety fallback (shouldn't happen)
                    print("DEBUG: No high-sec card found during PIN failure")

                self._cleanup_pin_state()

    def _cleanup_pin_state(self) -> None:
        """Centralized cleanup of PIN-related state on ShipView after success or lockout."""
        for attr in ['pin_attempts', 'pin_max_attempts', 'pending_pin_callback']:
            if hasattr(self.ship_view, attr):
                delattr(self.ship_view, attr)

    def _finish_unlock_with_pin(self, pin: str, matching_door, exit_label: str) -> None:
        """Called only on successful PIN for unlock."""
        matching_door.locked = False
        open_image = matching_door.images.get("open", "resources/images/image_missing.png")
        self.ship_view.drawing.set_background_image(open_image)
        self.ship_view.response_text.text = f"PIN accepted. Door unlocked. Access to {exit_label} is now open."

    def _finish_lock_with_pin(self, pin: str, matching_door, exit_label: str) -> None:
        """Called only on successful PIN for lock."""
        matching_door.locked = True
        locked_image = matching_door.images.get("locked", "resources/images/image_missing.png")
        self.ship_view.drawing.set_background_image(locked_image)
        self.ship_view.response_text.text = f"PIN accepted. Door locked. Access to {exit_label} is now closed."