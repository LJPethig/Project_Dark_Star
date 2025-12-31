# ui/inventory_view.py
import arcade
from constants import *

class InventoryView(arcade.View):
    """Full-screen view for player inventory or ship cargo."""

    ITEM_SPACING = 40  # Vertical spacing between each item line

    def __init__(self, game_manager, is_player: bool = True):
        super().__init__()
        self.game_manager = game_manager
        self.is_player = is_player  # True = player inventory, False = ship cargo
        self.previous_view = None

    def on_draw(self):
        self.clear()
        arcade.set_background_color(BACKGROUND_COLOR)  # From constants

        # Title (in accent color)
        if self.is_player:
            title = "YOUR INVENTORY"
        else:
            current_location = self.game_manager.get_current_location()
            room_name = current_location.name
            title = f"{room_name.upper()} INVENTORY"
        arcade.draw_text(
            title,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - TITLE_PADDING,
            ACCENT_COLOR,
            DESCRIPTION_TITLE_FONT_SIZE,
            anchor_x="center",
            font_name=FONT_NAME_PRIMARY
        )

        # Get items
        if self.is_player:
            item_ids = self.game_manager.get_player_inventory()
            items = [self.game_manager.items.get(item_id) for item_id in item_ids if item_id in self.game_manager.items]
        else:
            current_location = self.game_manager.get_current_location()
            room_id = current_location.id
            items = self.game_manager.get_cargo_for_room(room_id)

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
            current_y = SCREEN_HEIGHT - TITLE_PADDING - DESCRIPTION_TITLE_FONT_SIZE - SECTION_TITLE_PADDING

            for item in items:
                # Item name in ACCENT_COLOR
                item_name = item["name"] if isinstance(item, dict) else item.name
                arcade.draw_text(
                    item_name,
                    TEXT_PADDING,
                    current_y,
                    ACCENT_COLOR,
                    INPUT_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY
                )

                # Description in TEXT_COLOR
                desc = item["description"] if isinstance(item, dict) else item.description
                desc = desc[:150] + "..." if len(desc) > 150 else desc

                arcade.draw_text(
                    f"- {desc}",
                    TEXT_PADDING + 300,  # Fixed offset — adjust 300 to taste (e.g. 250–400)
                    current_y,
                    TEXT_COLOR,
                    INPUT_FONT_SIZE,
                    font_name=FONT_NAME_PRIMARY,
                    multiline=True,
                    width=SCREEN_WIDTH - (TEXT_PADDING + 300 + TEXT_PADDING)
                )

                current_y -= self.ITEM_SPACING

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