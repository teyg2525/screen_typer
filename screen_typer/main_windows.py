"""App entrypoint: region selection, hotkey arming, tray icon lifecycle."""

import ctypes
import threading

import pystray
from PIL import Image, ImageDraw

from screen_typer.platform_windows.hotkey import register_toggle_hotkey
from screen_typer.platform_windows.region_picker import pick_region
from screen_typer.watch_loop import WatchLoop

STATUS_RUNNING = "Screen Typer: ON"
STATUS_STOPPED = "Screen Typer: OFF"

DEDUP_TTL_OPTIONS = (0.5, 1, 2, 3, 4, 5)

_DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
_PROCESS_PER_MONITOR_DPI_AWARE = 2


def _enable_dpi_awareness() -> None:
    """Without this, a DPI-unaware process sees a virtualized, blurry desktop
    on scaled displays, which both misaligns region-picker coordinates and
    degrades OCR accuracy on the captured frame."""
    try:
        set_context = ctypes.windll.user32.SetProcessDpiAwarenessContext
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = ctypes.c_int
        if set_context(ctypes.c_void_p(_DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)):
            return
    except (AttributeError, OSError):
        pass
    try:
        if ctypes.windll.shcore.SetProcessDpiAwareness(_PROCESS_PER_MONITOR_DPI_AWARE) == 0:
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


def _make_icon_image(running: bool) -> Image.Image:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = (60, 200, 100, 255) if running else (150, 150, 150, 255)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return image


def main() -> None:
    _enable_dpi_awareness()

    print("Select the capture region: drag a rectangle over the word fall path.")
    region = pick_region()
    print(f"Region selected: {region}")

    watch_loop = WatchLoop(region)
    icon = pystray.Icon("screen_typer", _make_icon_image(False), STATUS_STOPPED)

    def toggle(icon_ref=None, item=None):
        watch_loop.toggle()
        icon.icon = _make_icon_image(watch_loop.is_running)
        icon.title = STATUS_RUNNING if watch_loop.is_running else STATUS_STOPPED

    def reselect_region(icon_ref=None, item=None):
        was_running = watch_loop.is_running
        watch_loop.stop()
        try:
            region = pick_region()
        except RuntimeError:
            print("Region reselection was cancelled")
        else:
            watch_loop.set_region(region)
            print(f"Region selected: {region}")
        if was_running:
            watch_loop.start()
        icon.icon = _make_icon_image(watch_loop.is_running)
        icon.title = STATUS_RUNNING if watch_loop.is_running else STATUS_STOPPED

    def toggle_letters_only(icon_ref=None, item=None):
        watch_loop.toggle_letters_only()

    def toggle_bright_only(icon_ref=None, item=None):
        watch_loop.toggle_bright_only()

    def make_set_dedup_ttl(seconds):
        def set_dedup_ttl(icon_ref=None, item=None):
            watch_loop.set_dedup_ttl(seconds)
        return set_dedup_ttl

    def make_dedup_ttl_checked(seconds):
        return lambda item: watch_loop.dedup_ttl == seconds

    def quit_app(icon_ref=None, item=None):
        watch_loop.stop()
        icon.stop()

    dedup_ttl_menu = pystray.Menu(
        *(
            pystray.MenuItem(
                f"{seconds}s",
                make_set_dedup_ttl(seconds),
                radio=True,
                checked=make_dedup_ttl_checked(seconds),
            )
            for seconds in DEDUP_TTL_OPTIONS
        )
    )

    icon.menu = pystray.Menu(
        pystray.MenuItem("Start/Stop", toggle, default=True),
        pystray.MenuItem("Reselect Region", reselect_region),
        pystray.MenuItem(
            "Letters Only",
            toggle_letters_only,
            checked=lambda item: watch_loop.letters_only,
        ),
        pystray.MenuItem(
            "Bright Letters Only",
            toggle_bright_only,
            checked=lambda item: watch_loop.bright_only,
        ),
        pystray.MenuItem("Already-Typed Threshold", dedup_ttl_menu),
        pystray.MenuItem("Quit", quit_app),
    )

    register_toggle_hotkey(lambda: toggle())
    print("Ready. Press Ctrl+Alt+T to start/stop the watch loop, or use the tray icon.")

    icon.run()


if __name__ == "__main__":
    main()
