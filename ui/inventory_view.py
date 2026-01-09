# ui/inventory_view.py
import arcade
from constants import *

class InventoryView(arcade.View):
    """Full-screen view for player inventory."""

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.previous_view = None

        # Selection state
        self.items = []          # Flat list of (display_text, item_or_none)
        self.selected_index = 0
        self.scroll_offset = 0

    def setup(self):
        """Build the display list and reset selection."""
        player = self.game_manager.player
        self.items = []

        # Worn section - fixed order
        self.items.append(("WORN:", None))
        slot_order = ["head", "body", "torso", "waist", "feet"]
        for slot in slot_order:
            item = player.equipped.get(slot)
            text = f"{slot.capitalize()}: {item.name if item else 'Nothing'}"
            self.items.append((text, item))

        # Carried section
        if player.get_inventory():
            self.items.append(("CARRIED:", None))
            for item in player.get_inventory():
                self.items.append((item.name, item))

        # Reset selection
        self.selected_index = 0
        self.scroll_offset = 0
        if self.items:
            self.selected_index = min(self.selected_index, len(self.items) - 1)

    def on_show_view(self):
        self.setup()

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

        # Empty case
        if not self.items:
            arcade.draw_text(
                INVENTORY_EMPTY_TEXT,
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                TEXT_COLOR,
                DESCRIPTION_FONT_SIZE,
                anchor_x="center",
                font_name=FONT_NAME_PRIMARY
            )
            self._draw_footer()
            return

        # Left side: list
        list_left = TEXT_PADDING
        list_width = SCREEN_WIDTH // 2 - TEXT_PADDING * 2
        list_top = title_y - DESCRIPTION_TITLE_FONT_SIZE - INVENTORY_HEADER_GAP
        visible_lines = (SCREEN_HEIGHT - INVENTORY_TOP_PADDING - EVENT_SECTION_HEIGHT - 100) // 30

        # Auto-scroll to keep selected in view
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_lines:
            self.scroll_offset = self.selected_index - visible_lines + 1

        current_y = list_top
        for i in range(self.scroll_offset, len(self.items)):
            if current_y < EVENT_SECTION_HEIGHT + 50:
                break
            display_text, item = self.items[i]
            is_header = item is None
            is_selected = (i == self.selected_index)

            if is_selected:
                arcade.draw_lbwh_rectangle_filled(
                    left=list_left,
                    bottom=current_y - INPUT_FONT_SIZE - 5,
                    width=list_width,
                    height=(current_y + 5) - (current_y - INPUT_FONT_SIZE - 5),
                    color=INVENTORY_HIGHLIGHT_BG
                )
                text_color = INVENTORY_HIGHLIGHT_TEXT
            else:
                text_color = OBJECT_COLOR if not is_header else OBJECT_COLOR
                text_color = TEXT_COLOR if not item and not is_header else text_color

            indent = 0 if is_header else INVENTORY_ITEM_INDENT
            font_size = INPUT_FONT_SIZE + 2 if is_header else INPUT_FONT_SIZE

            arcade.draw_text(
                display_text,
                list_left + indent,
                current_y,
                text_color,
                font_size,
                font_name=FONT_NAME_PRIMARY
            )
            current_y -= font_size + INVENTORY_LINE_GAP if is_header else INPUT_FONT_SIZE + INVENTORY_LINE_GAP

        # Right side: detail panel
        selected_item = None
        for i, (_, item) in enumerate(self.items):
            if i == self.selected_index and item is not None:
                selected_item = item
                break

        right_left = SCREEN_WIDTH // 2
        panel_width = SCREEN_WIDTH // 2 - TEXT_PADDING

        if selected_item:
            # Image (top 50%)
            image_path = f"resources/images/{selected_item.id}.png"
            texture = None
            try:
                texture = arcade.load_texture(image_path)
            except Exception:
                texture = arcade.load_texture("resources/images/image_missing.png")

            if texture:
                # Target dimensions = top half of right panel
                target_width = panel_width - TEXT_PADDING * 2
                target_height = (SCREEN_HEIGHT // 2) - INVENTORY_TOP_PADDING * 2

                orig_width = texture.width
                orig_height = texture.height

                if orig_width > 0 and orig_height > 0:
                    scale_w = target_width / orig_width
                    scale_h = target_height / orig_height
                    scale = min(scale_w, scale_h)

                    sprite = arcade.Sprite()
                    sprite.texture = texture
                    sprite.scale = scale
                    sprite.center_x = right_left + panel_width / 2
                    sprite.center_y = SCREEN_HEIGHT - INVENTORY_TOP_PADDING - (target_height / 2)

                    # Use a temporary SpriteList to draw (3.3.3 style)
                    temp_list = arcade.SpriteList()
                    temp_list.append(sprite)
                    temp_list.draw()
            else:
                # Ultimate fallback if both textures fail
                arcade.draw_text(
                    "No image",
                    right_left + panel_width / 2,
                    SCREEN_HEIGHT // 2,
                    TEXT_COLOR,
                    INPUT_FONT_SIZE,
                    anchor_x="center",
                    font_name=FONT_NAME_PRIMARY
                )

            # Description (bottom 50%)
            desc = selected_item.description or "No description available."
            arcade.draw_text(
                desc,
                right_left + TEXT_PADDING,
                SCREEN_HEIGHT // 2 - 40,
                TEXT_COLOR,
                INPUT_FONT_SIZE,
                width=panel_width,
                multiline=True,
                font_name=FONT_NAME_PRIMARY
            )
        else:
            # No item selected (header) - show hint
            arcade.draw_text(
                "Select an item to view details",
                right_left + TEXT_PADDING,
                SCREEN_HEIGHT // 2,
                TEXT_COLOR,
                INPUT_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY
            )

        self._draw_footer()

    def _draw_footer(self):
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
            return

        if key == arcade.key.UP and self.selected_index > 0:
            self.selected_index -= 1
        elif key == arcade.key.DOWN and self.selected_index < len(self.items) - 1:
            self.selected_index += 1
        else:
            return