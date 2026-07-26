"""Full-screen click-drag overlay for selecting the capture region."""

import objc
from AppKit import (
    NSApp,
    NSBezierPath,
    NSColor,
    NSEvent,
    NSRectFill,
    NSScreen,
    NSView,
    NSWindow,
    NSWindowStyleMaskBorderless,
    NSBackingStoreBuffered,
    NSFloatingWindowLevel,
)
from Foundation import NSMakeRect


class _SelectionView(NSView):
    def initWithFrame_onComplete_(self, frame, on_complete):
        self = objc.super(_SelectionView, self).initWithFrame_(frame)
        if self is None:
            result = None
        else:
            self._on_complete = on_complete
            self._start_point = None
            self._current_rect = None
            result = self
        return result

    def mouseDown_(self, event):
        self._start_point = self.convertPoint_fromView_(event.locationInWindow(), None)
        self._current_rect = NSMakeRect(self._start_point.x, self._start_point.y, 0, 0)

    def mouseDragged_(self, event):
        current_point = self.convertPoint_fromView_(event.locationInWindow(), None)
        x = min(self._start_point.x, current_point.x)
        y = min(self._start_point.y, current_point.y)
        width = abs(current_point.x - self._start_point.x)
        height = abs(current_point.y - self._start_point.y)
        self._current_rect = NSMakeRect(x, y, width, height)
        self.setNeedsDisplay_(True)

    def mouseUp_(self, event):
        rect = self._current_rect
        self._on_complete(rect)

    def drawRect_(self, dirty_rect):
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.25).set()
        NSRectFill(self.bounds())
        if self._current_rect is not None:
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.6, 1.0, 0.25).set()
            NSBezierPath.fillRect_(self._current_rect)
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.6, 1.0, 1.0).set()
            path = NSBezierPath.bezierPathWithRect_(self._current_rect)
            path.setLineWidth_(2.0)
            path.stroke()


def pick_region() -> tuple[float, float, float, float]:
    """Blocks (spinning the run loop) until the user drags out a rectangle.

    Returns (x, y, width, height) in screen points with a top-left origin,
    matching the coordinate convention ScreenCaptureKit's sourceRect expects.
    """
    screen = NSScreen.mainScreen()
    screen_frame = screen.frame()

    result_holder: dict = {}

    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        screen_frame, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
    )
    window.setLevel_(NSFloatingWindowLevel)
    window.setOpaque_(False)
    window.setBackgroundColor_(NSColor.clearColor())
    window.setIgnoresMouseEvents_(False)

    def on_complete(rect_bottom_left_origin):
        screen_height = screen_frame.size.height
        x = rect_bottom_left_origin.origin.x
        width = rect_bottom_left_origin.size.width
        height = rect_bottom_left_origin.size.height
        y_top_left = screen_height - rect_bottom_left_origin.origin.y - height
        result_holder["region"] = (x, y_top_left, width, height)
        window.close()
        NSApp().stopModal()

    view = _SelectionView.alloc().initWithFrame_onComplete_(
        NSMakeRect(0, 0, screen_frame.size.width, screen_frame.size.height), on_complete
    )
    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)

    NSApp().runModalForWindow_(window)

    if "region" not in result_holder:
        raise RuntimeError("Region selection was cancelled")

    return result_holder["region"]
