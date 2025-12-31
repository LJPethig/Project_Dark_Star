# repair_handler.py
"""
Dedicated handler for all repair-related commands.
Currently supports repairing damaged door panels.
Designed for future expansion (tools, consumables, progress, other objects).
"""

from models.security_panel import SecurityPanel


class RepairHandler:
    """
    Handles repair logic for damaged objects, starting with door panels.
    """

    def __init__(self, ship_view):
        self.ship_view = ship_view
        self.game_manager = ship_view.game_manager

    def handle_repair_door_panel(self, args: str) -> str:
        """
        Repair a damaged door panel in the current room.
        Syntax: repair door panel [target_exit]
        If no target and only one broken panel → auto-repair.
        If multiple → prompt for clarification.
        """
        current_location = self.game_manager.get_current_location()
        current_room_id = current_location.id

        # Find all broken door panels in this room
        broken_panels = []
        for door in self.game_manager.door_status:
            if current_room_id in door["rooms"]:
                for panel_data in door.get("panel_ids", []):
                    if panel_data["side"] == current_room_id:
                        panel = self.game_manager.security_panels.get(panel_data["id"])
                        if panel and panel.is_broken:
                            # Get exit label for player-friendly display
                            exit_label = self._get_exit_label(door, current_room_id)
                            broken_panels.append((panel, exit_label, door))

        if not broken_panels:
            return "There are no damaged door access panels in this room."

        # Auto-repair if only one
        if len(broken_panels) == 1 and not args.strip():
            panel, exit_label, matching_door = broken_panels[0]
            return self._perform_repair(panel, exit_label, matching_door)

        # If explicit target provided
        if args.strip():
            target = args.strip().lower()
            for panel, exit_label, door in broken_panels:
                if self._matches_exit(target, door, current_room_id):
                    return self._perform_repair(panel, exit_label, door)
            return f"No damaged door access panel to '{args}'."

        # Multiple broken panels — ask for clarification
        labels = [label for _, label, _ in broken_panels]
        return f"Which door access panel do you want to repair? ({', '.join(labels)})"

    def _get_exit_label(self, door: dict, current_room_id: str) -> str:
        """Get player-friendly label for the exit from current side."""
        other_room = next(r for r in door["rooms"] if r != current_room_id)
        exits = self.game_manager.get_current_location().exits
        for exit_key, ed in exits.items():
            if ed["target"] == other_room:
                return ed.get("label", other_room)
        return other_room

    def _matches_exit(self, target: str, door: dict, current_room_id: str) -> bool:
        """Check if target matches the exit on this side (using keywords/shortcuts)."""
        other_room = next(r for r in door["rooms"] if r != current_room_id)
        if target == other_room.lower():
            return True
        exits = self.game_manager.get_current_location().exits
        for exit_key, ed in exits.items():
            if ed["target"] == other_room:
                if (target == exit_key.lower() or
                    target in [s.lower() for s in ed.get("shortcuts", [])]):
                    return True
        return False

    def _perform_repair(self, panel: SecurityPanel, exit_label: str, matching_door: dict) -> str:
        """Perform the repair with visual flow: damaged panel → 8s delay → repaired panel (persistent)."""
        # Immediate: show damaged panel and starting message
        damaged_image = matching_door.get("panel_image_damaged", "resources/images/panel_damaged_default.png")
        self.ship_view.drawing.set_background_image(damaged_image)
        self.ship_view.response_text.text = "Repairing door access panel..."

        # Apply repair logic instantly (as before — magic repair)
        panel.is_broken = False
        panel.repair_progress = 1.0

        def on_repair_complete():
            # After 8 seconds: show repaired panel
            repaired_image = matching_door.get("panel_image", "resources/images/panel_default.png")  # fallback to normal panel
            self.ship_view.drawing.set_background_image(repaired_image)
            self.ship_view.response_text.text = f"You repair the door access panel to {exit_label}. It is now operational."

            # Refresh description to reflect fixed state
            self.ship_view.description_renderer.rebuild_description()
            self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()

        # Schedule the 8-second "working" delay
        self.ship_view.schedule_delayed_action(8.0, on_repair_complete)

        return ""  # Initial response shown visually