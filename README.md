# 🚀 Scrcpy Control Center

A modern, cross-platform **GUI & CLI Control Center** for [scrcpy](https://github.com/Genymobile/scrcpy) and ADB, supporting **Linux, Windows 10/11, and macOS**.

Designed for high-performance mobile screen mirroring, virtual secondary displays, camera/webcam streaming, and Android desktop mode management with zero latency and robust error handling.

> 💡 **Legacy Branch**: The original Linux-only GTK3 implementation is permanently preserved on the [`legacy-gtk`](https://github.com/ijlaal1610/scrcpy-menu/tree/legacy-gtk) branch.

---

## ✨ Key Capabilities

### 1. 📱 Screen Mirroring (up to 120 FPS Native)
- **Fluid High Refresh Rate**: Match 90Hz and 120Hz AMOLED mobile displays at native 120 FPS.
- **Audio Forwarding**: Stream device sound directly through computer speakers (`--audio-source=output`).
- **Power Management**: Turn device physical screen off while keeping mirroring alive (`--turn-screen-off`).
- **Bitrate & Latency Tuning**: Presets for Ultra Low-Lag, Presentation, and Gaming.

### 2. 🖥️ Virtual Secondary Display (`--new-display`)
- **Independent Workspace**: Run mobile apps in a secondary virtual display on your PC monitor while your phone's physical screen remains free.
- **Flex Display**: Dynamically resize the virtual display window like any native PC app (`--flex-display`).
- **Sound Control**: Dedicated toggle to stream or mute virtual display audio on PC.
- **DPI Scaling**: Switch between Phone (420 DPI), Tablet (240 DPI), and Desktop (180 DPI) for high screen density.
- **App Launcher**: Auto-launch specific applications (`--start-app=...`) on the virtual display.

### 3. ⚙️ Android Desktop Mode & OEM Rollback (ADB)
- Inspect and toggle Android global windowing flags (`force_desktop_mode_on_external_displays`, `enable_freeform_support`, `force_resizable_activities`).
- **Safe Rollback**: Deletes flag overrides (`settings delete global ...`) to cleanly restore your device manufacturer's factory default window manager behavior.
- ROM capability detection for Samsung DeX, Xiaomi/HyperOS, and standard AOSP.

### 4. 📷 Phone as Webcam / Camera Streaming
- **Zero-Latency Anti-Lag Engine**: Zero-buffer streaming (`--v4l2-buffer=0`) and audio bypass to eliminate USB clock-drift delay.
- Switch between Front and Rear camera sensors with 1080p, 720p, or 4K resolutions at 30/60 FPS.
- Platform-aware video sink routing (V4L2 on Linux, OBS Virtual Camera / DirectShow on Windows/macOS).

### 5. 🛠️ Robust Architecture & Diagnostics
- **Safe Subprocess Execution**: List-based argument construction without shell execution, eliminating command injection risks.
- **Non-Blocking Real-Time Logs**: Continuous stream draining with bounded buffer prevents OS pipe hangs during verbose video playback.
- **Atomic Config Persistence**: Restrictive file permissions and atomic writes guarantee settings memory across sessions.
- **System Diagnostics Matrix**: Instant assessment of scrcpy version capabilities, ADB status, and connected devices.

---

## 💻 Supported Platforms

| Platform | GUI Support | CLI Support | Virtual Display | Virtual Webcam |
| :--- | :---: | :---: | :---: | :---: |
| **Linux** (Ubuntu, Arch, Fedora, Debian) | ✅ PySide6 / Qt | ✅ Full | ✅ Scrcpy ≥ 2.2 | ✅ V4L2 Loopback |
| **Windows 10 / 11** | ✅ PySide6 / Qt | ✅ Full | ✅ Scrcpy ≥ 2.2 | ✅ OBS Virtual Cam |
| **macOS** (12+ Monterey, Ventura, Sonoma) | ✅ PySide6 / Qt | ✅ Full | ✅ Scrcpy ≥ 2.2 | ✅ OBS Virtual Cam |

---

## 📥 Installation

### Prerequisites
1. **scrcpy** (v2.2+ recommended, v3.0+ for flex-display):
   - **Linux**: `sudo apt install scrcpy` (or snap/pacman)
   - **Windows**: `winget install Genymobile.scrcpy` (or `scoop install scrcpy`)
   - **macOS**: `brew install scrcpy`
2. **Python 3.8+**
3. USB debugging enabled on your Android phone.

### Quick Install (All Platforms)

```bash
git clone https://github.com/ijlaal1610/scrcpy-menu.git
cd scrcpy-menu
pip install -e .
```

*For Linux desktop shortcut integration, you can also run `./install.sh`.*

---

## 🎯 Usage

### Modern Graphical Interface (GUI)
Launch the dark-themed Qt control center:
```bash
scrcpy-menu
```

### Lightweight Terminal Quick Menu (CLI)
Zero external dependencies required (runs in SSH, servers, or minimal environments):
```bash
scrcpy-menu --cli
```

### Diagnostics & Compatibility Check
Check installed scrcpy capabilities and connected devices:
```bash
scrcpy-menu --diagnostics
```

---

## ⌨️ Essential Keyboard Shortcuts

| Shortcut (MOD = Alt or Super) | Action |
| :--- | :--- |
| `MOD + f` | Toggle Fullscreen |
| `MOD + o` | Turn phone physical screen OFF (keep mirroring alive) |
| `MOD + Shift + o` | Turn phone physical screen ON |
| `MOD + h` | Android Home |
| `MOD + b` / `Backspace` | Android Back |
| `MOD + s` | Android App Switcher (Recents) |
| `MOD + c` / `MOD + v` | Clipboard copy / paste between PC and phone |
| `MOD + i` | Toggle mouse capture / pointer lock |

---

## 📄 License

MIT License. Developed by [ijlaal1610](https://github.com/ijlaal1610).
