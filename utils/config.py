import json
import os

CONFIG_FILE = os.path.join(os.environ.get("APPDATA", "."), "QuickDupe", "config.json")
CUSTOM_MACROS_FILE = os.path.join(
    os.environ.get("APPDATA", "."), "QuickDupe", "custom_macros.json"
)


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def load_custom_macros():
    """Load custom macros from JSON file"""
    if os.path.exists(CUSTOM_MACROS_FILE):
        try:
            with open(CUSTOM_MACROS_FILE, "r") as f:
                data = json.load(f)
                # Ensure required structure
                if "macros" not in data:
                    data["macros"] = []
                if "active_index" not in data:
                    data["active_index"] = 0
                # Ensure each macro has expected keys (backwards compat)
                for m in data.get("macros", []):
                    if "dc_delay" not in m:
                        m["dc_delay"] = 50
                return data
        except:
            pass
    # Return default structure with one empty macro
    return {
        "macros": [{"name": "Macro 1", "hotkey": "", "speed": 1.0, "dc_delay": 50, "events": []}],
        "active_index": 0,
    }


def save_custom_macros(data):
    """Save custom macros to JSON file"""
    os.makedirs(os.path.dirname(CUSTOM_MACROS_FILE), exist_ok=True)
    with open(CUSTOM_MACROS_FILE, "w") as f:
        json.dump(data, f, indent=2)
