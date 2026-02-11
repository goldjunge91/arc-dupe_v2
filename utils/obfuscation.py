import os
import sys
import time
import ctypes
import shutil
import random
import string


def _check_obfuscation_enabled():
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.exists(os.path.join(exe_dir, "obfuscate"))


OBFUSCATION_ENABLED = _check_obfuscation_enabled()

# generate a random name if needed
if OBFUSCATION_ENABLED:
    _name_length = random.randint(8, 18)
    _random_name = ''.join(random.choices(string.ascii_letters, k=_name_length))
else:
    _random_name = "QD"


def _log_obfus(msg: str):
    """Log obfuscation messages to APPDATA/QuickDupe/obfus.log"""
    try:
        log_path = os.path.join(os.environ.get('APPDATA', '.'), "QuickDupe", "obfus.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except Exception:
        pass


def rename_self_and_restart():
    """Create a copy of the EXE with a random name and launch it with elevation.

    Returns True on success (or when launch attempted), False otherwise.
    """
    _log_obfus(f"rename_self_and_restart called. OBFUSCATION_ENABLED={OBFUSCATION_ENABLED}, frozen={getattr(sys, 'frozen', False)}")

    if not OBFUSCATION_ENABLED:
        _log_obfus("Exiting: obfuscation not enabled")
        return False

    if not getattr(sys, 'frozen', False):
        _log_obfus("Exiting: not frozen exe")
        return False

    current_exe = sys.executable
    current_dir = os.path.dirname(current_exe)
    marker_file = os.path.join(current_dir, "DELETETOCHANGEID")

    _log_obfus(f"current_exe={current_exe}, current_dir={current_dir}, marker_file={marker_file}")
    _log_obfus(f"marker exists: {os.path.exists(marker_file)}")

    if os.path.exists(marker_file):
        _log_obfus("Exiting: marker file exists")
        return False

    new_name = f"{_random_name}.exe"
    new_path = os.path.join(current_dir, new_name)

    _log_obfus(f"Will copy to: {new_path}")

    try:
        shutil.copy2(current_exe, new_path)
        _log_obfus(f"Copy successful. File exists: {os.path.exists(new_path)}")

        with open(marker_file, 'w', encoding='utf-8') as f:
            f.write(new_name)
        _log_obfus("Marker file created")

        _log_obfus(f"Launching: {new_path}")
        # Use ShellExecuteW to request elevation
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", new_path, " ".join(sys.argv[1:]), None, 1)
            _log_obfus("Launched via ShellExecuteW")
        except Exception as e:
            _log_obfus(f"ShellExecuteW failed: {type(e).__name__}: {e}")
            # fallback to subprocess
            try:
                import subprocess
                subprocess.Popen([new_path] + sys.argv[1:])
                _log_obfus("Launched via subprocess.Popen fallback")
            except Exception as e2:
                _log_obfus(f"Fallback launch failed: {type(e2).__name__}: {e2}")
                return False

        _log_obfus("Exiting original process")
        sys.exit(0)

    except Exception as e:
        _log_obfus(f"ERROR: {type(e).__name__}: {e}")
        return False

    return True
