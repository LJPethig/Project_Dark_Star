# main.py
import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from ui.start_screen import StartScreen

class ProjectDarkStar(arcade.Window):
    """Main application window — borderless and fullscreen-like for immersion."""

    def __init__(self):
        # Create a borderless window (no title bar, no OS controls)
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            "",  # No title
            resizable=False,
            fullscreen=False,  # Not true fullscreen — keeps taskbar access
            style=arcade.Window.WINDOW_STYLE_BORDERLESS  # This removes OS chrome
        )

        # Black background
        arcade.set_background_color((0, 0, 0, 255))

        # Start with the start screen
        self.show_view(StartScreen(self))

def main():
    """Entry point."""
    game = ProjectDarkStar()
    arcade.run()

if __name__ == "__main__":
    main()