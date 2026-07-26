"""Registers a global hotkey to toggle the watch loop on/off."""

from typing import Callable

from quickmachotkey import quickHotKey, mask
from quickmachotkey.constants import kVK_ANSI_T, cmdKey, optionKey

DEFAULT_COMBO = (kVK_ANSI_T, mask(cmdKey, optionKey))  # Cmd+Option+T


def register_toggle_hotkey(on_toggle: Callable[[], None], combo=DEFAULT_COMBO) -> None:
    virtual_key, modifier_mask = combo

    @quickHotKey(virtualKey=virtual_key, modifierMask=modifier_mask)
    def _handler():
        on_toggle()
