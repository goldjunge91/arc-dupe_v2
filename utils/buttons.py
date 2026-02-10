# import
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Button as MouseButton, Controller as MouseController

# pynput controllers
pynput_keyboard = KeyboardController()
pynput_mouse = MouseController()

def release_buttons(self):
    # Release all buttons before starting
    pynput_mouse.release(MouseButton.left)
    pynput_mouse.release(MouseButton.right)
    pynput_keyboard.release(Key.tab)
    pynput_keyboard.release("e")
