# STACK-PAD v2.7.0

Virtual F13-F24 macro keypad for Windows - A small, always-on-top application that provides 12 programmable function keys (F13-F24) for mapping shortcuts across your favorite applications.

**Developer:** Dev.Essam / GitHub ( s0-5 )  
**Copyright © 2026**

## 🌟 Features

- **12 Virtual Function Keys** (F13-F24) in a compact 3x4 grid layout
- **Always-on-top** frameless window that stays accessible
- **Draggable interface** - move it anywhere on your screen
- **Dark theme** with customizable cyan accent colors
- **Edit Mode** - rename button labels while keeping F-key output locked
- **Auto Repeat** - configure automatic key repetition with customizable speed
- **System tray integration** - minimize to tray and control from there
- **Hide/Show** - minimize to a small floating button
- **Position lock** - lock the window position to prevent accidental moves
- **No external files** - everything is embedded, no folders created

## 🚀 Quick Start

1. **Run the application** - Double-click `STACK-PAD.exe`
2. **Bind keys in your apps**:
   - Open your target app (Discord, OBS, gaming software, etc.)
   - Navigate to keybind settings
   - Click "Record" or "Add Keybind"
   - Click the corresponding button in STACK-PAD
   - The app will record it as F13/F14/etc.

3. **Customize labels**:
   - Click "Edit Mode" in the bottom bar
   - Click any button to edit its label and color
   - Your customizations are saved automatically

## 🎮 Use Cases

- **Discord** - Mute, Deafen, Push-to-Talk shortcuts
- **OBS Studio** - Start/Stop recording, scene switching
- **Gaming** - Custom macros and shortcuts
- **Media Control** - Volume, mute, media playback
- **Productivity** - Quick actions and shortcuts

## ⚙️ Controls

- **🔒 Lock Button** - Lock/unlock window position
- **👁 Eye Button** - Hide to small floating button / Show main window
- **✕ Close Button** - Close application (with confirmation)
- **Edit Mode** - Enable to edit button labels and colors
- **Auto Repeat** - Configure automatic key repetition
- **On/Off Toggle** - Control auto-repeat activation

## 🔨 Building from Source

If you want to build the application from source code, follow these steps:

### Prerequisites

1. **Install Python 3.10 or higher** from [python.org](https://www.python.org/downloads/)

2. **Install the required dependencies** from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - PySide6 (GUI framework)
   - pydantic (data validation)
   - pywin32 (Windows API access)
   - pynput (keyboard input)
   - pyinstaller (EXE builder)

### Building the EXE

1. **Convert the icon** (optional but recommended):
   ```bash
   python -c "from PIL import Image; img = Image.open('STACK-PAD.png'); img.save('STACK-PAD.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])"
   ```

2. **Build the executable** using PyInstaller:
   ```bash
   pyinstaller --onefile --windowed --icon=STACK-PAD.ico --name=STACK-PAD --clean STACK_PAD.py
   ```

3. **Find your EXE** in the `dist/` folder:
   - The compiled `STACK-PAD.exe` will be located in the `dist/` directory
   - You can run it directly or distribute it to others

### Running from Source

Alternatively, you can run the application directly from Python:
```bash
python STACK_PAD.py
```

## 📝 License

This project is open source and available under the [MIT License](LICENSE.md).

## 🤝 Contributing

Contributions are welcome! This is an open source project, and we appreciate any help you can provide.

## 📧 Support

For issues, feature requests, or questions, please open an issue on [GitHub](https://github.com/s0-5/STACK-PAD/issues).


