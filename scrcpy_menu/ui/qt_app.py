import os
import sys
import time
import shlex
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
    query_installed_packages,
    get_top_apps_by_display,
    force_stop_app,
    get_virtual_display_id,
    send_display_key,
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
from .. import __version__

DARK_STYLESHEET = """
QMainWindow, QDialog, QWidget#central_widget {
    background-color: #121418;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}
QWidget#tab_mirror, QWidget#tab_vd, QWidget#tab_camera, QWidget#tab_shortcuts {
    background-color: #171a21;
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
    background-color: #1a1e27;
    border: 1px solid #2a3244;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
    color: #38bdf8;
}
QGroupBox::title {
    background-color: #1a1e27;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
}
QLabel {
    background-color: transparent;
    color: #e2e8f0;
}
QCheckBox {
    background-color: transparent;
    spacing: 8px;
    color: #cbd5e1;
}
QCheckBox:hover {
    color: #ffffff;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #38455e;
    background-color: #121418;
}
QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
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
    background-color: #121418;
    border: 1px solid #2e3648;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
    selection-background-color: #0284c7;
    min-height: 20px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #38bdf8;
}
QComboBox {
    combobox-popup: 0;
    padding-right: 24px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #2e3648;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8;
    margin-right: 2px;
}
QComboBox QAbstractItemView {
    background-color: #171a21;
    border: 1px solid #334155;
    border-radius: 6px;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    color: #f8fafc;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 4px 8px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #242c3d;
    color: #38bdf8;
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
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #121418;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #0284c7;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #121418;
    height: 8px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #0284c7;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""


class ScrcpyMainWindow(QtWidgets.QMainWindow):
    """Main application window with drag-and-drop, wireless pairing, and advanced scrcpy controls."""

    log_signal = Signal(str)
    process_exit_signal = Signal(int)
    cam_process_exit_signal = Signal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scrcpy Control Center")
        self.resize(880, 680)
        self.setMinimumSize(640, 480)
        self.setAcceptDrops(True)

        self.config = load_config()
        self.proc_manager = ScrcpyProcessManager()
        self.cam_proc_manager = ScrcpyProcessManager()
        self.platform_adapter = get_platform_adapter()
        self.capabilities = get_scrcpy_version_info()

        # Connect log and exit signals to safely update GUI on main thread
        self.log_signal.connect(self._append_log)
        self.process_exit_signal.connect(self._on_process_exited)
        self.cam_process_exit_signal.connect(self._on_cam_process_exited)
        self.proc_manager.register_log_callback(lambda line: self.log_signal.emit(line))
        self.proc_manager.register_exit_callback(lambda rc: self.process_exit_signal.emit(rc))
        self.cam_proc_manager.register_log_callback(lambda line: self.log_signal.emit(f"[camera] {line}"))
        self.cam_proc_manager.register_exit_callback(lambda rc: self.cam_process_exit_signal.emit(rc))

        self._setup_ui()
        self._load_saved_preferences()
        self._refresh_devices()

    def _create_tab_scroll_container(self, widget: QtWidgets.QWidget) -> QtWidgets.QScrollArea:
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        scroll.setWidget(widget)
        return scroll

    def _setup_ui(self):
        self.setStyleSheet(DARK_STYLESHEET)
        central = QtWidgets.QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Header Bar ──
        header_layout = QtWidgets.QHBoxLayout()

        # Title & Distinct Version Badges (App Version vs Scrcpy Core)
        title_box = QtWidgets.QHBoxLayout()
        title_box.setSpacing(8)
        lbl_app = QtWidgets.QLabel("Scrcpy Control Center")
        lbl_app.setStyleSheet("font-size: 17px; font-weight: 800; color: #38bdf8;")
        title_box.addWidget(lbl_app)

        lbl_app_ver = QtWidgets.QLabel(f"v{__version__}")
        lbl_app_ver.setToolTip(f"Scrcpy Control Center Application Version {__version__}")
        lbl_app_ver.setStyleSheet("background-color: #0284c7; color: #ffffff; border-radius: 4px; padding: 2px 7px; font-weight: bold; font-size: 11px;")
        title_box.addWidget(lbl_app_ver)

        v_core = self.capabilities.get("version_str", "Unknown")
        lbl_core_badge = QtWidgets.QLabel(f"scrcpy core: v{v_core}")
        lbl_core_badge.setToolTip("Detected system scrcpy binary version")
        lbl_core_badge.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 4px; padding: 2px 6px; font-size: 11px;")
        title_box.addWidget(lbl_core_badge)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Device selection combo
        lbl_dev = QtWidgets.QLabel("Device:")
        lbl_dev.setStyleSheet("font-weight: 600; color: #94a3b8;")
        header_layout.addWidget(lbl_dev)

        self.cmb_devices = QtWidgets.QComboBox()
        self.cmb_devices.setMinimumWidth(220)
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

        # ── Tab Widget with Scrollable Containers ──
        self.tabs = QtWidgets.QTabWidget()
        self.tab_mirror = QtWidgets.QWidget()
        self.tab_mirror.setObjectName("tab_mirror")
        self.tab_vd = QtWidgets.QWidget()
        self.tab_vd.setObjectName("tab_vd")
        self.tab_camera = QtWidgets.QWidget()
        self.tab_camera.setObjectName("tab_camera")
        self.tab_shortcuts = QtWidgets.QWidget()
        self.tab_shortcuts.setObjectName("tab_shortcuts")

        self._setup_tab_mirror()
        self._setup_tab_vd()
        self._setup_tab_camera()
        self._setup_tab_shortcuts()

        self.tabs.addTab(self._create_tab_scroll_container(self.tab_mirror), "📱 Screen Mirroring")
        self.tabs.addTab(self._create_tab_scroll_container(self.tab_vd), "🖥️ Virtual Display")
        self.tabs.addTab(self._create_tab_scroll_container(self.tab_camera), "📷 Camera / Webcam")
        self.tabs.addTab(self.tab_shortcuts, "⌨️ Shortcuts & Logs")

        main_layout.addWidget(self.tabs, stretch=1)

        # ── Bottom Control Panel ──
        bottom_box = QtWidgets.QHBoxLayout()
        self.lbl_status = QtWidgets.QLabel("● Ready")
        self.lbl_status.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
        bottom_box.addWidget(self.lbl_status)

        bottom_box.addStretch()

        self.btn_toggle_log = QtWidgets.QPushButton("📋 Show Logs")
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

        self.log_widget.setVisible(False)
        main_layout.addWidget(self.log_widget)

        # Ensure all combobox popups have a bounded height and smooth scrolling
        for cmb in self.findChildren(QtWidgets.QComboBox):
            cmb.setMaxVisibleItems(8)

    # ─────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────
    # TAB 1: SCREEN MIRRORING
    # ─────────────────────────────────────────────────────────────
    def _setup_tab_mirror(self):
        layout = QtWidgets.QVBoxLayout(self.tab_mirror)
        layout.setSpacing(10)

        # Presets Group
        grp_presets = QtWidgets.QGroupBox("Quick Presets")
        presets_layout = QtWidgets.QHBoxLayout(grp_presets)
        btn_120 = QtWidgets.QPushButton("🚀 120 FPS Native")
        btn_120.clicked.connect(lambda: self._apply_mirror_preset(120, "Native (No Downscale)", "8M", True, True))
        btn_60 = QtWidgets.QPushButton("📺 60 FPS Standard")
        btn_60.clicked.connect(lambda: self._apply_mirror_preset(60, "Native (No Downscale)", "8M", True, True))
        btn_lowlat = QtWidgets.QPushButton("⚡ Ultra Low-Lag")
        btn_lowlat.clicked.connect(lambda: self._apply_mirror_preset(60, "1280 (Downscale to 720p)", "4M", True, False))
        btn_1080 = QtWidgets.QPushButton("📽️ 1080p Capped")
        btn_1080.clicked.connect(lambda: self._apply_mirror_preset(60, "1920 (Downscale to 1080p)", "8M", True, True))

        presets_layout.addWidget(btn_120)
        presets_layout.addWidget(btn_60)
        presets_layout.addWidget(btn_lowlat)
        presets_layout.addWidget(btn_1080)
        layout.addWidget(grp_presets)

        # Stream & Display Options
        grp_opts = QtWidgets.QGroupBox("Display & Stream Options")
        form = QtWidgets.QFormLayout(grp_opts)
        form.setSpacing(6)

        self.cmb_mirror_fps = QtWidgets.QComboBox()
        self.cmb_mirror_fps.addItems(["120", "90", "60", "30", "0 (Unlimited)"])
        form.addRow("Max FPS:", self.cmb_mirror_fps)

        self.cmb_mirror_res = QtWidgets.QComboBox()
        self.cmb_mirror_res.setEditable(True)
        self.cmb_mirror_res.lineEdit().setPlaceholderText("Native or max size (e.g. 1920, 1280, 2400)")
        self.cmb_mirror_res.addItems([
            "Native (No Downscale)",
            "1920 (Downscale to 1080p)",
            "1600",
            "1440",
            "1280 (Downscale to 720p)",
            "1024",
            "800",
        ])
        form.addRow("Resolution / Max Size:", self.cmb_mirror_res)

        self.cmb_mirror_codec = QtWidgets.QComboBox()
        self.cmb_mirror_codec.addItems(["Default (H.264)", "H.265 / HEVC (--video-codec=h265)", "AV1 (--video-codec=av1)"])
        form.addRow("Video Codec:", self.cmb_mirror_codec)

        self.cmb_mirror_bitrate = QtWidgets.QComboBox()
        self.cmb_mirror_bitrate.setEditable(True)
        self.cmb_mirror_bitrate.addItems(["16M", "12M", "8M", "4M", "2M"])
        form.addRow("Video Bitrate:", self.cmb_mirror_bitrate)

        self.cmb_mirror_orientation = QtWidgets.QComboBox()
        self.cmb_mirror_orientation.addItems([
            "Unlocked (Auto / Follow Phone)",
            "0° Natural / Upright",
            "90° Counter-Clockwise (1)",
            "180° Inverted (2)",
            "90° Clockwise (3)",
        ])
        form.addRow("Orientation Lock:", self.cmb_mirror_orientation)

        self.chk_mirror_stay_awake = QtWidgets.QCheckBox("Stay Awake (--stay-awake) [prevent phone screen timeout]")
        form.addRow("", self.chk_mirror_stay_awake)

        self.chk_mirror_audio = QtWidgets.QCheckBox("Audio Forwarding (--audio-source=output) [stream device sound to PC]")
        form.addRow("", self.chk_mirror_audio)

        self.chk_mirror_turn_off = QtWidgets.QCheckBox("Turn device physical screen OFF (--turn-screen-off) [saves battery & thermals]")
        form.addRow("", self.chk_mirror_turn_off)

        self.chk_mirror_fullscreen = QtWidgets.QCheckBox("Start scrcpy in fullscreen mode (-f)")
        form.addRow("", self.chk_mirror_fullscreen)

        # Virtual Webcam Sink Output
        webcam_box = QtWidgets.QHBoxLayout()
        self.chk_mirror_v4l2 = QtWidgets.QCheckBox("Output screen mirror to Virtual Webcam")
        webcam_box.addWidget(self.chk_mirror_v4l2)
        self.cmb_mirror_sink = QtWidgets.QComboBox()
        self.cmb_mirror_sink.setEditable(True)
        sinks = self.platform_adapter.get_camera_sinks()
        self.cmb_mirror_sink.addItems(sinks if sinks else ["/dev/video2", "/dev/video0"])
        webcam_box.addWidget(self.cmb_mirror_sink)
        form.addRow("Virtual Webcam (V4L2):", webcam_box)

        layout.addWidget(grp_opts)

        # Input & Recording Options
        grp_advanced = QtWidgets.QGroupBox("Hardware Input (HID) & Recording")
        adv_form = QtWidgets.QFormLayout(grp_advanced)
        adv_form.setSpacing(6)

        self.chk_mirror_hid_kb = QtWidgets.QCheckBox("Hardware Keyboard Simulation (--keyboard=uhid) [bypasses on-screen keyboard]")
        adv_form.addRow("", self.chk_mirror_hid_kb)

        self.chk_mirror_prefer_text = QtWidgets.QCheckBox("Prefer Text Events (--prefer-text) [fixes typing lag, dropped keys, and special symbols]")
        adv_form.addRow("", self.chk_mirror_prefer_text)

        self.chk_mirror_hid_mouse = QtWidgets.QCheckBox("Hardware Mouse Capture (--mouse=uhid) [high-precision cursor lock]")
        adv_form.addRow("", self.chk_mirror_hid_mouse)

        self.chk_mirror_otg = QtWidgets.QCheckBox("OTG Mode (--otg) [use PC keyboard/mouse directly without screen mirroring]")
        adv_form.addRow("", self.chk_mirror_otg)

        self.chk_mirror_record = QtWidgets.QCheckBox("Record Session to MP4 video in ~/Videos (--record)")
        adv_form.addRow("", self.chk_mirror_record)

        self.txt_mirror_extra = QtWidgets.QLineEdit()
        self.txt_mirror_extra.setPlaceholderText("e.g. --window-title=\"Phone\" --crop=1200:1000:0:0 --display-buffer=50")
        adv_form.addRow("Extra Scrcpy Flags:", self.txt_mirror_extra)

        layout.addWidget(grp_advanced)
        layout.addStretch()

    def _apply_mirror_preset(self, fps: int, res: str, bitrate: str, awake: bool, audio: bool):
        self.cmb_mirror_fps.setCurrentText(str(fps) if fps != 0 else "0 (Unlimited)")
        self.cmb_mirror_res.setCurrentText(res)
        self.cmb_mirror_bitrate.setCurrentText(bitrate)
        self.chk_mirror_stay_awake.setChecked(awake)
        self.chk_mirror_audio.setChecked(audio)

    # ─────────────────────────────────────────────────────────────
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
        btn_blank.clicked.connect(lambda: self._apply_vd_preset("1920x1080 (FHD)", "180", True, "", force_desktop=True))
        btn_chrome = QtWidgets.QPushButton("🌐 Chrome Browser")
        btn_chrome.clicked.connect(lambda: self._apply_vd_preset("1920x1080 (FHD)", "180", True, "com.android.chrome", force_desktop=True))
        btn_desktop = QtWidgets.QPushButton("💻 Full Desktop Mode")
        btn_desktop.clicked.connect(lambda: self._apply_vd_preset("1920x1080 (FHD)", "180", True, "", force_desktop=True))
        btn_phone_ui = QtWidgets.QPushButton("📱 Phone UI Display")
        btn_phone_ui.clicked.connect(lambda: self._apply_vd_preset("2400x1080 (Phone Ratio)", "420", True, "", force_desktop=False))

        presets_layout.addWidget(btn_blank)
        presets_layout.addWidget(btn_chrome)
        presets_layout.addWidget(btn_desktop)
        presets_layout.addWidget(btn_phone_ui)
        layout.addWidget(grp_presets)

        # Display Configuration
        grp_cfg = QtWidgets.QGroupBox("Display & Resolution Settings")
        form = QtWidgets.QFormLayout(grp_cfg)
        form.setSpacing(6)

        # Force Desktop Mode on Virtual Display vs Phone UI Toggle
        self.chk_vd_force_desktop = QtWidgets.QCheckBox(
            "Force Desktop Mode on Virtual Display (uncheck to use as phone's standard display/launcher)"
        )
        self.chk_vd_force_desktop.setChecked(True)
        self.chk_vd_force_desktop.setToolTip(
            "When checked, enables Android freeform windows and desktop mode before launching.\n"
            "When unchecked, Android treats the virtual display as a normal phone display with your standard launcher/apps."
        )
        form.addRow("", self.chk_vd_force_desktop)

        # Resolution (Custom / Presets)
        self.cmb_vd_res = QtWidgets.QComboBox()
        self.cmb_vd_res.setEditable(True)
        self.cmb_vd_res.lineEdit().setPlaceholderText("e.g. 1920x1080, 2400x1080, or custom WxH")
        self.cmb_vd_res.addItems([
            "1920x1080 (FHD)",
            "2560x1440 (QHD)",
            "2400x1080 (Phone Ratio)",
            "2560x1080 (Ultrawide 21:9)",
            "1280x720 (HD)",
            "1024x768 (Tablet 4:3)",
            "3840x2160 (4K)",
            "Native",
        ])
        form.addRow("Resolution:", self.cmb_vd_res)

        # DPI / Scale (Custom / Presets)
        self.cmb_vd_dpi = QtWidgets.QComboBox()
        self.cmb_vd_dpi.setEditable(True)
        self.cmb_vd_dpi.lineEdit().setPlaceholderText("e.g. 180, 240, 320, 420")
        self.cmb_vd_dpi.addItems([
            "180 (Desktop Scale / Max Space)",
            "240 (Tablet Scale)",
            "320 (Compact)",
            "420 (Phone Scale)",
            "Default",
        ])
        form.addRow("DPI / Scale:", self.cmb_vd_dpi)

        self.cmb_vd_codec = QtWidgets.QComboBox()
        self.cmb_vd_codec.addItems(["Default (H.264)", "H.265 / HEVC (--video-codec=h265)", "AV1 (--video-codec=av1)"])
        form.addRow("Video Codec:", self.cmb_vd_codec)

        self.cmb_vd_bitrate = QtWidgets.QComboBox()
        self.cmb_vd_bitrate.setEditable(True)
        self.cmb_vd_bitrate.addItems(["16M", "12M", "8M", "4M", "2M"])
        form.addRow("Bitrate:", self.cmb_vd_bitrate)

        self.cmb_vd_fps = QtWidgets.QComboBox()
        self.cmb_vd_fps.addItems(["60", "90", "120", "30", "0 (Unlimited)"])
        form.addRow("Max FPS:", self.cmb_vd_fps)

        # App Launcher with Scanner
        app_box = QtWidgets.QHBoxLayout()
        self.cmb_vd_app_preset = QtWidgets.QComboBox()
        self.cmb_vd_app_preset.addItems([
            "(None — Blank Virtual Display)",
            "⚙️ Settings (com.android.settings)",
            "🌐 Chrome (com.android.chrome)",
            "▶️ YouTube (com.google.android.youtube)",
            "💬 Messages (com.google.android.apps.messaging)",
            "📸 Photos (com.google.android.apps.photos)",
            "✨ Gemini (com.google.android.apps.bard)",
        ])
        self.cmb_vd_app_preset.currentIndexChanged.connect(self._on_vd_app_preset_changed)
        app_box.addWidget(self.cmb_vd_app_preset, stretch=1)

        btn_scan_apps = QtWidgets.QPushButton("🔄 Scan Device Apps")
        btn_scan_apps.setToolTip("Scan connected phone for third-party installed packages")
        btn_scan_apps.clicked.connect(self._scan_installed_apps)
        app_box.addWidget(btn_scan_apps)
        form.addRow("Launch Preset App:", app_box)

        self.txt_vd_app = QtWidgets.QLineEdit()
        self.txt_vd_app.setPlaceholderText("Package name (e.g. com.android.chrome) or leave blank")
        app_ctrl_row = QtWidgets.QHBoxLayout()
        app_ctrl_row.addWidget(self.txt_vd_app, stretch=1)

        btn_switch_app = QtWidgets.QPushButton("🔀 App Switcher")
        btn_switch_app.setToolTip("Trigger App Switcher / Overview (Alt+Tab) directly on the virtual display")
        btn_switch_app.clicked.connect(self._on_switch_app_clicked)
        app_ctrl_row.addWidget(btn_switch_app)

        btn_back_app = QtWidgets.QPushButton("⬅️ Back")
        btn_back_app.setToolTip("Send Back key to the active virtual display")
        btn_back_app.clicked.connect(self._on_vd_back_clicked)
        app_ctrl_row.addWidget(btn_back_app)

        btn_kill_app = QtWidgets.QPushButton("🛑 Force-Stop App")
        btn_kill_app.setToolTip("Instantly terminate the top app running on the virtual display (without touching your physical phone screen)")
        btn_kill_app.clicked.connect(self._on_kill_active_app_clicked)
        app_ctrl_row.addWidget(btn_kill_app)
        form.addRow("Package Name:", app_ctrl_row)

        self.chk_vd_force_stop = QtWidgets.QCheckBox("Force-stop app before starting (+prefix) [moves app from phone to virtual display]")
        form.addRow("", self.chk_vd_force_stop)

        layout.addWidget(grp_cfg)

        # Virtual Display Behavior & Window Features
        grp_features = QtWidgets.QGroupBox("Virtual Display Behavior & Features")
        feat_form = QtWidgets.QFormLayout(grp_features)
        feat_form.setSpacing(6)

        self.chk_vd_flex = QtWidgets.QCheckBox("Flex Display (-x) [window resize dynamically resizes virtual display resolution]")
        feat_form.addRow("", self.chk_vd_flex)

        self.chk_vd_keep_active = QtWidgets.QCheckBox("Keep Active (--keep-active) [prevents virtual display sleeping when backgrounded]")
        feat_form.addRow("", self.chk_vd_keep_active)

        self.chk_vd_destroy = QtWidgets.QCheckBox("Destroy Content on Close (uncheck to preserve running apps back to phone)")
        feat_form.addRow("", self.chk_vd_destroy)

        self.chk_vd_no_decor = QtWidgets.QCheckBox("Clean Display — No Status/Nav Bars (--no-vd-system-decorations) [Requires App]")
        self.chk_vd_no_decor.setToolTip(
            "Disables Android status bar and navigation bar for a true borderless app screen.\n\n"
            "CRITICAL: Requires an application in 'Launch Preset App' or 'Package Name'.\n"
            "Without an app, Android cannot launch its secondary desktop launcher, leaving an empty surface that freezes waiting for content."
        )
        self.chk_vd_no_decor.toggled.connect(self._on_no_decor_toggled)
        feat_form.addRow("", self.chk_vd_no_decor)

        self.chk_vd_stay_awake = QtWidgets.QCheckBox("Keep Device Awake (--stay-awake) [prevents phone sleep/freeze]")
        feat_form.addRow("", self.chk_vd_stay_awake)

        self.chk_vd_screen_off = QtWidgets.QCheckBox("Turn physical phone screen OFF (--turn-screen-off)")
        feat_form.addRow("", self.chk_vd_screen_off)

        self.chk_vd_audio = QtWidgets.QCheckBox("PC Sound (--audio-source=output) [play virtual display sound through computer]")
        feat_form.addRow("", self.chk_vd_audio)

        self.chk_vd_hid_kb = QtWidgets.QCheckBox("Hardware Keyboard Simulation (--keyboard=uhid) [bypasses on-screen keyboard]")
        feat_form.addRow("", self.chk_vd_hid_kb)

        self.chk_vd_prefer_text = QtWidgets.QCheckBox("Prefer Text Events (--prefer-text) [fixes typing lag, dropped keys & symbols]")
        feat_form.addRow("", self.chk_vd_prefer_text)

        self.chk_vd_hid_mouse = QtWidgets.QCheckBox("Hardware Mouse Capture (--mouse=uhid) [recommended for virtual display]")
        self.chk_vd_hid_mouse.setChecked(True)
        self.chk_vd_hid_mouse.setToolTip(
            "Captures the mouse pointer directly as a hardware USB HID device on the virtual display.\n"
            "Eliminates 'Could not request inject mouse motion event' warnings on Android 14+ / 16."
        )
        feat_form.addRow("", self.chk_vd_hid_mouse)

        self.cmb_vd_ime = QtWidgets.QComboBox()
        self.cmb_vd_ime.addItems([
            "Default (Auto)",
            "Hide On-Screen Keyboard (--display-ime-policy=hide)",
            "Local Virtual Display (--display-ime-policy=local)",
        ])
        feat_form.addRow("On-Screen Keyboard:", self.cmb_vd_ime)

        btn_kb_setup = QtWidgets.QPushButton("⌨️ Configure Device Keyboard Layout")
        btn_kb_setup.setToolTip("Opens Android's Physical Keyboard Settings screen on phone to select keyboard layout (US, UK, etc.)")
        btn_kb_setup.clicked.connect(self._open_device_keyboard_settings)
        feat_form.addRow("Physical Keyboard Setup:", btn_kb_setup)

        lbl_kb_hint = QtWidgets.QLabel(
            "💡 Keyboard capture: Click inside the scrcpy display window to focus/capture input (or press MOD+i). "
            "If keys don't type initially, click 'Configure Device Keyboard Layout' to select a physical layout, or enable 'Prefer Text Events'."
        )
        lbl_kb_hint.setWordWrap(True)
        lbl_kb_hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        feat_form.addRow("", lbl_kb_hint)

        self.chk_vd_record = QtWidgets.QCheckBox("Record Virtual Display session to MP4 (--record)")
        feat_form.addRow("", self.chk_vd_record)

        self.txt_vd_extra = QtWidgets.QLineEdit()
        self.txt_vd_extra.setPlaceholderText("e.g. --window-title=\"Virtual Desktop\" --display-buffer=0")
        feat_form.addRow("Extra Scrcpy Flags:", self.txt_vd_extra)

        layout.addWidget(grp_features)

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

    def _on_vd_app_preset_changed(self, idx: int):
        txt = self.cmb_vd_app_preset.currentText()
        if txt.lower().startswith("(none") or txt.lower() in ("none", ""):
            self.txt_vd_app.setText("")
        elif "(" in txt and ")" in txt:
            pkg = txt.split("(")[-1].split(")")[0].strip()
            if not pkg.lower().startswith("none"):
                self.txt_vd_app.setText(pkg)
            else:
                self.txt_vd_app.setText("")
        else:
            self.txt_vd_app.setText(txt)

    def _on_no_decor_toggled(self, checked: bool):
        if checked:
            app = self.txt_vd_app.text().strip()
            if not app or app.lower() in ("none", "(none)", "none - blank virtual display") or app.lower().startswith("(none"):
                self.lbl_status.setText("● Notice: Clean Display requires a launched app; otherwise the screen freezes on blank")
                self.lbl_status.setStyleSheet("color: #eab308; font-weight: bold;")

    def _scan_installed_apps(self):
        target = self._get_selected_serial()
        self.lbl_status.setText("● Scanning device apps via ADB...")
        pkgs = query_installed_packages(target)
        if not pkgs:
            QtWidgets.QMessageBox.information(
                self, "App Scanner", "No third-party packages found or device not responding via ADB."
            )
            self.lbl_status.setText("● Ready")
            return

        self.cmb_vd_app_preset.clear()
        self.cmb_vd_app_preset.addItem("(None — Blank Virtual Display)")
        for p in pkgs:
            self.cmb_vd_app_preset.addItem(f"📦 {p} ({p})")
        QtWidgets.QMessageBox.information(
            self, "App Scanner", f"Discovered {len(pkgs)} launchable apps from device!"
        )
        self.lbl_status.setText("● Ready")

    def _on_kill_active_app_clicked(self):
        target_serial = self._get_selected_serial()
        self.lbl_status.setText("● Inspecting running app on virtual display...")
        apps_by_display = get_top_apps_by_display(target_serial)
        vd_apps = [pkg for d_id, pkg in apps_by_display.items() if d_id != 0]

        pkg_to_kill = ""
        if vd_apps:
            pkg_to_kill = vd_apps[0]
        else:
            raw_txt = self.txt_vd_app.text().strip()
            if raw_txt and raw_txt.lower() not in ("none", "(none)", "none - blank virtual display") and not raw_txt.lower().startswith("(none"):
                pkg_to_kill = raw_txt

        if not pkg_to_kill:
            QtWidgets.QMessageBox.information(
                self,
                "No Running App Detected",
                "Could not automatically detect an active app on the virtual display.\n\n"
                "Please enter the app package name in 'Package Name' to force-stop it."
            )
            self.lbl_status.setText("● Ready")
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Force-Stop Application",
            f"Are you sure you want to force-stop '{pkg_to_kill}' on the device?\n\n"
            "This will instantly terminate the process on the virtual display.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes,
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            success, msg = force_stop_app(pkg_to_kill, target_serial)
            if success:
                self.lbl_status.setText(f"● Terminated {pkg_to_kill}")
                self.lbl_status.setStyleSheet("color: #10b981; font-weight: bold;")
                QtWidgets.QMessageBox.information(self, "App Terminated", f"Successfully force-stopped '{pkg_to_kill}'.")
            else:
                self.lbl_status.setText(f"● Failed to terminate {pkg_to_kill}")
                self.lbl_status.setStyleSheet("color: #ef4444; font-weight: bold;")
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to stop app: {msg}")

    def _on_switch_app_clicked(self):
        target_serial = self._get_selected_serial()
        vd_id = get_virtual_display_id(target_serial)
        if vd_id is None:
            QtWidgets.QMessageBox.information(
                self,
                "Virtual Display Not Found",
                "Could not find an active virtual display on the device.\n\n"
                "Please make sure your virtual display session is running."
            )
            return

        succ = send_display_key(["keycombination", "KEYCODE_ALT_LEFT", "KEYCODE_TAB"], vd_id, target_serial)
        if succ:
            self.lbl_status.setText("● Triggered App Switcher on Virtual Display")
            self.lbl_status.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self.lbl_status.setText("● Failed to send App Switcher key")
            self.lbl_status.setStyleSheet("color: #ef4444; font-weight: bold;")

    def _on_vd_back_clicked(self):
        target_serial = self._get_selected_serial()
        vd_id = get_virtual_display_id(target_serial)
        if vd_id is None:
            QtWidgets.QMessageBox.information(
                self,
                "Virtual Display Not Found",
                "Could not find an active virtual display on the device."
            )
            return

        succ = send_display_key(["keyevent", "KEYCODE_BACK"], vd_id, target_serial)
        if succ:
            self.lbl_status.setText("● Sent Back to Virtual Display")
            self.lbl_status.setStyleSheet("color: #10b981; font-weight: bold;")

    def _apply_vd_preset(self, res: str, dpi: str, flex: bool, app: str, force_desktop: bool = True):
        self.cmb_vd_res.setCurrentText(res)
        self.cmb_vd_dpi.setCurrentText(dpi if dpi in ("180", "420") else "180 (Desktop Scale / Max Space)")
        self.chk_vd_flex.setChecked(flex)
        self.chk_vd_force_desktop.setChecked(force_desktop)
        self.txt_vd_app.setText("" if app.lower() in ("none", "(none)", "") else app)
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

    def _open_device_keyboard_settings(self):
        target = self._get_selected_serial()
        cmd = ["adb"]
        if target:
            cmd.extend(["-s", target])
        cmd.extend(["shell", "am", "start", "-a", "android.settings.HARD_KEYBOARD_SETTINGS"])
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
            if res.returncode == 0:
                self.lbl_status.setText("● Opened Keyboard Settings on phone")
            else:
                cmd_fallback = ["adb"]
                if target:
                    cmd_fallback.extend(["-s", target])
                cmd_fallback.extend(["shell", "am", "start", "-a", "android.settings.INPUT_METHOD_SETTINGS"])
                subprocess.run(cmd_fallback, timeout=5, check=False)
                self.lbl_status.setText("● Opened Input Settings on phone")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Keyboard Settings", f"Could not open device settings: {e}")

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
        self.cmb_cam_res.setEditable(True)
        self.cmb_cam_res.lineEdit().setPlaceholderText("e.g. 1920x1080, 1280x720, or custom WxH")
        self.cmb_cam_res.addItems([
            "1920x1080 (1080p)",
            "1280x720 (720p)",
            "2400x1080 (Ultrawide sensor crop)",
            "3840x2160 (4K)",
            "640x480",
        ])
        form.addRow("Resolution:", self.cmb_cam_res)

        self.cmb_cam_fps = QtWidgets.QComboBox()
        self.cmb_cam_fps.setEditable(True)
        self.cmb_cam_fps.addItems(["30", "60", "24", "15"])
        form.addRow("Frame Rate (FPS):", self.cmb_cam_fps)

        self.cmb_cam_bitrate = QtWidgets.QComboBox()
        self.cmb_cam_bitrate.setEditable(True)
        self.cmb_cam_bitrate.addItems(["8M", "12M", "16M", "4M", "2M"])
        form.addRow("Bitrate:", self.cmb_cam_bitrate)

        # Camera Facing + Hardware ID Discovery
        cam_id_box = QtWidgets.QHBoxLayout()
        self.cmb_cam_facing = QtWidgets.QComboBox()
        self.cmb_cam_facing.setEditable(True)
        self.cmb_cam_facing.addItems(["back", "front", "0", "1", "2", "3"])
        cam_id_box.addWidget(self.cmb_cam_facing, stretch=1)

        btn_detect_cams = QtWidgets.QPushButton("🔍 Detect Lenses")
        btn_detect_cams.setToolTip("Query connected device for physical camera IDs and lenses")
        btn_detect_cams.clicked.connect(self._detect_cameras)
        cam_id_box.addWidget(btn_detect_cams)
        form.addRow("Camera Sensor / ID:", cam_id_box)

        self.chk_cam_antilag = QtWidgets.QCheckBox("Anti-Lag / Zero Buffer (--v4l2-buffer=0, --no-audio) [Prevents frame backlog]")
        form.addRow("", self.chk_cam_antilag)

        # Virtual Webcam Device Node
        self.cmb_cam_sink = QtWidgets.QComboBox()
        self.cmb_cam_sink.setEditable(True)
        sinks = self.platform_adapter.get_camera_sinks()
        self.cmb_cam_sink.addItems(sinks if sinks else ["/dev/video2", "/dev/video0"])
        form.addRow("Virtual Webcam Sink:", self.cmb_cam_sink)

        self.txt_cam_extra = QtWidgets.QLineEdit()
        self.txt_cam_extra.setPlaceholderText("e.g. --camera-ar=16:9 --camera-high-speed")
        form.addRow("Extra Scrcpy Flags:", self.txt_cam_extra)

        layout.addWidget(grp_cfg)

        # Concurrent Webcam Stream Launcher
        grp_stream = QtWidgets.QGroupBox("Concurrent Stream Controls")
        stream_layout = QtWidgets.QVBoxLayout(grp_stream)
        stream_layout.setSpacing(6)

        lbl_concurrent_info = QtWidgets.QLabel(
            "💡 Pro-Tip: You can launch this webcam stream concurrently while Screen Mirroring or Virtual Display is active! "
            "Both video feeds encode and stream simultaneously via separate hardware pipelines."
        )
        lbl_concurrent_info.setWordWrap(True)
        lbl_concurrent_info.setStyleSheet("color: #38bdf8; font-size: 11px;")
        stream_layout.addWidget(lbl_concurrent_info)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_cam_action = QtWidgets.QPushButton("🎥 Launch Webcam (Concurrent)")
        self.btn_cam_action.setFixedHeight(34)
        self.btn_cam_action.clicked.connect(self._on_cam_action_clicked)
        btn_row.addWidget(self.btn_cam_action, stretch=1)

        self.lbl_cam_status = QtWidgets.QLabel("Status: Stopped")
        self.lbl_cam_status.setStyleSheet("color: #94a3b8; font-weight: bold; padding: 4px;")
        btn_row.addWidget(self.lbl_cam_status)
        stream_layout.addLayout(btn_row)

        layout.addWidget(grp_stream)
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

        # Header with MOD Selector & Filter
        top_box = QtWidgets.QHBoxLayout()

        lbl_mod = QtWidgets.QLabel("Shortcut MOD Key:")
        lbl_mod.setStyleSheet("font-weight: 600; color: #38bdf8;")
        top_box.addWidget(lbl_mod)

        self.cmb_shortcut_mod = QtWidgets.QComboBox()
        self.cmb_shortcut_mod.addItems([
            "Default (Left Alt)",
            "Left Super / Windows Key (lsuper)",
            "Right Alt / AltGr (ralt)",
            "Right Super (rsuper)",
            "Left Alt + Left Super (lalt,lsuper)",
        ])
        top_box.addWidget(self.cmb_shortcut_mod)

        top_box.addSpacing(16)

        lbl_search = QtWidgets.QLabel("Filter:")
        lbl_search.setStyleSheet("font-weight: 600; color: #94a3b8;")
        top_box.addWidget(lbl_search)

        self.txt_filter_sc = QtWidgets.QLineEdit()
        self.txt_filter_sc.setPlaceholderText("Search shortcut or action...")
        self.txt_filter_sc.textChanged.connect(self._filter_shortcuts)
        top_box.addWidget(self.txt_filter_sc, stretch=1)

        btn_diag = QtWidgets.QPushButton("🔍 Diagnostics Report")
        btn_diag.clicked.connect(self._show_diagnostics_dialog)
        top_box.addWidget(btn_diag)

        layout.addLayout(top_box)

        lbl_hint = QtWidgets.QLabel(
            "💡 'MOD' represents your shortcut modifier key (Left Alt by default, or your configured key above). "
            "Press these shortcuts while focusing the scrcpy display window."
        )
        lbl_hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(lbl_hint)

        # Table of Shortcuts (3 Columns: Category, Shortcut, Action)
        from ..cli import SHORTCUTS_LIST
        self.tbl_shortcuts = QtWidgets.QTableWidget(len(SHORTCUTS_LIST), 3)
        self.tbl_shortcuts.setHorizontalHeaderLabels(["Category", "Shortcut (MOD Key)", "Action"])
        self.tbl_shortcuts.horizontalHeader().setStretchLastSection(True)
        self.tbl_shortcuts.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_shortcuts.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_shortcuts.verticalHeader().setVisible(False)
        self.tbl_shortcuts.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        for row, entry in enumerate(SHORTCUTS_LIST):
            sc, desc, cat = entry[0], entry[1], entry[2]
            item_cat = QtWidgets.QTableWidgetItem(cat)
            item_sc = QtWidgets.QTableWidgetItem(sc)
            item_desc = QtWidgets.QTableWidgetItem(desc)

            item_cat.setForeground(QtGui.QBrush(QtGui.QColor("#94a3b8")))
            item_sc.setForeground(QtGui.QBrush(QtGui.QColor("#38bdf8")))
            item_sc.setFont(QtGui.QFont("Consolas", 10, QtGui.QFont.Weight.Bold))

            self.tbl_shortcuts.setItem(row, 0, item_cat)
            self.tbl_shortcuts.setItem(row, 1, item_sc)
            self.tbl_shortcuts.setItem(row, 2, item_desc)

        layout.addWidget(self.tbl_shortcuts)

    def _filter_shortcuts(self, query: str):
        query = query.lower().strip()
        for row in range(self.tbl_shortcuts.rowCount()):
            item_cat = self.tbl_shortcuts.item(row, 0)
            item_sc = self.tbl_shortcuts.item(row, 1)
            item_desc = self.tbl_shortcuts.item(row, 2)
            c_text = item_cat.text().lower() if item_cat else ""
            sc_text = item_sc.text().lower() if item_sc else ""
            desc_text = item_desc.text().lower() if item_desc else ""
            visible = (query in c_text or query in sc_text or query in desc_text)
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

        # Shortcut Modifier Key
        mod_choice = self.cmb_shortcut_mod.currentText()
        if "lsuper" in mod_choice:
            cmd.append("--shortcut-mod=lsuper")
        elif "ralt" in mod_choice:
            cmd.append("--shortcut-mod=ralt")
        elif "rsuper" in mod_choice:
            cmd.append("--shortcut-mod=rsuper")
        elif "lalt,lsuper" in mod_choice:
            cmd.append("--shortcut-mod=lalt,lsuper")

        if current_idx == 0:
            # ── Tab 0: Screen Mirroring ──
            if self.chk_mirror_otg.isChecked():
                cmd.append("--otg")
            else:
                fps = self.cmb_mirror_fps.currentText().split()[0]
                if fps.isdigit() and int(fps) > 0:
                    cmd.append(f"--max-fps={fps}")

                # Resolution / Max-size downscale
                m_res = self.cmb_mirror_res.currentText().strip()
                if m_res and not m_res.startswith("Native"):
                    size_val = m_res.split()[0]
                    if size_val.isdigit():
                        cmd.append(f"--max-size={size_val}")
                    elif "x" in size_val:
                        parts = size_val.split("x")
                        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                            cmd.append(f"--max-size={max(int(parts[0]), int(parts[1]))}")

                # Codec
                codec_txt = self.cmb_mirror_codec.currentText()
                if "h265" in codec_txt:
                    cmd.append("--video-codec=h265")
                elif "av1" in codec_txt:
                    cmd.append("--video-codec=av1")

                # Bitrate
                br = self.cmb_mirror_bitrate.currentText().strip()
                if br:
                    cmd.append(f"--video-bit-rate={br}")

                # Orientation Lock
                orient_txt = self.cmb_mirror_orientation.currentText()
                if "0°" in orient_txt:
                    cmd.append("--lock-video-orientation=0")
                elif "90° CCW" in orient_txt or "(1)" in orient_txt:
                    cmd.append("--lock-video-orientation=1")
                elif "180°" in orient_txt or "(2)" in orient_txt:
                    cmd.append("--lock-video-orientation=2")
                elif "90° CW" in orient_txt or "(3)" in orient_txt:
                    cmd.append("--lock-video-orientation=3")

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

                if self.chk_mirror_v4l2.isChecked():
                    sink = self.cmb_mirror_sink.currentText().strip()
                    if sink:
                        cmd.append(f"--v4l2-sink={sink}")
                        cmd.append("--v4l2-buffer=0")

                if self.chk_mirror_hid_kb.isChecked():
                    cmd.append("--keyboard=uhid")

                if self.chk_mirror_prefer_text.isChecked():
                    cmd.append("--prefer-text")

                if self.chk_mirror_hid_mouse.isChecked():
                    cmd.append("--mouse=uhid")

                if self.chk_mirror_record.isChecked():
                    cmd.append(f"--record={_get_record_arg()}")

                extra = self.txt_mirror_extra.text().strip()
                if extra:
                    try:
                        cmd.extend(shlex.split(extra))
                    except Exception as e:
                        print(f"Error parsing extra mirror flags: {e}", file=sys.stderr)

        elif current_idx == 1:
            # ── Tab 1: Virtual Display ──
            target = self._get_selected_serial()
            if self.chk_vd_force_desktop.isChecked():
                set_desktop_mode(True, target)
            else:
                restore_desktop_mode_defaults(target)

            # Resolution: width x height
            res = ""
            raw_res = self.cmb_vd_res.currentText().strip()
            if raw_res and not raw_res.lower().startswith("native"):
                first_part = raw_res.split()[0]
                if "x" in first_part:
                    wh = first_part.split("x")
                    if len(wh) == 2 and wh[0].isdigit() and wh[1].isdigit():
                        res = f"{wh[0]}x{wh[1]}"

            # DPI: positive integer only
            dpi = ""
            raw_dpi = self.cmb_vd_dpi.currentText().strip()
            if raw_dpi:
                first_dpi = raw_dpi.split()[0]
                if first_dpi.isdigit() and int(first_dpi) > 0:
                    dpi = first_dpi

            if res and dpi:
                cmd.append(f"--new-display={res}/{dpi}")
            elif res:
                cmd.append(f"--new-display={res}")
            elif dpi:
                cmd.append(f"--new-display=/{dpi}")
            else:
                cmd.append("--new-display")

            if self.chk_vd_flex.isChecked() and self.capabilities.get("has_flex_display", False):
                cmd.append("--flex-display")

            if self.chk_vd_keep_active.isChecked():
                cmd.append("--keep-active")

            if not self.chk_vd_destroy.isChecked():
                cmd.append("--no-vd-destroy-content")

            app = self.txt_vd_app.text().strip()
            has_app = bool(
                app
                and app.lower() not in ("none", "(none)", "none - blank virtual display")
                and not app.lower().startswith("(none")
            )

            if self.chk_vd_no_decor.isChecked():
                if has_app:
                    cmd.append("--no-vd-system-decorations")
                else:
                    self.lbl_status.setText("● Notice: Clean display skipped (requires an app to avoid freeze)")
                    self.lbl_status.setStyleSheet("color: #eab308; font-weight: bold;")

            if self.chk_vd_stay_awake.isChecked():
                cmd.append("--stay-awake")

            if self.chk_vd_screen_off.isChecked():
                cmd.append("--turn-screen-off")

            if self.chk_vd_audio.isChecked():
                cmd.append("--audio-source=output")
            else:
                cmd.append("--no-audio")

            # Codec
            codec_txt = self.cmb_vd_codec.currentText()
            if "h265" in codec_txt:
                cmd.append("--video-codec=h265")
            elif "av1" in codec_txt:
                cmd.append("--video-codec=av1")

            # Bitrate
            br = self.cmb_vd_bitrate.currentText().strip()
            if br:
                cmd.append(f"--video-bit-rate={br}")

            # FPS
            fps = self.cmb_vd_fps.currentText().split()[0]
            if fps.isdigit() and int(fps) > 0:
                cmd.append(f"--max-fps={fps}")

            if self.chk_vd_hid_kb.isChecked():
                cmd.append("--keyboard=uhid")

            if self.chk_vd_prefer_text.isChecked():
                cmd.append("--prefer-text")

            ime_policy = self.cmb_vd_ime.currentText()
            if "hide" in ime_policy:
                cmd.append("--display-ime-policy=hide")
            elif "local" in ime_policy:
                cmd.append("--display-ime-policy=local")

            if self.chk_vd_hid_mouse.isChecked():
                cmd.append("--mouse=uhid")

            if self.chk_vd_record.isChecked():
                cmd.append(f"--record={_get_record_arg()}")

            if has_app:
                prefix = "+" if self.chk_vd_force_stop.isChecked() else ""
                cmd.append(f"--start-app={prefix}{app}")

            extra = self.txt_vd_extra.text().strip()
            if extra:
                try:
                    cmd.extend(shlex.split(extra))
                except Exception as e:
                    print(f"Error parsing extra virtual display flags: {e}", file=sys.stderr)

        elif current_idx == 2:
            return self._build_camera_command()

        return cmd

    def _build_camera_command(self) -> List[str]:
        cmd = ["scrcpy"]
        target = self._get_selected_serial()
        if target:
            cmd.append(f"--serial={target}")

        cmd.append("--video-source=camera")
        raw_cam_res = self.cmb_cam_res.currentText().strip()
        if raw_cam_res and not raw_cam_res.lower().startswith("native"):
            first_cam = raw_cam_res.split()[0]
            if "x" in first_cam:
                wh = first_cam.split("x")
                if len(wh) == 2 and wh[0].isdigit() and wh[1].isdigit():
                    cmd.append(f"--camera-size={wh[0]}x{wh[1]}")

        fps = self.cmb_cam_fps.currentText().split()[0]
        if fps.isdigit() and int(fps) > 0:
            cmd.append(f"--camera-fps={fps}")

        facing = self.cmb_cam_facing.currentText().strip()
        if facing in ("front", "back"):
            cmd.append(f"--camera-facing={facing}")
        elif facing.isdigit():
            cmd.append(f"--camera-id={facing}")

        br = self.cmb_cam_bitrate.currentText().strip()
        if br:
            cmd.append(f"--video-bit-rate={br}")

        if self.chk_cam_antilag.isChecked():
            cmd.append("--v4l2-buffer=0")
            cmd.append("--no-audio")

        sink = self.cmb_cam_sink.currentText().strip()
        if sink and self.capabilities.get("has_v4l2_sink", False):
            cmd.append(f"--v4l2-sink={sink}")

        extra = self.txt_cam_extra.text().strip()
        if extra:
            try:
                cmd.extend(shlex.split(extra))
            except Exception as e:
                print(f"Error parsing extra camera flags: {e}", file=sys.stderr)

        return cmd

    def _on_cam_action_clicked(self):
        if self.cam_proc_manager.is_running():
            self.cam_proc_manager.stop()
            self.lbl_cam_status.setText("Status: Stopping...")
            self.lbl_cam_status.setStyleSheet("color: #eab308; font-weight: bold;")
        else:
            cmd = self._build_camera_command()
            success = self.cam_proc_manager.start(cmd)
            if success:
                self.btn_cam_action.setText("⏹ Stop Webcam Stream")
                self.btn_cam_action.setObjectName("btn_stop")
                self.btn_cam_action.setStyle(self.btn_cam_action.style())
                self.lbl_cam_status.setText("Status: 🟢 Streaming")
                self.lbl_cam_status.setStyleSheet("color: #10b981; font-weight: bold;")
            else:
                QtWidgets.QMessageBox.critical(self, "Camera Error", "Could not start webcam stream. Check the live logs for details.")

    @Slot(int)
    def _on_cam_process_exited(self, return_code: int):
        self.btn_cam_action.setText("🎥 Launch Webcam (Concurrent)")
        self.btn_cam_action.setObjectName("")
        self.btn_cam_action.setStyle(self.btn_cam_action.style())
        self.lbl_cam_status.setText("Status: Stopped")
        self.lbl_cam_status.setStyleSheet("color: #94a3b8; font-weight: bold;")

    def _on_action_clicked(self):
        if self.proc_manager.is_running():
            self.proc_manager.stop()
            self.lbl_status.setText("● Stopping scrcpy...")
            self.lbl_status.setStyleSheet("color: #eab308; font-weight: bold;")
        else:
            current_idx = self.tabs.currentIndex()
            if current_idx == 1 and self.chk_vd_no_decor.isChecked():
                app = self.txt_vd_app.text().strip()
                has_app = bool(
                    app
                    and app.lower() not in ("none", "(none)", "none - blank virtual display")
                    and not app.lower().startswith("(none")
                )
                if not has_app:
                    reply = QtWidgets.QMessageBox.question(
                        self,
                        "Clean Display Requires an App",
                        "Clean Display (--no-vd-system-decorations) removes all Android system bars and desktop launchers.\n\n"
                        "Without launching an app via '--start-app', Android creates a 0-frame blank display, causing scrcpy to freeze on launch.\n\n"
                        "Would you like to turn off Clean Display and launch the standard Android desktop?",
                        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
                        QtWidgets.QMessageBox.StandardButton.Yes,
                    )
                    if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                        self.chk_vd_no_decor.setChecked(False)
                    else:
                        return

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
            self.log_widget.setVisible(True)
            self.btn_toggle_log.setText("📋 Hide Logs")

    def _copy_logs(self):
        QtWidgets.QApplication.clipboard().setText(self.txt_logs.toPlainText())

    def _clear_logs(self):
        self.txt_logs.clear()
        self.proc_manager.clear_logs()

    def _toggle_log_panel(self):
        is_vis = not self.log_widget.isVisible()
        self.log_widget.setVisible(is_vis)
        self.btn_toggle_log.setText("📋 Hide Logs" if is_vis else "📋 Show Logs")

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
        self.cmb_mirror_res.setCurrentText(c.get("mirror_res", "Native Display Size"))
        self.cmb_mirror_codec.setCurrentText(c.get("mirror_codec", "Default (H.264)"))
        self.cmb_mirror_bitrate.setCurrentText(c.get("mirror_bitrate", "8M"))
        self.cmb_mirror_orientation.setCurrentText(c.get("mirror_orientation", "Auto-Rotate (Unlocked)"))
        self.chk_mirror_stay_awake.setChecked(c.get("mirror_stay_awake", True))
        self.chk_mirror_audio.setChecked(c.get("mirror_audio", True))
        self.chk_mirror_turn_off.setChecked(c.get("mirror_turn_screen_off", False))
        self.chk_mirror_fullscreen.setChecked(c.get("mirror_fullscreen", False))
        self.chk_mirror_v4l2.setChecked(c.get("mirror_v4l2", False))
        if self.capabilities.get("has_v4l2_sink", False):
            self.cmb_mirror_sink.setCurrentText(c.get("mirror_sink", "/dev/video0"))
        self.chk_mirror_hid_kb.setChecked(c.get("mirror_hid_keyboard", False))
        self.chk_mirror_prefer_text.setChecked(c.get("mirror_prefer_text", False))
        self.chk_mirror_hid_mouse.setChecked(c.get("mirror_hid_mouse", False))
        self.chk_mirror_otg.setChecked(c.get("mirror_otg", False))
        self.chk_mirror_record.setChecked(c.get("mirror_record", False))
        self.txt_mirror_extra.setText(c.get("mirror_extra", ""))

        # Virtual Display
        self.chk_vd_force_desktop.setChecked(c.get("vd_force_desktop", True))
        self.cmb_vd_res.setCurrentText(c.get("vd_resolution", "1920x1080 (FHD)"))
        self.cmb_vd_dpi.setCurrentText(c.get("vd_dpi", "180 (Desktop Scale / Max Space)"))
        self.cmb_vd_codec.setCurrentText(c.get("vd_codec", "Default (H.264)"))
        self.cmb_vd_fps.setCurrentText(c.get("vd_fps", "60"))
        self.cmb_vd_bitrate.setCurrentText(c.get("vd_bitrate", "16M"))
        self.chk_vd_flex.setChecked(c.get("vd_flex", True))
        self.chk_vd_keep_active.setChecked(c.get("vd_keep_active", True))
        self.chk_vd_destroy.setChecked(c.get("vd_destroy_content", False))
        self.chk_vd_no_decor.setChecked(c.get("vd_no_decor", False))
        self.chk_vd_stay_awake.setChecked(c.get("vd_stay_awake", True))
        self.chk_vd_screen_off.setChecked(c.get("vd_screen_off", False))
        self.chk_vd_audio.setChecked(c.get("vd_audio", True))
        self.chk_vd_hid_kb.setChecked(c.get("vd_hid_keyboard", False))
        self.chk_vd_prefer_text.setChecked(c.get("vd_prefer_text", False))
        self.cmb_vd_ime.setCurrentText(c.get("vd_ime", "Default (Auto)"))
        self.chk_vd_hid_mouse.setChecked(c.get("vd_hid_mouse", True))
        self.chk_vd_record.setChecked(c.get("vd_record", False))
        raw_app = c.get("vd_app", "")
        self.txt_vd_app.setText("" if raw_app.lower() in ("none", "(none)") else raw_app)
        self.chk_vd_force_stop.setChecked(c.get("vd_force_stop", False))
        self.txt_vd_extra.setText(c.get("vd_extra", ""))

        # Camera
        self.cmb_cam_res.setCurrentText(c.get("camera_size", "1920x1080"))
        self.cmb_cam_fps.setCurrentText(c.get("camera_fps", "30"))
        self.cmb_cam_bitrate.setCurrentText(c.get("camera_bitrate", "8M"))
        self.chk_cam_antilag.setChecked(c.get("camera_anti_lag", True))
        self.cmb_cam_facing.setCurrentText(c.get("camera_facing", "back"))
        self.txt_cam_extra.setText(c.get("camera_extra", ""))

        # Shortcuts MOD
        self.cmb_shortcut_mod.setCurrentText(c.get("shortcut_mod", "Default (Left Alt)"))

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
        c["mirror_res"] = self.cmb_mirror_res.currentText()
        c["mirror_codec"] = self.cmb_mirror_codec.currentText()
        c["mirror_bitrate"] = self.cmb_mirror_bitrate.currentText()
        c["mirror_orientation"] = self.cmb_mirror_orientation.currentText()
        c["mirror_stay_awake"] = self.chk_mirror_stay_awake.isChecked()
        c["mirror_audio"] = self.chk_mirror_audio.isChecked()
        c["mirror_turn_screen_off"] = self.chk_mirror_turn_off.isChecked()
        c["mirror_fullscreen"] = self.chk_mirror_fullscreen.isChecked()
        c["mirror_v4l2"] = self.chk_mirror_v4l2.isChecked()
        if self.capabilities.get("has_v4l2_sink", False):
            c["mirror_sink"] = self.cmb_mirror_sink.currentText()
        c["mirror_hid_keyboard"] = self.chk_mirror_hid_kb.isChecked()
        c["mirror_prefer_text"] = self.chk_mirror_prefer_text.isChecked()
        c["mirror_hid_mouse"] = self.chk_mirror_hid_mouse.isChecked()
        c["mirror_otg"] = self.chk_mirror_otg.isChecked()
        c["mirror_record"] = self.chk_mirror_record.isChecked()
        c["mirror_extra"] = self.txt_mirror_extra.text().strip()

        c["vd_force_desktop"] = self.chk_vd_force_desktop.isChecked()
        c["vd_resolution"] = self.cmb_vd_res.currentText()
        c["vd_dpi"] = self.cmb_vd_dpi.currentText()
        c["vd_codec"] = self.cmb_vd_codec.currentText()
        c["vd_fps"] = self.cmb_vd_fps.currentText()
        c["vd_bitrate"] = self.cmb_vd_bitrate.currentText()
        c["vd_flex"] = self.chk_vd_flex.isChecked()
        c["vd_keep_active"] = self.chk_vd_keep_active.isChecked()
        c["vd_destroy_content"] = self.chk_vd_destroy.isChecked()
        c["vd_no_decor"] = self.chk_vd_no_decor.isChecked()
        c["vd_stay_awake"] = self.chk_vd_stay_awake.isChecked()
        c["vd_screen_off"] = self.chk_vd_screen_off.isChecked()
        c["vd_audio"] = self.chk_vd_audio.isChecked()
        c["vd_hid_keyboard"] = self.chk_vd_hid_kb.isChecked()
        c["vd_prefer_text"] = self.chk_vd_prefer_text.isChecked()
        c["vd_ime"] = self.cmb_vd_ime.currentText()
        c["vd_hid_mouse"] = self.chk_vd_hid_mouse.isChecked()
        c["vd_record"] = self.chk_vd_record.isChecked()
        c["vd_app"] = self.txt_vd_app.text().strip()
        c["vd_force_stop"] = self.chk_vd_force_stop.isChecked()
        c["vd_extra"] = self.txt_vd_extra.text().strip()

        c["camera_size"] = self.cmb_cam_res.currentText()
        c["camera_fps"] = self.cmb_cam_fps.currentText()
        c["camera_bitrate"] = self.cmb_cam_bitrate.currentText()
        c["camera_anti_lag"] = self.chk_cam_antilag.isChecked()
        c["camera_facing"] = self.cmb_cam_facing.currentText()
        c["camera_extra"] = self.txt_cam_extra.text().strip()

        c["shortcut_mod"] = self.cmb_shortcut_mod.currentText()

        save_config(c)
        if self.proc_manager.is_running():
            self.proc_manager.stop()
        if self.cam_proc_manager.is_running():
            self.cam_proc_manager.stop()
        event.accept()


def run_qt_app() -> int:
    """Launch Qt Application."""
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set dark base palette to prevent any white or transparent flashing on repaint
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#121418"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#e2e8f0"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#171a21"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#1a1e27"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor("#1e2533"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor("#ffffff"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#e2e8f0"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#242c3d"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#f1f5f9"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor("#38bdf8"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#0284c7"))
    dark_palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
    app.setPalette(dark_palette)

    app.setApplicationName("Scrcpy Control Center")
    app.setOrganizationName("scrcpy-menu")
    window = ScrcpyMainWindow()
    window.show()
    return app.exec()
