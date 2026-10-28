#!/usr/bin/env bash
# scrcpy-menu installer for Linux
set -e

INSTALL_BIN="$HOME/.local/bin"
INSTALL_APPS="$HOME/.local/share/applications"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing scrcpy-menu..."

mkdir -p "$INSTALL_BIN"
mkdir -p "$INSTALL_APPS"

# Install package in user mode
if command -v pip3 >/dev/null 2>&1; then
    echo "✔ Installing scrcpy-menu package..."
    pip3 install --user --break-system-packages -e "$DIR" >/dev/null 2>&1 || pip3 install --user -e "$DIR"
else
    cp "$DIR/scrcpy-menu" "$INSTALL_BIN/scrcpy-menu"
    chmod +x "$INSTALL_BIN/scrcpy-menu"
fi

# Ensure launcher script is in ~/.local/bin
cp "$DIR/scrcpy-menu" "$INSTALL_BIN/scrcpy-menu"
chmod +x "$INSTALL_BIN/scrcpy-menu"
echo "✔ Copied launcher script to $INSTALL_BIN/scrcpy-menu"

# Install desktop entry
sed "s|^Exec=scrcpy-menu|Exec=$INSTALL_BIN/scrcpy-menu|g" "$DIR/scrcpy-menu.desktop" > "$INSTALL_APPS/scrcpy-menu.desktop"
chmod +x "$INSTALL_APPS/scrcpy-menu.desktop"
echo "✔ Installed desktop entry to $INSTALL_APPS/scrcpy-menu.desktop"

# Refresh desktop database if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$INSTALL_APPS" >/dev/null 2>&1 || true
    echo "✔ Desktop application menu updated"
fi

echo ""
echo "🎉 Installation successful!"
echo "Run 'scrcpy-menu' for GUI or 'scrcpy-menu --cli' for terminal mode."
