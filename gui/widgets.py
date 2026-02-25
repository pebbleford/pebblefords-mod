"""
Custom reusable widgets for the Among Us Mod Manager GUI.
Built with tkinter for maximum compatibility.
"""

import tkinter as tk
from tkinter import ttk


class ModCard(tk.Frame):
    """A card widget representing a single mod."""

    def __init__(self, parent, mod_info, colors, on_toggle=None,
                 on_uninstall=None, on_click=None, **kwargs):
        super().__init__(parent, bg=colors["bg_card"], cursor="hand2", **kwargs)
        self.mod_info = mod_info
        self.colors = colors
        self.on_toggle = on_toggle
        self.on_uninstall = on_uninstall
        self._selected = False

        self.configure(
            highlightbackground=colors["border"],
            highlightthickness=1,
            padx=12, pady=8,
        )

        # Left section - mod info
        info_frame = tk.Frame(self, bg=colors["bg_card"])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        name_text = mod_info.name
        name_label = tk.Label(
            info_frame, text=name_text,
            bg=colors["bg_card"], fg=colors["text"],
            font=("Segoe UI", 11, "bold"), anchor="w",
        )
        name_label.pack(anchor="w")

        detail_parts = []
        if mod_info.version != "unknown":
            detail_parts.append(f"v{mod_info.version}")
        if mod_info.author != "unknown":
            detail_parts.append(f"by {mod_info.author}")
        detail_parts.append(mod_info.size_str)

        detail_label = tk.Label(
            info_frame, text="  |  ".join(detail_parts),
            bg=colors["bg_card"], fg=colors["text_secondary"],
            font=("Segoe UI", 9), anchor="w",
        )
        detail_label.pack(anchor="w")

        if mod_info.description:
            desc = mod_info.description[:100] + ("..." if len(mod_info.description) > 100 else "")
            desc_label = tk.Label(
                info_frame, text=desc,
                bg=colors["bg_card"], fg=colors["text_dim"],
                font=("Segoe UI", 8), anchor="w",
            )
            desc_label.pack(anchor="w", pady=(2, 0))

        # Right section - controls
        controls = tk.Frame(self, bg=colors["bg_card"])
        controls.pack(side=tk.RIGHT, padx=(10, 0))

        # Toggle button
        toggle_text = "Enabled" if mod_info.enabled else "Disabled"
        toggle_color = colors["accent_green"] if mod_info.enabled else colors["disabled"]
        self.toggle_btn = tk.Button(
            controls, text=toggle_text,
            bg=toggle_color, fg="white",
            font=("Segoe UI", 9), relief=tk.FLAT,
            padx=10, pady=2, cursor="hand2",
            command=lambda: self._on_toggle(),
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=2)

        # Uninstall button
        self.remove_btn = tk.Button(
            controls, text="X",
            bg=colors["error"], fg="white",
            font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
            padx=6, pady=2, cursor="hand2",
            command=lambda: self._on_uninstall(),
        )
        self.remove_btn.pack(side=tk.LEFT, padx=2)

        # Hover effects
        for widget in [self, info_frame, name_label, detail_label]:
            widget.bind("<Enter>", lambda e: self._on_enter())
            widget.bind("<Leave>", lambda e: self._on_leave())
            if on_click:
                widget.bind("<Button-1>", lambda e: on_click(mod_info))

    def _on_enter(self):
        self.configure(bg=self.colors["bg_hover"])
        for w in self.winfo_children():
            self._set_bg_recursive(w, self.colors["bg_hover"])

    def _on_leave(self):
        self.configure(bg=self.colors["bg_card"])
        for w in self.winfo_children():
            self._set_bg_recursive(w, self.colors["bg_card"])

    def _set_bg_recursive(self, widget, color):
        try:
            if not isinstance(widget, tk.Button):
                widget.configure(bg=color)
            for child in widget.winfo_children():
                self._set_bg_recursive(child, color)
        except tk.TclError:
            pass

    def _on_toggle(self):
        if self.on_toggle:
            self.on_toggle(self.mod_info)

    def _on_uninstall(self):
        if self.on_uninstall:
            self.on_uninstall(self.mod_info)


