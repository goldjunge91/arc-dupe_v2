from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Button as MouseButton, Controller as MouseController
from extra import gamepad
from utils.network import start_packet_drop, stop_packet_drop
init_gamepad = gamepad.init_gamepad
get_gamepad = gamepad.get_gamepad

# pynput controllers
pynput_keyboard = KeyboardController()
pynput_mouse = MouseController()
# vgamepad loaded lazily to avoid crash if ViGEmBus not installed


def run_keydoor_macro(self):
    """
    Keydoor macro (configurable timings):
    1. Disconnect
    2. Hold Xbox X button (drops key)
    3. TAB to exit inventory
    4. Start E spam, reconnect almost immediately
    5. Continue E spam after reconnect
    """
    is_disconnected = False
    gp = get_gamepad()
    vg_mod = gamepad.vg

    # Only require gamepad if NOT using drag drop
    if gp is None and not self.use_drag_drop_var.get():
        print("[KEYDOOR] Skipping - ViGEmBus not installed (enable drag drop or install ViGEmBus)")
        self.root.after(0, lambda: self.dc_status_var.set("ERROR: Install ViGEmBus"))
        self.root.after(0, lambda: self.dc_status_label.config(foreground="red"))
        self.keydoor_running = False
        return

    # Get configurable values
    x_hold_ms = self.keydoor_x_hold_var.get()
    tab_hold_ms = self.keydoor_tab_hold_var.get()
    wait_before_e_ms = self.keydoor_wait_before_e_var.get()
    espam_count = self.keydoor_espam_count_var.get()
    e_hold_ms = self.keydoor_e_hold_var.get()
    e_delay_ms = self.keydoor_e_delay_var.get()

    # ===== Disconnect FIRST =====
    print("[KEYDOOR] Disconnecting...")
    start_packet_drop()
    is_disconnected = True

    # ===== Drop item (Xbox X or drag fallback) =====
    print(f"[KEYDOOR] use_drag_drop_var = {self.use_drag_drop_var.get()}")
    if self.use_drag_drop_var.get():
        # Drag fallback using pynput - need to open inventory first
        print(f"[KEYDOOR] Opening inventory...")
        pynput_keyboard.press(Key.tab)
        self.vsleep(300)
        pynput_keyboard.release(Key.tab)
        self.vsleep(120)

        print(f"[KEYDOOR] Using drag drop: {self.keydoor_drag_start} → {self.keydoor_drag_end}")

        # Clear any stuck mouse state first
        pynput_mouse.release(MouseButton.left)

        # Move to start position
        pynput_mouse.position = self.keydoor_drag_start
        self.vsleep(30)

        # Press and drag
        pynput_mouse.press(MouseButton.left)
        self.vsleep(80)  # Click registers

        # Smooth drag - 20 steps over ~150ms
        start_x, start_y = self.keydoor_drag_start
        end_x, end_y = self.keydoor_drag_end
        dx = end_x - start_x
        dy = end_y - start_y
        steps = 20
        for i in range(1, steps + 1):
            t = i / steps
            x = int(start_x + dx * t)
            y = int(start_y + dy * t)
            pynput_mouse.position = (x, y)
            self.vsleep(7)

        pynput_mouse.release(MouseButton.left)
        print(f"[KEYDOOR] Drag complete")
    else:
        # Xbox X button - move to recorded slot position first
        print(f"[KEYDOOR] Moving to {self.keydoor_slot_pos}, holding X for {x_hold_ms}ms")
        pynput_mouse.position = self.keydoor_slot_pos
        self.vsleep(20)
        gp.press_button(button=vg_mod.XUSB_BUTTON.XUSB_GAMEPAD_X) # type: ignore
        gp.update()

        # Hold for configured time (cancelable)
        t = 0
        while t < x_hold_ms:
            if self.keydoor_stop:
                gp.release_button(button=vg_mod.XUSB_BUTTON.XUSB_GAMEPAD_X)
                gp.update()
                self.finish_keydoor(is_disconnected)
                return
            self.vsleep(10)
            t += 10

        gp.release_button(button=vg_mod.XUSB_BUTTON.XUSB_GAMEPAD_X)
        gp.update()
        print("[KEYDOOR] X released - key should be dropped")

                if self.keydoor_stop:
                    self.finish_keydoor(is_disconnected)
                    return

    # TAB to exit inventory
    pynput_keyboard.press(Key.tab)
    self.vsleep(tab_hold_ms)
    pynput_keyboard.release(Key.tab)
    self.vsleep(wait_before_e_ms)
    print("[KEYDOOR] TAB - exited inventory")

    if self.keydoor_stop:
        self.finish_keydoor(is_disconnected)
        return

    # ===== E spam - reconnect after just 1 press =====
    print("[KEYDOOR] Starting E spam...")
    pynput_keyboard.press('e')
    self.vsleep(e_hold_ms)
    pynput_keyboard.release('e')
    self.vsleep(7)

    # ===== Reconnect almost immediately =====
    print("[KEYDOOR] Reconnecting...")
    stop_packet_drop()
    is_disconnected = False

    # ===== Continue E spam after reconnect =====
    print(f"[KEYDOOR] Spamming E {espam_count}x...")
    for i in range(espam_count):
        if self.keydoor_stop:
            break
        pynput_keyboard.press('e')
        self.vsleep(e_hold_ms)
        pynput_keyboard.release('e')
        self.vsleep(e_delay_ms)

    # Done
    print("[KEYDOOR] Done!")
    self.finish_keydoor(is_disconnected)

def finish_keydoor(self, is_disconnected):
    """Clean up keydoor macro"""
    if is_disconnected:
        stop_packet_drop()
    self.keydoor_running = False
    self.keydoor_stop = False
    # Use root.after to update UI from main thread
    self.root.after(0, lambda: self.dc_status_var.set("Ready"))
    self.root.after(0, lambda: self.dc_status_label.config(foreground="gray"))
    self.root.after(0, lambda: self.show_overlay("Keydoor done."))