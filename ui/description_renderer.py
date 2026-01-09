# ui/description_renderer.py
import arcade
from constants import *
from ui.text_utils import parse_markup_line  # Import shared utility

class DescriptionRenderer:
    """Handles parsing and rendering of room descriptions and object lists."""

    def __init__(self, view):
        self.view = view
        self.description_texts = []  # List of arcade.Text objects

    def rebuild_description(self):
        """Rebuild description texts for the CURRENT location (queried live)."""
        self.description_texts = []
        current_location = self.view.game_manager.get_current_location()
        current_y = SCREEN_HEIGHT - TITLE_PADDING - DESCRIPTION_TITLE_FONT_SIZE - SECTION_TITLE_PADDING

        # Parse description lines using shared utility
        for line in current_location.description:
            if not line.strip():
                current_y -= LINE_SPACING
                continue

            line_texts, line_height = parse_markup_line(
                line=line,
                x=self.view.text_left + self.view.text_padding,
                y=current_y,
                width=self.view.text_width - 2 * self.view.text_padding
            )
            self.description_texts.extend(line_texts)
            current_y -= line_height + LINE_SPACING

        # Dynamic "You see:" section for objects (names only)
        objects = current_location.objects
        if objects:
            current_y -= LINE_SPACING * 2

            see_text = arcade.Text(
                "You see",
                x=self.view.text_left + self.view.text_padding,
                y=current_y,
                color=TEXT_COLOR,
                font_size=DESCRIPTION_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY,
                anchor_y="top"
            )
            current_y -= see_text.content_height + LINE_SPACING
            self.description_texts.append(see_text)

            for obj in objects:
                obj_name = obj.name if hasattr(obj, 'name') else "Unknown"
                txt = arcade.Text(
                    obj_name,
                    x=self.view.text_left + self.view.text_padding,
                    y=current_y,
                    color=OBJECT_COLOR,
                    font_size=DESCRIPTION_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY,
                    width=self.view.text_width - 2 * self.view.text_padding - 60,
                    multiline=True,
                    anchor_y="top"
                )
                current_y -= txt.content_height #+ LINE_SPACING
                self.description_texts.append(txt)

    def get_description_texts(self):
        """Return the list of rendered text objects for drawing."""
        return self.description_texts