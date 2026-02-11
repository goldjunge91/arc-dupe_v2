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

tab_hold = max(1, TAB_KEY_PRESS_DELAY_MS / 2)