# ui/drawing.py
import arcade
from constants import *


class DrawingManager:
    """Handles all rendering and drawing logic for ShipView."""

    def __init__(self, view):
        self.view = view
        self.background_list = arcade.SpriteList()

    def _create_scaled_sprite(self, image_path: str) -> None:
        """
        Shared logic to load an image, scale it to fit the image section
        while preserving aspect ratio, and add it to the background SpriteList.
        """
        self.background_list = arcade.SpriteList()

        try:
            texture = arcade.load_texture(image_path)
            if not texture:
                print(f"Failed to load texture: {image_path}")
                return

            # Target dimensions = image section area
            target_width = self.view.image_section.width
            target_height = SCREEN_HEIGHT - EVENT_SECTION_HEIGHT

            orig_width = texture.width
            orig_height = texture.height
            if orig_width == 0 or orig_height == 0:
                return

            scale_w = target_width / orig_width
            scale_h = target_height / orig_height
            scale = min(scale_w, scale_h)

            bg_sprite = arcade.Sprite()
            bg_sprite.texture = texture
            bg_sprite.scale = scale

            bg_sprite.center_x = self.view.image_section.left + target_width / 2
            bg_sprite.center_y = self.view.image_section.bottom + target_height / 2

            self.background_list.append(bg_sprite)

        except Exception as e:
            print(f"Background load failed ({image_path}): {e}")

    def load_background(self):
        """Load and scale the current room's background image."""
        current_location = self.view.game_manager.get_current_location()
        self._create_scaled_sprite(current_location.background)

    def draw_background(self):
        """Draw the background image."""
        self.background_list.draw()

    def draw_overlay(self):
        """Draw overlay on image section."""
        arcade.draw_lrbt_rectangle_filled(
            self.view.image_section.left, self.view.image_section.right,
            self.view.image_section.bottom, self.view.image_section.top,
            BACKGROUND_OVERLAY
        )

    def draw_window_border(self):
        """Draw outer window border."""
        arcade.draw_lrbt_rectangle_outline(
            0, SCREEN_WIDTH, 0, SCREEN_HEIGHT,
            DIVIDER_COLOR, DIVIDER_THICKNESS
        )

    def draw_dividers(self):
        """Draw all UI dividers."""
        divider_color = DIVIDER_COLOR

        # Divider between image and text sections
        arcade.draw_line(
            self.view.text_left,
            self.view.event_section_height,
            self.view.text_left,
            SCREEN_HEIGHT,
            divider_color,
            DIVIDER_THICKNESS
        )

        # Divider at bottom of description section
        arcade.draw_line(
            self.view.text_left,
            self.view.description_section.bottom,
            self.view.text_left + self.view.text_width,
            self.view.description_section.bottom,
            divider_color,
            DIVIDER_THICKNESS
        )

        # Divider at bottom of response section
        arcade.draw_line(
            self.view.text_left,
            self.view.response_section.bottom,
            self.view.text_left + self.view.text_width,
            self.view.response_section.bottom,
            divider_color,
            DIVIDER_THICKNESS
        )

        # Divider at top of event section
        arcade.draw_line(
            0, 60, SCREEN_WIDTH, 60,
            divider_color,
            DIVIDER_THICKNESS
        )

    def draw_text_elements(self):
        """Draw all text objects."""
        self.view.description_title.draw()
        for txt in self.view.description_texts:
            txt.draw()
        self.view.response_text.draw()
        self.view.input_text.draw()

    def set_background_image(self, image_path: str):
        """Load and display a new background image (e.g., locked door, panel)."""
        self._create_scaled_sprite(image_path)