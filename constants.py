# constants.py

# Window settings
SCREEN_WIDTH = 1270
SCREEN_HEIGHT = 770
SCREEN_TITLE = ""

# Background colour
BACKGROUND_COLOR = (0, 0, 0, 255)  # Solid black

# Font settings
FONT_NAME_PRIMARY = "Share Tech Mono"
FONT_NAME_FALLBACK = "Courier New"

# Font sizes
FONT_SIZE_DEFAULT = 14
FONT_SIZE_TITLE = 18
FONT_SIZE_PROMPT = 14
FONT_SIZE_SMALL = 12

# Colours (RGBA tuples)
TEXT_COLOR = (200, 200, 200, 255)         # Light grey
ACCENT_COLOR = (0, 220, 220, 255)         # Cyan
ALERT_COLOR = (255, 140, 0, 255)          # Dark orange
CURSOR_COLOR = (0, 255, 0, 255)           # Green
PANEL_OVERLAY = (0, 0, 0, 200)            # Semi-transparent black panel
BACKGROUND_OVERLAY = (0, 0, 0, 100)        # Subtle dark overlay for images


# Added for complete sectioning of ship_view

# Layout ratios and heights
LEFT_PANEL_RATIO = 0.45                # Image width ratio
DESCRIPTION_SECTION_RATIO = 0.55       # Proportion of right text area for description
EVENT_SECTION_HEIGHT = 60              # Pixels for bottom event section

# Fixed heights
INPUT_SECTION_HEIGHT = 100              # Fixed pixel height for input section

# Padding and spacing
TEXT_PADDING = 20                      # Horizontal padding in text sections
TITLE_PADDING = 20                     # Vertical space below title
SECTION_TITLE_PADDING = 20             # Space between title and first description line
RESPONSE_PADDING_TOP = 20              # Top padding in response section
INPUT_PADDING_TOP = 40              # Bottom padding in input section
LINE_SPACING = 0                      # Vertical space between description lines

# Font sizes
DESCRIPTION_TITLE_FONT_SIZE = 16
DESCRIPTION_FONT_SIZE = 12
RESPONSE_FONT_SIZE = 12
INPUT_FONT_SIZE = 12

# Colors and styles
DIVIDER_COLOR = (100, 150, 200, 180)   # RGBA
DIVIDER_THICKNESS = 2
EVENT_SECTION_BG_COLOR = (20, 30, 50, 180)  # Dark semi-transparent for event area