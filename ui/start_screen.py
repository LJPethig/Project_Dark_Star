# ui/start_screen.py
import arcade
from constants import *
from game_manager import GameManager
from ui.ship_view import ShipView

class StartScreen(arcade.View):
    """Start screen where the player enters their name and ship name."""

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.game_manager = GameManager()

        # Load background image using SpriteList (correct for Arcade 3.3.3)
        self.background_list = arcade.SpriteList()
        try:
            texture = arcade.load_texture("resources/images/start_screen.png")
            bg_sprite = arcade.Sprite()
            bg_sprite.texture = texture
            bg_sprite.center_x = SCREEN_WIDTH / 2
            bg_sprite.center_y = SCREEN_HEIGHT / 2
            bg_sprite.width = SCREEN_WIDTH
            bg_sprite.height = SCREEN_HEIGHT
            self.background_list.append(bg_sprite)
        except Exception as e:
            print(f"Start screen background load failed: {e}")

    def on_draw(self):
        """Draw the start screen."""
        self.clear()

        # Draw background using SpriteList
        self.background_list.draw()

        # Dark overlay for text readability
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, PANEL_OVERLAY)

        # Title
        arcade.draw_text(
            "PROJECT DARK STAR",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 120,
            ACCENT_COLOR, FONT_SIZE_TITLE,
            anchor_x="center", font_name=FONT_NAME_PRIMARY
        )

        # Flavor introduction
        intro_lines = [
            "The year is 2178.",
            "Humanity has spread across the solar system and beyond.",
            "Corporations dominate, but out in the black, independent traders still carve out a living.",
            "",
            "You are one of them — pilot, engineer, survivor.",
            "Your ship is your home, your lifeline, your freedom."
        ]
        y = SCREEN_HEIGHT - 290
        for line in intro_lines:
            arcade.draw_text(
                line,
                SCREEN_WIDTH / 2, y,
                TEXT_COLOR, FONT_SIZE_DEFAULT,
                anchor_x="center", font_name=FONT_NAME_PRIMARY
            )
            y -= 40

        # Instructions
        arcade.draw_text(
            "Press ENTER to continue",
            SCREEN_WIDTH / 2, 100,
            (150, 150, 150, 255), FONT_SIZE_SMALL,
            anchor_x="center", font_name=FONT_NAME_PRIMARY
        )

    def on_key_press(self, key, modifiers):
        """Handle input."""
        if key == arcade.key.ENTER:
            self.game_manager.create_new_game()
            ship_view = ShipView(self.game_manager)
            self.window.show_view(ship_view)
