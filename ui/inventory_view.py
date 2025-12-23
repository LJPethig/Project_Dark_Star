# ui/inventory_view.py
import arcade
from constants import *

class InventoryView(arcade.View):
    """Full-screen view for player inventory or ship cargo."""

    def __init__(self, game_manager, is_player: bool = True):
        super().__init__()
        self.game_manager = game_manager
        self.is_player = is_player  # True = player inventory, False = ship cargo
        self.previous_view = None

    def on_draw(self):
        self.clear()
        arcade.set_background_color(BACKGROUND_COLOR)  # From constants

        # Title
        title = "YOUR GEAR" if self.is_player else "SHIP CARGO HOLD"
        arcade.draw_text(
            title,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - TITLE_PADDING,
            ACCENT_COLOR,
            DESCRIPTION_TITLE_FONT_SIZE,
            anchor_x="center",
            font_name=FONT_NAME_PRIMARY
        )

        items = self.game_manager.get_player_inventory() if self.is_player else self.game_manager.get_ship_cargo()
        if not items:
            arcade.draw_text(
                "Empty",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                TEXT_COLOR,
                DESCRIPTION_FONT_SIZE,
                anchor_x="center",
                font_name=FONT_NAME_PRIMARY
            )
        else:
            # Start drawing items from top
            current_y = SCREEN_HEIGHT - TITLE_PADDING - DESCRIPTION_TITLE_FONT_SIZE - SECTION_TITLE_PADDING

            for item in items:
                # Item name
                arcade.draw_text(
                    item.name,
                    TEXT_PADDING,
                    current_y,
                    ACCENT_COLOR,
                    DESCRIPTION_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY
                )

                # Item description (truncated if too long)
                desc = item.description[:100] + "..." if len(item.description) > 100 else item.description
                arcade.draw_text(
                    desc,
                    TEXT_PADDING + 20,  # Slight indent
                    current_y - LINE_SPACING,
                    TEXT_COLOR,
                    INPUT_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY,
                    multiline=True,
                    width=SCREEN_WIDTH - TEXT_PADDING * 4
                )

                # Move down for next item
                current_y -= 80  # Fixed spacing between items (can be made constant later)

        # Footer instructions
        arcade.draw_text(
            "Press ESC or I to return",
            SCREEN_WIDTH / 2,
            TEXT_PADDING,
            TEXT_COLOR,
            INPUT_FONT_SIZE,
            anchor_x="center",
            font_name=FONT_NAME_PRIMARY
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE or (key == arcade.key.I and not modifiers):
            if self.previous_view:
                self.window.show_view(self.previous_view)
            else:
                self.window.close()