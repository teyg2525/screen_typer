"""Simulates system-wide keyboard input via CGEvent, wherever OS focus is."""

from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventKeyboardSetUnicodeString,
    CGEventPost,
    kCGHIDEventTap,
)

_KEY_EVENT_SOURCE = None


def type_text(text: str) -> None:
    if text:
        key_down = CGEventCreateKeyboardEvent(_KEY_EVENT_SOURCE, 0, True)
        CGEventKeyboardSetUnicodeString(key_down, len(text), text)
        CGEventPost(kCGHIDEventTap, key_down)

        key_up = CGEventCreateKeyboardEvent(_KEY_EVENT_SOURCE, 0, False)
        CGEventKeyboardSetUnicodeString(key_up, len(text), text)
        CGEventPost(kCGHIDEventTap, key_up)
