import arcade
from constants import *


class ShipView(arcade.View):
    """Main view with correct section-based layout."""

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.current_location = game_manager.get_current_location()

        self.current_input = ""
        self.last_response = ""

        # Cursor blink
        self.cursor_visible = True
        self.blink_timer = 0.0

        # Section manager
        self.section_manager = arcade.SectionManager(self)

        # Left: Image section (55%)
        image_width = int(SCREEN_WIDTH * LEFT_PANEL_RATIO)
        self.image_section = arcade.Section(
            left=0,
            bottom=0,
            width=image_width,
            height=SCREEN_HEIGHT
        )
        self.section_manager.add_section(self.image_section)

        # Right text panel starts above event section
        self.text_left = image_width
        self.text_width = SCREEN_WIDTH - image_width

        # Event section height (full width, bottom)
        self.event_section_height = EVENT_SECTION_HEIGHT

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
        self.section_manager.add_section(self.description_section)
        self.section_manager.add_section(self.response_section)
        self.section_manager.add_section(self.input_section)

        # Load background
        self.background_list = arcade.SpriteList()
        self._load_background()

        # Text padding
        self.text_padding = TEXT_PADDING

        # --- Description section content (global Y) ---
        self.description_title = arcade.Text(
            self.current_location["name"],
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
            y=self.input_section.bottom + self.input_section.height - INPUT_PADDING_BOTTOM,
            color=TEXT_COLOR,
            font_size=INPUT_FONT_SIZE,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width - 2 * self.text_padding,
            multiline=True,
            anchor_y="bottom"
        )

    def _load_background(self):
        self.background_list = arcade.SpriteList()
        try:
            texture = arcade.load_texture(self.current_location["background"])
            bg_sprite = arcade.Sprite()
            bg_sprite.texture = texture
            bg_sprite.center_x = self.image_section.width / 2
            bg_sprite.center_y = SCREEN_HEIGHT / 2
            bg_sprite.width = self.image_section.width
            bg_sprite.height = SCREEN_HEIGHT
            self.background_list.append(bg_sprite)
        except Exception as e:
            print(f"Background load failed: {e}")

    def _rebuild_description(self):
        self.description_texts = []
        current_y = SCREEN_HEIGHT - TITLE_PADDING - DESCRIPTION_TITLE_FONT_SIZE - SECTION_TITLE_PADDING

        for line in self.current_location["description"]:
            if not line.strip():
                current_y -= LINE_SPACING
                continue

            txt = arcade.Text(
                line,
                x=self.text_left + self.text_padding,
                y=current_y,
                color=TEXT_COLOR,
                font_size=DESCRIPTION_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY,
                width=self.text_width - 2 * self.text_padding,
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

        # Dividers between right sections (global Y)
        divider_color = DIVIDER_COLOR
        arcade.draw_line(
            self.text_left + 20,
            self.description_section.bottom,
            self.text_left + self.text_width - 20,
            self.description_section.bottom,
            divider_color,
            DIVIDER_THICKNESS
        )
        arcade.draw_line(
            self.text_left + 20,
            self.response_section.bottom,
            self.text_left + self.text_width - 20,
            self.response_section.bottom,
            divider_color,
            DIVIDER_THICKNESS
        )

        # Event section background (reserved)
        arcade.draw_lrbt_rectangle_filled(
            0, SCREEN_WIDTH,
            0, self.event_section_height,
            EVENT_SECTION_BG_COLOR
        )

        # Draw all text (global coordinates)
        self.description_title.draw()
        for txt in self.description_texts:
            txt.draw()
        self.response_text.draw()
        self.input_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            cmd = self.current_input.strip().lower()
            self.current_input = ""

            self.last_response = ""
            self._update_response_display()

            if cmd:
                self.last_response = f"> {cmd}\n"

            response = None

            if cmd in self.current_location["exits"]:
                next_id = self.current_location["exits"][cmd]
                self.current_location = self.game_manager.ship["rooms"][next_id]
                self._load_background()
                self._rebuild_description()
                response = f"You enter the {self.current_location['name']}."
            else:
                if cmd:
                    response = "You can't go that way."

            if response:
                self.last_response += response
                self._update_response_display()

            self._update_input_display()

        elif key == arcade.key.BACKSPACE:
            if self.current_input:
                self.current_input = self.current_input[:-1]
                self._update_input_display()

        elif 32 <= key <= 126:
            self.current_input += chr(key)
            self._update_input_display()