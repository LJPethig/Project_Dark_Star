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

        # --- Description section content (global Y) ---
        current_location = self.game_manager.get_current_location()  # Query live from GameManager
        self.description_title = arcade.Text(
            current_location["name"],
            x=self.text_left + self.text_padding,
            y=SCREEN_HEIGHT - TITLE_PADDING,
            color=ACCENT_COLOR,
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

        # --- Response section content (global Y) ---
        self.response_text = arcade.Text(
            "",
            x=self.text_left + self.text_padding,
            y=self.response_section.bottom + self.response_section.height - RESPONSE_PADDING_TOP,
            color=TEXT_COLOR,
            font_size=RESPONSE_FONT_SIZE,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width - 2 * self.text_padding,
            multiline=True,
            anchor_y="top"
        )

        # --- Input section content (global Y) ---
        self.input_text = arcade.Text(
            "> ",
            x=self.text_left + self.text_padding,
            y=self.input_section.bottom + self.input_section.height - INPUT_PADDING_TOP,
            color=TEXT_COLOR,
            font_size=INPUT_FONT_SIZE,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width - 2 * self.text_padding,
            multiline=True,
            anchor_y="top"
        )


    def _update_response_display(self):
        self.response_text.text = self.last_response

    def _update_input_display(self):
        cursor = "█" if self.cursor_visible else " "
        self.input_text.text = f"> {self.current_input}{cursor}"

    def change_location(self, new_room_id: str) -> None:
        self.game_manager.set_current_location(new_room_id)
        self.drawing.load_background()  # Refresh background
        self.description_renderer.rebuild_description()  # Refresh description
        self.description_texts = self.description_renderer.get_description_texts()  # NEW: Sync ShipView's texts
        self.description_title.text = self.game_manager.get_current_location()["name"]

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

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            cmd = self.current_input.strip()
            self.current_input = ""
            self._update_input_display()

            if not cmd:
                return

            # Show what the player typed
            self.last_response = f"> {cmd}\n"

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

    def _show_panel_sequence(self, panel_image: str, final_image: str, success_message: str):
        """Non-blocking: show panel → wait 5s → show success message + final image."""
        # Step 1: Show panel and initial message
        self.drawing.set_background_image(panel_image)
        self.response_text.text = "Accessing door panel, checking card ID"

        # Step 2: Schedule step 2 after 5 seconds
        def step2(delta_time):
            # Step 2: Show success and final image
            self.response_text.text = success_message
            self.drawing.set_background_image(final_image)
            # Remove schedule (runs once)
            arcade.unschedule(step2)

        arcade.schedule(step2, 5.0)