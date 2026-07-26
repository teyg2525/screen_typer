"""py2app build config: `python setup.py py2app` produces dist/Screen Typer.app"""

from setuptools import setup

APP = ["screen_typer/main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "packages": ["screen_typer"],
    "plist": {
        "CFBundleName": "Screen Typer",
        "CFBundleDisplayName": "Screen Typer",
        "CFBundleIdentifier": "com.screentyper.app",
        "LSUIElement": True,
        "NSScreenCaptureUsageDescription": (
            "Screen Typer needs to capture a screen region to read falling words."
        ),
        "NSAppleEventsUsageDescription": (
            "Screen Typer needs Accessibility access to type recognized words."
        ),
    },
}

setup(
    app=APP,
    name="Screen Typer",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
