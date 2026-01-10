# constants.py

# Game starting room
STARTING_ROOM = "med-bay"  # player start room
PLAYER_NAME = "Jack Harrow"
SHIP_NAME = "Tempus Fugit"

# Window settings
SCREEN_WIDTH = 1270
SCREEN_HEIGHT = 770
SCREEN_TITLE = ""

# Font settings
FONT_NAME_PRIMARY = "Share Tech Mono"
FONT_NAME_FALLBACK = "Courier New"

# Font sizes
FONT_SIZE_DEFAULT = 14
FONT_SIZE_TITLE = 18
FONT_SIZE_PROMPT = 14
FONT_SIZE_SMALL = 12

DESCRIPTION_TITLE_FONT_SIZE = 16
DESCRIPTION_FONT_SIZE = 12
RESPONSE_FONT_SIZE = 12
INPUT_FONT_SIZE = 12

# Colors and styles
DIVIDER_COLOR = (100, 150, 200, 180)   # RGBA
DIVIDER_THICKNESS = 2
EVENT_SECTION_BG_COLOR = (20, 30, 50, 180)  # Dark semi-transparent for event area

# Colours (RGBA tuples)

BACKGROUND_COLOR = (0, 0, 0, 255)  # Solid black

TITLE_COLOR = (176, 100, 176, 255)
TEXT_COLOR = (176, 172, 176, 255)
EXIT_COLOR = (11, 70, 140, 255)
OBJECT_COLOR = (143, 112, 75, 255)
PLAYER_INPUT_COLOR = (68, 120, 106, 255)
ALERT_COLOR = (255, 140, 0, 255)
CURSOR_COLOR = (0, 255, 0, 255)           # Green
PANEL_OVERLAY = (0, 0, 0, 200)            # Semi-transparent black panel
BACKGROUND_OVERLAY = (0, 0, 0, 100)        # Subtle dark overlay for images
CLOCK_COLOR = (100, 100, 100, 255)          # Mid grey
CLOCK_FLASH_COLOR = (255, 255, 255, 255)    # White

INVENTORY_HIGHLIGHT_BG = OBJECT_COLOR    # Background color for selected/highlight bar
INVENTORY_HIGHLIGHT_TEXT = (0, 0, 0, 255)  # Text color on highlight bar (black for max contrast)

# Chronometer settings
START_DATE_TIME = (2276, 1, 1, 0, 0)  # year, month, day, hour, minute — launch epoch
SHIP_PANEL_REPAIR_MINUTES = 30        # Ship time advance on panel repair
SHORT_WAIT = 8.0                      # Player-visible delay in seconds for panel repair
CLOCK_UPDATE_INTERVAL = 60.0          # Real-time seconds between normal clock ticks

CARD_SWIPE_WAIT = 3.0  # Player-visible delay in seconds for door card swipe



# Ship_view sections, heights, padding and spacing

# Layout ratios and heights
LEFT_PANEL_RATIO = 0.45                # Image width ratio
DESCRIPTION_SECTION_RATIO = 0.50       # Proportion of right text area for description
EVENT_SECTION_HEIGHT = 60              # Pixels for bottom event section

# Fixed heights
INPUT_SECTION_HEIGHT = 100              # Fixed pixel height for input section

# Padding and spacing
TEXT_PADDING = 20                      # Horizontal padding in text sections
TITLE_PADDING = 20                     # Vertical space below title
SECTION_TITLE_PADDING = 20             # Space between title and first description line
RESPONSE_PADDING_TOP = 20              # Top padding in response section
INPUT_PADDING_TOP = 40              # Bottom padding in input section
LINE_SPACING = 4                      # Vertical space between description lines


# inventory_view sections, heights, padding and spacing

# padding and spacing
INVENTORY_TOP_PADDING = 40          # Space from screen top to title
INVENTORY_SECTION_GAP = 40               # Vertical gap between worn/carried sections
INVENTORY_ITEM_INDENT = 20               # Left indent for items under headers

INVENTORY_LINE_GAP = 14                 # was 10 — bigger breathing room between lines
INVENTORY_HEADER_GAP = 30               # bigger gap after headers

INVENTORY_DESC_INDENT = 250             # Indent for description text

INVENTORY_EMPTY_TEXT = "The black is quiet. No gear aboard."  # Flavor text when inventory is empty
