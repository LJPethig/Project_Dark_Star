# repair_handler.py
"""
Dedicated handler for all repair-related commands.
Currently supports repairing damaged door panels.
Designed for future expansion (tools, consumables, progress, other objects).
"""

from models.security_panel import SecurityPanel
from models.door import Door


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

        # NEW: Use centralized helper from Ship — eliminates duplication
        broken_panels = self.game_manager.ship.get_broken_panels_in_room(current_location)

        if not broken_panels:
            return "There are no damaged door access panels in this room."

        # Auto-repair if only one
        if len(broken_panels) == 1 and not args.strip():
            panel, exit_label, matching_door = broken_panels[0]
            return self._perform_repair(panel, exit_label, matching_door)

        # If explicit target provided
        if args.strip():
            target = args.strip().lower()
            matching_door = self.game_manager.ship.find_door_from_room(current_location, target)
            if matching_door:
                panel = matching_door.get_panel_for_room(current_location)
                if panel and panel.is_broken:
                    exit_label = next(
                        (ed.get("label", matching_door.get_other_room(current_location).name)
                         for ed in current_location.exits.values()
                         if ed.get("target") == matching_door.get_other_room(current_location).id),
                        matching_door.get_other_room(current_location).name
                    )
                    return self._perform_repair(panel, exit_label, matching_door)
            return f"No damaged door access panel to '{args}'."

        # Multiple broken panels — ask for clarification
        labels = [label for _, label, _ in broken_panels]
        return f"Which door access panel do you want to repair? ({', '.join(labels)})"

    def _perform_repair(self, panel: SecurityPanel, exit_label: str, matching_door: Door) -> str:
        """Perform the repair with visual flow: damaged panel → 8s delay → repaired panel (persistent)."""
        # Immediate: show damaged panel and starting message
        damaged_image = matching_door.images.get("panel_damaged", "resources/images/image_missing.png")
        self.ship_view.drawing.set_background_image(damaged_image)
        self.ship_view.response_text.text = "Repairing door access panel..."

        # Apply repair logic instantly (as before — magic repair)
        panel.is_broken = False
        panel.repair_progress = 1.0

        def on_repair_complete():
            # After 8 seconds: show repaired panel
            repaired_image = matching_door.images.get("panel", "resources/images/image_missing.png")
            self.ship_view.drawing.set_background_image(repaired_image)
            self.ship_view.response_text.text = f"You repair the door access panel to {exit_label}. It is now operational."

            # Refresh description to reflect fixed state
            self.ship_view.description_renderer.rebuild_description()
            self.ship_view.description_texts = self.ship_view.description_renderer.get_description_texts()

        # Schedule the 8-second "working" delay
        self.ship_view.schedule_delayed_action(8.0, on_repair_complete)

        return ""  # Initial response shown visually