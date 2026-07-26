"""Simulates system-wide keyboard input via pynput, wherever OS focus is."""

from pynput.keyboard import Controller

_controller = Controller()


def type_text(text: str) -> None:
    if text:
        _controller.type(text)
