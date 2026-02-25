"""
Among Us Mod Manager — Modern GUI using customtkinter.
Styled after the original MatuxGG Mod Manager.
"""

import os
import subprocess
import threading
import webbrowser
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.config import Settings, APP_NAME, APP_VERSION
from core.path_detector import detect_among_us_path, validate_among_us_path
from core.mod_manager import ModManager
from core.bepinex_manager import BepInExManager
from core.profiles import ProfileManager
from core.mod_browser import ModBrowser
from core.mod_catalog import ModCatalog, CatalogMod

# Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

RED = "#c0392b"
RED_HOVER = "#e74c3c"
GREEN = "#00b894"
GREEN_HOVER = "#00d4aa"
ORANGE = "#e67e22"
BLUE = "#0984e3"
DARK_BG = "#0b0e17"
CARD_BG = "#141b2d"
CARD_HOVER = "#1c2640"
SIDEBAR_BG = "#0f1623"
TEXT_DIM = "#5a6580"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = Settings()

        self.title("Among Us Mod Manager")
        w = self.settings.get("window_width", 1100)
        h = self.settings.get("window_height", 720)
        self.geometry(f"{w}x{h}")
        self.minsize(900, 580)

        # Systems
        self.mod_manager = None
        self.bepinex_manager = None
        self.profile_manager = ProfileManager()
        self.mod_browser = ModBrowser()
        self.catalog = ModCatalog()
        self.collapsed: set[str] = set()
        self._busy = False

        self._init_game_path()
        self._build_ui()
        self.after(200, self._on_start)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_game_path(self):
        path = self.settings.get("among_us_path", "")
        if not path or not validate_among_us_path(path):
            path = detect_among_us_path()
            if path:
                self.settings.set("among_us_path", path)
        if path and validate_among_us_path(path):
            self.mod_manager = ModManager(path)
            self.bepinex_manager = BepInExManager(path)

    # ═══════════════════════════════════════
    # BUILD UI
    # ═══════════════════════════════════════
    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()
        self._build_statusbar()

    def _build_header(self):
        header = ctk.CTkFrame(self, height=60, fg_color="#0d1321", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20)

        ctk.CTkLabel(title_frame, text="AMONG US", font=("Segoe UI Black", 20),
                      text_color=RED).pack(side="left")
        ctk.CTkLabel(title_frame, text="  MOD MANAGER", font=("Segoe UI", 16),
                      text_color="#e8eaf0").pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=20)

        ctk.CTkButton(btn_frame, text="LAUNCH GAME", font=("Segoe UI", 13, "bold"),
                       fg_color=GREEN, hover_color=GREEN_HOVER, text_color="white",
                       height=38, width=160, corner_radius=8,
                       command=self._launch_game).pack(side="right", padx=5)

        ctk.CTkButton(btn_frame, text="UPDATE MODS", font=("Segoe UI", 13, "bold"),
                       fg_color=RED, hover_color=RED_HOVER, text_color="white",
                       height=38, width=160, corner_radius=8,
                       command=self._update_mods).pack(side="right", padx=5)

        ctk.CTkButton(btn_frame, text="Settings", font=("Segoe UI", 11),
                       fg_color="#1e2940", hover_color="#2a3a55", text_color="#8892a8",
                       height=34, width=90, corner_radius=8,
                       command=self._open_settings).pack(side="right", padx=5)

        # Red accent line
        ctk.CTkFrame(self, height=2, fg_color=RED, corner_radius=0).grid(
            row=0, column=0, sticky="sew")

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=DARK_BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_sidebar(body)
        self._build_main(body)

    def _build_sidebar(self, parent):
        sb = ctk.CTkFrame(parent, width=210, fg_color=SIDEBAR_BG, corner_radius=0)
        sb.grid(row=0, column=0, sticky="ns")
        sb.grid_propagate(False)

        scroll = ctk.CTkScrollableFrame(sb, fg_color=SIDEBAR_BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Sort ──
        self._section(scroll, "SORT BY")
        self.sort_var = ctk.StringVar(value="category")
        for val, label in [("category","Category"),("name","Name"),
                           ("author","Author"),("installed","Installed"),("stars","Popular")]:
            ctk.CTkRadioButton(scroll, text=label, variable=self.sort_var, value=val,
                                font=("Segoe UI", 12), text_color="#8892a8",
                                fg_color=RED, hover_color=RED_HOVER,
                                border_color="#2a3650",
                                command=self._render).pack(anchor="w", padx=16, pady=2)

        self._divider(scroll)

        # ── Share Code ──
        self._section(scroll, "SHARE CONFIG")
        self.share_entry = ctk.CTkEntry(scroll, font=("Consolas", 11), height=32,
                                         fg_color="#0d1220", border_color="#1e2940")
        self.share_entry.pack(fill="x", padx=16, pady=(0, 6))

        share_row = ctk.CTkFrame(scroll, fg_color="transparent")
        share_row.pack(fill="x", padx=16)
        ctk.CTkButton(share_row, text="Copy", height=28, font=("Segoe UI", 11),
                       fg_color="#1e2940", hover_color="#2a3a55", text_color="#8892a8",
                       corner_radius=6, command=self._copy_code).pack(side="left", expand=True, fill="x", padx=(0,3))
        ctk.CTkButton(share_row, text="Apply", height=28, font=("Segoe UI", 11),
                       fg_color=RED, hover_color=RED_HOVER, corner_radius=6,
                       command=self._apply_code).pack(side="left", expand=True, fill="x", padx=(3,0))

        self._divider(scroll)

        # ── Actions ──
        self._section(scroll, "ACTIONS")
        for text, cmd in [
            ("Install from File...", self._install_from_file),
            ("Remove All Mods", self._remove_all),
            ("Backup Mods", self._backup),
            ("Restore Backup...", self._restore),
        ]:
            ctk.CTkButton(scroll, text=text, height=30, font=("Segoe UI", 11),
                           fg_color="transparent", hover_color="#1c2a42",
                           text_color="#8892a8", anchor="w",
                           corner_radius=6, command=cmd).pack(fill="x", padx=12, pady=1)

        self._divider(scroll)

        # ── Profiles ──
        self._section(scroll, "PROFILES")
        prow = ctk.CTkFrame(scroll, fg_color="transparent")
        prow.pack(fill="x", padx=16, pady=(0, 6))
        self.profile_var = ctk.StringVar()
        ctk.CTkEntry(prow, textvariable=self.profile_var, height=28,
                      font=("Segoe UI", 11), fg_color="#0d1220",
                      border_color="#1e2940").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(prow, text="Save", width=50, height=28, font=("Segoe UI", 11),
                       fg_color=GREEN, hover_color=GREEN_HOVER, corner_radius=6,
                       command=self._save_profile).pack(side="left", padx=(6,0))

        self.profiles_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.profiles_frame.pack(fill="x", padx=16)

        # ── Bottom status ──
        bottom = ctk.CTkFrame(sb, fg_color=SIDEBAR_BG, corner_radius=0)
        bottom.pack(side="bottom", fill="x", padx=12, pady=12)

        self.bep_label = ctk.CTkLabel(bottom, text="BepInEx: --", font=("Segoe UI", 11),
                                       text_color=TEXT_DIM)
        self.bep_label.pack(anchor="w")
        self.game_label = ctk.CTkLabel(bottom, text="Game: --", font=("Segoe UI", 11),
                                        text_color=TEXT_DIM)
        self.game_label.pack(anchor="w", pady=(2,0))

        ctk.CTkButton(bottom, text="Install BepInEx", height=32,
                       font=("Segoe UI", 11, "bold"),
                       fg_color=ORANGE, hover_color="#f0932b", corner_radius=6,
                       command=self._install_bepinex).pack(fill="x", pady=(8,0))

    def _build_main(self, parent):
        main = ctk.CTkFrame(parent, fg_color=DARK_BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Toolbar
        tb = ctk.CTkFrame(main, height=44, fg_color="#111827", corner_radius=0)
        tb.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(tb, text="Mods", font=("Segoe UI", 15, "bold")).pack(side="left", padx=16)
        self.count_label = ctk.CTkLabel(tb, text="", font=("Segoe UI", 11),
                                         text_color=TEXT_DIM)
        self.count_label.pack(side="left", padx=8)

        ctk.CTkButton(tb, text="Select None", width=80, height=28, font=("Segoe UI", 10),
                       fg_color="transparent", hover_color="#1e2940",
                       text_color=TEXT_DIM, corner_radius=6,
                       command=self._select_none).pack(side="right", padx=4, pady=6)
        ctk.CTkButton(tb, text="Select All", width=80, height=28, font=("Segoe UI", 10),
                       fg_color="transparent", hover_color="#1e2940",
                       text_color=TEXT_DIM, corner_radius=6,
                       command=self._select_all).pack(side="right", padx=4, pady=6)
        ctk.CTkButton(tb, text="Refresh", width=80, height=28, font=("Segoe UI", 10),
                       fg_color=BLUE, hover_color="#2d9cef", corner_radius=6,
                       command=self._refresh_catalog).pack(side="right", padx=4, pady=6)

        # Scrollable mod list
        self.mod_scroll = ctk.CTkScrollableFrame(main, fg_color=DARK_BG, corner_radius=0)
        self.mod_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.mod_scroll.grid_columnconfigure(0, weight=1)

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=34, fg_color="#111827", corner_radius=0)
        bar.grid(row=2, column=0, sticky="ew")

        self.progress = ctk.CTkProgressBar(bar, width=200, height=8,
                                            fg_color="#1a2438", progress_color=RED,
                                            corner_radius=4)
        self.progress.pack(side="left", padx=12, pady=10)
        self.progress.set(0)

        self.status_lbl = ctk.CTkLabel(bar, text="Ready", font=("Segoe UI", 11),
                                        text_color="#8892a8")
        self.status_lbl.pack(side="left", padx=8)

        ctk.CTkLabel(bar, text=f"v{APP_VERSION}", font=("Segoe UI", 10),
                      text_color=TEXT_DIM).pack(side="right", padx=12)

    # Helpers
    def _section(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 10, "bold"),
                      text_color=TEXT_DIM).pack(anchor="w", padx=16, pady=(12, 4))

    def _divider(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color="#1a2438").pack(fill="x", padx=16, pady=8)

    # ═══════════════════════════════════════
    # RENDER MOD LIST
    # ═══════════════════════════════════════
    def _render(self):
        for w in self.mod_scroll.winfo_children():
            w.destroy()

        mods = self.catalog.get_mods()
        if not mods:
            ctk.CTkLabel(self.mod_scroll, text="Click 'Refresh' to load the mod catalog.",
                          font=("Segoe UI", 13), text_color=TEXT_DIM).pack(pady=60)
            return

        total = len(mods)
        installed = sum(1 for m in mods if m.installed)
        selected = sum(1 for m in mods if m.selected)
        self.count_label.configure(text=f"{total} mods · {installed} installed · {selected} selected")

        sort = self.sort_var.get()
        if sort == "category":
            for cat in self.catalog.get_categories():
                cat_mods = [m for m in mods if m.category == cat]
                if not cat_mods:
                    continue
                self._render_cat_header(cat, cat_mods)
                if cat not in self.collapsed:
                    for mod in cat_mods:
                        self._render_mod(mod)
        else:
            self.catalog.sort_mods(sort)
            for mod in mods:
                self._render_mod(mod)

    def _render_cat_header(self, cat, cat_mods):
        is_collapsed = cat in self.collapsed
        inst = sum(1 for m in cat_mods if m.installed)
        arrow = "▶" if is_collapsed else "▼"

        btn = ctk.CTkButton(
            self.mod_scroll,
            text=f"  {arrow}   {cat.upper()}   ({inst}/{len(cat_mods)})",
            font=("Segoe UI", 12, "bold"), anchor="w", height=36,
            fg_color="#111827", hover_color="#1c2640",
            text_color="#e8eaf0", corner_radius=6,
            command=lambda c=cat: self._toggle_cat(c),
        )
        btn.pack(fill="x", padx=8, pady=(10, 2))

    def _render_mod(self, mod: CatalogMod):
        card_color = CARD_BG if mod.installed else "#0e1525"

        card = ctk.CTkFrame(self.mod_scroll, fg_color=card_color, corner_radius=8,
                             border_width=1, border_color="#1e2940" if not mod.installed else GREEN)
        card.pack(fill="x", padx=8, pady=2)
        card.grid_columnconfigure(1, weight=1)

        # Left: green bar for installed
        if mod.installed:
            ctk.CTkFrame(card, width=4, fg_color=GREEN, corner_radius=2).pack(
                side="left", fill="y", padx=(0, 0), pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=8)
        inner.grid_columnconfigure(1, weight=1)

        # Checkbox
        var = ctk.BooleanVar(value=mod.selected)
        cb = ctk.CTkCheckBox(inner, text="", variable=var, width=24,
                              fg_color=RED, hover_color=RED_HOVER,
                              border_color="#2a3650", checkbox_width=20, checkbox_height=20,
                              command=lambda m=mod, v=var: self._on_check(m, v))
        cb.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="n", pady=4)

        # Top row: name + badges
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(top, text=mod.name, font=("Segoe UI", 13, "bold"),
                      text_color="#e8eaf0").pack(side="left")

        if mod.installed:
            v = f"INSTALLED v{mod.installed_version}" if mod.installed_version else "INSTALLED"
            ctk.CTkLabel(top, text=f" {v} ", font=("Segoe UI", 9, "bold"),
                          text_color="white", fg_color=GREEN,
                          corner_radius=4).pack(side="left", padx=(8, 0))

        if mod.has_update:
            ctk.CTkLabel(top, text=f" UPDATE {mod.version} ", font=("Segoe UI", 9, "bold"),
                          text_color="white", fg_color=ORANGE,
                          corner_radius=4).pack(side="left", padx=(4, 0))

        # Right buttons
        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(side="right")

        if mod.download_url or (hasattr(mod, 'local_dll') and mod.local_dll):
            btn_text = "Install" if (hasattr(mod, 'local_dll') and mod.local_dll) else "Download"
            ctk.CTkButton(btn_frame, text=btn_text, width=80, height=26,
                           font=("Segoe UI", 10, "bold"),
                           fg_color=GREEN, hover_color=GREEN_HOVER, corner_radius=6,
                           command=lambda m=mod: self._download_single(m)).pack(side="left", padx=2)

        if mod.repo_url:
            ctk.CTkButton(btn_frame, text="GitHub", width=60, height=26,
                           font=("Segoe UI", 10),
                           fg_color="#1e2940", hover_color="#2a3a55",
                           text_color="#8892a8", corner_radius=6,
                           command=lambda m=mod: webbrowser.open(m.repo_url)).pack(side="left", padx=2)

        if mod.installed:
            ctk.CTkButton(btn_frame, text="Remove", width=65, height=26,
                           font=("Segoe UI", 10),
                           fg_color=RED, hover_color=RED_HOVER, corner_radius=6,
                           command=lambda m=mod: self._remove_single(m)).pack(side="left", padx=2)

        # Details line
        parts = [f"by {mod.author}"]
        if mod.version:
            parts.append(f"v{mod.version}")
        if mod.size_str:
            parts.append(mod.size_str)
        if mod.stars:
            parts.append(f"★ {mod.stars}")
        if mod.download_count:
            parts.append(f"{mod.download_count:,} downloads")

        detail_frame = ctk.CTkFrame(inner, fg_color="transparent")
        detail_frame.grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(detail_frame, text="  ·  ".join(parts),
                      font=("Segoe UI", 10), text_color=TEXT_DIM).pack(anchor="w")

        if mod.description:
            ctk.CTkLabel(detail_frame, text=mod.description, font=("Segoe UI", 10),
                          text_color="#8892a8", wraplength=550,
                          justify="left").pack(anchor="w", pady=(2, 0))

        if mod.dependencies:
            dep_names = []
            for dep_id in mod.dependencies:
                dep = self.catalog.get_mod_by_id(dep_id)
                dep_names.append(dep.name if dep else dep_id)
            ctk.CTkLabel(detail_frame, text="Requires: " + ", ".join(dep_names),
                          font=("Segoe UI", 9), text_color=ORANGE,
                          wraplength=550).pack(anchor="w", pady=(1, 0))

    # ═══════════════════════════════════════
    # MOD OPERATIONS
    # ═══════════════════════════════════════
    def _on_check(self, mod, var):
        mod.selected = var.get()
        sel = sum(1 for m in self.catalog.get_mods() if m.selected)
        inst = sum(1 for m in self.catalog.get_mods() if m.installed)
        self.count_label.configure(
            text=f"{len(self.catalog.get_mods())} mods · {inst} installed · {sel} selected")

    def _install_single_mod(self, mod):
        """Download and install a single mod. Called from worker threads."""
        import shutil

        # Handle local/built-in mods (like Pebbleford's Mod)
        if hasattr(mod, 'local_dll') and mod.local_dll:
            import sys
            # Try multiple locations: PyInstaller bundle, app directory, script directory
            candidates = []
            # PyInstaller _MEIPASS (bundled exe)
            if hasattr(sys, '_MEIPASS'):
                candidates.append(os.path.join(sys._MEIPASS, mod.local_dll))
                candidates.append(os.path.join(sys._MEIPASS, os.path.basename(mod.local_dll)))
            # Directory of the exe / script
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            candidates.append(os.path.join(app_dir, mod.local_dll))
            candidates.append(os.path.join(app_dir, os.path.basename(mod.local_dll)))
            # Source directory
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidates.append(os.path.join(src_dir, mod.local_dll))

            local_path = None
            for c in candidates:
                if os.path.exists(c):
                    local_path = c
                    break

            if local_path:
                self._status(f"Installing {mod.name} (built-in)...")
                plugins_dir = os.path.join(self.settings.get("among_us_path", ""), "BepInEx", "plugins")
                os.makedirs(plugins_dir, exist_ok=True)
                dest = os.path.join(plugins_dir, os.path.basename(local_path))
                shutil.copy2(local_path, dest)
                self.catalog.mark_installed(mod.id, mod.version or "1.0.0")
                mod.selected = True
                return
            else:
                raise RuntimeError(f"Built-in mod DLL not found. Tried: {candidates}")

        from core.mod_browser import OnlineMod

        if not mod.download_url:
            # Try fetching release info if we don't have a URL yet
            self._status(f"Fetching info for {mod.name}...")
            self.catalog.fetch_release_info(mod)
        if not mod.download_url:
            raise RuntimeError(f"No download URL for {mod.name}")

        self._status(f"Downloading {mod.name}...")
        om = OnlineMod(name=mod.name, author=mod.author, description=mod.description,
                       version=mod.version, download_url=mod.download_url,
                       repo_url=mod.repo_url, file_size=mod.file_size)
        local = self.mod_browser.download_mod(om,
            progress_callback=lambda t, v: self._status(t))
        self._status(f"Installing {mod.name}...")
        self.mod_manager.install_mod(local, mod_name=mod.name, version=mod.version,
                                     author=mod.author, description=mod.description,
                                     source_url=mod.repo_url)
        self.catalog.mark_installed(mod.id, mod.version)
        mod.selected = True

    def _download_single(self, mod):
        if not self._check_ready():
            return
        if self._busy:
            return
        self._busy = True

        def do():
            try:
                # Resolve dependencies first
                deps = self.catalog.get_dependencies(mod)
                all_to_install = deps + [mod]
                total = len(all_to_install)

                for i, m in enumerate(all_to_install):
                    if m.installed:
                        continue
                    if m.id != mod.id:
                        self._status(f"Installing dependency: {m.name}...")
                    self._prog((i) / total)
                    self._install_single_mod(m)
                    self._prog((i + 1) / total)

                self._status(f"Installed {mod.name}!" + (f" (+{len(deps)} dependencies)" if deps else ""))
                self._prog(1.0)
                self._detect_installed()
                self.after(300, self._render)
                self.after(2000, lambda: self._prog(0))
            except Exception as e:
                self._status(f"Error: {e}")
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self._busy = False

        threading.Thread(target=do, daemon=True).start()

    def _update_mods(self):
        if not self._check_ready() or self._busy:
            return

        selected = self.catalog.get_selected_mods()
        all_mods = self.catalog.get_mods()
        to_install = [m for m in selected if not m.installed and m.download_url]
        to_remove = [m for m in all_mods if m.installed and not m.selected and m.id != "bepinex"]
        to_update = [m for m in selected if m.installed and m.has_update and m.download_url]

        # Resolve dependencies for all mods being installed
        dep_set = set()
        deps_to_install = []
        for mod in to_install:
            for dep in self.catalog.get_dependencies(mod):
                if dep.id not in dep_set and dep not in to_install:
                    dep_set.add(dep.id)
                    deps_to_install.append(dep)

        if not to_install and not to_remove and not to_update:
            messagebox.showinfo("No Changes", "Select or deselect mods, then click Update.")
            return

        parts = []
        if to_install:
            parts.append("INSTALL:\n" + "\n".join(f"  + {m.name}" for m in to_install))
        if deps_to_install:
            parts.append("DEPENDENCIES:\n" + "\n".join(f"  + {m.name} (required)" for m in deps_to_install))
        if to_update:
            parts.append("UPDATE:\n" + "\n".join(f"  ~ {m.name}" for m in to_update))
        if to_remove:
            parts.append("REMOVE:\n" + "\n".join(f"  - {m.name}" for m in to_remove))
        if not messagebox.askyesno("Update Mods", "\n\n".join(parts) + "\n\nProceed?"):
            return

        self._busy = True
        def do():
            all_installs = deps_to_install + to_install + to_update
            total = len(to_remove) + len(all_installs)
            done = 0

            for mod in to_remove:
                self._status(f"Removing {mod.name}...")
                try:
                    for im in self.mod_manager.get_installed_mods():
                        if mod.name.lower() in im.name.lower():
                            self.mod_manager.uninstall_mod(im)
                    self.catalog.mark_uninstalled(mod.id)
                except Exception as e:
                    self._status(f"Error: {e}")
                done += 1
                self._prog(done / total)

            for mod in all_installs:
                if mod.installed:
                    done += 1
                    continue
                try:
                    self._install_single_mod(mod)
                except Exception as e:
                    self._status(f"Error: {mod.name} - {e}")
                done += 1
                self._prog(done / total)

            self._detect_installed()
            self._status("Done! All mods updated.")
            self._prog(1.0)
            self.after(300, self._render)
            self.after(2500, lambda: self._prog(0))
            self._busy = False

        threading.Thread(target=do, daemon=True).start()

    def _remove_single(self, mod):
        if not self.mod_manager:
            return
        if not messagebox.askyesno("Remove", f"Remove '{mod.name}'?"):
            return
        for im in self.mod_manager.get_installed_mods():
            if mod.name.lower() in im.name.lower():
                self.mod_manager.uninstall_mod(im)
        self.catalog.mark_uninstalled(mod.id)
        self._status(f"Removed {mod.name}")
        self._render()

    def _remove_all(self):
        if not self.mod_manager:
            return
        if not messagebox.askyesno("Remove All", "Remove ALL mods?"):
            return
        for im in self.mod_manager.get_installed_mods():
            self.mod_manager.uninstall_mod(im)
        for m in self.catalog.get_mods():
            if m.installed:
                self.catalog.mark_uninstalled(m.id)
        self._status("All mods removed")
        self._render()

    def _select_all(self):
        for m in self.catalog.get_mods():
            m.selected = True
        self._render()

    def _select_none(self):
        for m in self.catalog.get_mods():
            m.selected = False
        self._render()

    def _toggle_cat(self, cat):
        if cat in self.collapsed:
            self.collapsed.discard(cat)
        else:
            self.collapsed.add(cat)
        self._render()

    # ═══════════════════════════════════════
    # CATALOG REFRESH
    # ═══════════════════════════════════════
    def _refresh_catalog(self):
        if self._busy:
            return
        self._busy = True
        def do():
            self._status("Fetching mod info from GitHub...")
            self.catalog.fetch_all_releases(
                progress_callback=lambda t, v: (self._status(t), self._prog(v)))
            self._detect_installed()
            self.catalog.check_updates()
            self._status("Catalog updated!")
            self._prog(1.0)
            self.after(300, self._render)
            self.after(2000, lambda: self._prog(0))
            self._busy = False
        threading.Thread(target=do, daemon=True).start()

    # ═══════════════════════════════════════
    # SHARE CODES
    # ═══════════════════════════════════════
    def _copy_code(self):
        code = self.catalog.generate_share_code()
        self.share_entry.delete(0, "end")
        self.share_entry.insert(0, code)
        self.clipboard_clear()
        self.clipboard_append(code)
        self._status("Code copied!")

    def _apply_code(self):
        code = self.share_entry.get().strip()
        if not code:
            return
        count = self.catalog.apply_share_code(code)
        self._status(f"Applied code: {count} mods selected")
        self._render()

    # ═══════════════════════════════════════
    # PROFILES
    # ═══════════════════════════════════════
    def _save_profile(self):
        name = self.profile_var.get().strip()
        if not name:
            return
        self.profile_manager.save_profile(name, [m.to_dict() for m in self.catalog.get_mods()])
        self.profile_var.set("")
        self._status(f"Profile saved: {name}")
        self._refresh_profiles()

    def _refresh_profiles(self):
        for w in self.profiles_frame.winfo_children():
            w.destroy()
        for p in self.profile_manager.list_profiles():
            row = ctk.CTkFrame(self.profiles_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkButton(row, text=p.name, height=24, font=("Segoe UI", 10),
                           fg_color="transparent", hover_color="#1c2a42",
                           text_color="#8892a8", anchor="w", corner_radius=4,
                           command=lambda pr=p: self._load_profile(pr)).pack(
                               side="left", fill="x", expand=True)
            ctk.CTkButton(row, text="✕", width=24, height=24, font=("Segoe UI", 10),
                           fg_color="transparent", hover_color=RED,
                           text_color=TEXT_DIM, corner_radius=4,
                           command=lambda pr=p: (
                               self.profile_manager.delete_profile(pr.name),
                               self._refresh_profiles())).pack(side="right")

    def _load_profile(self, profile):
        ids = set()
        for d in profile.mods:
            if d.get("selected", False) or d.get("installed", False):
                ids.add(d.get("id", ""))
        for m in self.catalog.get_mods():
            m.selected = m.id in ids
        self._status(f"Loaded: {profile.name}")
        self._render()

    # ═══════════════════════════════════════
    # BEPINEX / INSTALL / BACKUP
    # ═══════════════════════════════════════
    def _install_bepinex(self):
        if not self.bepinex_manager:
            messagebox.showwarning("No Game", "Set the Among Us path in Settings.")
            return
        if self._busy:
            return
        self._busy = True
        def do():
            self._status("Downloading BepInEx...")
            self._prog(0.1)
            ok = self.bepinex_manager.download_and_install(
                progress_callback=lambda t, v: (self._status(t), self._prog(v) if v >= 0 else None))
            self.after(0, self._update_sidebar)
            self._prog(0)
            if ok:
                self._status("BepInEx installed!")
                self.after(0, lambda: messagebox.showinfo("Done", "BepInEx installed!"))
            else:
                self._status("BepInEx failed")
                self.after(0, lambda: messagebox.showerror("Error", "Failed to install BepInEx."))
            self._busy = False
        threading.Thread(target=do, daemon=True).start()

    def _install_from_file(self):
        if not self._check_ready():
            return
        files = filedialog.askopenfilenames(title="Select mod files",
                                             filetypes=[("Mod files", "*.dll *.zip"), ("All", "*.*")])
        for f in files:
            try:
                m = self.mod_manager.install_mod(f)
                self._status(f"Installed: {m.name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        if files:
            self._render()

    def _backup(self):
        if not self.mod_manager:
            return
        try:
            p = self.mod_manager.backup_mods()
            messagebox.showinfo("Backup", f"Saved to:\n{p}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _restore(self):
        if not self.mod_manager:
            return
        backups = self.mod_manager.get_backups()
        if not backups:
            messagebox.showinfo("Backups", "No backups found.")
            return
        # Simple dialog
        names = [f"{b['name']} ({b['mod_count']} mods, {b['date']})" for b in backups]
        dialog = ctk.CTkInputDialog(text="Enter backup name to restore:\n\n" + "\n".join(names),
                                     title="Restore Backup")
        val = dialog.get_input()
        if val:
            for b in backups:
                if b["name"] in val or val in b["name"]:
                    self.mod_manager.restore_backup(b["path"])
                    self._status(f"Restored: {b['name']}")
                    self._render()
                    return

    # ═══════════════════════════════════════
    # LAUNCH / SETTINGS
    # ═══════════════════════════════════════
    def _launch_game(self):
        path = self.settings.get("among_us_path", "")
        if not path:
            messagebox.showwarning("No Game", "Set the path in Settings.")
            return
        exe = os.path.join(path, "Among Us.exe")
        if not os.path.exists(exe):
            messagebox.showerror("Not Found", f"Among Us.exe not at:\n{exe}")
            return
        try:
            subprocess.Popen([exe], cwd=path)
            self._status("Game launched!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_settings(self):
        win = ctk.CTkToplevel(self)
        win.title("Settings")
        win.geometry("560x400")
        win.transient(self)
        win.grab_set()
        win.after(100, win.lift)

        ctk.CTkLabel(win, text="Settings", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", padx=24, pady=(20, 16))

        # Path
        ctk.CTkLabel(win, text="Among Us Installation Path",
                      font=("Segoe UI", 12, "bold"), text_color="#8892a8").pack(
                          anchor="w", padx=24)
        prow = ctk.CTkFrame(win, fg_color="transparent")
        prow.pack(fill="x", padx=24, pady=(4, 16))

        pvar = ctk.StringVar(value=self.settings.get("among_us_path", ""))
        ctk.CTkEntry(prow, textvariable=pvar, font=("Segoe UI", 12), height=36).pack(
            side="left", fill="x", expand=True)
        ctk.CTkButton(prow, text="Browse", width=70, height=36,
                       fg_color="#1e2940", hover_color="#2a3a55", corner_radius=6,
                       command=lambda: pvar.set(
                           filedialog.askdirectory(title="Among Us folder") or pvar.get())
                       ).pack(side="left", padx=(6, 0))
        ctk.CTkButton(prow, text="Detect", width=70, height=36,
                       fg_color=BLUE, hover_color="#2d9cef", corner_radius=6,
                       command=lambda: pvar.set(detect_among_us_path() or pvar.get())
                       ).pack(side="left", padx=(6, 0))

        # BepInEx
        ctk.CTkLabel(win, text="BepInEx", font=("Segoe UI", 12, "bold"),
                      text_color="#8892a8").pack(anchor="w", padx=24, pady=(0, 4))
        brow = ctk.CTkFrame(win, fg_color="transparent")
        brow.pack(fill="x", padx=24, pady=(0, 16))
        ctk.CTkButton(brow, text="Install BepInEx", height=34, fg_color=GREEN,
                       hover_color=GREEN_HOVER, corner_radius=6,
                       command=lambda: (win.destroy(), self._install_bepinex())).pack(side="left")
        ctk.CTkButton(brow, text="Uninstall BepInEx", height=34, fg_color=RED,
                       hover_color=RED_HOVER, corner_radius=6,
                       command=lambda: self._uninstall_bep(win)).pack(side="left", padx=(8, 0))

        # Save
        def save():
            p = pvar.get().strip()
            if p and validate_among_us_path(p):
                self.settings.set("among_us_path", p)
                self.mod_manager = ModManager(p)
                self.bepinex_manager = BepInExManager(p)
                self._update_sidebar()
            elif p:
                messagebox.showwarning("Invalid", "Among Us.exe not found there.")
                return
            win.destroy()
            self._status("Settings saved")

        ctk.CTkButton(win, text="Save Settings", height=40, width=200,
                       font=("Segoe UI", 13, "bold"),
                       fg_color=RED, hover_color=RED_HOVER, corner_radius=8,
                       command=save).pack(pady=20)

    def _uninstall_bep(self, parent):
        if not self.bepinex_manager:
            return
        if messagebox.askyesno("Uninstall", "Remove BepInEx and ALL mods?", parent=parent):
            self.bepinex_manager.uninstall()
            self._update_sidebar()
            self._status("BepInEx removed")

    # ═══════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════
    def _check_ready(self):
        if not self.mod_manager:
            messagebox.showwarning("No Game", "Set the Among Us path in Settings.")
            return False
        if not self.bepinex_manager or not self.bepinex_manager.is_installed:
            messagebox.showwarning("BepInEx", "Install BepInEx first (sidebar).")
            return False
        return True

    def _status(self, t):
        self.after(0, lambda: self.status_lbl.configure(text=t))

    def _prog(self, v):
        self.after(0, lambda: self.progress.set(max(0, min(1, v))))

    def _update_sidebar(self):
        path = self.settings.get("among_us_path", "")
        if path:
            self.game_label.configure(text=f"Game: {os.path.basename(path)}", text_color=GREEN)
        else:
            self.game_label.configure(text="Game: Not set", text_color=RED)

        if self.bepinex_manager and self.bepinex_manager.is_installed:
            self.bep_label.configure(text="BepInEx: Installed", text_color=GREEN)
        else:
            self.bep_label.configure(text="BepInEx: Not installed", text_color=ORANGE)

    def _detect_installed(self):
        """Scan game files to detect which catalog mods are actually installed."""
        path = self.settings.get("among_us_path", "")
        if path:
            self.catalog.detect_installed_from_files(path)

    def _on_start(self):
        self._update_sidebar()
        self._refresh_profiles()
        self._detect_installed()
        has_versions = any(m.version for m in self.catalog.get_mods())
        if not has_versions:
            self._refresh_catalog()
        else:
            self._render()

    def _on_close(self):
        self.settings.set("window_width", self.winfo_width())
        self.settings.set("window_height", self.winfo_height())
        self.destroy()
