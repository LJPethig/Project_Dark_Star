# ui/layout_manager.py
import arcade
from constants import *

class LayoutManager:
    """Handles the creation and positioning of all UI sections for ShipView."""

    def __init__(self, view):
        self.view = view
        self.image_section = None
        self.description_section = None
        self.response_section = None
        self.input_section = None
        self.event_section = None
        self.text_left = 0
        self.text_width = 0
        self.event_section_height = EVENT_SECTION_HEIGHT

    def setup_sections(self):
        """Create and position all sections, returning them for the section manager."""
        # Left: Image section
        image_width = int(SCREEN_WIDTH * LEFT_PANEL_RATIO)
        self.image_section = arcade.Section(
            left=0,
            bottom=self.event_section_height,
            width=image_width,
            height=SCREEN_HEIGHT
        )

        # Right text panel starts above event section
        self.text_left = image_width
        self.text_width = SCREEN_WIDTH - image_width

        # Event section height (full width, bottom)
        # Already set in __init__

        # Calculate heights for right-side sections
        right_text_height = SCREEN_HEIGHT - self.event_section_height
        description_section_height = int(right_text_height * DESCRIPTION_SECTION_RATIO)
        input_section_height = INPUT_SECTION_HEIGHT
        response_section_height = right_text_height - description_section_height - input_section_height

        # Create sections
        self.description_section = arcade.Section(
            left=self.text_left,
            bottom=self.event_section_height + input_section_height + response_section_height,
            width=self.text_width,
            height=description_section_height
        )
        self.response_section = arcade.Section(
            left=self.text_left,
            bottom=self.event_section_height + input_section_height,
            width=self.text_width,
            height=response_section_height
        )
        self.input_section = arcade.Section(
            left=self.text_left,
            bottom=self.event_section_height,
            width=self.text_width,
            height=input_section_height
        )
        self.event_section = arcade.Section(
            left=0,
            bottom=0,
            width=self.text_width,
            height=self.event_section_height
        )

        return [
            self.image_section,
            self.description_section,
            self.response_section,
            self.input_section,
            self.event_section
        ]

    # Accessors for ShipView to use in other methods
    def get_text_left(self):
        return self.text_left

    def get_text_width(self):
        return self.text_width

    def get_event_section_height(self):
        return self.event_section_height