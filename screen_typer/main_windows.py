"""App entrypoint: region selection, hotkey arming, tray icon lifecycle."""

import threading

import pystray
from PIL import Image, ImageDraw

from screen_typer.platform_windows.hotkey import register_toggle_hotkey
from screen_typer.platform_windows.region_picker import pick_region
from screen_typer.watch_loop import WatchLoop

STATUS_RUNNING = "Screen Typer: ON"
STATUS_STOPPED = "Screen Typer: OFF"


def _make_icon_image(running: bool) -> Image.Image:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = (60, 200, 100, 255) if running else (150, 150, 150, 255)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return image


def main() -> None:
    print("Select the capture region: drag a rectangle over the word fall path.")
    region = pick_region()
    print(f"Region selected: {region}")

    watch_loop = WatchLoop(region)
    icon = pystray.Icon("screen_typer", _make_icon_image(False), STATUS_STOPPED)

    def toggle(icon_ref=None, item=None):
        watch_loop.toggle()
        icon.icon = _make_icon_image(watch_loop.is_running)
        icon.title = STATUS_RUNNING if watch_loop.is_running else STATUS_STOPPED

    def quit_app(icon_ref=None, item=None):
        watch_loop.stop()
        icon.stop()

    icon.menu = pystray.Menu(
        pystray.MenuItem("Start/Stop", toggle, default=True),
        pystray.MenuItem("Quit", quit_app),
    )

    register_toggle_hotkey(lambda: toggle())
    print("Ready. Press Ctrl+Alt+T to start/stop the watch loop, or use the tray icon.")

    icon.run()


if __name__ == "__main__":
    main()
