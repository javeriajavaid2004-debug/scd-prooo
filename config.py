"""Global configuration values for Devil Run."""

# DATABASE CONFIGURATION
# NOTE: Uses the specific server name you provided.
DB_CONNECTION_STRING = (
	r"DRIVER={ODBC Driver 17 for SQL Server};"
	r"SERVER=.\SQLEXPRESS;" 
	r"DATABASE=devil_run_db;"
	r"Trusted_Connection=yes;"
)

# DISPLAY SETTINGS
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 700
TILE_SIZE = 40
FPS = 60
DEFAULT_FULLSCREEN = False # Toggle with F11

# GAMEPLAY CONSTANTS
CAMERA_LOOKAHEAD = 180
# Reduced scroll length so goals are reachable (4 screens wide)
LEVEL_SCROLL_LENGTH_SCREENS = 4 
LEVEL_SCROLL_LENGTH = 4 

# COLOR PALETTE
INK = (15, 10, 12)             # Deepest Black
PEACH_DARK = (60, 35, 20)       # Deep Brown (Platforms)
PEACH_MED = (95, 55, 35)        # UI Brown
PEACH_LIGHT = (30, 18, 12)      # Very Dark Brown (Background)
ACCENT_RED = (150, 85, 50)      # Accent Brown (Traps/Buttons)
ACCENT_YELLOW = (255, 215, 0)  # Gold (Stars)
ACCENT_WHITE = (240, 240, 240) # Text
CYAN = (180, 120, 80)          # Brownish Dialogue Accent
GOAL_GREEN = (0, 255, 0)       # BRIGHT GREEN (Goal)

# Aliases
RED = ACCENT_RED
YELLOW = ACCENT_YELLOW
WHITE = ACCENT_WHITE
BLACK = INK

# PHYSICS DEFAULTS (Tuned for better jump feel)
PLAYER_SPEED = 8
JUMP_FORCE = -22        
GRAVITY = 0.8           
MAX_FALL_SPEED = 14
COYOTE_TIME = 0.15      
JUMP_BUFFER_TIME = 0.15 

# SYSTEM CONFIG
DIALOGUE_DISPLAY_MS = 2500      
MAX_TOXICITY_TIER = 4
DEFAULT_LEVEL_ID = 1
MAX_COMMUNITY_TRAPS = 3 
TOTAL_LEVELS = 12       
BOSS_UNLOCK_STARS = 22  

# ASSET MAPPING
PLATFORM_COLOR = PEACH_DARK
BACKGROUND_COLOR = PEACH_LIGHT
GOAL_COLOR = GOAL_GREEN
PLAYER_COLOR = ACCENT_WHITE  # Changed to white for visibility against dark red
TRAP_COLOR = ACCENT_RED
HUD_TEXT_COLOR = ACCENT_WHITE
UI_BUTTON_BG = ACCENT_RED
UI_BUTTON_TEXT = ACCENT_WHITE
UI_BORDER_COLOR = INK

# FONTS
FONT_NAME = "freesansbold.ttf"
TITLE_FONT_SIZE = 52
HUD_FONT_SIZE = 22
AUTH_FONT_SIZE = 32

# RANKING TIERS
RANKS = [
    (0, "Noob (Pure Shame)"),
    (5, "Amateur (Just Stop)"),
    (10, "Rookie (Barely Competent)"),
    (15, "Veteran (Moderately Hated)"),
    (22, "Elite (Toxic Master)"),
    (28, "GOD (The Narrator's Equal)"),
]