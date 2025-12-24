# ship_view.py

import arcade
from constants import *
from command_processor import CommandProcessor


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

        # Left: Image section
        image_width = int(SCREEN_WIDTH * LEFT_PANEL_RATIO)
        self.image_section = arcade.Section(
            left=0,
            bottom= EVENT_SECTION_HEIGHT,
            width=image_width,
            height=SCREEN_HEIGHT
        )
        self.section_manager.add_section(self.image_section)

        # Right text panel starts above event section
        self.text_left = image_width
        self.text_width = SCREEN_WIDTH - image_width

        # Event section height (full width, bottom)
        self.event_section_height = EVENT_SECTION_HEIGHT
        self.event_section_width = SCREEN_WIDTH

        # Calculate heights for right-side sections
        right_text_height = SCREEN_HEIGHT - self.event_section_height
        self.description_section_height = int(right_text_height * DESCRIPTION_SECTION_RATIO)
        self.input_section_height = INPUT_SECTION_HEIGHT
        self.response_section_height = right_text_height - self.description_section_height - self.input_section_height

        # Create sections
        self.description_section = arcade.Section(
            left=self.text_left,
            bottom=self.event_section_height + self.input_section_height + self.response_section_height,
            width=self.text_width,
            height=self.description_section_height
        )
        self.response_section = arcade.Section(
            left=self.text_left,
            bottom=self.event_section_height + self.input_section_height,
            width=self.text_width,
            height=self.response_section_height
        )
        self.input_section = arcade.Section(
            left=self.text_left,
            bottom=self.event_section_height,
            width=self.text_width,
            height=self.input_section_height
        )
        self.event_section = arcade.Section(
            left=0,
            bottom=0,
            width=self.text_width,
            height=self.event_section_height
        )
        self.section_manager.add_section(self.description_section)
        self.section_manager.add_section(self.response_section)
        self.section_manager.add_section(self.input_section)
        self.section_manager.add_section(self.event_section)

        # Load background
        self.background_list = arcade.SpriteList()
        self._load_background()

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

        self.description_texts = []
        self._rebuild_description()

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

    def _load_background(self):
        """Load background image for the CURRENT location (queried live)."""
        self.background_list = arcade.SpriteList()
        current_location = self.game_manager.get_current_location()  # Always live
        try:
            texture = arcade.load_texture(current_location["background"])
            bg_sprite = arcade.Sprite()
            bg_sprite.texture = texture
            bg_sprite.center_x = self.image_section.width / 2
            bg_sprite.center_y = (SCREEN_HEIGHT + EVENT_SECTION_HEIGHT) / 2
            bg_sprite.width = self.image_section.width
            bg_sprite.height = SCREEN_HEIGHT - EVENT_SECTION_HEIGHT
            self.background_list.append(bg_sprite)
        except Exception as e:
            print(f"Background load failed: {e}")

    def _rebuild_description(self):
        """Rebuild description texts for the CURRENT location (queried live)."""
        self.description_texts = []
        current_location = self.game_manager.get_current_location()  # Always live
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
                    # Start of highlighted text
                    j = line.find('*', i + 1)
                    if j != -1:
                        highlighted = line[i + 1:j]
                        parts.append((highlighted, ACCENT_COLOR))  # (text, color)
                        i = j + 1
                    else:
                        parts.append((line[i], TEXT_COLOR))
                        i += 1
                else:
                    # Normal text until next '*'
                    j = line.find('*', i)
                    if j == -1:
                        j = len(line)
                    normal = line[i:j]
                    parts.append((normal, TEXT_COLOR))
                    i = j

            # Create Text objects for each part on the same line
            x_pos = self.text_left + self.text_padding
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
                    width=self.text_width - 2 * self.text_padding,
                    multiline=True,
                    anchor_y="top"
                )
                x_pos += txt.content_width  # Advance x for next part
                line_height = max(line_height, txt.content_height)
                self.description_texts.append(txt)

            current_y -= line_height + LINE_SPACING

        # NEW: Dynamic "You see:" section for objects (names only)
        objects = current_location.get("objects", [])
        if objects:
            # Add spacing before section
            current_y -= LINE_SPACING * 2

            # "You see:" header
            see_text = arcade.Text(
                "You see:",
                x=self.text_left + self.text_padding,
                y=current_y,
                color=ACCENT_COLOR,
                font_size=DESCRIPTION_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY,
                anchor_y="top"
            )
            current_y -= see_text.content_height + LINE_SPACING
            self.description_texts.append(see_text)

            # List each object (just name)
            for obj in objects:
                obj_line = f"- {obj.name}"
                txt = arcade.Text(
                    obj_line,
                    x=self.text_left + self.text_padding + 30,  # Indent for bullet effect
                    y=current_y,
                    color=TEXT_COLOR,
                    font_size=DESCRIPTION_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY,
                    width=self.text_width - 2 * self.text_padding - 60,
                    multiline=True,
                    anchor_y="top"
                )
                current_y -= txt.content_height + LINE_SPACING
                self.description_texts.append(txt)

    def _update_response_display(self):
        self.response_text.text = self.last_response

    def _update_input_display(self):
        cursor = "█" if self.cursor_visible else " "
        self.input_text.text = f"> {self.current_input}{cursor}"

    def change_location(self, new_room_id: str) -> None:
        """Update the current location via GameManager (single source of truth) and refresh all visual elements."""
        self.game_manager.set_current_location(new_room_id)
        self._load_background()      # Now uses live location from GameManager
        self._rebuild_description()  # Now uses live location from GameManager
        self.description_title.text = self.game_manager.get_current_location()["name"]
        # Future extensions can go here: animations, sound effects, event triggers, etc.

    def on_update(self, delta_time: float):
        self.blink_timer += delta_time
        if self.blink_timer >= 0.5:
            self.blink_timer = 0.0
            self.cursor_visible = not self.cursor_visible
            self._update_input_display()

    def on_draw(self):
        self.clear()

        # Draw background image
        self.background_list.draw()

        # Overlay on image section
        arcade.draw_lrbt_rectangle_filled(
            self.image_section.left, self.image_section.right,
            self.image_section.bottom, self.image_section.top,
            BACKGROUND_OVERLAY
        )

        # Window border
        arcade.draw_lrbt_rectangle_outline(
        0,
            SCREEN_WIDTH,
        0,
            SCREEN_HEIGHT,
            DIVIDER_COLOR,
            DIVIDER_THICKNESS
        )

        # Divider between RH image and LH text sections
        divider_color = DIVIDER_COLOR
        arcade.draw_line(
            self.text_left,
            self.event_section_height,
            self.text_left,
            SCREEN_HEIGHT,
            divider_color,
            DIVIDER_THICKNESS
        )

        # Divider at bottom of description section
        divider_color = DIVIDER_COLOR
        arcade.draw_line(
            self.text_left,
            self.description_section.bottom,
            self.text_left + self.text_width,
            self.description_section.bottom,
            divider_color,
            DIVIDER_THICKNESS
        )
        # Divider at bottom of response section
        arcade.draw_line(
            self.text_left,
            self.response_section.bottom,
            self.text_left + self.text_width,
            self.response_section.bottom,
            divider_color,
            DIVIDER_THICKNESS
        )
        # divider at top of event section
        arcade.draw_line(
            0,
            60,
            SCREEN_WIDTH,
            60,
            divider_color,
            DIVIDER_THICKNESS
        )

        # # Event section background (reserved)
        # arcade.draw_lrbt_rectangle_filled(
        #     0, SCREEN_WIDTH,
        #     0, self.event_section_height,
        #     EVENT_SECTION_BG_COLOR
        # )

        # Draw all text (global coordinates)
        self.description_title.draw()
        for txt in self.description_texts:
            txt.draw()
        self.response_text.draw()
        self.input_text.draw()

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