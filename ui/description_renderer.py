# ui/description_renderer.py
import arcade
from constants import *

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

        for line in current_location["description"]:
            if not line.strip():
                current_y -= LINE_SPACING
                continue

            # Split line into normal text and *highlighted* parts
            parts = []
            i = 0
            while i < len(line):
                if line[i] == '*':
                    j = line.find('*', i + 1)
                    if j != -1:
                        highlighted = line[i + 1:j]
                        parts.append((highlighted, ACCENT_COLOR))  # (text, color)
                        i = j + 1
                    else:
                        parts.append((line[i], TEXT_COLOR))
                        i += 1
                else:
                    j = line.find('*', i)
                    if j == -1:
                        j = len(line)
                    normal = line[i:j]
                    parts.append((normal, TEXT_COLOR))
                    i = j

            # Create Text objects for each part on the same line
            x_pos = self.view.text_left + self.view.text_padding
            line_height = 0
            for text_part, color in parts:
                if not text_part.strip():
                    continue

                txt = arcade.Text(
                    text_part,
                    x=x_pos,
                    y=current_y,
                    color=color,
                    font_size=DESCRIPTION_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY,
                    width=self.view.text_width - 2 * self.view.text_padding,
                    multiline=True,
                    anchor_y="top",
                    anchor_x="left"
                )
                x_pos += txt.content_width  # Advance for next part
                line_height = max(line_height, txt.content_height)
                self.description_texts.append(txt)

            current_y -= line_height + LINE_SPACING

        # Dynamic "You see:" section for objects (names only)
        objects = current_location.get("objects", [])
        if objects:
            # Add spacing before section
            current_y -= LINE_SPACING * 2

            # "You see:" header
            see_text = arcade.Text(
                "You see:",
                x=self.view.text_left + self.view.text_padding,
                y=current_y,
                color=TEXT_COLOR,
                font_size=DESCRIPTION_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY,
                anchor_y="top"
            )
            current_y -= see_text.content_height + LINE_SPACING
            self.description_texts.append(see_text)

            # List each object (just name)
            for obj in objects:
                obj_name = obj.name if hasattr(obj, 'name') else "Unknown"
                obj_line = f"- {obj_name}"
                txt = arcade.Text(
                    obj_line,
                    x=self.view.text_left + self.view.text_padding,
                    y=current_y,
                    color=OBJECT_COLOR,
                    font_size=DESCRIPTION_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY,
                    width=self.view.text_width - 2 * self.view.text_padding - 60,
                    multiline=True,
                    anchor_y="top"
                )
                current_y -= txt.content_height + LINE_SPACING
                self.description_texts.append(txt)

    def get_description_texts(self):
        """Return the list of rendered text objects for drawing."""
        return self.description_texts