"""App entrypoint: permission checks, region selection, hotkey arming."""

import sys

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSMenu,
    NSMenuItem,
    NSStatusBar,
    NSVariableStatusItemLength,
)
from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
from Foundation import NSObject
from Quartz import CGPreflightScreenCaptureAccess, CGRequestScreenCaptureAccess

from screen_typer.hotkey import register_toggle_hotkey
from screen_typer.region_picker import pick_region
from screen_typer.watch_loop import WatchLoop

STATUS_RUNNING = "Screen Typer: ON"
STATUS_STOPPED = "Screen Typer: OFF"


class _MenuController(NSObject):
    def initWithStatusItem_watchLoop_(self, status_item, watch_loop):
        self = objc.super(_MenuController, self).init()
        if self is not None:
            self._status_item = status_item
            self._watch_loop = watch_loop
        return self

    def toggle_(self, sender):
        self._watch_loop.toggle()
        self._status_item.button().setTitle_(
            STATUS_RUNNING if self._watch_loop.is_running else STATUS_STOPPED
        )

    def quit_(self, sender):
        NSApplication.sharedApplication().terminate_(self)


def _ensure_permissions() -> None:
    if not AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True}):
        print(
            "Accessibility permission required. Grant it in System Settings > "
            "Privacy & Security > Accessibility, then relaunch.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not CGPreflightScreenCaptureAccess():
        CGRequestScreenCaptureAccess()
        print(
            "Screen Recording permission required. Grant it in System Settings > "
            "Privacy & Security > Screen Recording, then relaunch.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    _ensure_permissions()

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
    status_item.button().setTitle_(STATUS_STOPPED)

    print("Select the capture region: drag a rectangle over the word fall path.")
    region = pick_region()
    print(f"Region selected: {region}")

    watch_loop = WatchLoop(region)

    controller = _MenuController.alloc().initWithStatusItem_watchLoop_(status_item, watch_loop)

    menu = NSMenu.alloc().init()
    toggle_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Start/Stop", "toggle:", ""
    )
    toggle_item.setTarget_(controller)
    menu.addItem_(toggle_item)
    menu.addItem_(NSMenuItem.separatorItem())
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "quit:", "q")
    quit_item.setTarget_(controller)
    menu.addItem_(quit_item)
    status_item.setMenu_(menu)

    register_toggle_hotkey(lambda: controller.toggle_(None))
    print("Ready. Press Cmd+Option+T to start/stop the watch loop, or use the menu bar item.")

    app.run()


if __name__ == "__main__":
    main()
