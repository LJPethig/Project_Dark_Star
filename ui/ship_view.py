# ship_view.py

import arcade
from constants import *
from command_processor import CommandProcessor
from ui.layout_manager import LayoutManager  # Import the new layout manager
from ui.drawing import DrawingManager
from ui.description_renderer import DescriptionRenderer

class ShipView(arcade.View):
    """Main view with correct section-based layout."""

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        # Removed self.current_location - always query game_manager.get_current_location() live

        self.command_processor = CommandProcessor(self)

        self.current_input = ""
        self.last_response = ""

        # Cursor blink
        self.cursor_visible = True
        self.blink_timer = 0.0

        # Section manager
        self.section_manager = arcade.SectionManager(self)

        # NEW: Use LayoutManager to handle section creation and positioning
        self.layout = LayoutManager(self)
        sections = self.layout.setup_sections()
        for section in sections:
            self.section_manager.add_section(section)

        # ADD THESE 5 LINES HERE:
        self.image_section = self.layout.image_section
        self.description_section = self.layout.description_section
        self.response_section = self.layout.response_section
        self.input_section = self.layout.input_section
        self.event_section = self.layout.event_section

        # Store layout values for use in other methods
        self.text_left = self.layout.get_text_left()
        self.text_width = self.layout.get_text_width()
        self.event_section_height = self.layout.get_event_section_height()

        # Drawing manager
        self.drawing = DrawingManager(self)
        self.drawing.load_background()

        # Text padding
        self.text_padding = TEXT_PADDING

        # For security PIN logic
        self.last_panel = None
        self.last_door = None

        # --- Description section content (global Y) ---
        current_location = self.game_manager.get_current_location()  # Query live from GameManager
        self.description_title = arcade.Text(
            current_location.name,
            x=self.text_left + self.text_padding,
            y=SCREEN_HEIGHT - TITLE_PADDING,
            color=EXIT_COLOR,
            font_size=DESCRIPTION_TITLE_FONT_SIZE,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width - 2 * self.text_padding,
            multiline=True,
            anchor_y="top"
        )

        # Description renderer
        self.description_renderer = DescriptionRenderer(self)
        self.description_renderer.rebuild_description()
        self.description_texts = self.description_renderer.get_description_texts()

        # --- Response section: list of colored Text objects using markup ---
        self.response_texts = []
        self.response_y_start = self.response_section.bottom + self.response_section.height - RESPONSE_PADDING_TOP

        # --- Input section content (global Y) ---
        self.input_text = arcade.Text(
            "> ",
            x=self.text_left + self.text_padding,
            y=self.input_section.bottom + self.input_section.height - INPUT_PADDING_TOP,
            color=PLAYER_INPUT_COLOR,
            font_size=INPUT_FONT_SIZE,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width - 2 * self.text_padding,
            multiline=True,
            anchor_y="top"
        )

        # --- Ship time display (bottom-right, event section) ---
        self.ship_time_text = arcade.Text(
            "",
            x=SCREEN_WIDTH - TEXT_PADDING,
            y=self.event_section_height // 2,
            color=CLOCK_COLOR,
            font_size=FONT_SIZE_SMALL,
            font_name=FONT_NAME_PRIMARY,
            anchor_x="right",
            anchor_y="center"
        )

    def _update_response_display(self):
        self._rebuild_response()

    def _update_input_display(self):
        cursor = "█" if self.cursor_visible else " "
        self.input_text.text = f"> {self.current_input}{cursor}"

    def change_location(self, new_room_id: str) -> None:
        self.game_manager.set_current_location(new_room_id)
        self.drawing.load_background()  # Refresh background
        self.description_renderer.rebuild_description()  # Refresh description
        self.description_texts = self.description_renderer.get_description_texts()  # NEW: Sync ShipView's texts
        self.description_title.text = self.game_manager.get_current_location().name

    def on_update(self, delta_time: float):
        self.blink_timer += delta_time
        if self.blink_timer >= 0.5:
            self.blink_timer = 0.0
            self.cursor_visible = not self.cursor_visible
            self._update_input_display()

    def on_draw(self):
        self.clear()

        # Draw background image
        self.drawing.draw_background()

        # Overlay on image section
        self.drawing.draw_overlay()

        # Window border
        self.drawing.draw_window_border()

        # Dividers
        self.drawing.draw_dividers()

        # Ensure latest description texts before drawing
        self.description_texts = self.description_renderer.get_description_texts()  # NEW: Always fresh

        # Draw all text (global coordinates)
        self.drawing.draw_text_elements()

        # Draw response texts (markup-colored)
        for text in self.response_texts:
            text.draw()

        # Draw ship time (always on top)
        self.ship_time_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            cmd = self.current_input.strip()
            self.current_input = ""
            self._update_input_display()

            if not cmd:
                return

            # Show what the player typed
            self.last_response = f"+> {cmd}+\n\n"

            # Delegate to command processor
            response = self.command_processor.process(cmd)

            # Handle quit/exit specially (since it calls arcade.exit())
            if response == "Thanks for playing Project Dark Star. Goodbye!":
                self.last_response += response + "\n"
                self._update_response_display()
                arcade.exit()
                return

            # Normal response
            if response:
                self.last_response += response + "\n"
                self._update_response_display()

        elif key == arcade.key.BACKSPACE:
            if self.current_input:
                self.current_input = self.current_input[:-1]
                self._update_input_display()

        elif 32 <= key <= 126:
            self.current_input += chr(key)
            self._update_input_display()

    def on_show_view(self):
        """Called when this view becomes active — perfect place to start the clock."""
        super().on_show_view()  # Always keep this if present

        # Show current time immediately
        self.update_ship_time_display()

        # Start ticking every 60 seconds
        arcade.schedule(self._clock_tick, CLOCK_UPDATE_INTERVAL)

    def update_ship_time_display(self):
        """Refresh the ship time text in the event section."""
        if hasattr(self.game_manager, "chronometer"):
            self.ship_time_text.text = self.game_manager.chronometer.get_formatted()
        else:
            self.ship_time_text.text = "Chronometer not initialized"

    def _clock_tick(self, delta_time: float):
        """Called every CLOCK_UPDATE_INTERVAL seconds to update clock during normal play."""
        if self.game_manager.chronometer is not None:
            self.game_manager.chronometer.advance(1)
        self.update_ship_time_display()

    def flash_ship_time(self):
        """Briefly highlight the clock to signal a significant time advance."""
        # Temporarily brighten the clock
        self.ship_time_text.color = CLOCK_FLASH_COLOR

        def reset_color(delta_time):
            self.ship_time_text.color = CLOCK_COLOR
            arcade.unschedule(reset_color)

        # Flash for 0.5 seconds
        arcade.schedule_once(reset_color, 0.5)

    def schedule_delayed_action(self, delay_seconds: float, callback):
        def _delayed(delta_time):
            print("schedule_delayed_action is used!")
            callback()
            arcade.unschedule(_delayed)

        arcade.schedule(_delayed, delay_seconds)

    def on_hide_view(self):
        """Stop the clock when leaving this view (e.g., inventory)."""
        super().on_hide_view()
        arcade.unschedule(self._clock_tick)

    def _rebuild_response(self):
        """Rebuild response using markup parsing — same system as description."""
        self.response_texts = []

        if not self.last_response:
            return

        from ui.text_utils import parse_markup_line  # Local import to avoid circular

        lines = self.last_response.split("\n")
        current_y = self.response_y_start

        for line in lines:
            line = line.rstrip()
            if not line:
                current_y -= RESPONSE_FONT_SIZE # + 4
                continue

            line_texts, line_height = parse_markup_line(
                line=line,
                x=self.text_left + self.text_padding,
                y=current_y,
                width=self.text_width - 2 * self.text_padding,
                font_size=RESPONSE_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY
            )
            self.response_texts.extend(line_texts)
            current_y -= line_height + LINE_SPACING