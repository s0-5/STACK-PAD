import sys
import os
from pathlib import Path
from typing import Optional
import ctypes
from ctypes import wintypes
import time
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QComboBox, QLineEdit, QDialog,
    QDialogButtonBox, QFormLayout, QMessageBox, QSystemTrayIcon, QMenu, QStyle
)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QIcon, QColor, QPixmap, QCursor

from pydantic import BaseModel, Field, field_validator

if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    sw_hide = 0
    kernel32.FreeConsole()

try:
    from pynput.keyboard import Key, Controller as KeyboardController
    HAS_PYNPUT = True
    keyboard = KeyboardController()
except ImportError:
    HAS_PYNPUT = False
    keyboard = None

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002

VK = {
    "F13": 0x7C, "F14": 0x7D, "F15": 0x7E, "F16": 0x7F,
    "F17": 0x80, "F18": 0x81, "F19": 0x82, "F20": 0x83,
    "F21": 0x84, "F22": 0x85, "F23": 0x86, "F24": 0x87,
}

PYNPUT_KEY_MAP = {
    "F13": Key.f13, "F14": Key.f14, "F15": Key.f15, "F16": Key.f16,
    "F17": Key.f17, "F18": Key.f18, "F19": Key.f19, "F20": Key.f20,
    "F21": Key.f21, "F22": Key.f22, "F23": Key.f23, "F24": Key.f24,
}

def send_key(key_name: str, down_up_delay_ms: int = 25) -> bool:
    key_name = key_name.upper().strip()
    if key_name not in VK:
        return False

    if HAS_PYNPUT and key_name in PYNPUT_KEY_MAP:
        try:
            pynput_key = PYNPUT_KEY_MAP[key_name]
            keyboard.press(pynput_key)
            if down_up_delay_ms > 0:
                time.sleep(down_up_delay_ms / 1000.0)
            keyboard.release(pynput_key)
            return True
        except Exception:
            pass
    
    return _send_input_fallback(key_name, down_up_delay_ms)

def _send_input_fallback(key_name: str, down_up_delay_ms: int) -> bool:
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t),
            ]

        class INPUT_UNION(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("union", INPUT_UNION),
            ]

        vk = VK[key_name]
        
        ki_down = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=0)
        union_down = INPUT_UNION(ki=ki_down)
        inp_down = INPUT(type=INPUT_KEYBOARD, union=union_down)
        result_down = user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
        
        if result_down == 0:
            return False
        
        if down_up_delay_ms > 0:
            time.sleep(down_up_delay_ms / 1000.0)
        
        ki_up = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
        union_up = INPUT_UNION(ki=ki_up)
        inp_up = INPUT(type=INPUT_KEYBOARD, union=union_up)
        result_up = user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))
        
        return result_up != 0
    except Exception:
        return False

def get_f_key_list() -> list[str]:
    return list(VK.keys())

class KeyBinding(BaseModel):
    label: str = Field(default="", max_length=18)
    color_tag: str = Field(default="gray")
    output_key: str = Field(default="F13")
    
    @field_validator("color_tag")
    @classmethod
    def validate_color_tag(cls, v: str) -> str:
        allowed = ["purple", "cyan", "green", "orange", "red", "blue", "yellow", "gray"]
        if v not in allowed:
            return "gray"
        return v
    
    @field_validator("output_key")
    @classmethod
    def validate_output_key(cls, v: str) -> str:
        valid_keys = [f"F{i}" for i in range(13, 25)]
        if v not in valid_keys:
            return "F13"
        return v

class Profile(BaseModel):
    profile_id: str
    profile_name: str
    description: str = ""
    icon: str = "default"
    bindings: dict[str, KeyBinding] = Field(default_factory=dict)

class AppConfig(BaseModel):
    default_profile_id: str = "default"
    profiles: list[Profile] = Field(default_factory=list)
    
    def get_profile(self, profile_id: str) -> Optional[Profile]:
        for profile in self.profiles:
            if profile.profile_id == profile_id:
                return profile
        return None
    
    def get_default_profile(self) -> Optional[Profile]:
        return self.get_profile(self.default_profile_id)

