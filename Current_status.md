# QuickDC - Current Status

## Overview
Tool for game exploits (ARC). Two preset methods: Keydoor and Throwable Dupe.

## Core Features
- **Keydoor Method**: Drop key, exit inventory, disconnect, spam E, reconnect while spamming, stop
- **Throwable Dupe**: Full macro (throw, disconnect, spam M1, reconnect, spam M1, wait, E, Q, repeat)
- **WinDivert packet drop**: Uses pydivert (like Clumsy) for instant disconnect
- **pynput**: Better keypress timing than keyboard library
- **Overlay notifications**: Shows status on screen

## Tech Stack
- Python 3 + tkinter (GUI)
- `keyboard` library (global hotkey registration)
- `pynput` (keyboard/mouse simulation with precise timing)
- `pydivert` / WinDivert (packet dropping like Clumsy)
- PyInstaller (exe build)

## File Structure
```
quickdc/
├── quickdc.py          # Main application
├── QuickDC.spec        # PyInstaller spec file
├── icon.ico / icon.png # App icon
├── requirements.txt
├── README.md
├── Current_status.md   # This file
└── dist/
    └── QuickDC.exe     # Built executable
```

## Config Location
`%APPDATA%/QuickDC/config.json`

## Config Format
```json
{
  "dc_hotkey": "alt+1",
  "throwable_hotkey": "alt+2",
  "throwable_repeat": true
}
```

## How It Works

### Keydoor Method (runs once)
1. Press G (drop key)
2. Press Tab (exit inventory)
3. Start packet drop (disconnect)
4. Spam E at ~60/sec for ~1.6s
5. Stop packet drop (reconnect) - keep spamming
6. Continue E spam for ~1.55s
7. Done

### Throwable Dupe (repeats if enabled)
1. M1 click (initial throw)
2. Disconnect (packet drop)
3. Spam M1 25 times
4. Reconnect (stop packet drop)
5. Spam M1 10 times
6. Wait 1 second
7. E key
8. Wait 300ms
9. Q key
10. Wait 750ms
11. Repeat if enabled

### Packet Drop (WinDivert)
- Captures ALL packets with filter "true"
- Receives packets but never re-injects them
- Effectively drops all network traffic instantly

## Build Command
```bash
pip install keyboard pynput pydivert pyinstaller
pyinstaller QuickDC.spec --noconfirm
```

## Recent Changes
1. Removed all profiles/customization - simplified to 2 preset methods
2. Switched from netsh/Clumsy to WinDivert packet dropping
3. Added pynput for better keypress timing
4. Implemented Throwable macro with exact Lua script timings
5. Implemented Keydoor macro (runs once)
6. Added overlay notifications
7. Always reconnects if stopped mid-cycle

## TODO / Next Up
- [ ] Update keydoor drop method (gamepad emulation or keyboard equivalent)

## Known Issues
- WinDivert requires admin and driver installation
- Hotkey recording requires window focus

## Requirements
- Windows 10/11
- Run as Administrator (for WinDivert)
- WinDivert driver installed
- Python 3.x (if running from source)
