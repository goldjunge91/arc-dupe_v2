from __future__ import annotations

from typing import Callable, Dict, Tuple

import ctypes

from pynput.keyboard import Key
from pynput.mouse import Button as MouseButton

Position = Tuple[int, int]


def run_slot_swap_macro(
    *,
    vsleep: Callable[[int], None],
    keyboard,
    mouse,
    slot1_pos: Position,
    slot2_pos: Position,
    timings: Dict[str, int],
    stop_check: Callable[[], bool],
    log: Callable[[str], None] = print,
) -> None:
    """Swap two inventory slots using two Alt+LMB drags.

    Sequence per slot:
    1) Move to the recorded slot position
    2) Hold Alt and left mouse button
    3) Drag a short distance to the left
    4) Release left mouse button, then Alt

    Running the same sequence for slot 1 and slot 2 swaps their contents
    when the configured left movement matches one inventory slot width.
    """
    if not slot1_pos or not slot2_pos:
        raise ValueError("Slot swap positions are not set")

    alt_delay = max(0, int(timings.get("alt_delay", 20)))
    click_hold_ms = max(0, int(timings.get("click_hold_ms", 25)))
    move_left_px = max(0, int(timings.get("move_left_px", 120)))
    move_steps = max(1, int(timings.get("move_steps", 12)))
    step_delay = max(0, int(timings.get("step_delay", 5)))
    settle_delay = max(0, int(timings.get("settle_delay", 25)))
    between_slots_delay = max(0, int(timings.get("between_slots_delay", 40)))

    def _stop() -> bool:
        return stop_check()

    def _set_mouse_pos(pos: Position) -> None:
        x, y = int(pos[0]), int(pos[1])
        try:
            mouse.position = (x, y)
        except Exception:
            pass
        try:
            ctypes.windll.user32.SetCursorPos(x, y)
        except Exception:
            pass

    def _cleanup() -> None:
        try:
            mouse.release(MouseButton.left)
        except Exception:
            pass
        try:
            keyboard.release(Key.alt)
        except Exception:
            pass

    def _alt_drag_left(pos: Position) -> None:
        start_x, start_y = int(pos[0]), int(pos[1])
        end_x = max(0, start_x - move_left_px)

        _set_mouse_pos((start_x, start_y))
        vsleep(alt_delay)
        keyboard.press(Key.alt)
        vsleep(alt_delay)
        mouse.press(MouseButton.left)
        vsleep(click_hold_ms)

        for i in range(1, move_steps + 1):
            if _stop():
                break
            t = i / move_steps
            x = int(round(start_x + (end_x - start_x) * t))
            try:
                mouse.position = (x, start_y)
            except Exception:
                pass
            try:
                ctypes.windll.user32.SetCursorPos(x, start_y)
            except Exception:
                pass
            vsleep(step_delay)

        mouse.release(MouseButton.left)
        vsleep(settle_delay)
        keyboard.release(Key.alt)
        vsleep(settle_delay)

    # Clean input state before starting
    _cleanup()
    try:
        mouse.release(MouseButton.right)
    except Exception:
        pass
    try:
        keyboard.release(Key.tab)
    except Exception:
        pass
    try:
        keyboard.release("q")
    except Exception:
        pass

    log(f"[SLOT-SWAP] Slot1={slot1_pos} Slot2={slot2_pos} move_left_px={move_left_px}")

    if _stop():
        return
    _alt_drag_left(slot1_pos)
    if _stop():
        return

    vsleep(between_slots_delay)

    if _stop():
        return
    _alt_drag_left(slot2_pos)
    if _stop():
        return

    log("[SLOT-SWAP] Done")
    _cleanup()
