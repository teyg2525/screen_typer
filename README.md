# Screen Typer

Watches a screen region for falling words (e.g. in a typing game) and types
each newly-recognized word automatically via native OCR + synthetic
keystrokes, so you don't have to.

Runs on macOS and Windows, using each OS's native OCR engine.

## How it works

1. On launch, drag out a rectangle covering the word's fall path (from where
   it spawns near the top to near where it disappears).
2. Press the hotkey (**Cmd+Option+T** on macOS, **Ctrl+Alt+T** on Windows) to
   start the watch loop. It repeatedly captures the region, runs OCR (Vision
   on macOS, Windows.Media.Ocr on Windows), and types out any word it hasn't
   typed in the last few seconds — so a word falling through several capture
   cycles is typed exactly once.
3. Press the hotkey again to stop.
4. Keep the target game window focused — keystrokes go wherever OS focus
   currently is; the app does not target a specific window.

macOS shows a menu bar item (`Screen Typer: ON` / `Screen Typer: OFF`) with a
Start/Stop and Quit menu. Windows shows an equivalent system tray icon.

## Project layout

- `screen_typer/main.py` — cross-platform entrypoint; dispatches to
  `main_macos.py` or `main_windows.py` based on `platform.system()`.
- `screen_typer/watch_loop.py` — capture → OCR → dedup → type loop, run on a
  background thread. Picks the platform backend at import time.
- `screen_typer/dedup.py` — TTL-based tracker so a word is typed once even
  while visible across multiple capture cycles.
- `screen_typer/text_observation.py` — shared OCR result type returned by
  both platform backends.
- `screen_typer/platform_macos/` — macOS backend:
  - `capture.py` — `ScreenCaptureKit` region capture.
  - `ocr.py` — `Vision` framework `VNRecognizeTextRequest` (fast recognition
    level, language correction off, for low latency on short word blobs).
  - `keystrokes.py` — `CGEvent`-based Unicode text injection.
  - `hotkey.py` — global hotkey (default Cmd+Option+T) via `quickmachotkey`.
  - `region_picker.py` — full-screen drag-to-select overlay (AppKit).
- `screen_typer/main_macos.py` — permission checks, region picker, hotkey
  registration, menu bar status item.
- `screen_typer/platform_windows/` — Windows backend:
  - `capture.py` — region screenshots via `mss`.
  - `ocr.py` — `Windows.Media.Ocr` via `winrt`.
  - `keystrokes.py` — Unicode text injection via `pynput`.
  - `hotkey.py` — global hotkey (default Ctrl+Alt+T) via `pynput`.
  - `region_picker.py` — full-screen drag-to-select overlay (Tkinter).
- `screen_typer/main_windows.py` — region picker, hotkey registration, system
  tray icon (`pystray`).

## macOS

### Requirements

- macOS 14+ (uses ScreenCaptureKit's `SCScreenshotManager`, available since
  macOS 14).
- Python 3.10+ (project uses a `.venv` with Homebrew Python 3.10; system
  Python 3.9 from Xcode command line tools is not sufficient for py2app's
  needs).

### Setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running (development)

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

### Building a standalone .app

```bash
source .venv/bin/activate
python setup.py py2app
open "dist/Screen Typer.app"
```

Test against the built `.app`, not the dev script — permission grants and
behavior can differ once bundled.

## Windows

### Requirements

- Windows 10 (with the OCR language pack for your target language installed
  via Settings > Time & Language > Language, e.g. English) or Windows 11.
- Python 3.10+ (from python.org or the Microsoft Store).

### Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Running

```powershell
.venv\Scripts\activate
python -m screen_typer.main
```

No special OS permission prompts are required on Windows (unlike macOS's
TCC/Accessibility/Screen Recording gates) — `mss` and `pynput` work without
elevation for a normal desktop session.

This backend has not been runtime-tested on an actual Windows machine yet;
the implementation is based on documented `winrt`/`mss`/`pynput`/`pystray`
APIs. If you hit issues, check:
- `winrt-Windows.Media.Ocr` and friends installed correctly (`pip show
  winrt-Windows.Media.Ocr`).
- The OCR language pack is installed, otherwise `OcrEngine.try_create_from_language`
  will return `None` and no text will be recognized.
- Antivirus/Defender flagging synthetic keystrokes from `pynput` — some
  security software treats programmatic key injection as suspicious by
  default.

### Packaging (not yet set up)

There is no `PyInstaller`/`cx_Freeze` build script for Windows yet — for now,
run from source via `python -m screen_typer.main`. `PyInstaller` is the
natural choice if/when a standalone `.exe` is needed, similar to how
`py2app` bundles the macOS build.

## Tuning

- `POLL_INTERVAL_SECONDS` in `watch_loop.py` controls capture frequency
  (default ~12fps).
- `DEDUP_TTL_SECONDS` in `watch_loop.py` controls how long a word is
  remembered as "already typed" — should comfortably exceed how long a word
  stays visible while falling through the capture region.
- `DEFAULT_COMBO` in `platform_macos/hotkey.py` / `platform_windows/hotkey.py`
  controls the start/stop hotkey for each platform.
