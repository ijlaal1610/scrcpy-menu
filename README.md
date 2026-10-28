# 🚀 Scrcpy Control Center

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/ijlaal1610/scrcpy-menu)
[![Platforms](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-emerald.svg)](https://github.com/ijlaal1610/scrcpy-menu)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

A modern, cross-platform **GUI & CLI Control Center** for [scrcpy](https://github.com/Genymobile/scrcpy) and ADB, built with PySide6 / Qt and supporting **Linux (x86_64 & ARM64), Windows 10/11 (x64 & ARM), and macOS (Apple Silicon & Intel)**.

Designed for high-performance mobile screen mirroring, virtual secondary displays, phone-as-webcam streaming, and Android desktop mode management with zero latency, responsive scrolling, and robust error handling.

> 💡 **Legacy Branch**: The original Linux-only GTK3 implementation is permanently preserved on the [`legacy-gtk`](https://github.com/ijlaal1610/scrcpy-menu/tree/legacy-gtk) branch.

---

## ✨ Key Capabilities

### 1. 📱 High-Performance Screen Mirroring
- **Fluid Refresh Rates**: Match 90Hz and 120Hz AMOLED mobile displays at native 120 FPS.
- **Custom Resolutions & Downscaling**: Choose native size, capped 1080p/720p presets, or arbitrary custom resolutions (`WxH`).
- **Modern Video Codecs**: Select between `Default (H.264)`, `H.265 / HEVC`, or `AV1` for maximum fidelity and low bandwidth.
- **Orientation Lock**: Lock video feed to 0°, 90° CCW, 180°, or 90° CW.
- **Audio Forwarding**: Stream device sound directly through computer speakers (`--audio-source=output`).
- **Power & Battery Saver**: Turn physical phone screen completely OFF while maintaining high-frame-rate mirroring (`--turn-screen-off`).
- **Virtual Webcam Sink**: Stream your phone's mirrored display directly into V4L2 virtual cameras or OBS.

### 2. 🖥️ Virtual Secondary Display (`--new-display`)
- **Independent Workspace**: Run mobile apps in a secondary virtual display on your PC monitor while your phone's physical screen remains free for calls or other apps.
- **Dynamic Flex Display**: Continuously resize the virtual display window dynamically like any native desktop application (`--flex-display`).
- **Custom Resolutions & Density**: Set custom resolutions (e.g. `1920x1080`, `2560x1440`, `2400x1080`) and custom DPI scaling (180 Desktop Scale, 240 Tablet, 320 Compact, 420 Phone).
- **Device App Scanner**: Integrated `🔄 Scan Device Apps` button queries installed third-party packages from your phone over ADB, allowing you to launch any app directly onto the virtual display.
- **Clean Display Option**: Strip Android system navigation and status bars for borderless fullscreen apps (`--no-vd-system-decorations`).
- **Session Preservation**: Optional toggle to preserve running apps back to the phone when the virtual display window closes (`--no-vd-destroy-content`).

### 3. ⌨️ Hardware Input (HID) & Typing Engine
- **USB HID Keyboard & Mouse Simulation**: Forward physical PC keyboard and mouse input as raw hardware USB HID devices (`--keyboard=uhid`, `--mouse=uhid`), avoiding Android touch-injection latency.
- **Prefer Text Events Mode (`--prefer-text`)**: Injects characters as direct text events, eliminating missed keystrokes, typing lag, or dead keys across international keyboard layouts.
- **On-Screen Keyboard (IME) Policy**: Control whether Android pops up an on-screen keyboard over your virtual desktop (`--display-ime-policy=hide` or `local`).
- **1-Click Device Keyboard Setup**: Built-in button triggers Android's physical hardware keyboard settings page directly on your phone to set your preferred layout.
- **OTG Mode**: Control your phone with PC peripherals directly without video mirroring (`--otg`).

### 4. ⚙️ Android Desktop Mode & OEM Rollback (ADB)
- Inspect and toggle Android global windowing flags (`force_desktop_mode_on_external_displays`, `enable_freeform_support`, `force_resizable_activities`).
- **Safe Rollback**: Deletes flag overrides (`settings delete global ...`) to cleanly restore your device manufacturer's factory default window manager behavior.
- ROM capability detection for Samsung DeX, Xiaomi/HyperOS, and standard AOSP.

### 5. 📷 Phone as Webcam / Camera Streaming
- **Zero-Latency Anti-Lag Engine**: Zero-buffer streaming (`--v4l2-buffer=0`) and audio bypass to eliminate USB clock-drift delay.
- Switch between Front, Rear, and multi-lens camera sensors with 1080p, 720p, or 4K resolutions at 30/60 FPS.
- Platform-aware video sink routing (V4L2 on Linux, OBS Virtual Camera / DirectShow on Windows/macOS).

### 6. 📶 Wireless ADB & Android 11+ Pairing Manager
- **One-Click Wi-Fi Connect**: Connect to devices over local networks (`192.0.2.1:5555`).
- **Android 11+ Pairing**: Built-in support for Android 11+ wireless pairing codes and dynamic pairing ports (`adb pair <ip>:<port> <code>`).
- **ADB Daemon Refresh**: 1-click server restart directly from the toolbar or CLI.

### 7. 🎬 Session Recording & Drag-and-Drop
- **One-Click MP4 Recording**: Record screen mirroring or virtual display sessions directly to high-quality MP4 (`~/Videos/scrcpy_<timestamp>.mp4`).
- **Drag-and-Drop Operations**: Drag any `.apk` directly onto the window to automatically install it, or drag files/folders to instantly push them to `/sdcard/Download/`.

---

## 💻 Supported Platforms & Architectures

| Platform | Architecture | GUI Support | CLI Support | Pre-compiled Standalone Binary |
| :--- | :--- | :---: | :---: | :--- |
| **Linux** | x86_64 (Intel / AMD) | ✅ PySide6 | ✅ Full | `scrcpy-control-center-linux-x86_64` |
| **Linux** | ARM64 (`aarch64` / Pi) | ✅ PySide6 | ✅ Full | `scrcpy-control-center-linux-aarch64` |
| **Windows** | x64 (Intel / AMD) | ✅ PySide6 | ✅ Full | `scrcpy-control-center-windows-x64.exe` |
| **Windows on ARM** | ARM64 (Snapdragon X Elite, Surface) | ✅ PySide6 | ✅ Full | Seamless execution via Windows 11 Prism |
| **macOS** | Apple Silicon (M1 / M2 / M3 / M4) | ✅ PySide6 | ✅ Full | `scrcpy-control-center-macos-arm64` |
| **macOS** | Intel (`x86_64`) | ✅ PySide6 | ✅ Full | `scrcpy-control-center-macos-x86_64` |

---

## 📥 Installation

### Option A: Standalone Executable (Zero Python Setup)
Precompiled binaries generated by our GitHub Actions release workflow:
1. Download the executable for your OS from [GitHub Releases](https://github.com/ijlaal1610/scrcpy-menu/releases).
2. Mark executable on Linux/macOS (`chmod +x scrcpy-control-center-*`) and run.

### Option B: Python Package

#### Prerequisites
1. **scrcpy** (v2.2+ recommended, v3.0+ for flex-display):
   - **Linux**: `sudo apt install scrcpy` (or `pacman -S scrcpy`)
   - **Windows**: `winget install Genymobile.scrcpy` (or `scoop install scrcpy`)
   - **macOS**: `brew install scrcpy`
2. **Python 3.8+**
3. USB debugging enabled on your Android phone.

```bash
git clone https://github.com/ijlaal1610/scrcpy-menu.git
cd scrcpy-menu
pip install -e .
```

*For Linux desktop application menu integration (`.desktop` launcher), run `./install.sh`.*

---

## 🎯 Usage

### Modern Graphical Interface (GUI)
```bash
scrcpy-menu
```

### Lightweight Terminal Quick Menu (CLI)
Zero external dependencies required (runs in SSH, servers, or minimal environments):
```bash
scrcpy-menu --cli
```

### Diagnostics & Capability Report
Inspect scrcpy version support and connected devices:
```bash
scrcpy-menu --diagnostics
```

---

## ⌨️ Scrcpy Keyboard & Mouse Shortcuts

In the table below, **`MOD`** is your shortcut modifier key (by default **Left-Alt** or **Left-Super / Windows Key**, configurable in the Shortcuts tab):

| Category | Shortcut | Action |
| :--- | :--- | :--- |
| **Window** | `MOD + f` or `F11` | Toggle fullscreen mode |
| **Window** | `MOD + w` or Double-click border | Resize window to remove black borders |
| **Window** | `MOD + g` | Resize window to 1:1 pixel mapping |
| **Window** | `MOD + Left` / `Right` | Rotate display 90 degrees left / right |
| **Window** | `MOD + Shift + Left` / `Right` | Flip display horizontally (mirror effect) |
| **Window** | `MOD + z` / `MOD + Shift + z` | Pause / Unpause video stream |
| **Navigation** | `Right-click` or `MOD + b` | Back button (Android) |
| **Navigation** | `Middle-click` or `MOD + h` | Home button (Android) |
| **Navigation** | `4th-click` or `MOD + s` | App Switcher (Recents overview on phone) |
| **Navigation** | `5th-click` or `MOD + n` | Expand notification panel |
| **Power** | `MOD + o` | Turn phone physical screen OFF (keep mirroring) |
| **Power** | `MOD + Shift + o` | Turn phone physical screen back ON |
| **Power** | `MOD + p` | Power key (wake/sleep phone) |
| **Hardware** | `MOD + i` | Toggle mouse capture / pointer lock |
| **Hardware** | `MOD + k` | Open hardware keyboard settings on phone |
| **Clipboard** | `MOD + c` / `MOD + v` | Copy / Paste clipboard between PC and phone |
| **Clipboard** | `MOD + Shift + v` | Paste PC clipboard text as raw keystrokes |
| **Files** | Drag & drop `.apk` | Automatically install APK onto device |
| **Files** | Drag & drop files | Push files directly to `/sdcard/Download/` |

---

## ❓ Frequently Asked Questions & Troubleshooting

### Why doesn't the keyboard type immediately when scrcpy opens?
* **Focus Grab**: scrcpy does not capture keystrokes until you **click once inside the scrcpy display window** (or press `MOD + i` to grab input focus).
* **Physical Keyboard Layout**: When using Hardware Keyboard Simulation (`--keyboard=uhid`), Android recognizes your PC keyboard as an external physical USB keyboard. If Android has no layout configured, click the **`⌨️ Configure Device Keyboard Layout`** button in Scrcpy Control Center (or press `MOD + k`) to select your keyboard language (e.g. English US).
* **Text Injection Alternative**: If special characters or accented keys drop, enable **`Prefer Text Events (--prefer-text)`** in Scrcpy Control Center.

### Why does the App Switcher (`MOD + s`) open on the phone screen instead of the Virtual Display?
In Android's SystemUI architecture, the Overview/Recents component is tied by default to the primary display (`Display 0`). To switch apps on the virtual display:
1. Press **`MOD + h`** (Home) to open the `SecondaryDisplayLauncher` app drawer directly inside the virtual display window.
2. Use the **`🔄 Scan Device Apps`** selector in Scrcpy Control Center to launch apps directly on the virtual display.
3. Use a secondary display launcher like [Taskbar](https://github.com/farmerbb/Taskbar) for an on-screen desktop taskbar.

### How to stream the phone webcam in the background without opening a preview window?
* In the **Camera / Webcam** tab, uncheck **`Show desktop preview window`**.
* Scrcpy will run with `--no-video-playback`, piping your phone's camera feed directly into `/dev/video2` (or your chosen V4L2 virtual webcam node) with 0 desktop CPU/GPU window overhead and minimal latency. Select `/dev/video2` in OBS, Zoom, or Google Meet.

### How to eliminate webcam latency when streaming concurrently or over Wi-Fi?
* Over wireless ADB, streaming two high-bitrate video streams concurrently can cause network queue latency.
* Switch to the **`⚡ 720p Low Latency / Wi-Fi`** preset (1280x720 @ 30 FPS, 4M bitrate, zero display buffer).
* For maximum 1080p60 fidelity with zero latency across both webcam and virtual display, connect via USB.

---

## 📄 License

MIT License. Developed by [ijlaal1610](https://github.com/ijlaal1610).
