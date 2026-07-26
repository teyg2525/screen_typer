"""Cross-platform entrypoint: dispatches to the OS-specific app."""

import platform
import sys


def main() -> None:
    system = platform.system()
    if system == "Darwin":
        from screen_typer.main_macos import main as platform_main
    elif system == "Windows":
        from screen_typer.main_windows import main as platform_main
    else:
        print(f"Unsupported platform: {system}", file=sys.stderr)
        sys.exit(1)

    platform_main()


if __name__ == "__main__":
    main()