EMBEDDED_CONFIG = {
    "default_profile_id": "default",
    "profiles": [
        {
            "profile_id": "default",
            "profile_name": "Default",
            "description": "General shortcuts for Discord + media controls.",
            "icon": "default",
            "bindings": {
                "F13": {
                    "label": " Mute",
                    "color_tag": "red",
                    "output_key": "F13"
                },
                "F14": {
                    "label": "Discord Deafen",
                    "color_tag": "purple",
                    "output_key": "F14"
                },
                "F15": {
                    "label": "Media Mute",
                    "color_tag": "cyan",
                    "output_key": "F15"
                },
                "F16": {
                    "label": "Vol +",
                    "color_tag": "cyan",
                    "output_key": "F16"
                },
                "F17": {
                    "label": "Vol -",
                    "color_tag": "cyan",
                    "output_key": "F17"
                },
                "F18": {
                    "label": "Push-To-Talk",
                    "color_tag": "green",
                    "output_key": "F18"
                },
                "F19": {
                    "label": "Screenshot",
                    "color_tag": "orange",
                    "output_key": "F19"
                },
                "F20": {
                    "label": "OBS Start/Stop",
                    "color_tag": "red",
                    "output_key": "F20"
                },
                "F21": {
                    "label": "Scene Next",
                    "color_tag": "red",
                    "output_key": "F21"
                },
                "F22": {
                    "label": "Scene Prev",
                    "color_tag": "red",
                    "output_key": "F22"
                },
                "F23": {
                    "label": "Browser Focus",
                    "color_tag": "blue",
                    "output_key": "F23"
                },
                "F24": {
                    "label": "Gaming Mode",
                    "color_tag": "yellow",
                    "output_key": "F24"
                }
            }
        }
    ]
}

class ConfigManager:
    
    def __init__(self):
        self.config: Optional[AppConfig] = None
    
    def load(self) -> AppConfig:
        try:
            self.config = AppConfig(**EMBEDDED_CONFIG)
        except Exception:
            self.config = self._create_default_config()
        
        return self.config
    
    def save(self) -> bool:
        return True
    
    def _create_default_config(self) -> AppConfig:
        return AppConfig(**EMBEDDED_CONFIG)

COLORS = {
    "bg_primary": "#1e1e1e",
    "bg_secondary": "#252525",
    "bg_tertiary": "#2d2d2d",
    "text_primary": "#ffffff",
    "text_secondary": "#b0b0b0",
    "accent_cyan": "#00d4ff",
    "accent_purple": "#9d4edd",
    "accent_green": "#06d6a0",
    "accent_orange": "#ff9e00",
    "accent_red": "#ef476f",
    "accent_blue": "#118ab2",
    "accent_yellow": "#ffd60a",
    "accent_gray": "#6c757d",
    "border": "#3a3a3a",
    "hover": "#353535",
}

def get_color_for_tag(tag: str) -> str:
    color_map = {
        "purple": COLORS["accent_purple"],
        "cyan": COLORS["accent_cyan"],
        "green": COLORS["accent_green"],
        "orange": COLORS["accent_orange"],
        "red": COLORS["accent_red"],
        "blue": COLORS["accent_blue"],
        "yellow": COLORS["accent_yellow"],
        "gray": COLORS["accent_gray"],
    }
    return color_map.get(tag, COLORS["accent_gray"])

class KeyButton(QPushButton):
    
    clicked_signal = Signal(str)
    
    def __init__(self, key_name: str, binding: KeyBinding, parent=None):
        super().__init__(parent)
        self.key_name = key_name
        self.binding = binding
        self.output_key = binding.output_key
        
        self.setMinimumSize(90, 50)
        self.setMaximumSize(90, 50)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.update_display()
        self.clicked.connect(lambda: self.clicked_signal.emit(self.output_key))
    
    def update_display(self):
        label = self.binding.label if self.binding.label else self.key_name
        color = get_color_for_tag(self.binding.color_tag)
        
        style = f"""
        QPushButton {{
            background-color: {COLORS["bg_secondary"]};
            border: 2px solid {color};
            border-radius: 8px;
            color: {COLORS["text_primary"]};
            font-size: 10px;
            font-weight: 500;
            padding: 4px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["hover"]};
            border-color: {color};
        }}
        QPushButton:pressed {{
            background-color: {color};
            color: {COLORS["bg_primary"]};
        }}
        """
        self.setStyleSheet(style)
        self.setText(label)
        self.setToolTip(f"{self.key_name} → {self.output_key}\n{label}")
    
    def update_binding(self, binding: KeyBinding):
        self.binding = binding
        self.output_key = binding.output_key
        self.update_display()

