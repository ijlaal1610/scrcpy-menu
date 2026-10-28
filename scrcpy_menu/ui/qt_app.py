"""Modern Cross-Platform Qt GUI for Scrcpy Control Center using PySide6 (with PyQt fallback)."""

import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, QTimer, Signal, Slot
except ImportError:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal, pyqtSlot as Slot
    except ImportError:
        raise ImportError("Neither PySide6 nor PyQt6 is installed. Please install PySide6 via 'pip install PySide6'.")

from ..core.config import load_config, save_config
from ..core.device import (
    get_connected_devices,
    is_adb_available,
    connect_wireless,
    pair_wireless,
    restart_adb_server,
    install_apk,
    push_file,
    query_device_cameras,
    query_device_encoders,
)
from ..core.desktop_mode import (
    DESKTOP_MODE_FLAGS,
    get_desktop_mode_status,
    set_desktop_mode,
    restore_desktop_mode_defaults,
    detect_desktop_mode_support,
)
from ..core.capabilities import get_scrcpy_version_info, generate_system_diagnostics
from ..core.process import ScrcpyProcessManager
from ..platform_adapters import get_platform_adapter

DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #121418;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}
QWidget {
    background-color: transparent;
    color: #e2e8f0;
}
QTabWidget::pane {
    border: 1px solid #232834;
    background-color: #171a21;
    border-radius: 8px;
    padding: 6px;
}
QTabBar::tab {
    background-color: #1a1e27;
    color: #94a3b8;
    padding: 10px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #242c3d;
    color: #38bdf8;
    border-bottom: 2px solid #38bdf8;
}
QTabBar::tab:hover:!selected {
    background-color: #202633;
    color: #cbd5e1;
}
QGroupBox {
    border: 1px solid #2a3244;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 600;
    color: #38bdf8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
}
QPushButton {
    background-color: #242c3d;
    color: #f1f5f9;
    border: 1px solid #38455e;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2f3a52;
    border-color: #38bdf8;
}
QPushButton:pressed {
    background-color: #1e2533;
}
QPushButton#btn_primary {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    font-size: 14px;
    padding: 10px 20px;
}
QPushButton#btn_primary:hover {
    background-color: #0369a1;
}
QPushButton#btn_stop {
    background-color: #dc2626;
    color: #ffffff;
    border: none;
    font-size: 14px;
    padding: 10px 20px;
}
QPushButton#btn_stop:hover {
    background-color: #b91c1c;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: #1a1e27;
    border: 1px solid #2e3648;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
    selection-background-color: #0284c7;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #38bdf8;
}
QComboBox QAbstractItemView {
    background-color: #1a1e27;
    border: 1px solid #2e3648;
    selection-background-color: #242c3d;
    selection-color: #38bdf8;
}
QCheckBox {
    spacing: 8px;
    color: #cbd5e1;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #38455e;
    background-color: #1a1e27;
}
QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}
QTextEdit, QPlainTextEdit {
    background-color: #0d0f13;
    border: 1px solid #242c3d;
    border-radius: 6px;
    color: #94a3b8;
    font-family: 'Consolas', 'DejaVu Sans Mono', monospace;
    font-size: 12px;
}
QTableWidget {
    background-color: #121418;
    border: 1px solid #242c3d;
    border-radius: 6px;
    gridline-color: #1a1e27;
}
QHeaderView::section {
    background-color: #1a1e27;
    color: #38bdf8;
    padding: 6px;
    border: 1px solid #242c3d;
    font-weight: 600;
}
QScrollBar:vertical {
    background: #121418;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #242c3d;
    border-radius: 4px;
}
"""


class ScrcpyMainWindow(QtWidgets.QMainWindow):
    """Main application window with drag-and-drop, wireless pairing, and advanced scrcpy controls."""

    log_signal = Signal(str)
    process_exit_signal = Signal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scrcpy Control Center")
        self.resize(920, 750)
        self.setMinimumSize(800, 620)
        self.setAcceptDrops(True)

        self.config = load_config()
        self.proc_manager = ScrcpyProcessManager()
        self.platform_adapter = get_platform_adapter()
        self.capabilities = get_scrcpy_version_info()

        # Connect log and exit signals to safely update GUI on main thread
        self.log_signal.connect(self._append_log)
        self.process_exit_signal.connect(self._on_process_exited)
        self.proc_manager.register_log_callback(lambda line: self.log_signal.emit(line))
        self.proc_manager.register_exit_callback(lambda rc: self.process_exit_signal.emit(rc))

        self._setup_ui()
        self._load_saved_preferences()
        self._refresh_devices()

    def _setup_ui(self):
        self.setStyleSheet(DARK_STYLESHEET)
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ── Header Bar ──
        header_layout = QtWidgets.QHBoxLayout()

        # Title & Version Badge
        title_box = QtWidgets.QHBoxLayout()
        lbl_app = QtWidgets.QLabel("Scrcpy Control Center")
        lbl_app.setStyleSheet("font-size: 17px; font-weight: 800; color: #38bdf8;")
        title_box.addWidget(lbl_app)

        v_str = self.capabilities.get("version_str", "Unknown")
        lbl_badge = QtWidgets.QLabel(f"v{v_str}")
        lbl_badge.setStyleSheet("background-color: #1e293b; color: #38bdf8; border-radius: 4px; padding: 2px 6px; font-weight: bold;")
        title_box.addWidget(lbl_badge)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Device selection combo
        lbl_dev = QtWidgets.QLabel("Device:")
        lbl_dev.setStyleSheet("font-weight: 600; color: #94a3b8;")
        header_layout.addWidget(lbl_dev)

        self.cmb_devices = QtWidgets.QComboBox()
        self.cmb_devices.setMinimumWidth(230)
        header_layout.addWidget(self.cmb_devices)

        btn_refresh_dev = QtWidgets.QPushButton("🔄 Refresh")
        btn_refresh_dev.clicked.connect(self._refresh_devices)
        header_layout.addWidget(btn_refresh_dev)

        btn_wifi_dev = QtWidgets.QPushButton("📶 Wi-Fi & Pair")
        btn_wifi_dev.setToolTip("Connect or pair wirelessly via ADB")
        btn_wifi_dev.clicked.connect(self._dialog_wifi_manager)
        header_layout.addWidget(btn_wifi_dev)

        btn_restart_adb = QtWidgets.QPushButton("⚡ Restart ADB")
        btn_restart_adb.setToolTip("Restart the local ADB server daemon")
        btn_restart_adb.clicked.connect(self._restart_adb_daemon)
        header_layout.addWidget(btn_restart_adb)

        main_layout.addLayout(header_layout)

        # ── Tab Widget ──
        self.tabs = QtWidgets.QTabWidget()
        self.tab_mirror = QtWidgets.QWidget()
        self.tab_vd = QtWidgets.QWidget()
        self.tab_camera = QtWidgets.QWidget()
        self.tab_shortcuts = QtWidgets.QWidget()

        self._setup_tab_mirror()
        self._setup_tab_vd()
        self._setup_tab_camera()
        self._setup_tab_shortcuts()

        self.tabs.addTab(self.tab_mirror, "📱 Screen Mirroring")
        self.tabs.addTab(self.tab_vd, "🖥️ Virtual Display")
        self.tabs.addTab(self.tab_camera, "📷 Camera / Webcam")
        self.tabs.addTab(self.tab_shortcuts, "⌨️ Shortcuts & Logs")

        main_layout.addWidget(self.tabs, stretch=1)

        # ── Bottom Control Panel ──
        bottom_box = QtWidgets.QHBoxLayout()
        self.lbl_status = QtWidgets.QLabel("● Ready")
        self.lbl_status.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
        bottom_box.addWidget(self.lbl_status)

        bottom_box.addStretch()

        self.btn_toggle_log = QtWidgets.QPushButton("📋 Toggle Log Panel")
        self.btn_toggle_log.clicked.connect(self._toggle_log_panel)
        bottom_box.addWidget(self.btn_toggle_log)

        self.btn_action = QtWidgets.QPushButton("▶ Launch Scrcpy")
        self.btn_action.setObjectName("btn_primary")
        self.btn_action.clicked.connect(self._on_action_clicked)
        bottom_box.addWidget(self.btn_action)

        main_layout.addLayout(bottom_box)

        # ── Collapsible Live Log Panel ──
        self.log_widget = QtWidgets.QWidget()
        log_layout = QtWidgets.QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(0, 4, 0, 0)
        log_layout.setSpacing(6)

        log_header = QtWidgets.QHBoxLayout()
        lbl_log = QtWidgets.QLabel("Live Console Output (drag APKs / files here to push):")
        lbl_log.setStyleSheet("font-weight: bold; color: #94a3b8;")
        log_header.addWidget(lbl_log)
        log_header.addStretch()

        btn_copy_log = QtWidgets.QPushButton("Copy Logs")
        btn_copy_log.clicked.connect(self._copy_logs)
        log_header.addWidget(btn_copy_log)

        btn_clear_log = QtWidgets.QPushButton("Clear")
        btn_clear_log.clicked.connect(self._clear_logs)
        log_header.addWidget(btn_clear_log)
        log_layout.addLayout(log_header)

        self.txt_logs = QtWidgets.QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setMaximumHeight(140)
        log_layout.addWidget(self.txt_logs)

        main_layout.addWidget(self.log_widget)

    # ─────────────────────────────────────────────────────────────
    # TAB 1: SCREEN MIRRORING
    # ─────────────────────────────────────────────────────────────
    def _setup_tab_mirror(self):
        layout = QtWidgets.QVBoxLayout(self.tab_mirror)
        layout.setSpacing(12)

        # Presets Group
        grp_presets = QtWidgets.QGroupBox("Quick Presets")
        presets_layout = QtWidgets.QHBoxLayout(grp_presets)
        btn_120 = QtWidgets.QPushButton("🚀 120 FPS Native")
        btn_120.clicked.connect(lambda: self._apply_mirror_preset(120, "8M", True, True))
        btn_60 = QtWidgets.QPushButton("📺 60 FPS Standard")
        btn_60.clicked.connect(lambda: self._apply_mirror_preset(60, "8M", True, True))
        btn_lowlat = QtWidgets.QPushButton("⚡ Ultra Low-Lag")
        btn_lowlat.clicked.connect(lambda: self._apply_mirror_preset(60, "4M", True, False))

        presets_layout.addWidget(btn_120)
        presets_layout.addWidget(btn_60)
        presets_layout.addWidget(btn_lowlat)
        layout.addWidget(grp_presets)

        # Stream & Display Options
        grp_opts = QtWidgets.QGroupBox("Display & Stream Options")
        form = QtWidgets.QFormLayout(grp_opts)
        form.setSpacing(8)

        self.cmb_mirror_fps = QtWidgets.QComboBox()
        self.cmb_mirror_fps.addItems(["120", "90", "60", "30", "0 (Unlimited)"])
        form.addRow("Max FPS:", self.cmb_mirror_fps)

        self.cmb_mirror_bitrate = QtWidgets.QComboBox()
        self.cmb_mirror_bitrate.addItems(["16M", "12M", "8M", "4M", "2M"])
        form.addRow("Video Bitrate:", self.cmb_mirror_bitrate)

        self.chk_mirror_stay_awake = QtWidgets.QCheckBox("Stay Awake (prevent phone screen timeout)")
        form.addRow("", self.chk_mirror_stay_awake)

        self.chk_mirror_audio = QtWidgets.QCheckBox("Audio Forwarding (stream device sound to PC)")
        form.addRow("", self.chk_mirror_audio)

        self.chk_mirror_turn_off = QtWidgets.QCheckBox("Turn device physical screen off while mirroring")
        form.addRow("", self.chk_mirror_turn_off)

        self.chk_mirror_fullscreen = QtWidgets.QCheckBox("Start scrcpy in fullscreen mode")
        form.addRow("", self.chk_mirror_fullscreen)

        layout.addWidget(grp_opts)

        # Input & Recording Options
        grp_advanced = QtWidgets.QGroupBox("Hardware Input (HID) & Recording")
        adv_form = QtWidgets.QFormLayout(grp_advanced)
        adv_form.setSpacing(8)

        self.chk_mirror_hid_kb = QtWidgets.QCheckBox("Hardware Keyboard Simulation (--keyboard=uhid) [bypasses on-screen keyboard]")
        adv_form.addRow("", self.chk_mirror_hid_kb)

        self.chk_mirror_hid_mouse = QtWidgets.QCheckBox("Hardware Mouse Capture (--mouse=uhid) [high-precision cursor lock]")
        adv_form.addRow("", self.chk_mirror_hid_mouse)

        self.chk_mirror_otg = QtWidgets.QCheckBox("OTG Mode (--otg) [use PC keyboard/mouse directly without screen mirroring]")
        adv_form.addRow("", self.chk_mirror_otg)

        self.chk_mirror_record = QtWidgets.QCheckBox("Record Session to MP4 video in ~/Videos (--record)")
        adv_form.addRow("", self.chk_mirror_record)

        layout.addWidget(grp_advanced)
        layout.addStretch()

    def _apply_mirror_preset(self, fps: int, bitrate: str, awake: bool, audio: bool):
        self.cmb_mirror_fps.setCurrentText(str(fps) if fps != 0 else "0 (Unlimited)")
        self.cmb_mirror_bitrate.setCurrentText(bitrate)
        self.chk_mirror_stay_awake.setChecked(awake)
        self.chk_mirror_audio.setChecked(audio)

    # ─────────────────────────────────────────────────────────────
    # TAB 2: VIRTUAL DISPLAY
    # ─────────────────────────────────────────────────────────────
    def _setup_tab_vd(self):
        layout = QtWidgets.QVBoxLayout(self.tab_vd)
        layout.setSpacing(10)

        # Presets Group
        grp_presets = QtWidgets.QGroupBox("Virtual Display Presets")
        presets_layout = QtWidgets.QHBoxLayout(grp_presets)

        btn_blank = QtWidgets.QPushButton("🖥️ 1080p Blank")
        btn_blank.clicked.connect(lambda: self._apply_vd_preset("1920x1080", "180", True, ""))
        btn_chrome = QtWidgets.QPushButton("🌐 Chrome Browser")
        btn_chrome.clicked.connect(lambda: self._apply_vd_preset("1920x1080", "180", True, "com.android.chrome"))
        btn_desktop = QtWidgets.QPushButton("💻 Full Desktop Mode")
        btn_desktop.clicked.connect(lambda: self._apply_vd_preset("1920x1080", "180", True, "", force_desktop=True))

        presets_layout.addWidget(btn_blank)
        presets_layout.addWidget(btn_chrome)
        presets_layout.addWidget(btn_desktop)
        layout.addWidget(grp_presets)

        # Display Configuration
        grp_cfg = QtWidgets.QGroupBox("Display & Resolution Settings")
        form = QtWidgets.QFormLayout(grp_cfg)
        form.setSpacing(6)

        self.cmb_vd_res = QtWidgets.QComboBox()
        self.cmb_vd_res.addItems(["1920x1080", "2560x1440", "1280x720", "1024x768", "Native"])
        form.addRow("Resolution:", self.cmb_vd_res)

        self.cmb_vd_dpi = QtWidgets.QComboBox()
        self.cmb_vd_dpi.addItems(["180 (Desktop Scale)", "240 (Tablet)", "320 (Large)", "420 (Phone)", "Default"])
        form.addRow("DPI / Scale:", self.cmb_vd_dpi)

        self.cmb_vd_bitrate = QtWidgets.QComboBox()
        self.cmb_vd_bitrate.addItems(["16M", "12M", "8M", "4M"])
        form.addRow("Bitrate:", self.cmb_vd_bitrate)

        self.chk_vd_flex = QtWidgets.QCheckBox("Flex Display (allow window resizing to dynamically resize Android virtual display)")
        form.addRow("", self.chk_vd_flex)

        self.chk_vd_keep_active = QtWidgets.QCheckBox("Keep Active (prevent virtual display from sleeping when backgrounded)")
        form.addRow("", self.chk_vd_keep_active)

        self.chk_vd_audio = QtWidgets.QCheckBox("PC Sound (play virtual display sound through computer speakers)")
        form.addRow("", self.chk_vd_audio)

        self.chk_vd_destroy = QtWidgets.QCheckBox("Destroy Content (close apps on virtual display when window is closed)")
        form.addRow("", self.chk_vd_destroy)

        self.chk_vd_hid_kb = QtWidgets.QCheckBox("Hardware Keyboard Simulation (--keyboard=uhid)")
        form.addRow("", self.chk_vd_hid_kb)

        self.chk_vd_record = QtWidgets.QCheckBox("Record Virtual Display session to MP4 (--record)")
        form.addRow("", self.chk_vd_record)

        self.txt_vd_app = QtWidgets.QLineEdit()
        self.txt_vd_app.setPlaceholderText("e.g. com.android.chrome or leave blank")
        form.addRow("Auto-launch App:", self.txt_vd_app)

        layout.addWidget(grp_cfg)

        # Android Desktop Mode ADB Manager Group
        grp_dt = QtWidgets.QGroupBox("Android Desktop Mode & Freeform Windows (via ADB)")
        dt_layout = QtWidgets.QVBoxLayout(grp_dt)

        lbl_dt_info = QtWidgets.QLabel(
            "Controls Android global windowing flags (force_desktop_mode_on_external_displays, enable_freeform_support). "
            "Enabling this allows multi-window desktop environments on supported ROMs."
        )
        lbl_dt_info.setWordWrap(True)
        lbl_dt_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        dt_layout.addWidget(lbl_dt_info)

        dt_btn_box = QtWidgets.QHBoxLayout()
        self.lbl_dt_status = QtWidgets.QLabel("Status: Checking...")
        self.lbl_dt_status.setStyleSheet("font-weight: bold;")
        dt_btn_box.addWidget(self.lbl_dt_status)
        dt_btn_box.addStretch()

        btn_enable_dt = QtWidgets.QPushButton("✔ Enable Flags")
        btn_enable_dt.clicked.connect(self._enable_desktop_flags)
        dt_btn_box.addWidget(btn_enable_dt)

        btn_restore_dt = QtWidgets.QPushButton("↺ Restore OEM Defaults")
        btn_restore_dt.clicked.connect(self._restore_desktop_flags)
        dt_btn_box.addWidget(btn_restore_dt)

        dt_layout.addLayout(dt_btn_box)
        layout.addWidget(grp_dt)
        layout.addStretch()

    def _apply_vd_preset(self, res: str, dpi: str, flex: bool, app: str, force_desktop: bool = False):
        self.cmb_vd_res.setCurrentText(res)
        self.cmb_vd_dpi.setCurrentIndex(0 if dpi == "180" else 4)
        self.chk_vd_flex.setChecked(flex)
        self.txt_vd_app.setText(app)
        if force_desktop:
            self._enable_desktop_flags()

    def _enable_desktop_flags(self):
        target = self._get_selected_serial()
        succ, msg = set_desktop_mode(True, target)
        if succ:
            QtWidgets.QMessageBox.information(self, "Desktop Mode", msg)
        else:
            QtWidgets.QMessageBox.warning(self, "Desktop Mode Warning", msg)
        self._check_desktop_mode_status()

    def _restore_desktop_flags(self):
        target = self._get_selected_serial()
        succ, msg = restore_desktop_mode_defaults(target)
        QtWidgets.QMessageBox.information(self, "OEM Defaults Restored", msg)
        self._check_desktop_mode_status()

    def _check_desktop_mode_status(self):
        target = self._get_selected_serial()
        status_list = get_desktop_mode_status(target)
        all_on = True
        for flag, desc, val in status_list:
            if val != "1":
                all_on = False
                break
        if all_on:
            self.lbl_dt_status.setText("Status: ✅ Desktop Flags Enabled")
            self.lbl_dt_status.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self.lbl_dt_status.setText("Status: ⚠️ Partial / OEM Default")
            self.lbl_dt_status.setStyleSheet("color: #eab308; font-weight: bold;")

    # ─────────────────────────────────────────────────────────────
    # TAB 3: CAMERA / WEBCAM
    # ─────────────────────────────────────────────────────────────
    def _setup_tab_camera(self):
        layout = QtWidgets.QVBoxLayout(self.tab_camera)
        layout.setSpacing(12)

        # Presets Group
        grp_presets = QtWidgets.QGroupBox("Camera Presets")
        presets_layout = QtWidgets.QHBoxLayout(grp_presets)

        btn_cam30 = QtWidgets.QPushButton("📷 1080p @ 30fps (Anti-Lag)")
        btn_cam30.clicked.connect(lambda: self._apply_cam_preset("1920x1080", "30", True))
        btn_cam60 = QtWidgets.QPushButton("📷 1080p @ 60fps (Anti-Lag)")
        btn_cam60.clicked.connect(lambda: self._apply_cam_preset("1920x1080", "60", True))
        btn_cam_std = QtWidgets.QPushButton("📷 1080p Standard (Buffering)")
        btn_cam_std.clicked.connect(lambda: self._apply_cam_preset("1920x1080", "30", False))

        presets_layout.addWidget(btn_cam30)
        presets_layout.addWidget(btn_cam60)
        presets_layout.addWidget(btn_cam_std)
        layout.addWidget(grp_presets)

        # Configuration Group
        grp_cfg = QtWidgets.QGroupBox("Webcam & Sensor Settings")
        form = QtWidgets.QFormLayout(grp_cfg)
        form.setSpacing(8)

        self.cmb_cam_res = QtWidgets.QComboBox()
        self.cmb_cam_res.addItems(["1920x1080", "1280x720", "3840x2160 (4K)", "640x480"])
        form.addRow("Resolution:", self.cmb_cam_res)

        self.cmb_cam_fps = QtWidgets.QComboBox()
        self.cmb_cam_fps.addItems(["30", "60"])
        form.addRow("Frame Rate (FPS):", self.cmb_cam_fps)

        self.cmb_cam_bitrate = QtWidgets.QComboBox()
        self.cmb_cam_bitrate.addItems(["8M", "12M", "16M", "4M"])
        form.addRow("Bitrate:", self.cmb_cam_bitrate)

        # Camera Facing + Hardware ID Discovery
        cam_id_box = QtWidgets.QHBoxLayout()
        self.cmb_cam_facing = QtWidgets.QComboBox()
        self.cmb_cam_facing.addItems(["back", "front"])
        cam_id_box.addWidget(self.cmb_cam_facing)

        btn_detect_cams = QtWidgets.QPushButton("🔍 Detect Lenses")
        btn_detect_cams.setToolTip("Query connected device for physical camera IDs and lenses")
        btn_detect_cams.clicked.connect(self._detect_cameras)
        cam_id_box.addWidget(btn_detect_cams)
        form.addRow("Camera Sensor:", cam_id_box)

        self.chk_cam_antilag = QtWidgets.QCheckBox("Anti-Lag / Zero Buffer (--v4l2-buffer=0) [Prevents frame backlog]")
        form.addRow("", self.chk_cam_antilag)

        # Virtual Webcam Device Node
        self.cmb_cam_sink = QtWidgets.QComboBox()
        sinks = self.platform_adapter.get_camera_sinks()
        self.cmb_cam_sink.addItems(sinks)
        form.addRow("Virtual Webcam Sink:", self.cmb_cam_sink)

        layout.addWidget(grp_cfg)
        layout.addStretch()

    def _apply_cam_preset(self, res: str, fps: str, antilag: bool):
        self.cmb_cam_res.setCurrentText(res)
        self.cmb_cam_fps.setCurrentText(fps)
        self.chk_cam_antilag.setChecked(antilag)

    def _detect_cameras(self):
        target = self._get_selected_serial()
        cams = query_device_cameras(target)
        if not cams:
            QtWidgets.QMessageBox.information(
                self, "Camera Detection", "No camera descriptions returned by scrcpy. The default 'front' / 'back' will be used."
            )
            return

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Detected Camera Sensors")
        dlg.resize(550, 320)
        d_layout = QtWidgets.QVBoxLayout(dlg)

        lbl = QtWidgets.QLabel("Available lenses reported by device:")
        lbl.setStyleSheet("font-weight: bold; color: #38bdf8;")
        d_layout.addWidget(lbl)

        txt = QtWidgets.QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText("\n".join(cams))
        d_layout.addWidget(txt)

        btn_close = QtWidgets.QPushButton("Done")
        btn_close.clicked.connect(dlg.accept)
        d_layout.addWidget(btn_close)
        dlg.exec()

    # ─────────────────────────────────────────────────────────────
    # TAB 4: SHORTCUTS & LOGS
    # ─────────────────────────────────────────────────────────────
    def _setup_tab_shortcuts(self):
        layout = QtWidgets.QVBoxLayout(self.tab_shortcuts)
        layout.setSpacing(10)

        # Filter box
        filter_box = QtWidgets.QHBoxLayout()
        lbl_search = QtWidgets.QLabel("Filter Shortcuts:")
        lbl_search.setStyleSheet("font-weight: 600; color: #94a3b8;")
        filter_box.addWidget(lbl_search)

        self.txt_filter_sc = QtWidgets.QLineEdit()
        self.txt_filter_sc.setPlaceholderText("Search shortcut or action...")
        self.txt_filter_sc.textChanged.connect(self._filter_shortcuts)
        filter_box.addWidget(self.txt_filter_sc)

        btn_diag = QtWidgets.QPushButton("🔍 View Diagnostics Report")
        btn_diag.clicked.connect(self._show_diagnostics_dialog)
        filter_box.addWidget(btn_diag)

        layout.addLayout(filter_box)

        # Table of Shortcuts
        from ..cli import SHORTCUTS_LIST
        self.tbl_shortcuts = QtWidgets.QTableWidget(len(SHORTCUTS_LIST), 2)
        self.tbl_shortcuts.setHorizontalHeaderLabels(["Shortcut (MOD = Alt or Super)", "Action"])
        self.tbl_shortcuts.horizontalHeader().setStretchLastSection(True)
        self.tbl_shortcuts.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_shortcuts.verticalHeader().setVisible(False)
        self.tbl_shortcuts.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        for row, (sc, desc) in enumerate(SHORTCUTS_LIST):
            item_sc = QtWidgets.QTableWidgetItem(sc)
            item_desc = QtWidgets.QTableWidgetItem(desc)
            item_sc.setForeground(QtGui.QBrush(QtGui.QColor("#38bdf8")))
            self.tbl_shortcuts.setItem(row, 0, item_sc)
            self.tbl_shortcuts.setItem(row, 1, item_desc)

        layout.addWidget(self.tbl_shortcuts)

    def _filter_shortcuts(self, query: str):
        query = query.lower().strip()
        for row in range(self.tbl_shortcuts.rowCount()):
            item_sc = self.tbl_shortcuts.item(row, 0)
            item_desc = self.tbl_shortcuts.item(row, 1)
            sc_text = item_sc.text().lower() if item_sc else ""
            desc_text = item_desc.text().lower() if item_desc else ""
            visible = (query in sc_text or query in desc_text)
            self.tbl_shortcuts.setRowHidden(row, not visible)

    def _show_diagnostics_dialog(self):
        target = self._get_selected_serial()
        diag_text = generate_system_diagnostics(target)
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("System Diagnostics & Capability Matrix")
        dlg.resize(680, 500)
        d_layout = QtWidgets.QVBoxLayout(dlg)

        txt = QtWidgets.QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(diag_text)
        d_layout.addWidget(txt)

        btn_box = QtWidgets.QHBoxLayout()
        btn_copy = QtWidgets.QPushButton("Copy to Clipboard")
        btn_copy.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(diag_text))
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)
        btn_box.addWidget(btn_copy)
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        d_layout.addLayout(btn_box)
        dlg.exec()

    # ─────────────────────────────────────────────────────────────
    # DRAG & DROP APK INSTALL & FILE PUSH
    # ─────────────────────────────────────────────────────────────
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return

        target = self._get_selected_serial()
        for url in urls:
            path = url.toLocalFile()
            if not path or not os.path.exists(path):
                continue

            if path.lower().endswith(".apk"):
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Install APK",
                    f"Do you want to install '{os.path.basename(path)}' on the connected device?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                )
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.lbl_status.setText("● Installing APK...")
                    succ, msg = install_apk(path, target)
                    if succ:
                        QtWidgets.QMessageBox.information(self, "APK Installed", msg)
                    else:
                        QtWidgets.QMessageBox.critical(self, "Install Failed", msg)
                    self.lbl_status.setText("● Ready")
            else:
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Push File",
                    f"Push '{os.path.basename(path)}' to /sdcard/Download/ on device?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                )
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.lbl_status.setText("● Pushing file...")
                    succ, msg = push_file(path, "/sdcard/Download/", target)
                    if succ:
                        QtWidgets.QMessageBox.information(self, "File Pushed", msg)
                    else:
                        QtWidgets.QMessageBox.critical(self, "Push Failed", msg)
                    self.lbl_status.setText("● Ready")

    # ─────────────────────────────────────────────────────────────
    # EXECUTION & COMMAND BUILDING
    # ─────────────────────────────────────────────────────────────
    def _build_command_for_active_tab(self) -> List[str]:
        current_idx = self.tabs.currentIndex()
        target_serial = self._get_selected_serial()
        cmd = ["scrcpy"]

        if target_serial:
            cmd.append(f"--serial={target_serial}")

        # Helper for record file
        def _get_record_arg() -> str:
            videos_dir = Path.home() / "Videos"
            videos_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            return str(videos_dir / f"scrcpy_{timestamp}.mp4")

        if current_idx == 0:
            # ── Tab 0: Screen Mirroring ──
            if self.chk_mirror_otg.isChecked():
                cmd.append("--otg")
            else:
                fps = self.cmb_mirror_fps.currentText().split()[0]
                if fps != "0":
                    cmd.append(f"--max-fps={fps}")

                cmd.append(f"--video-bit-rate={self.cmb_mirror_bitrate.currentText()}")

                if self.chk_mirror_stay_awake.isChecked():
                    cmd.append("--stay-awake")

                if self.chk_mirror_audio.isChecked():
                    cmd.append("--audio-source=output")
                else:
                    cmd.append("--no-audio")

                if self.chk_mirror_turn_off.isChecked():
                    cmd.append("--turn-screen-off")

                if self.chk_mirror_fullscreen.isChecked():
                    cmd.append("-f")

                if self.chk_mirror_hid_kb.isChecked():
                    cmd.append("--keyboard=uhid")

                if self.chk_mirror_hid_mouse.isChecked():
                    cmd.append("--mouse=uhid")

                if self.chk_mirror_record.isChecked():
                    cmd.append(f"--record={_get_record_arg()}")

        elif current_idx == 1:
            # ── Tab 1: Virtual Display ──
            res = self.cmb_vd_res.currentText()
            dpi_txt = self.cmb_vd_dpi.currentText().split()[0]

            if res != "Native" and dpi_txt != "Default":
                cmd.append(f"--new-display={res}/{dpi_txt}")
            elif res != "Native":
                cmd.append(f"--new-display={res}")
            else:
                cmd.append("--new-display")

            if self.chk_vd_flex.isChecked() and self.capabilities.get("has_flex_display", False):
                cmd.append("--flex-display")

            if self.chk_vd_keep_active.isChecked():
                cmd.append("--keep-active")

            if not self.chk_vd_destroy.isChecked():
                cmd.append("--no-vd-destroy-content")

            if self.chk_vd_audio.isChecked():
                cmd.append("--audio-source=output")
            else:
                cmd.append("--no-audio")

            if self.chk_vd_hid_kb.isChecked():
                cmd.append("--keyboard=uhid")

            if self.chk_vd_record.isChecked():
                cmd.append(f"--record={_get_record_arg()}")

            cmd.append(f"--video-bit-rate={self.cmb_vd_bitrate.currentText()}")

            app = self.txt_vd_app.text().strip()
            if app:
                cmd.append(f"--start-app={app}")

        elif current_idx == 2:
            # ── Tab 2: Camera / Webcam ──
            cmd.append("--video-source=camera")
            cmd.append(f"--camera-size={self.cmb_cam_res.currentText().split()[0]}")
            cmd.append(f"--camera-fps={self.cmb_cam_fps.currentText()}")
            cmd.append(f"--camera-facing={self.cmb_cam_facing.currentText()}")
            cmd.append(f"--video-bit-rate={self.cmb_cam_bitrate.currentText()}")

            if self.chk_cam_antilag.isChecked():
                cmd.append("--v4l2-buffer=0")
                cmd.append("--no-audio")

            sink = self.cmb_cam_sink.currentText().strip()
            if sink and self.capabilities.get("has_v4l2_sink", False):
                cmd.append(f"--v4l2-sink={sink}")

        return cmd

    def _on_action_clicked(self):
        if self.proc_manager.is_running():
            self.proc_manager.stop()
            self.lbl_status.setText("● Stopping scrcpy...")
            self.lbl_status.setStyleSheet("color: #eab308; font-weight: bold;")
        else:
            cmd = self._build_command_for_active_tab()
            success = self.proc_manager.start(cmd)
            if success:
                self.btn_action.setText("⏹ Stop Scrcpy")
                self.btn_action.setObjectName("btn_stop")
                self.btn_action.setStyle(self.btn_action.style())
                self.lbl_status.setText("● Scrcpy Running")
                self.lbl_status.setStyleSheet("color: #10b981; font-weight: bold;")
            else:
                QtWidgets.QMessageBox.critical(self, "Launch Error", "Could not start scrcpy. Check the live logs for details.")

    @Slot(str)
    def _append_log(self, line: str):
        self.txt_logs.appendPlainText(line.rstrip())
        sb = self.txt_logs.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(int)
    def _on_process_exited(self, return_code: int):
        self.btn_action.setText("▶ Launch Scrcpy")
        self.btn_action.setObjectName("btn_primary")
        self.btn_action.setStyle(self.btn_action.style())
        if return_code == 0:
            self.lbl_status.setText("● Process Completed (0)")
            self.lbl_status.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self.lbl_status.setText(f"● Process Exited ({return_code})")
            self.lbl_status.setStyleSheet("color: #ef4444; font-weight: bold;")

    def _copy_logs(self):
        QtWidgets.QApplication.clipboard().setText(self.txt_logs.toPlainText())

    def _clear_logs(self):
        self.txt_logs.clear()
        self.proc_manager.clear_logs()

    def _toggle_log_panel(self):
        self.log_widget.setVisible(not self.log_widget.isVisible())

    # ─────────────────────────────────────────────────────────────
    # DEVICE MANAGEMENT, WI-FI MANAGER & CONFIG PERSISTENCE
    # ─────────────────────────────────────────────────────────────
    def _refresh_devices(self):
        self.cmb_devices.clear()
        devices = get_connected_devices()
        if not devices:
            self.cmb_devices.addItem("No devices connected", "")
            return

        for d in devices:
            self.cmb_devices.addItem(d.get("display_name", d["serial"]), d["serial"])

        saved = self.config.get("selected_device", "")
        if saved:
            idx = self.cmb_devices.findData(saved)
            if idx >= 0:
                self.cmb_devices.setCurrentIndex(idx)

        self._check_desktop_mode_status()

    def _get_selected_serial(self) -> Optional[str]:
        data = self.cmb_devices.currentData()
        return data if data else None

    def _restart_adb_daemon(self):
        self.lbl_status.setText("● Restarting ADB server...")
        succ, msg = restart_adb_server()
        if succ:
            QtWidgets.QMessageBox.information(self, "ADB Restart", "ADB server successfully restarted.")
            self._refresh_devices()
        else:
            QtWidgets.QMessageBox.critical(self, "ADB Error", msg)
        self.lbl_status.setText("● Ready")

    def _dialog_wifi_manager(self):
        """Unified Wi-Fi connection and Android 11+ pairing manager dialog."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("ADB Wireless Manager")
        dlg.resize(460, 280)
        d_layout = QtWidgets.QVBoxLayout(dlg)

        tabs = QtWidgets.QTabWidget()

        # Tab 1: Connect
        w_connect = QtWidgets.QWidget()
        c_layout = QtWidgets.QFormLayout(w_connect)
        txt_conn_ip = QtWidgets.QLineEdit()
        txt_conn_ip.setPlaceholderText("e.g. 192.0.2.1:5555")
        c_layout.addRow("Device IP:Port:", txt_conn_ip)
        btn_do_connect = QtWidgets.QPushButton("Connect")
        c_layout.addRow("", btn_do_connect)
        tabs.addTab(w_connect, "Connect (Standard)")

        # Tab 2: Pair (Android 11+)
        w_pair = QtWidgets.QWidget()
        p_layout = QtWidgets.QFormLayout(w_pair)
        txt_pair_ip = QtWidgets.QLineEdit()
        txt_pair_ip.setPlaceholderText("e.g. 192.0.2.1:37123 (from Pairing screen)")
        p_layout.addRow("Pairing IP:Port:", txt_pair_ip)
        txt_pair_code = QtWidgets.QLineEdit()
        txt_pair_code.setPlaceholderText("e.g. 123456 (6-digit code)")
        p_layout.addRow("Pairing Code:", txt_pair_code)
        btn_do_pair = QtWidgets.QPushButton("Pair & Auto-Connect")
        p_layout.addRow("", btn_do_pair)
        tabs.addTab(w_pair, "Pair New Device (Android 11+)")

        d_layout.addWidget(tabs)

        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)
        d_layout.addWidget(btn_close)

        def _handle_connect():
            addr = txt_conn_ip.text().strip()
            succ, msg = connect_wireless(addr)
            if succ:
                QtWidgets.QMessageBox.information(dlg, "Connected", msg)
                self._refresh_devices()
                dlg.accept()
            else:
                QtWidgets.QMessageBox.critical(dlg, "Connection Failed", msg)

        def _handle_pair():
            addr = txt_pair_ip.text().strip()
            code = txt_pair_code.text().strip()
            succ, msg = pair_wireless(addr, code)
            if succ:
                QtWidgets.QMessageBox.information(dlg, "Pairing Successful", f"{msg}\nNow connecting...")
                self._refresh_devices()
                dlg.accept()
            else:
                QtWidgets.QMessageBox.critical(dlg, "Pairing Failed", msg)

        btn_do_connect.clicked.connect(_handle_connect)
        btn_do_pair.clicked.connect(_handle_pair)

        dlg.exec()

    def _load_saved_preferences(self):
        c = self.config
        # Mirror
        self.cmb_mirror_fps.setCurrentText(c.get("mirror_fps", "120"))
        self.cmb_mirror_bitrate.setCurrentText(c.get("mirror_bitrate", "8M"))
        self.chk_mirror_stay_awake.setChecked(c.get("mirror_stay_awake", True))
        self.chk_mirror_audio.setChecked(c.get("mirror_audio", True))
        self.chk_mirror_turn_off.setChecked(c.get("mirror_turn_screen_off", False))
        self.chk_mirror_fullscreen.setChecked(c.get("mirror_fullscreen", False))
        self.chk_mirror_hid_kb.setChecked(c.get("mirror_hid_keyboard", False))
        self.chk_mirror_hid_mouse.setChecked(c.get("mirror_hid_mouse", False))
        self.chk_mirror_otg.setChecked(c.get("mirror_otg", False))
        self.chk_mirror_record.setChecked(c.get("mirror_record", False))

        # Virtual Display
        self.cmb_vd_res.setCurrentText(c.get("vd_resolution", "1920x1080"))
        self.chk_vd_flex.setChecked(c.get("vd_flex", True))
        self.chk_vd_keep_active.setChecked(c.get("vd_keep_active", True))
        self.chk_vd_audio.setChecked(c.get("vd_audio", True))
        self.chk_vd_destroy.setChecked(c.get("vd_destroy_content", False))
        self.chk_vd_hid_kb.setChecked(c.get("vd_hid_keyboard", False))
        self.chk_vd_record.setChecked(c.get("vd_record", False))
        self.cmb_vd_bitrate.setCurrentText(c.get("vd_bitrate", "16M"))
        self.txt_vd_app.setText(c.get("vd_app", ""))

        # Camera
        self.cmb_cam_res.setCurrentText(c.get("camera_size", "1920x1080"))
        self.cmb_cam_fps.setCurrentText(c.get("camera_fps", "30"))
        self.cmb_cam_bitrate.setCurrentText(c.get("camera_bitrate", "8M"))
        self.chk_cam_antilag.setChecked(c.get("camera_anti_lag", True))
        self.cmb_cam_facing.setCurrentText(c.get("camera_facing", "back"))

        # Last tab
        last_tab = c.get("last_tab", 0)
        if 0 <= last_tab < self.tabs.count():
            self.tabs.setCurrentIndex(last_tab)

    def closeEvent(self, event):
        """Save settings automatically on close."""
        c = self.config
        c["selected_device"] = self._get_selected_serial() or ""
        c["last_tab"] = self.tabs.currentIndex()

        c["mirror_fps"] = self.cmb_mirror_fps.currentText().split()[0]
        c["mirror_bitrate"] = self.cmb_mirror_bitrate.currentText()
        c["mirror_stay_awake"] = self.chk_mirror_stay_awake.isChecked()
        c["mirror_audio"] = self.chk_mirror_audio.isChecked()
        c["mirror_turn_screen_off"] = self.chk_mirror_turn_off.isChecked()
        c["mirror_fullscreen"] = self.chk_mirror_fullscreen.isChecked()
        c["mirror_hid_keyboard"] = self.chk_mirror_hid_kb.isChecked()
        c["mirror_hid_mouse"] = self.chk_mirror_hid_mouse.isChecked()
        c["mirror_otg"] = self.chk_mirror_otg.isChecked()
        c["mirror_record"] = self.chk_mirror_record.isChecked()

        c["vd_resolution"] = self.cmb_vd_res.currentText()
        c["vd_flex"] = self.chk_vd_flex.isChecked()
        c["vd_keep_active"] = self.chk_vd_keep_active.isChecked()
        c["vd_audio"] = self.chk_vd_audio.isChecked()
        c["vd_destroy_content"] = self.chk_vd_destroy.isChecked()
        c["vd_hid_keyboard"] = self.chk_vd_hid_kb.isChecked()
        c["vd_record"] = self.chk_vd_record.isChecked()
        c["vd_bitrate"] = self.cmb_vd_bitrate.currentText()
        c["vd_app"] = self.txt_vd_app.text().strip()

        c["camera_size"] = self.cmb_cam_res.currentText()
        c["camera_fps"] = self.cmb_cam_fps.currentText()
        c["camera_bitrate"] = self.cmb_cam_bitrate.currentText()
        c["camera_anti_lag"] = self.chk_cam_antilag.isChecked()
        c["camera_facing"] = self.cmb_cam_facing.currentText()

        save_config(c)
        if self.proc_manager.is_running():
            self.proc_manager.stop()
        event.accept()


def run_qt_app() -> int:
    """Launch Qt Application."""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Scrcpy Control Center")
    app.setOrganizationName("scrcpy-menu")
    window = ScrcpyMainWindow()
    window.show()
    return app.exec()
