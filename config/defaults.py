# Centralized default timing values (in milliseconds)
# These are conservative defaults used where per-macro config is not set.

# Mouse click hold (how long to hold button down for context clicks)
CLICK_HOLD_MS = 25

# Wait for context menu to appear after right-click
CONTEXT_MENU_WAIT_MS = 50

# Delay after pressing TAB to allow inventory to open/close
# Split into two halves in macros (press hold + post-release wait).
# Default total ~70ms (matches keycard inv default), so use 35ms each.
TAB_KEY_PRESS_DELAY_MS = 15
TAB_CLOSE_DELAY_MS = 35

# Small delay after reconnect call to let reconnect start
RECONNECT_START_DELAY_MS = 25

# How long to hold a key press (e.g., 'e') between press and release
KEY_PRESS_HOLD_MS = 30

# Keycard-specific defaults
KEYCARD_E_DC_DELAY_DEFAULT = 0  # ms between E and disconnect (0 = simultaneous)
KEYCARD_OFFLINE_ESPAM_DEFAULT = 500
KEYCARD_RECONNECT_ESPAM_DEFAULT = 152
# Match UI default for keycard E‑spam delay (ms between E presses)
# Named as _ESPAM_DELAY to match config key `keycard_espam_delay`.
KEYCARD_ESPAM_DELAY_DEFAULT = 50

# Keycard interaction timing defaults (match UI shown in screenshot)
KEYCARD_DC_WAIT_DEFAULT = 50
KEYCARD_INV_DELAY_DEFAULT = 70
KEYCARD_RCLICK_DELAY_DEFAULT = 200
KEYCARD_DROP_DELAY_DEFAULT = 200

# ==================== NEUE GAMEPAD TIMING KONSTANTEN ====================
# Keycard Gamepad Combo Timing (Y -> Down -> Down -> A Sequenz)

# Minimum Delay zwischen E-Press und DC-Start (Sicherheitswert)
KEYCARD_E_DC_MIN_DELAY_MS = 2

# Delay nach Mouse-Position-Set bevor Gamepad-Combo startet
KEYCARD_MOUSE_POSITION_DELAY_MS = 50

# Y-Button Timing (Menü öffnen)
KEYCARD_GAMEPAD_Y_PRESS_DURATION_MS = 60  # Wie lange Y gehalten wird
KEYCARD_GAMEPAD_Y_RELEASE_WAIT_MS = 150   # Wartezeit nach Y-Release (Menü-Animation)

# DPad Navigation Timing (Down x2 für "Drop" Option)
KEYCARD_GAMEPAD_DPAD_PRESS_DURATION_MS = 30   # Wie lange DPad Down gehalten wird
KEYCARD_GAMEPAD_DPAD_RELEASE_WAIT_MS = 30     # Wartezeit zwischen DPad-Inputs

# A-Button Timing (Drop bestätigen)
KEYCARD_GAMEPAD_A_PRESS_DURATION_MS = 30      # Wie lange A gehalten wird

# Delay vor dem Reconnect (gibt Gamepad-Inputs Zeit zum Verarbeiten)
KEYCARD_PRE_RECONNECT_DELAY_MS = 50

tab_hold = max(1, TAB_KEY_PRESS_DELAY_MS / 2)