class EditKeyDialog(QDialog):
    
    def __init__(self, key_name: str, binding: KeyBinding, parent=None):
        super().__init__(parent)
        self.key_name = key_name
        self.binding = binding
        
        self.setWindowTitle(f"Edit {key_name}")
        self.setMinimumWidth(300)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS["bg_primary"]};
                color: {COLORS["text_primary"]};
            }}
            QLabel {{
                color: {COLORS["text_primary"]};
            }}
            QLineEdit, QComboBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 6px;
                color: {COLORS["text_primary"]};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {COLORS["accent_cyan"]};
            }}
        """)
        
        layout = QFormLayout(self)
        
        self.key_label = QLabel(f"Key: {key_name} → {binding.output_key}")
        layout.addRow("", self.key_label)
        
        self.label_input = QLineEdit(binding.label)
        self.label_input.setMaxLength(18)
        layout.addRow("Label:", self.label_input)
        
        color_layout = QHBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.setMinimumWidth(200)
        color_layout.addWidget(self.color_combo)
        
        layout.addRow("Color:", color_layout)
        self.populate_color_combo()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def populate_color_combo(self):
        self.color_combo.clear()
        default_colors = [
            ("purple", "#9d4edd"),
            ("cyan", "#00d4ff"),
            ("green", "#06d6a0"),
            ("orange", "#ff9e00"),
            ("red", "#ef476f"),
            ("blue", "#118ab2"),
            ("yellow", "#ffd60a"),
            ("gray", "#6c757d"),
        ]
        
        for name, color in default_colors:
            self.add_color_item(name, color)
        
        current_tag = self.binding.color_tag
        for i in range(self.color_combo.count()):
            if self.color_combo.itemData(i) == current_tag:
                self.color_combo.setCurrentIndex(i)
                break
    
    def add_color_item(self, tag: str, color: str):
        pixmap = QPixmap(20, 20)
        pixmap.fill(QColor(color))
        icon = QIcon(pixmap)
        self.color_combo.addItem(icon, tag, tag)
    
    def get_binding(self) -> KeyBinding:
        return KeyBinding(
            label=self.label_input.text(),
            color_tag=self.color_combo.currentData() or self.color_combo.currentText(),
            output_key=self.binding.output_key
        )

class RepeatKeyDialog(QDialog):
    
    def __init__(self, current_interval_ms: int = 1000, parent=None):
        super().__init__(parent)
        self.selected_key = None
        self.interval_ms = current_interval_ms
        
        self.setWindowTitle("Auto Repeat Settings")
        self.setMinimumWidth(350)
        self.setMinimumHeight(450)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS["bg_primary"]};
                color: {COLORS["text_primary"]};
            }}
            QLabel {{
                color: {COLORS["text_primary"]};
            }}
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS["text_primary"]};
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["hover"]};
                border-color: {COLORS["accent_cyan"]};
            }}
            QLineEdit, QComboBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 6px;
                color: {COLORS["text_primary"]};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {COLORS["accent_cyan"]};
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        key_label = QLabel("Select Key to Repeat:")
        key_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(key_label)
        
        grid = QGridLayout()
        grid.setSpacing(5)
        
        f_keys = get_f_key_list()
        for idx, key_name in enumerate(f_keys):
            row = idx // 3
            col = idx % 3
            btn = QPushButton(key_name)
            btn.clicked.connect(lambda checked, k=key_name: self.select_key(k))
            grid.addWidget(btn, row, col)
        
        layout.addLayout(grid)
        
        self.selected_key_label = QLabel("Selected: None")
        self.selected_key_label.setStyleSheet("font-size: 11px; color: " + COLORS["accent_cyan"] + ";")
        layout.addWidget(self.selected_key_label)
        
        layout.addSpacing(10)
        
        speed_label = QLabel("Repeat Speed:")
        speed_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(speed_label)
        
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unit:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Milliseconds", "Seconds", "Minutes", "Hours"])
        self.unit_combo.setCurrentText("Seconds")
        self.unit_combo.currentTextChanged.connect(self.update_interval)
        unit_layout.addWidget(self.unit_combo)
        layout.addLayout(unit_layout)
        
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        self.value_input = QLineEdit("1.0")
        self.value_input.setPlaceholderText("Enter value")
        self.value_input.textChanged.connect(self.update_interval)
        value_layout.addWidget(self.value_input)
        layout.addLayout(value_layout)
        
        preset_label = QLabel("Presets:")
        layout.addWidget(preset_label)
        preset_layout = QHBoxLayout()
        
        turbo_btn = QPushButton("Turbo")
        turbo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["accent_red"]};
                font-weight: bold;
            }}
        """)
        turbo_btn.clicked.connect(lambda: self.set_preset("0.001", "Seconds"))
        preset_layout.addWidget(turbo_btn)
        
        for label, value, unit in [("Fast", "0.1", "Seconds"), ("Normal", "1", "Seconds"), ("Slow", "5", "Seconds")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, v=value, u=unit: self.set_preset(v, u))
            preset_layout.addWidget(btn)
        
        layout.addLayout(preset_layout)
        
        self.interval_label = QLabel()
        self.interval_label.setStyleSheet("font-size: 10px; color: " + COLORS["text_secondary"] + ";")
        self.update_interval()
        layout.addWidget(self.interval_label)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_dialog)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def select_key(self, key_name: str):
        self.selected_key = key_name
        self.selected_key_label.setText(f"Selected: {key_name}")
        self.selected_key_label.setStyleSheet("font-size: 11px; color: " + COLORS["accent_green"] + ";")
    
    def set_preset(self, value: str, unit: str):
        self.value_input.setText(value)
        self.unit_combo.setCurrentText(unit)
    
    def update_interval(self):
        try:
            value = float(self.value_input.text() or "1.0")
            unit = self.unit_combo.currentText()
            
            if unit == "Milliseconds":
                interval_ms = int(value)
            elif unit == "Seconds":
                interval_ms = int(value * 1000)
            elif unit == "Minutes":
                interval_ms = int(value * 60 * 1000)
            elif unit == "Hours":
                interval_ms = int(value * 60 * 60 * 1000)
            else:
                interval_ms = 1000
            
            interval_ms = max(1, min(interval_ms, 216000000))
            
            self.interval_ms = interval_ms
            
            if interval_ms < 1000:
                self.interval_label.setText(f"Interval: {interval_ms} ms")
            elif interval_ms < 60000:
                self.interval_label.setText(f"Interval: {interval_ms/1000:.3f} seconds")
            elif interval_ms < 3600000:
                self.interval_label.setText(f"Interval: {interval_ms/60000:.2f} minutes")
            else:
                self.interval_label.setText(f"Interval: {interval_ms/3600000:.2f} hours")
        except ValueError:
            self.interval_label.setText("Invalid value")
    
    def accept_dialog(self):
        if self.selected_key:
            self.accept()
        else:
            QMessageBox.warning(self, "No Key Selected", "Please select a key to repeat.")
    
    def get_interval_ms(self) -> int:
        return self.interval_ms

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        self.current_profile: Optional[Profile] = self.config.get_default_profile()
        self.edit_mode = False
        self.position_locked = False
        self.old_pos = None
        self.is_minimized = False
        
        self.global_repeat_timer = None
        self.current_repeat_key = None
        
        self.minimize_button = None
        
        self.repeat_interval_ms = 1000
        
        self.init_ui()
        self.init_tray()
        self.load_profile(self.config.default_profile_id)
    
    def init_ui(self):
        self.setWindowTitle("STACK-PAD v2.7.0")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.setFixedSize(320, 340)
        self.position_bottom_right()
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS["bg_primary"]};
            }}
            QWidget {{
                background-color: {COLORS["bg_primary"]};
                color: {COLORS["text_primary"]};
            }}
        """)
        
        self.top_bar = self.create_top_bar()
        main_layout.addWidget(self.top_bar)
        
        self.key_grid = self.create_key_grid()
        main_layout.addWidget(self.key_grid)
        
        self.bottom_bar = self.create_bottom_bar()
        main_layout.addWidget(self.bottom_bar)
    
    def create_top_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)
        
        title_label = QLabel("STACK-PAD")
        title_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {COLORS["accent_cyan"]};
        """)
        left_layout.addWidget(title_label)
        
        version_copyright_layout = QHBoxLayout()
        version_copyright_layout.setSpacing(5)
        
        version_label = QLabel("v2.7.0")
        version_label.setStyleSheet(f"""
            font-size: 9px;
            color: {COLORS["text_secondary"]};
        """)
        version_copyright_layout.addWidget(version_label)
        
        copyright_label = QLabel("Dev.Essam / GitHub ( s0-5 ) © 2026")
        copyright_label.setStyleSheet(f"""
            font-size: 8px;
            color: {COLORS["text_secondary"]};
        """)
        version_copyright_layout.addWidget(copyright_label)
        version_copyright_layout.addStretch()
        
        left_layout.addLayout(version_copyright_layout)
        layout.addLayout(left_layout)
        
        layout.addStretch()
        
        self.lock_btn = QPushButton("🔒")
        self.lock_btn.setFixedSize(30, 30)
        self.lock_btn.setToolTip("Lock/Unlock Position")
        self.lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["hover"]};
            }}
        """)
        self.lock_btn.clicked.connect(self.toggle_lock)
        layout.addWidget(self.lock_btn)
        
        self.minimize_btn = QPushButton("👁")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setToolTip("Hide/Show Application")
        self.minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["hover"]};
            }}
        """)
        self.minimize_btn.clicked.connect(self.toggle_minimize)
        layout.addWidget(self.minimize_btn)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setToolTip("Close Application")
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                color: {COLORS["accent_red"]};
            }}
            QPushButton:hover {{
                background-color: {COLORS["accent_red"]};
                color: {COLORS["text_primary"]};
            }}
        """)
        self.close_btn.clicked.connect(self.close_application)
        layout.addWidget(self.close_btn)
        
        return bar
    
    def create_key_grid(self) -> QWidget:
        grid_widget = QWidget()
        main_layout = QVBoxLayout(grid_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        key_grid = QGridLayout()
        key_grid.setSpacing(10)
        
        self.key_buttons = {}
        f_keys = get_f_key_list()
        
        for idx, key_name in enumerate(f_keys):
            row = idx // 3
            col = idx % 3
            
            binding = None
            if self.current_profile and key_name in self.current_profile.bindings:
                binding = self.current_profile.bindings[key_name]
            else:
                binding = KeyBinding(label=key_name, output_key=key_name)
            
            btn = KeyButton(key_name, binding)
            btn.clicked_signal.connect(self.on_key_clicked)
            self.key_buttons[key_name] = btn
            key_grid.addWidget(btn, row, col)
        
        main_layout.addLayout(key_grid)
        
        return grid_widget
    
    def create_bottom_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self.edit_btn = QPushButton("Edit Mode")
        self.edit_btn.setCheckable(True)
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:checked {{
                background-color: {COLORS["accent_cyan"]};
                color: {COLORS["bg_primary"]};
            }}
            QPushButton:hover {{
                background-color: {COLORS["hover"]};
            }}
        """)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        layout.addWidget(self.edit_btn)
        
        self.auto_repeat_btn = QPushButton("Auto Repeat")
        self.auto_repeat_btn.setCheckable(True)
        self.auto_repeat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:checked {{
                background-color: {COLORS["accent_red"]};
                color: {COLORS["text_primary"]};
            }}
            QPushButton:hover {{
                background-color: {COLORS["hover"]};
            }}
        """)
        self.auto_repeat_btn.clicked.connect(self.on_auto_repeat_clicked)
        layout.addWidget(self.auto_repeat_btn)
        
        self.repeat_control_btn = QPushButton("Off")
        self.repeat_control_btn.setCheckable(True)
        self.repeat_control_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:checked {{
                background-color: {COLORS["accent_green"]};
                color: {COLORS["text_primary"]};
            }}
            QPushButton:hover {{
                background-color: {COLORS["hover"]};
            }}
        """)
        self.repeat_control_btn.clicked.connect(self.toggle_repeat_control)
        layout.addWidget(self.repeat_control_btn)
        
        layout.addStretch()
        
        return bar
    
    def init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        self.tray.setIcon(icon)
        self.tray.setToolTip("STACK-PAD v2.7.0")
        
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show/Hide")
        show_action.triggered.connect(self.toggle_visibility)
        
        lock_action = tray_menu.addAction("Lock Position")
        lock_action.triggered.connect(self.toggle_lock)
        
        tray_menu.addSeparator()
        
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()
    
    def position_bottom_right(self):
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 50
        self.move(x, y)
    
    def load_profile(self, profile_id: str):
        profile = self.config.get_profile(profile_id)
        if profile is None:
            return
        
        self.current_profile = profile
        
        for key_name, btn in self.key_buttons.items():
            if key_name in profile.bindings:
                btn.update_binding(profile.bindings[key_name])
    
    
    def on_key_clicked(self, output_key: str):
        if self.edit_mode:
            key_name = None
            for k, btn in self.key_buttons.items():
                if btn.output_key == output_key:
                    key_name = k
                    break
            
            if key_name and self.current_profile:
                binding = self.current_profile.bindings.get(key_name)
                if binding:
                    dialog = EditKeyDialog(key_name, binding, self)
                    if dialog.exec():
                        new_binding = dialog.get_binding()
                        self.current_profile.bindings[key_name] = new_binding
                        self.key_buttons[key_name].update_binding(new_binding)
                        self.config_manager.save()
        else:
            send_key(output_key)
    
    def on_auto_repeat_clicked(self):
        if self.auto_repeat_btn.isChecked():
            current_interval = getattr(self, 'repeat_interval_ms', 1000)
            dialog = RepeatKeyDialog(current_interval, self)
            if dialog.exec() and dialog.selected_key:
                self.current_repeat_key = dialog.selected_key
                self.repeat_interval_ms = dialog.get_interval_ms()
                self.start_global_repeat(dialog.selected_key, self.repeat_interval_ms)
                self.repeat_control_btn.setChecked(True)
                self.repeat_control_btn.setText("On")
            else:
                self.auto_repeat_btn.setChecked(False)
        else:
            self.stop_global_repeat()
    
    def toggle_repeat_control(self):
        if self.repeat_control_btn.isChecked():
            if hasattr(self, 'current_repeat_key') and hasattr(self, 'repeat_interval_ms'):
                if hasattr(self, 'global_repeat_timer') and self.global_repeat_timer and self.global_repeat_timer.isActive():
                    pass
                else:
                    self.start_global_repeat(self.current_repeat_key, self.repeat_interval_ms)
                self.repeat_control_btn.setText("On")
            else:
                self.auto_repeat_btn.setChecked(True)
                self.on_auto_repeat_clicked()
        else:
            self.pause_global_repeat()
            self.repeat_control_btn.setText("Off")
    
    def start_global_repeat(self, repeat_key: str, interval_ms: int = 1000):
        self.stop_global_repeat()
        
        self.current_repeat_key = repeat_key
        self.repeat_interval_ms = interval_ms
        
        timer = QTimer(self)
        timer.timeout.connect(lambda: self.repeat_key_press(repeat_key))
        timer.start(interval_ms)
        
        self.global_repeat_timer = timer
        self.auto_repeat_btn.setText(f"Auto Repeat ({repeat_key})")
    
    def pause_global_repeat(self):
        if hasattr(self, 'global_repeat_timer') and self.global_repeat_timer:
            self.global_repeat_timer.stop()
    
    def stop_global_repeat(self):
        if hasattr(self, 'global_repeat_timer') and self.global_repeat_timer:
            self.global_repeat_timer.stop()
            self.global_repeat_timer.deleteLater()
            self.global_repeat_timer = None
        
        if hasattr(self, 'current_repeat_key'):
            delattr(self, 'current_repeat_key')
        
        if hasattr(self, 'auto_repeat_btn'):
            self.auto_repeat_btn.setChecked(False)
            self.auto_repeat_btn.setText("Auto Repeat")
        
        if hasattr(self, 'repeat_control_btn'):
            self.repeat_control_btn.setChecked(False)
            self.repeat_control_btn.setText("Off")
    
    def repeat_key_press(self, output_key: str):
        send_key(output_key)
    
    def toggle_edit_mode(self):
        self.edit_mode = self.edit_btn.isChecked()
        if self.edit_mode:
            self.edit_btn.setText("Edit Mode ON")
        else:
            self.edit_btn.setText("Edit Mode")
    
    def toggle_lock(self):
        self.position_locked = not self.position_locked
        if self.position_locked:
            self.lock_btn.setText("🔒")
            self.lock_btn.setToolTip("Position Locked")
        else:
            self.lock_btn.setText("🔓")
            self.lock_btn.setToolTip("Position Unlocked")
    
    def toggle_minimize(self):
        if self.is_minimized:
            self.show_main_window()
        else:
            self.hide_to_button()
    
    def close_application(self):
        reply = QMessageBox.question(
            self, "Close Application",
            "Do you want to close the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.stop_global_repeat()
            
            if self.minimize_button:
                self.minimize_button.hide()
                self.minimize_button.deleteLater()
            
            QApplication.quit()
    
    def hide_to_button(self):
        self.saved_pos = self.pos()
        
        self.hide()
        self.is_minimized = True
        
        self.minimize_button = QWidget()
        self.minimize_button.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.minimize_button.setAttribute(Qt.WA_TranslucentBackground, False)
        self.minimize_button.setFixedSize(35, 35)
        dark_red = "#8B0000"
        self.minimize_button.setStyleSheet(f"""
            QWidget {{
                background-color: {dark_red};
                border: 2px solid {dark_red};
                border-radius: 17px;
            }}
        """)
        
        self.minimize_button.mousePressEvent = self.minimize_button_press
        self.minimize_button.mouseMoveEvent = self.minimize_button_move
        self.minimize_button.mouseReleaseEvent = self.minimize_button_release
        
        layout = QVBoxLayout(self.minimize_button)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("👁")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; background: transparent;")
        layout.addWidget(label)
        
        self.minimize_button.mouseDoubleClickEvent = lambda e: self.show_main_window()
        
        if hasattr(self, 'saved_pos'):
            self.minimize_button.move(self.saved_pos)
        else:
            screen = QApplication.primaryScreen().geometry()
            x = screen.width() - 50
            y = screen.height() - 50
            self.minimize_button.move(x, y)
        
        self.minimize_button.show()
        self.minimize_button.raise_()
        self.minimize_button.activateWindow()
    
    def show_main_window(self):
        if self.minimize_button:
            if self.minimize_button.isVisible():
                self.saved_pos = self.minimize_button.pos()
            self.minimize_button.hide()
            self.minimize_button.deleteLater()
            self.minimize_button = None
        
        self.is_minimized = False
        
        if hasattr(self, 'saved_pos'):
            self.move(self.saved_pos)
        self.show()
        self.raise_()
        self.activateWindow()
    
    def minimize_button_press(self, event):
        if event.button() == Qt.LeftButton:
            self.minimize_old_pos = event.globalPosition().toPoint()
            self.minimize_click_start = event.globalPosition().toPoint()
    
    def minimize_button_move(self, event):
        if hasattr(self, 'minimize_old_pos'):
            delta = event.globalPosition().toPoint() - self.minimize_old_pos
            self.minimize_button.move(self.minimize_button.pos() + delta)
            self.minimize_old_pos = event.globalPosition().toPoint()
    
    def minimize_button_release(self, event):
        if hasattr(self, 'minimize_old_pos'):
            if hasattr(self, 'minimize_click_start'):
                moved = (event.globalPosition().toPoint() - self.minimize_click_start).manhattanLength()
                if moved < 5:
                    self.show_main_window()
                delattr(self, 'minimize_click_start')
            delattr(self, 'minimize_old_pos')
    
    
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_visibility()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.position_locked:
            self.old_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.old_pos and not self.position_locked:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.old_pos = None
        super().mouseReleaseEvent(event)
    
    def closeEvent(self, event):
        self.stop_global_repeat()
        
        if self.minimize_button:
            self.minimize_button.hide()
            self.minimize_button.deleteLater()
        
        if self.tray.isVisible():
            QMessageBox.information(
                self, "Keys Pad",
                "The application will continue to run in the system tray.\n"
                "To quit, choose Exit from the tray menu."
            )
            self.hide()
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