class OnlineModCard(tk.Frame):
    """A card widget for an online mod available for download."""

    def __init__(self, parent, online_mod, colors, on_download=None,
                 on_visit=None, **kwargs):
        super().__init__(parent, bg=colors["bg_card"], **kwargs)
        self.online_mod = online_mod
        self.colors = colors

        self.configure(
            highlightbackground=colors["border"],
            highlightthickness=1,
            padx=12, pady=8,
        )

        # Left section
        info_frame = tk.Frame(self, bg=colors["bg_card"])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        name_label = tk.Label(
            info_frame, text=online_mod.name,
            bg=colors["bg_card"], fg=colors["text"],
            font=("Segoe UI", 11, "bold"), anchor="w",
        )
        name_label.pack(anchor="w")

        details = f"by {online_mod.author}  |  {online_mod.version}  |  {online_mod.size_str}"
        if online_mod.stars:
            details += f"  |  {online_mod.stars} stars"
        if online_mod.download_count:
            details += f"  |  {online_mod.download_count:,} downloads"

        detail_label = tk.Label(
            info_frame, text=details,
            bg=colors["bg_card"], fg=colors["text_secondary"],
            font=("Segoe UI", 9), anchor="w",
        )
        detail_label.pack(anchor="w")

        if online_mod.description:
            desc = online_mod.description[:120] + ("..." if len(online_mod.description) > 120 else "")
            desc_label = tk.Label(
                info_frame, text=desc,
                bg=colors["bg_card"], fg=colors["text_dim"],
                font=("Segoe UI", 8), anchor="w", wraplength=500, justify=tk.LEFT,
            )
            desc_label.pack(anchor="w", pady=(2, 0))

        # Right section
        controls = tk.Frame(self, bg=colors["bg_card"])
        controls.pack(side=tk.RIGHT, padx=(10, 0))

        if online_mod.download_url:
            dl_btn = tk.Button(
                controls, text="Download",
                bg=colors["accent_green"], fg="white",
                font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                padx=12, pady=4, cursor="hand2",
                command=lambda: on_download(online_mod) if on_download else None,
            )
            dl_btn.pack(side=tk.TOP, pady=2)

        if online_mod.repo_url:
            visit_btn = tk.Button(
                controls, text="GitHub",
                bg=colors["bg_hover"], fg=colors["text"],
                font=("Segoe UI", 8), relief=tk.FLAT,
                padx=8, pady=2, cursor="hand2",
                command=lambda: on_visit(online_mod) if on_visit else None,
            )
            visit_btn.pack(side=tk.TOP, pady=2)

        # Hover
        for widget in [self, info_frame, name_label, detail_label]:
            widget.bind("<Enter>", lambda e: self.configure(bg=colors["bg_hover"]))
            widget.bind("<Leave>", lambda e: self.configure(bg=colors["bg_card"]))


class ScrollableFrame(tk.Frame):
    """A scrollable frame widget."""

    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, bg=colors["bg"], **kwargs)

        self.canvas = tk.Canvas(self, bg=colors["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg=colors["bg"])

        self.scrollable.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind canvas resize to update inner frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self):
        for widget in self.scrollable.winfo_children():
            widget.destroy()


class StatusBar(tk.Frame):
    """Bottom status bar."""

    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, bg=colors["bg_secondary"], **kwargs)
        self.colors = colors

        self.configure(padx=10, pady=4)

        self.status_label = tk.Label(
            self, text="Ready",
            bg=colors["bg_secondary"], fg=colors["text_secondary"],
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side=tk.LEFT)

        self.right_label = tk.Label(
            self, text="",
            bg=colors["bg_secondary"], fg=colors["text_dim"],
            font=("Segoe UI", 9),
        )
        self.right_label.pack(side=tk.RIGHT)

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def set_right(self, text: str):
        self.right_label.configure(text=text)


class ProgressDialog(tk.Toplevel):
    """A modal progress dialog."""

    def __init__(self, parent, title, colors):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=colors["bg"])
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 150) // 2
        self.geometry(f"+{x}+{y}")

        self.label = tk.Label(
            self, text="Please wait...",
            bg=colors["bg"], fg=colors["text"],
            font=("Segoe UI", 11),
        )
        self.label.pack(pady=(20, 10))

        self.progress = ttk.Progressbar(self, length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.detail_label = tk.Label(
            self, text="",
            bg=colors["bg"], fg=colors["text_secondary"],
            font=("Segoe UI", 9),
        )
        self.detail_label.pack(pady=5)

    def update_progress(self, text: str, value: float):
        self.label.configure(text=text)
        if value >= 0:
            self.progress["value"] = value * 100
        self.update()

    def done(self):
        self.grab_release()
        self.destroy()
