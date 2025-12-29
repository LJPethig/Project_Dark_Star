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
        current_room_id = current_location["id"]

        # Use shared finder logic
        matching_door, panel_id, exit_label, error = self._find_door_and_panel(args, current_room_id)

        if error:
            return error

        # Already correct state?
        if (action == "unlock" and not matching_door["locked"]) or \
           (action == "lock" and matching_door["locked"]):
            return f"That hatch is already {action}ed."

        panel = self.game_manager.security_panels.get(panel_id)
        if not panel:
            return f"Panel '{panel_id}' not found."

        # Check for damage before proceeding
        if panel.is_broken:
            damaged_image = matching_door.get("panel_image_damaged", "resources/images/panel_damaged_default.png")
            self.ship_view.drawing.set_background_image(damaged_image)
            return "The panel on this side is damaged and currently unusable. Repairing it may be possible"

        # Check if player has ANY ID card
        player_inv = self.game_manager.get_player_inventory()
        has_any_card = "id_card_low_sec" in player_inv or "id_card_high_sec" in player_inv

        if not has_any_card:
            return "You need an ID card to swipe."

        # Has any card → show panel + initial message
        panel_image = matching_door.get("panel_image", "resources/images/panel_default.png")
        self.ship_view.drawing.set_background_image(panel_image)
        self.ship_view.response_text.text = "Accessing door panel, checking card ID..."

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
                    matching_door["locked"] = action == "lock"
                    image_key = "open_image" if action == "unlock" else "locked_image"
                    image = matching_door.get(image_key, "resources/images/open_hatch.png" if action == "unlock" else "resources/images/closed_hatch.png")
                    self.ship_view.drawing.set_background_image(image)
                    self.ship_view.response_text.text = f"ID accepted, door {action}ed. The hatch to {exit_label} is now {'open' if action == 'unlock' else 'closed'}."
            else:
                # Failure image (opposite state)
                image_key = "locked_image" if action == "unlock" else "open_image"
                image = matching_door.get(image_key)
                self.ship_view.drawing.set_background_image(image)
                self.ship_view.response_text.text = message

        self.ship_view.schedule_delayed_action(5.0, on_delay_complete)

        return "Accessing door panel, checking card ID..."

    def _find_door_and_panel(self, target: str, current_room_id: str) -> tuple[dict | None, str | None, str | None, str | None]:
        """Shared logic to find matching door, panel on current side, exit label, or error."""
        matching_door = None
        next_room_id = None
        exit_label = None

        for door in self.game_manager.door_status:
            if current_room_id in door["rooms"]:
                other_room = next(r for r in door["rooms"] if r != current_room_id)

                if target == other_room.lower():
                    matching_door = door
                    next_room_id = other_room
                    exit_label = other_room
                    break

                for exit_key, ed in self.game_manager.get_current_location()["exits"].items():
                    if target == exit_key.lower() or target in [s.lower() for s in ed.get("shortcuts", [])]:
                        if ed["target"] == other_room:
                            matching_door = door
                            next_room_id = other_room
                            exit_label = ed.get("label", other_room)
                            break
                if matching_door:
                    break

        if not matching_door:
            return None, None, None, f"No door connected to '{target}'. Try a valid room or direction."

        panel_id = None
        for panel_data in matching_door.get("panel_ids", []):
            if panel_data["side"] == current_room_id:
                panel_id = panel_data["id"]
                break

        if not panel_id:
            return matching_door, None, exit_label, "No panel on this side of the door."

        return matching_door, panel_id, exit_label, None

    def _start_pin_prompt(self, action: str, matching_door: dict, exit_label: str) -> None:
        """Initiate PIN entry phase with attempt tracking."""
        self.ship_view.pin_attempts = 0
        self.ship_view.pin_max_attempts = 3
        prompt = f"Enter PIN to {action} the door to {exit_label} ({self.ship_view.pin_attempts}/{self.ship_view.pin_max_attempts} attempts)"
        self.ship_view.response_text.text = prompt

    def _handle_pin_input(self, pin: str, action: str, matching_door: dict, exit_label: str, finish_callback) -> None:
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
                image_key = "open_image" if not matching_door["locked"] else "locked_image"
                final_image = matching_door.get(image_key, "resources/images/closed_hatch.png")
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
                    else:
                        self.ship_view.response_text.text += "\nID card invalidated, but inventory full - damaged card dropped."

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

    def _finish_unlock_with_pin(self, pin: str, matching_door: dict, exit_label: str) -> None:
        """Called only on successful PIN for unlock."""
        matching_door["locked"] = False
        open_image = matching_door.get("open_image", "resources/images/open_hatch.png")
        self.ship_view.drawing.set_background_image(open_image)
        self.ship_view.response_text.text = f"PIN accepted. Door unlocked. The hatch to {exit_label} is now open."

    def _finish_lock_with_pin(self, pin: str, matching_door: dict, exit_label: str) -> None:
        """Called only on successful PIN for lock."""
        matching_door["locked"] = True
        locked_image = matching_door.get("locked_image", "resources/images/closed_hatch.png")
        self.ship_view.drawing.set_background_image(locked_image)
        self.ship_view.response_text.text = f"PIN accepted. Door locked. The hatch to {exit_label} is now closed."