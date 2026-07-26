"""Registers a global hotkey to toggle the watch loop on/off."""

from typing import Callable

from pynput import keyboard

DEFAULT_COMBO = "<ctrl>+<alt>+t"  # Ctrl+Alt+T


def register_toggle_hotkey(on_toggle: Callable[[], None], combo: str = DEFAULT_COMBO) -> None:
    listener = keyboard.GlobalHotKeys({combo: on_toggle})
    listener.start()
