"""
Among Us Mod Manager - Main Entry Point
A fully-featured mod manager for Among Us with BepInEx support.

Features:
  - Auto-detect Among Us installation (Steam / Epic Games)
  - Install, uninstall, enable, disable mods
  - BepInEx mod loader management
  - Mod profiles (save/load configurations)
  - Browse and download mods from GitHub
  - Mod backups and restore
  - Mod conflict detection
  - Dark/Light theme

Usage:
  python main.py
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
