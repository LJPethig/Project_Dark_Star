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
            ("Head  :",  player.head_slot),
            ("Body  :",  player.body_slot),
            ("Torso :", player.torso_slot),
            ("Waist :", player.waist_slot),
            ("Feet  :",  player.feet_slot),
        ]

        self.carried_items = player.get_inventory().copy()

        self.selected_index = 0
        self.scroll_offset = 0

        # Auto-select first non-empty slot (optional, controlled by constant)
        if INVENTORY_SKIP_EMPTY_SLOTS:
            # First try worn slots
            for idx, (_, item) in enumerate(self.worn_slots):
                if item is not None:
                    self.selected_index = idx
                    break
            else:
                # If all worn empty, jump to first carried (if any)
                if self.carried_items:
                    self.selected_index = len(self.worn_slots)


    def on_show_view(self):
        self.setup()

    def on_draw(self):
        self.clear()
        arcade.set_background_color(BACKGROUND_COLOR)

        # Title
        title_y = SCREEN_HEIGHT - INVENTORY_TOP_PADDING
        arcade.draw_text(
            "YOUR INVENTORY",
            SCREEN_WIDTH / 4,
            title_y,
            TITLE_COLOR,
            FONT_SIZE_TITLE,
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
        list_top = title_y - DESCRIPTION_TITLE_FONT_SIZE - INVENTORY_HEADER_GAP

        current_y = list_top

        # WORN header
        arcade.draw_text(
            "WORN",
            list_left,
            current_y,
            TITLE_COLOR,
            FONT_SIZE_SUB_HEADING,
            font_name=FONT_NAME_PRIMARY)

        current_y -= FONT_SIZE_SUB_HEADING + INVENTORY_HEADER_GAP

        # Worn slots
        for idx, (slot_name, item) in enumerate(self.worn_slots):
            is_selected = (self.selected_index == idx)

            # Slot label
            slot_text = slot_name
            arcade.draw_text(
                slot_text,
                list_left,
                current_y,
                TITLE_COLOR,
                FONT_SIZE_DEFAULT,
                font_name=FONT_NAME_PRIMARY
            )

            # Measure slot width (still needed for item positioning)
            slot_measure = arcade.Text(
                slot_text,
                0, 0,
                TITLE_COLOR,
                FONT_SIZE_DEFAULT,
                font_name=FONT_NAME_PRIMARY
            )
            slot_w = slot_measure.content_width

            # Item name - larger + bold when selected
            item_text = item.name if item else "Nothing"
            item_color = (
                INVENTORY_HIGHLIGHT_TEXT if is_selected else
                TEXT_COLOR if item_text == "Nothing" else
                PORTABLE_OBJECT_COLOR
            )
            item_size = FONT_SIZE_INVENTORY_HIGHLIGHTED if is_selected else FONT_SIZE_SMALL

            arcade.draw_text(
                item_text,
                list_left + slot_w + INVENTORY_HORIZONTAL_PADDING,
                current_y,
                item_color,
                item_size,
                font_name=FONT_NAME_PRIMARY,
                bold=is_selected  # Enable bold for selected items
            )

            current_y -= FONT_SIZE_SMALL + INVENTORY_VERTICAL_PADDING + INVENTORY_LINE_GAP

        # CARRIED header
        current_y -= INVENTORY_SECTION_GAP
        arcade.draw_text("CARRIED",
                         list_left,
                         current_y,
                         TITLE_COLOR,
                         FONT_SIZE_SUB_HEADING,
                         font_name=FONT_NAME_PRIMARY
                         )

        current_y -= FONT_SIZE_SUB_HEADING + INVENTORY_HEADER_GAP

        # Carried items
        for carried_idx, item in enumerate(self.carried_items):
            idx = len(self.worn_slots) + carried_idx
            is_selected = (self.selected_index == idx)

            item_color = INVENTORY_HIGHLIGHT_TEXT if is_selected else PORTABLE_OBJECT_COLOR
            item_size = FONT_SIZE_INVENTORY_HIGHLIGHTED if is_selected else FONT_SIZE_SMALL

            arcade.draw_text(
                item.name,
                list_left,
                current_y,
                item_color,
                item_size,
                font_name=FONT_NAME_PRIMARY,
                bold=is_selected
            )

            current_y -= FONT_SIZE_SMALL + INVENTORY_VERTICAL_PADDING + INVENTORY_LINE_GAP

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
                    sprite.center_y = INVENTORY_IMAGE_CENTER_Y

                    temp_list = arcade.SpriteList()
                    temp_list.append(sprite)
                    temp_list.draw()

            desc = selected_item.description or "No description available."
            arcade.draw_text(
                desc,
                right_left + TEXT_PADDING,
                SCREEN_HEIGHT // 2 - 40,
                TEXT_COLOR,
                FONT_SIZE_SMALL,
                width=panel_width,
                multiline=True,
                font_name=FONT_NAME_PRIMARY
            )

        # Outer window border
        arcade.draw_lrbt_rectangle_outline(
            0, SCREEN_WIDTH, 0, SCREEN_HEIGHT,
            DIVIDER_COLOR, DIVIDER_THICKNESS
        )

        # Vertical divider between left list and right panel
        arcade.draw_line(
            SCREEN_WIDTH // 2, 0,
            SCREEN_WIDTH // 2, SCREEN_HEIGHT,
            DIVIDER_COLOR, DIVIDER_THICKNESS
        )

        self._draw_footer()

    def _draw_footer(self):
        status_text = self.game_manager.player.get_carry_status()

        arcade.draw_text(
            status_text,
            (SCREEN_WIDTH / 4) * 1,
            TEXT_PADDING,  # slightly higher than return instruction
            TEXT_COLOR,  # soft cyan/white for visibility
            FONT_SIZE_SMALL,
            anchor_x="center",
            font_name=FONT_NAME_PRIMARY
        )

        arcade.draw_text(
            "Press ESC or I to return",
            (SCREEN_WIDTH / 4) * 3,
            TEXT_PADDING,
            TEXT_COLOR,
            FONT_SIZE_SMALL,
            anchor_x="center",
            font_name=FONT_NAME_PRIMARY
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE or (key == arcade.key.I and not modifiers):
            if self.previous_view:
                self.window.show_view(self.previous_view)
            return

        if not INVENTORY_SKIP_EMPTY_ON_NAV:
            # Normal behavior if disabled
            total_slots = len(self.worn_slots) + len(self.carried_items)
            if key == arcade.key.UP and self.selected_index > 0:
                self.selected_index -= 1
            elif key == arcade.key.DOWN and self.selected_index < total_slots - 1:
                self.selected_index += 1
            return

        # Skip empty slots logic
        total_slots = len(self.worn_slots) + len(self.carried_items)

        if key == arcade.key.UP:
            new_index = self.selected_index - 1
            while new_index >= 0:
                if new_index < len(self.worn_slots):
                    if self.worn_slots[new_index][1] is not None:
                        self.selected_index = new_index
                        break
                else:
                    carried_idx = new_index - len(self.worn_slots)
                    if carried_idx >= 0 and self.carried_items[carried_idx]:
                        self.selected_index = new_index
                        break
                new_index -= 1

        elif key == arcade.key.DOWN:
            new_index = self.selected_index + 1
            while new_index < total_slots:
                if new_index < len(self.worn_slots):
                    if self.worn_slots[new_index][1] is not None:
                        self.selected_index = new_index
                        break
                else:
                    carried_idx = new_index - len(self.worn_slots)
                    if carried_idx < len(self.carried_items) and self.carried_items[carried_idx]:
                        self.selected_index = new_index
                        break
                new_index += 1