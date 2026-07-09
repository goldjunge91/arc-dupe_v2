# Slot Swap Tool (Dupe Item)

Inventory slot swap macro to automate item duplication. 

It mimics mouse clicks, moves, and hotkeys using fine-grained timing to swap items out of their slots.

It includes a build script to compile your own unique executable so you don't get banned for binary signatures.

---

## Features

- **Slot Position Recording**: Click directly on the target inventory/storage slots to define coordinates (supports 2 or more slots).
- **Alt-Drag Emulation**: Drags the item to the left by a configurable pixel distance while simulating `Alt` key behavior.
- **Customizable Timing & Speed**:
  - **Move Left Distance**: Pixel offset for dragging items.
  - **Move Steps & Step Delay**: Adjusts how smoothly and fast mouse movement transitions occur.
  - **Settle Delay**: Wait time after clicks or key actions for the game to process them.
  - **Speed Factor**: A global scaling multiplier (e.g., `2.0x`) to compress all delays for ultra-fast execution.
- **Initial Tab Press**: Optionally prepends a `Tab` keypress to open/activate menus.
- **Looping/Repeat**: Automates repetition of the swap sequence for a specified count.
- **Emergency Stop**: Pressing `ESC` instantly aborts the active macro.

---

## Building from Source

To compile the tool with a unique binary signature:

1. **Open a terminal** and navigate to the `duper` folder:
   ```powershell
   cd c:\GIT\QuickDupe\duper
   ```
2. **Ensure your project virtual environment is active** (or standard Python environment with dependencies installed: `pynput`, `keyboard`).
3. **Run the build script**:
   ```powershell
   python build.py
   ```

### How the Build Process Works
- The build script (`build.py`) generates a unique signature (UUID + random string).
- It injects this signature into `slot_swap_tool.py` at `BUILD_ID = "__BUILD_ID_PLACEHOLDER__"`.
- It invokes `PyInstaller` using the bundled `SlotSwapTool.spec` to output a standalone executable: `duper/dist/SlotSwapTool.exe`.
- It automatically restores `slot_swap_tool.py` back to its placeholder state so your Git repository remains clean.

---

## Usage

1. Run the compiled executable `dist/SlotSwapTool.exe` (run as Administrator to ensure global hotkeys and mouse actions register correctly over game windows).
2. Click **Record Slots** and click on your target inventory slots in order. Press `Enter` to save, or `ESC` to cancel recording.
3. Bind a custom activation hotkey.
4. Tune parameters (Move Left, Delays, Speed Factor) to match your screen resolution and the game's responsiveness.
5. Press your hotkey to start/stop the macro, or use the UI controls. Press `ESC` at any time to force-stop.
