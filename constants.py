# constants.py

# Game starting room
STARTING_ROOM = "captains quarters"  # player start room
PLAYER_NAME = "Jack Harrow"
SHIP_NAME = "Tempus Fugit"

# Life support constants

# Ship physical parameters
SHIP_VOLUME_M3 = 550.0                  # Approximate total pressurized habitable volume (m³)
                                        # Roughly Serenity-class small freighter scale

# Crew & human metabolism (resting adult baseline)
# Sources: NASA ECLSS, submariner physiology refs
DEFAULT_CREW_COUNT = 1                  # Metabolic load factor (humans consuming/producing gas)

HUMAN_O2_CONSUMPTION_M3_PER_MIN = 0.000275   # ≈ 0.275 L/min (midpoint of 0.25–0.3 L/min range)
HUMAN_CO2_PRODUCTION_M3_PER_MIN = 0.000225   # ≈ 0.225 L/min (midpoint of 0.20–0.25 L/min range)

# System efficiencies (0.0 = failed/off → 1.0 = perfect)
# Current defaults reflect current testing values
CO2_SCRUBBER_EFFICIENCY    = 1.0
OXYGEN_GENERATOR_EFFICIENCY = 1.0
THERMAL_CONTROL_EFFICIENCY  = 0.0

# Room temperature presets (°C) — used for target_temperature in Room init
ROOM_TEMP_PRESETS = {
    "cold":   8.0,     # Unheated storage, deep holds, external-adjacent spaces
    "cool":  14.0,     # Cargo bays, airlocks, utility corridors
    "normal": 20.0,    # Cabins, galley, recreation (human comfort baseline)
    "warm":  24.0,     # Medical bay, passenger cabins, drug/herb storage
    "hot":   28.0,     # Engineering, reactor spaces, machinery heat load
}


# Window settings
SCREEN_WIDTH = 1270
SCREEN_HEIGHT = 770
SCREEN_TITLE = ""

# Font settings
FONT_NAME_PRIMARY = "Share Tech Mono"
FONT_NAME_FALLBACK = "Courier New"

# Font sizes
DEFAULT_FONT_SIZE = 14
TITLE_FONT_SIZE = 18
SUB_HEADING_FONT_SIZE = 14
PROMPT_FONT_SIZE = 14
SMALL_FONT_SIZE = 12
INVENTORY_HIGHLIGHTED_FONT_SIZE = 14
DESCRIPTION_TITLE_FONT_SIZE = 16
DESCRIPTION_FONT_SIZE = 12
RESPONSE_FONT_SIZE = 12
INPUT_FONT_SIZE = 12

# Colors and styles
DIVIDER_COLOR = (100, 150, 200, 180)   # RGBA
DIVIDER_THICKNESS = 2

# Colours (RGBA tuples)

BACKGROUND_COLOR = (0, 0, 0, 255)  # Solid black
TITLE_COLOR = (39, 230, 236, 200)
TEXT_COLOR = (186, 186, 186, 255)
EXIT_COLOR = (39, 230, 236, 200)
FIXED_OBJECT_COLOR = (39, 230, 236, 255)
PORTABLE_OBJECT_COLOR = (190, 165, 205, 255)
INVENTORY_HIGHLIGHT_TEXT_COLOR = (39, 230, 236, 255)
PLAYER_INPUT_COLOR = (126, 151, 174, 255)
ALERT_COLOR = (255, 140, 0, 255)
CURSOR_COLOR = (0, 255, 0, 255)           # Green
START_SCREEN_OVERLAY_COLOR = (0, 0, 0, 200)            # Semi-transparent black panel
IMAGE_OVERLAY_COLOR = (0, 0, 0, 100)        # Subtle dark overlay for images
CLOCK_COLOR = (100, 100, 100, 255)          # Mid grey
CLOCK_FLASH_COLOR = (255, 255, 255, 255)    # White

# Chronometer settings
START_DATE_TIME = (2276, 1, 1, 0, 0)  # year, month, day, hour, minute — launch epoch
SHIP_PANEL_REPAIR_MINUTES = 30        # Increased for testing life support (180 days)
SHORT_WAIT = 8.0                      # Player-visible delay in seconds for panel repair
CLOCK_UPDATE_INTERVAL = 60         # Real-time seconds between normal clock ticks

CARD_SWIPE_WAIT = 3.0  # Player-visible delay in seconds for door card swipe


# Ship_view sections, heights, padding and spacing

# Layout ratios and heights
LEFT_PANEL_RATIO = 0.45                # Image width ratio
DESCRIPTION_SECTION_RATIO = 0.60       # Proportion of right text area for description
EVENT_SECTION_HEIGHT = 70              # Pixels for bottom event section

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
INVENTORY_SECTION_GAP = 30               # Vertical gap between worn/carried sections

INVENTORY_LINE_GAP = 2                 # room between lines
INVENTORY_HEADER_GAP = 30               # bigger gap after headers
INVENTORY_HORIZONTAL_PADDING = 10
INVENTORY_VERTICAL_PADDING = 12

INVENTORY_SKIP_EMPTY_SLOTS = True
INVENTORY_SKIP_EMPTY_ON_NAV = True
INVENTORY_EMPTY_TEXT = "The black is quiet. No gear aboard."  # Flavor text when inventory is empty

INVENTORY_IMAGE_CENTER_Y = SCREEN_HEIGHT - INVENTORY_TOP_PADDING - ((SCREEN_HEIGHT // 2) - INVENTORY_TOP_PADDING * 2) / 2
