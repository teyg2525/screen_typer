"""Full-screen click-drag overlay for selecting the capture region."""

import tkinter as tk


def pick_region() -> tuple[float, float, float, float]:
    """Blocks until the user drags out a rectangle or presses Escape to cancel.

    Returns (x, y, width, height) in screen points with a top-left origin,
    matching the coordinate convention the capture backend expects.
    """
    result_holder: dict = {}

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.25)
    root.attributes("-topmost", True)
    root.configure(bg="black")
    root.config(cursor="cross")

    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    state = {"start_x": None, "start_y": None, "rect_id": None}

    def on_mouse_down(event):
        state["start_x"] = event.x_root
        state["start_y"] = event.y_root
        state["rect_id"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#3399FF", width=2
        )

    def on_mouse_drag(event):
        if state["rect_id"] is not None:
            start_x = state["start_x"] - root.winfo_rootx()
            start_y = state["start_y"] - root.winfo_rooty()
            canvas.coords(state["rect_id"], start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        end_x, end_y = event.x_root, event.y_root
        x = min(state["start_x"], end_x)
        y = min(state["start_y"], end_y)
        width = abs(end_x - state["start_x"])
        height = abs(end_y - state["start_y"])
        if width > 2 and height > 2:
            result_holder["region"] = (x, y, width, height)
        root.destroy()

    def on_escape(event):
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    root.bind("<Escape>", on_escape)

    root.mainloop()

    if "region" not in result_holder:
        raise RuntimeError("Region selection was cancelled")

    return result_holder["region"]
