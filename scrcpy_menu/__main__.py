"""Entrypoint for python -m scrcpy_menu."""

import sys
from .cli import run_cli_menu
from .core.capabilities import generate_system_diagnostics
from . import __version__


def main():
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"scrcpy-menu v{__version__}")
        sys.exit(0)

    if "--diagnostics" in sys.argv or "-d" in sys.argv:
        print(generate_system_diagnostics())
        sys.exit(0)

    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"scrcpy-menu v{__version__} - Cross-platform Scrcpy Control Center")
        print("\nUsage:")
        print("  scrcpy-menu             Launch modern Qt GUI")
        print("  scrcpy-menu --cli       Launch interactive terminal quick menu")
        print("  scrcpy-menu --diagnostics View host/device diagnostics report")
        print("  scrcpy-menu --version   Print version info")
        sys.exit(0)

    if "--cli" in sys.argv:
        run_cli_menu()
        return

    # Attempt GUI launch
    try:
        from .ui.qt_app import run_qt_app
        sys.exit(run_qt_app())
    except ImportError as e:
        print(f"[*] Qt GUI libraries not detected ({e}).", file=sys.stderr)
        print("[*] Launching interactive terminal menu instead.\n", file=sys.stderr)
        run_cli_menu()
    except Exception as e:
        print(f"[!] GUI Error: {e}", file=sys.stderr)
        print("[*] Falling back to terminal menu.\n", file=sys.stderr)
        run_cli_menu()


if __name__ == "__main__":
    main()
