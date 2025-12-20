import arcade
from constants import *


class ShipView(arcade.View):
    """Main view for the player's ship interior using arcade.Text."""

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.current_location = game_manager.get_current_location()

        self.current_input = ""
        self.last_response = ""  # Only the most recent response is kept

        # Cursor blink
        self.cursor_visible = True
        self.blink_timer = 0.0

        # Section manager
        self.section_manager = arcade.SectionManager(self)

        # Left: Image section (70%)
        image_width = int(SCREEN_WIDTH * LEFT_PANEL_RATIO)
        self.image_section = arcade.Section(
            left=0,
            bottom=0,
            width=image_width,
            height=SCREEN_HEIGHT
        )
        self.section_manager.add_section(self.image_section)

        # Right: Full text panel (30%)
        text_left = image_width
        text_width = SCREEN_WIDTH - text_left
        self.text_section = arcade.Section(
            left=text_left,
            bottom=0,
            width=text_width,
            height=SCREEN_HEIGHT
        )
        self.section_manager.add_section(self.text_section)

        # Load background
        self.background_list = arcade.SpriteList()
        self._load_background()

        # Common text positioning
        self.text_x = text_left + 40
        self.text_width = text_width - 80

        # --- UPPER AREA: Fixed room title + description ---
        self.title_text = arcade.Text(
            self.current_location["name"],
            x=self.text_x,
            y=SCREEN_HEIGHT - 60,
            color=ACCENT_COLOR,
            font_size=FONT_SIZE_TITLE,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width,
            multiline=True,
            anchor_y="top"
        )

        self.description_texts = []
        self._rebuild_description()

        # --- LOWER AREA: Split into response + input ---
        self.lower_section_height = int(SCREEN_HEIGHT * 0.45)  # ~45% of screen

        # Response area (top part of lower section)
        self.response_text = arcade.Text(
            "",
            x=self.text_x,
            y=self.lower_section_height - 60,  # Start near top of lower section
            color=TEXT_COLOR,
            font_size=FONT_SIZE_DEFAULT,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width,
            multiline=True,
            anchor_y="top"
        )

        # Input prompt fixed at very bottom
        self.input_text = arcade.Text(
            "> ",
            x=self.text_x,
            y=80,  # Fixed position from bottom
            color=TEXT_COLOR,
            font_size=FONT_SIZE_PROMPT,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width,
            multiline=True,
            anchor_y="bottom"
        )

        # Divider between upper (description) and lower section
        # Optional: another divider between response and input
        self.divider_y = self.lower_section_height
        self.response_input_divider_y = 140  # Adjust based on input height

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
        current_y = SCREEN_HEIGHT - 140

        for line in self.current_location["description"]:
            if not line.strip():
                current_y -= 30
                continue

            msg_text = arcade.Text(
                line,
                x=self.text_x,
                y=current_y,
                color=TEXT_COLOR,
                font_size=FONT_SIZE_DEFAULT,
                font_name=FONT_NAME_PRIMARY,
                width=self.text_width,
                multiline=True,
                anchor_y="top"
            )
            current_y -= msg_text.content_height + 12
            self.description_texts.append(msg_text)

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

        # Overlays
        arcade.draw_lrbt_rectangle_filled(
            self.image_section.left, self.image_section.right,
            self.image_section.bottom, self.image_section.top,
            BACKGROUND_OVERLAY
        )
        arcade.draw_lrbt_rectangle_filled(
            self.text_section.left, self.text_section.right,
            self.text_section.bottom, self.text_section.top,
            PANEL_OVERLAY
        )

        # Divider between upper and lower
        arcade.draw_line(
            self.text_section.left + 20,
            self.divider_y,
            self.text_section.right - 20,
            self.divider_y,
            (100, 150, 200, 180),
            2
        )

        # Optional divider between response and input (comment out if not wanted)
        arcade.draw_line(
            self.text_section.left + 20,
            self.response_input_divider_y,
            self.text_section.right - 20,
            self.response_input_divider_y,
            (80, 120, 160, 140),
            1
        )

        # Draw upper fixed content
        self.title_text.draw()
        for txt in self.description_texts:
            txt.draw()

        # Draw latest response in lower top area
        self.response_text.draw()

        # Draw fixed input prompt at bottom
        self.input_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            cmd = self.current_input.strip().lower()
            self.current_input = ""

            # Clear previous response immediately
            self.last_response = ""
            self._update_response_display()

            if cmd:
                # Optionally show the command itself (comment out if you don't want to see it)
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

        elif 32 <= key <= 126:  # Printable ASCII
            self.current_input += chr(key)
            self._update_input_display()