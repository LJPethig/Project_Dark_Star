import arcade
from constants import *


class ShipView(arcade.View):
    """Main view for the player's ship interior using arcade.Text for clean text rendering."""

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.current_location = game_manager.get_current_location()

        self.current_input = ""
        self.messages = self.current_location["description"][:]  # Copy list

        # Cursor blink
        self.cursor_visible = True
        self.blink_timer = 0.0

        # Section manager
        self.section_manager = arcade.SectionManager(self)

        # Left: Image section (e.g., 70%)
        image_width = int(SCREEN_WIDTH * LEFT_PANEL_RATIO)
        self.image_section = arcade.Section(
            left=0,
            bottom=0,
            width=image_width,
            height=SCREEN_HEIGHT
        )
        self.section_manager.add_section(self.image_section)

        # Right: Text panel section (e.g., 30%)
        text_left = image_width
        self.text_section = arcade.Section(
            left=text_left,
            bottom=0,
            width=SCREEN_WIDTH - text_left,
            height=SCREEN_HEIGHT
        )
        self.section_manager.add_section(self.text_section)

        # Load background
        self.background_list = arcade.SpriteList()
        self._load_background()

        # Text objects (persistent)
        self.text_x = self.text_section.left + 40
        self.text_width = self.text_section.width - 80

        # Title
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

        # Input prompt at bottom
        self.input_text = arcade.Text(
            "> ",
            x=self.text_x,
            y=100,
            color=TEXT_COLOR,
            font_size=FONT_SIZE_PROMPT,
            font_name=FONT_NAME_PRIMARY,
            width=self.text_width,
            multiline=True,
            anchor_y="bottom"
        )

        # List of message Text objects
        self.message_texts = []
        self._rebuild_messages()

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

    def _rebuild_messages(self):
        """Rebuild message display — oldest messages at top, newest at bottom."""
        self.message_texts = []

        current_y = SCREEN_HEIGHT - 140  # Start below the title

        # Show last 30 messages, oldest first in the list
        for line in self.messages[-30:]:
            if not line.strip():  # Blank line
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
            self.message_texts.append(msg_text)

        # No reverse() needed — order is now correct!

    def _update_input_display(self):
        """Update the input line with blinking cursor."""
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

        # Semi-transparent overlay on image section
        arcade.draw_lrbt_rectangle_filled(
            self.image_section.left, self.image_section.right,
            self.image_section.bottom, self.image_section.top,
            BACKGROUND_OVERLAY
        )

        # Solid background for text panel
        arcade.draw_lrbt_rectangle_filled(
            self.text_section.left, self.text_section.right,
            self.text_section.bottom, self.text_section.top,
            PANEL_OVERLAY
        )

        # Draw all text objects
        self.title_text.draw()
        for msg in self.message_texts:
            msg.draw()
        self.input_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            cmd = self.current_input.strip().lower()
            self.current_input = ""

            if cmd:  # Only add non-empty commands
                self.messages.append(f"> {cmd}")

            # Handle navigation
            if cmd in self.current_location["exits"]:
                next_id = self.current_location["exits"][cmd]
                self.current_location = self.game_manager.ship["rooms"][next_id]
                self.messages = self.current_location["description"][:]
                self.title_text.text = self.current_location["name"]
                self._load_background()
            else:
                if cmd:
                    self.messages.append("You can't go that way.")

            # Rebuild message display and clear input
            self._rebuild_messages()
            self._update_input_display()

        elif key == arcade.key.BACKSPACE:
            self.current_input = self.current_input[:-1]
            self._update_input_display()

        elif 32 <= key <= 126:  # Printable ASCII
            self.current_input += chr(key)
            self._update_input_display()