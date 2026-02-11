"""Utility module extracted from `quickdupeobfus.py`.

Provides thin wrappers to initialize and access a virtual Xbox 360 controller
via the `vgamepad` (ViGEm) library.

Functions:
- install_vigem(): launch bundled ViGEmBus installer if present
- init_gamepad(): try to import/create a virtual gamepad (returns True on success)
- get_gamepad(): return the created gamepad instance or None

This module intentionally keeps imports lazy so the main application can run
even when ViGEmBus / vgamepad isn't installed.
"""

from __future__ import annotations

import os
import sys
import subprocess
import logging
import threading
import time
from typing import Optional

log = logging.getLogger("QuickDupe.gamepad")

# vgamepad module reference (set when available)
vg = None

# The created virtual gamepad (vx360) instance
_gamepad = None

# Warn flag if ViGEm problems were detected
_vigem_warned = False


def install_vigem() -> bool:
    """Run the bundled ViGEmBus installer if available.

    Returns True if the installer was launched, False otherwise.
    """
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    installer_path = os.path.join(base_path, "ViGEmBus_1.22.0_x64_x86_arm64.exe")

    if os.path.exists(installer_path):
        log.info("Launching ViGEmBus installer: %s", installer_path)
        try:
            subprocess.Popen([installer_path])
            return True
        except Exception:
            log.exception("Failed to launch ViGEmBus installer")
            return False
    else:
        log.warning("ViGEmBus installer not found at: %s", installer_path)
        return False


def init_gamepad() -> bool:
    """Attempt to import `vgamepad` and create a virtual Xbox controller.

    Returns True on success. On failure this will attempt to auto-run the
    bundled ViGEmBus installer and set a warn flag.
    """
    global _gamepad, vg, _vigem_warned

    try:
        import vgamepad as vgamepad_module
        vg = vgamepad_module
        _gamepad = vg.VX360Gamepad()
        # Reset any stray state and push an initial update
        try:
            _gamepad.reset()
        except Exception:
            # Older versions may not expose reset; ignore
            pass
        try:
            _gamepad.update()
        except Exception:
            # Some environments may raise until driver is fully available
            pass
        log.info("Virtual Xbox controller initialized")
        return True
    except Exception as exc:
        log.warning("ViGEmBus/vgamepad initialization failed: %s", exc)
        # Attempt to auto-install driver if present alongside the application
        if install_vigem():
            log.info("ViGEmBus installer launched. Please restart the application once installation completes.")
        else:
            log.warning("Please install ViGEmBus manually: https://github.com/nefarius/ViGEmBus/releases")
        _vigem_warned = True
        return False


def get_gamepad():
    """Return the current VX360Gamepad instance or None if not initialized."""
    return _gamepad


def vigem_warned() -> bool:
    """Return True if an initialization attempt failed and the user was warned."""
    return _vigem_warned


__all__ = [
    "install_vigem",
    "init_gamepad",
    "get_gamepad",
    "vg",
    "vigem_warned",
]
