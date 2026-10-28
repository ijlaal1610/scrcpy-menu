# 🚀 Scrcpy Menu & Control Center

An advanced **GTK GUI & interactive CLI control center** for [scrcpy](https://github.com/Genymobile/scrcpy) with out-of-the-box support for:

- 📷 **Webcam / Camera Mirroring (up to 60 FPS)** with V4L2 virtual webcam output (`/dev/video2`) and anti-lag optimizations.
- 📱 **Screen Mirroring (up to 120 FPS Native)** with audio forwarding, power management, and downscaling presets.
- 🖥️ **Virtual Secondary Display (`--new-display`)** with Flex Display (`-x`), resizable windows, app launcher, DPI scaling, and hardware screen-off support.
- ⚙️ **Android Desktop Mode Support**: One-click ADB toggle for Android freeform windows and desktop mode on external/virtual displays.
- ⌨️ **Interactive Cheat Sheet**: Complete reference for all keyboard and mouse shortcuts.

---

## ✨ Features

### 1. 📷 Camera / Virtual Webcam
- High-framerate mobile camera streaming (30 FPS or 60 FPS Ultra Smooth).
- Automatic discovery of front and rear camera sensor IDs via `scrcpy --list-cameras`.
- Seamless `/dev/video2` loopback driver streaming for OBS, Zoom, Google Meet, and browsers.
- **⚡ Anti-Lag Engine**:
  - Independent zero-buffer mode (`--v4l2-buffer=0`) prevents frame pile-up in the kernel.
  - Video-only routing (`--no-audio`) prevents clock-drift delays over USB.
  - Bitrate limiter (`-b 8M`) prevents USB bus choke.

### 2. 📱 Screen Mirroring
- Matches 120Hz AMOLED mobile displays at native 120 FPS.
- Screen resolutions: Native (2400×1080), 1080p, or 720p downscaled.
- Forward device audio to PC speakers (`--audio-source=output`).
- Automatic wake lock (`--stay-awake`) and optional screen turn-off (`--turn-screen-off`).

### 3. 🖥️ Virtual Secondary Display (`--new-display`)
- Run applications independently on your PC monitor while your phone's screen remains free for personal use.
- **Flex Display (`-x`)**: Window is freely resizable like any native desktop application.
- **App Launcher**: Start apps directly on the virtual display (`--start-app=...`) with package discovery and optional force-stop.
- **DPI Selector**: Choose from 420 (standard) down to 180 (desktop mode) for maximum workspace.
- **Freeze Prevention**: Software screen-off and stay-awake flags prevent Android from suspending background renderers.
- Codec choices: H.264, H.265/HEVC, and AV1.

### 4. ⚙️ Android Desktop Mode (via ADB)
One-click inspection and configuration of Android global windowing flags:
- `force_desktop_mode_on_external_displays`
- `enable_freeform_support`
- `force_resizable_activities`
- `enable_non_resizable_multi_window`

### 5. ⌨️ Complete Keyboard & Mouse Shortcuts
Integrated reference in both GUI (Tab 4) and CLI for all controls:
- **Navigation**: Right-click = BACK, Middle-click = HOME, 4th-click = APP SWITCHER.
- **Power**: `MOD + o` turns physical screen OFF while keeping virtual display active.
- **Clipboard & Drag/Drop**: Real-time clipboard sharing and APK/file installation by dragging files directly into the window.

---

## 📥 Installation

### Requirements
- Linux with Python 3.8+
- [scrcpy](https://github.com/Genymobile/scrcpy) (v3.0+ recommended for virtual displays)
- Android device with USB debugging enabled
- GTK 3 dependencies (for GUI):
  ```bash
  sudo apt install python3-gi gir1.2-gtk-3.0 v4l2loopback-dkms
  ```

### Quick Install
```bash
git clone https://github.com/ijlaal1610/scrcpy-menu.git
cd scrcpy-menu
chmod +x install.sh
./install.sh
```

---

## 🎯 Usage

### Graphical Mode (GUI)
Run from terminal or click **"Scrcpy – Camera / Mirror"** in your application launcher:
```bash
scrcpy-menu
```

### Terminal Quick Menu (CLI)
For lightweight terminal sessions, SSH, or quick access:
```bash
scrcpy-menu --cli
```

---

## 📄 License
MIT License. Created by [ijlaal1610](https://github.com/ijlaal1610).
