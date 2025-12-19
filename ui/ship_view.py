# ui/ship_view.py
import arcade
from constants import *

class ShipView(arcade.View):
    """Main view for the player's ship interior using Sections for clean layout."""

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.current_location = game_manager.get_current_location()

        self.current_input = ""
        self.messages = self.current_location["description"][:]  # Copy

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

        # Right: Text panel section (30%)
        text_left = image_width
        self.text_section = arcade.Section(
            left=text_left,
            bottom=0,
            width=SCREEN_WIDTH - text_left,
            height=SCREEN_HEIGHT
        )
        self.section_manager.add_section(self.text_section)

        # Load background for current location
        self.background_list = arcade.SpriteList()
        self._load_background()

    def _load_background(self):
        """Load and fit background image in the image section."""
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

    def on_update(self, delta_time: float):
        self.blink_timer += delta_time
        if self.blink_timer >= 0.5:
            self.blink_timer = 0.0
            self.cursor_visible = not self.cursor_visible

    def on_draw(self):
        self.clear()

        # Image section
        self.background_list.draw()
        arcade.draw_lrbt_rectangle_filled(
            self.image_section.left, self.image_section.right,
            self.image_section.bottom, self.image_section.top,
            BACKGROUND_OVERLAY
        )

        # Text panel — solid background
        arcade.draw_lrbt_rectangle_filled(
            self.text_section.left, self.text_section.right,
            self.text_section.bottom, self.text_section.top,
            PANEL_OVERLAY
        )

        # Text in right panel
        x = self.text_section.left + 40
        y = SCREEN_HEIGHT - 80

        # Room title
        arcade.draw_text(
            self.current_location["name"],
            x, y,
            ACCENT_COLOR, FONT_SIZE_TITLE,
            font_name=FONT_NAME_PRIMARY
        )
        y -= 100

        # Description and messages
        for line in self.messages:
            arcade.draw_text(
                line,
                x, y,
                TEXT_COLOR, FONT_SIZE_DEFAULT,
                width=self.text_section.width - 80,
                font_name=FONT_NAME_PRIMARY
            )
            y -= 45

        # Input prompt
        cursor = "█" if self.cursor_visible else " "
        arcade.draw_text(
            f"> {self.current_input}{cursor}",
            x, 100,
            TEXT_COLOR, FONT_SIZE_PROMPT,
            font_name=FONT_NAME_PRIMARY
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            cmd = self.current_input.strip().lower()
            self.current_input = ""
            self.messages.append(f"> {cmd}")

            if cmd in self.current_location["exits"]:
                next_id = self.current_location["exits"][cmd]
                self.current_location = self.game_manager.ship["rooms"][next_id]
                self.messages = self.current_location["description"][:]
                self._load_background()
            else:
                self.messages.append("You can't go that way.")
        elif key == arcade.key.BACKSPACE:
            self.current_input = self.current_input[:-1]
        elif 32 <= key <= 126:
            self.current_input += chr(key)