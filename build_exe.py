"""Build script to create a standalone .exe of the Among Us Mod Manager."""
import PyInstaller.__main__
import os
import shutil

APP_NAME = "AmongUsModManager"
SCRIPT = "main.py"
ICON = None  # No icon for now

# Clean old build
for d in ["build", "dist"]:
    if os.path.exists(d):
        shutil.rmtree(d)

args = [
    SCRIPT,
    "--name", APP_NAME,
    "--onefile",
    "--windowed",  # No console window
    "--noconfirm",
    # Include the custom mod DLL
    "--add-data", "custom_mod/bin/Release/net6.0/CustomMod.dll;custom_mod/bin/Release/net6.0",
    # Include core and gui modules
    "--hidden-import", "customtkinter",
    "--hidden-import", "core",
    "--hidden-import", "gui",
    "--collect-all", "customtkinter",
]

if ICON and os.path.exists(ICON):
    args.extend(["--icon", ICON])

print(f"Building {APP_NAME}.exe...")
PyInstaller.__main__.run(args)
print(f"\nDone! Exe is at: dist/{APP_NAME}.exe")
