# Screen Typer

Watches a screen region for falling words (e.g. in a typing game) and types
each newly-recognized word automatically via native OCR + synthetic
keystrokes, so you don't have to.

## How it works

1. On launch, drag out a rectangle covering the word's fall path (from where
   it spawns near the top to near where it disappears).
2. Press **Cmd+Option+T** to start the watch loop. It repeatedly captures the
   region, runs OCR (macOS Vision framework), and types out any word it
   hasn't typed in the last few seconds — so a word falling through several
   capture cycles is typed exactly once.
3. Press **Cmd+Option+T** again to stop.
4. Keep the target game window focused — keystrokes go wherever OS focus
   currently is; the app does not target a specific window.

A menu bar item shows `Screen Typer: ON` / `Screen Typer: OFF`.

## Requirements

- macOS 14+ (uses ScreenCaptureKit's `SCScreenshotManager`, available since
  macOS 14).
- Python 3.10+ (project uses a `.venv` with Homebrew Python 3.10; system
  Python 3.9 from Xcode command line tools is not sufficient for py2app's
  needs).

## Setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running (development)

```bash
source .venv/bin/activate
python -m screen_typer.main
```

On first run you'll be prompted for:
- **Accessibility** (System Settings > Privacy & Security > Accessibility) —
  needed for the global hotkey and to simulate keystrokes.
- **Screen Recording** (System Settings > Privacy & Security > Screen
  Recording) — needed to capture the region.

Grant both, then relaunch. During development these permissions are granted
to your terminal app (or to `python3.10` itself); when you build and run the
packaged `.app` (below), you'll need to grant them again to that bundle
specifically — macOS ties TCC permissions to the exact binary identity.

## Building a standalone .app

```bash
source .venv/bin/activate
python setup.py py2app
open "dist/Screen Typer.app"
```

Test against the built `.app`, not the dev script — permission grants and
behavior can differ once bundled.

## Project layout

- `screen_typer/main.py` — entrypoint: permission checks, region picker,
  hotkey registration, menu bar status item.
- `screen_typer/region_picker.py` — full-screen drag-to-select overlay.
- `screen_typer/watch_loop.py` — capture → OCR → dedup → type loop, run on a
  background thread.
- `screen_typer/dedup.py` — TTL-based tracker so a word is typed once even
  while visible across multiple capture cycles.
- `screen_typer/hotkey.py` — global hotkey (default Cmd+Option+T) via
  `quickmachotkey`.
- `screen_typer/platform_macos/` — the only OS-specific package:
  - `capture.py` — `ScreenCaptureKit` region capture.
  - `ocr.py` — `Vision` framework `VNRecognizeTextRequest` (fast recognition
    level, language correction off, for low latency on short word blobs).
  - `keystrokes.py` — `CGEvent`-based Unicode text injection.

## Windows portability

Not built yet, but the codebase is structured for it: everything outside
`platform_macos/` (dedup logic, watch loop orchestration, region picking)
is already OS-agnostic. A Windows port would add a `platform_windows/`
package with the same three-function interface (`capture_frame`,
`recognize_text`, `type_text`), backed by:
- `winrt Windows.Media.Ocr` for native OCR
- `mss` for region screenshots
- `pynput` for the global hotkey and keystroke simulation

then a `platform.system()` switch in `main.py` to select the right module —
no changes needed to `watch_loop.py` or `dedup.py`.

## Tuning

- `POLL_INTERVAL_SECONDS` in `watch_loop.py` controls capture frequency
  (default ~12fps).
- `DEDUP_TTL_SECONDS` in `watch_loop.py` controls how long a word is
  remembered as "already typed" — should comfortably exceed how long a word
  stays visible while falling through the capture region.
- `DEFAULT_COMBO` in `hotkey.py` controls the start/stop hotkey.
