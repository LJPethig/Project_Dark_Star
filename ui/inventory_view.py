# ui/inventory_view.py
import arcade
from constants import *

class InventoryView(arcade.View):
    """Full-screen view for player inventory."""

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.previous_view = None

        # Separate collections — no flat strings, no parsing
        self.worn_slots = []   # list of (slot_name, item)
        self.carried_items = []
        self.selected_index = 0  # 0-4 worn, 5+ carried
        self.scroll_offset = 0

    def setup(self):
        player = self.game_manager.player

        self.worn_slots = [
            ("Head",  player.head_slot),
            ("Body",  player.body_slot),
            ("Torso", player.torso_slot),
            ("Waist", player.waist_slot),
            ("Feet",  player.feet_slot),
        ]

        self.carried_items = player.get_inventory().copy()

        self.selected_index = 0
        self.scroll_offset = 0

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
            TITLE_COLOR,
            DESCRIPTION_TITLE_FONT_SIZE,
            anchor_x="center",
            font_name=FONT_NAME_PRIMARY
        )

        # Empty case
        if not self.worn_slots and not self.carried_items:
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

        current_y = list_top

        # WORN header
        arcade.draw_text("WORN", list_left, current_y, TITLE_COLOR, INPUT_FONT_SIZE + 2, font_name=FONT_NAME_PRIMARY)
        current_y -= (INPUT_FONT_SIZE + 2) + INVENTORY_HEADER_GAP

        # Worn slots
        for idx, (slot_name, item) in enumerate(self.worn_slots):
            is_selected = (self.selected_index == idx)

            # Slot label (bigger, TITLE_COLOR, flush left)
            slot_text = f"{slot_name}:"
            arcade.draw_text(
                slot_text,
                list_left,
                current_y,
                TITLE_COLOR,
                INPUT_FONT_SIZE + 2,
                font_name=FONT_NAME_PRIMARY
            )

            # Measure slot width
            slot_measure = arcade.Text(
                slot_text,
                0, 0,
                TITLE_COLOR,
                INPUT_FONT_SIZE + 2,
                font_name=FONT_NAME_PRIMARY
            )
            slot_w = slot_measure.content_width

            # Item name
            item_text = item.name if item else "Nothing"
            item_color = INVENTORY_HIGHLIGHT_TEXT if is_selected else TEXT_COLOR

            # Measure item text width for tight highlight
            item_measure = arcade.Text(
                item_text,
                0, 0,
                item_color,
                INPUT_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY
            )
            item_text_w = item_measure.content_width

            # Highlight — tight box around item text
            if is_selected:
                h_padding = 10   # each side
                v_padding = 2    # top/bottom
                line_height = INPUT_FONT_SIZE + INVENTORY_LINE_GAP

                item_start_x = list_left + slot_w + 10
                item_width = item_text_w + (h_padding * 2)

                arcade.draw_lbwh_rectangle_filled(
                    left=item_start_x - h_padding,
                    bottom=current_y - INPUT_FONT_SIZE - v_padding + 2,  # lift to center text
                    width=item_width,
                    height=line_height + (v_padding * 2),
                    color=INVENTORY_HIGHLIGHT_BG
                )

            # Draw item name
            arcade.draw_text(
                item_text,
                list_left + slot_w + 10,
                current_y,
                item_color,
                INPUT_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY
            )

            current_y -= (INPUT_FONT_SIZE + 12) + INVENTORY_LINE_GAP  # ← increased from +2 to +12 for breathing room

        # CARRIED header
        current_y -= INVENTORY_SECTION_GAP
        arcade.draw_text("CARRIED", list_left, current_y, TITLE_COLOR, INPUT_FONT_SIZE + 2, font_name=FONT_NAME_PRIMARY)
        current_y -= (INPUT_FONT_SIZE + 2) + INVENTORY_HEADER_GAP

        # Carried items
        for carried_idx, item in enumerate(self.carried_items):
            idx = len(self.worn_slots) + carried_idx
            is_selected = (self.selected_index == idx)

            item_color = INVENTORY_HIGHLIGHT_TEXT if is_selected else TEXT_COLOR
            item_measure = arcade.Text(
                item.name,
                0, 0,
                item_color,
                INPUT_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY
            )
            item_text_w = item_measure.content_width

            if is_selected:
                h_padding = 10
                v_padding = 2
                line_height = INPUT_FONT_SIZE + INVENTORY_LINE_GAP

                item_start_x = list_left + INVENTORY_ITEM_INDENT
                item_width = item_text_w + (h_padding * 2)

                arcade.draw_lbwh_rectangle_filled(
                    left=item_start_x - h_padding,
                    bottom=current_y - INPUT_FONT_SIZE - v_padding + 2,
                    width=item_width,
                    height=line_height + (v_padding * 2),
                    color=INVENTORY_HIGHLIGHT_BG
                )

            arcade.draw_text(
                item.name,
                list_left + INVENTORY_ITEM_INDENT,
                current_y,
                item_color,
                INPUT_FONT_SIZE,
                font_name=FONT_NAME_PRIMARY
            )

            current_y -= INPUT_FONT_SIZE + 8 + INVENTORY_LINE_GAP  # ← +8 for normal font (was +0)

        # Right side: detail panel
        if self.selected_index < len(self.worn_slots):
            selected_item = self.worn_slots[self.selected_index][1]
        else:
            carried_idx = self.selected_index - len(self.worn_slots)
            selected_item = self.carried_items[carried_idx] if carried_idx < len(self.carried_items) else None

        right_left = SCREEN_WIDTH // 2
        panel_width = SCREEN_WIDTH // 2 - TEXT_PADDING

        if selected_item:
            image_path = f"resources/images/{selected_item.id}.png"
            texture = None
            try:
                texture = arcade.load_texture(image_path)
            except Exception:
                texture = arcade.load_texture("resources/images/image_missing.png")

            if texture:
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

                    temp_list = arcade.SpriteList()
                    temp_list.append(sprite)
                    temp_list.draw()
            else:
                arcade.draw_text(
                    "No image",
                    right_left + panel_width / 2,
                    SCREEN_HEIGHT // 2,
                    TEXT_COLOR,
                    INPUT_FONT_SIZE,
                    anchor_x="center",
                    font_name=FONT_NAME_PRIMARY
                )

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

        total_slots = len(self.worn_slots) + len(self.carried_items)

        if key == arcade.key.UP and self.selected_index > 0:
            self.selected_index -= 1
        elif key == arcade.key.DOWN and self.selected_index < total_slots - 1:
            self.selected_index += 1