# Quick Dupe

Duplication macros for item exploits.

## Features

- **Keydoor Method** - Key duplication using Xbox controller emulation
- **Throwable Dupe** - Throwable item duplication with auto-loop
- **Triggernade Dupe** - Triggernade duplication with inventory drop
- **E-Spam Collection** - Rapid E key spam for item pickup
- **Manual Disconnect** - Toggle packet drop (inbound/outbound)

## Requirements

- Windows 10/11
- Run as Administrator
- ViGEmBus driver (bundled, auto-installs on first run)

## Installation

### Option 1: Prebuilt EXE

1. Download the latest release from [Releases](../../releases).
2. Extract everything into one folder so the bundled files stay next to `QuickDupe.exe`.
3. Right-click `QuickDupe.exe` and choose **Run as administrator**.
4. Approve the ViGEmBus installation prompt on first launch (needed for controller emulation). WinDivert will be loaded automatically when you toggle packet drop.
5. Config and logs are stored under `%APPDATA%\QuickDupe\` (`config.json`, `custom_macros.json`, `debug.log`).

### Option 2: Run from source / build your own

1. Install Python 3.10+.
2. Install dependencies:
```
pip install -r requirements.txt
pip install pyinstaller  # only needed if you want an exe
```
3. Run from source:
```
python quickdupe.py
```
4. To build an exe:
```
pyinstaller QuickDupe.spec
```
5. Your exe will be in the `dist` folder.

## How to Use

1. Start QuickDupe (exe or `python quickdupe.py`) as Administrator.
2. In the UI, set or record hotkeys for the macros you need (Keydoor, Throwable, Triggernade, E-Spam, Manual/Outbound/Inbound Disconnect, etc.).
3. Press the configured hotkey in-game to run the macro. **ESC** stops all macros immediately.
4. Use the disconnect toggle for packet drop/reconnect, and record a triggernade drop position that matches your screen resolution if needed.

## Notes

- Press ESC to stop all macros
- Triggernade drop position can be recorded for your screen resolution

### 1.5.2 Notes:
In order to build/launch 1.5.2 you will need to download the following PNG files to the same directory as script:
`N.png`
`NE.png`
`E.png`
`SE.png`
`S.png`
`SW.png`
`NONE.png`
