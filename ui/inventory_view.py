# ui/inventory_view.py
import arcade
from constants import *

class InventoryView(arcade.View):
    """Full-screen view for player inventory."""

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.previous_view = None

    def on_draw(self):
        self.clear()
        arcade.set_background_color(BACKGROUND_COLOR)

        # Title
        title_y = SCREEN_HEIGHT - INVENTORY_TOP_PADDING
        arcade.draw_text(
            "YOUR INVENTORY",
            SCREEN_WIDTH / 2,
            title_y,
            OBJECT_COLOR,
            DESCRIPTION_TITLE_FONT_SIZE,
            anchor_x="center",
            font_name=FONT_NAME_PRIMARY
        )

        current_y = title_y - DESCRIPTION_TITLE_FONT_SIZE - 40  # basic gap

        # Loose inventory section
        loose_items = self.game_manager.player.get_inventory()
        if loose_items:
            arcade.draw_text(
                "Carried Items:",
                TEXT_PADDING,
                current_y,
                OBJECT_COLOR,
                INPUT_FONT_SIZE + 2,  # slightly bolder
                font_name=FONT_NAME_PRIMARY
            )
            current_y -= 30

            for item in loose_items:
                arcade.draw_text(
                    item.name,
                    TEXT_PADDING + 20,
                    current_y,
                    OBJECT_COLOR,
                    INPUT_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY
                )

                desc = item.description or "No description available."
                arcade.draw_text(
                    f"- {desc}",
                    TEXT_PADDING + 250,
                    current_y,
                    TEXT_COLOR,
                    INPUT_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY,
                    multiline=True,
                    width=SCREEN_WIDTH - (TEXT_PADDING + 250 + TEXT_PADDING),
                    anchor_y="top"
                )

                # Crude height estimation
                current_y -= 80 + (len(desc) // 80) * INPUT_FONT_SIZE

            current_y -= 40  # gap between sections

        # Equipped section
        equipped = self.game_manager.player.equipped
        if any(equipped.values()):  # only show if something is equipped
            arcade.draw_text(
                "Equipped:",
                TEXT_PADDING,
                current_y,
                OBJECT_COLOR,
                INPUT_FONT_SIZE + 2,
                font_name=FONT_NAME_PRIMARY
            )
            current_y -= 30

            for slot, item in equipped.items():
                name = item.name if item else "Nothing"
                arcade.draw_text(
                    f"{slot.capitalize()}: {name}",
                    TEXT_PADDING + 20,
                    current_y,
                    OBJECT_COLOR if item else TEXT_COLOR,
                    INPUT_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY
                )
                current_y -= INPUT_FONT_SIZE + 10  # simple spacing

        # Empty case (if no loose + no equipped)
        if not loose_items and not any(equipped.values()):
            arcade.draw_text(
                "Empty",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                TEXT_COLOR,
                DESCRIPTION_FONT_SIZE,
                anchor_x="center",
                font_name=FONT_NAME_PRIMARY
            )

        # Footer
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