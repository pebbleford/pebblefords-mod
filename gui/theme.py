"""
Theme and color definitions for Among Us Mod Manager.
Among Us inspired dark theme with polished modern look.
"""

COLORS = {
    "dark": {
        # Backgrounds
        "bg":              "#0b0e17",
        "bg_secondary":    "#111827",
        "bg_card":         "#1a2234",
        "bg_card_hover":   "#222d42",
        "bg_card_active":  "#1e3a5f",
        "sidebar_bg":      "#0f1623",
        "sidebar_active":  "#1c2a42",
        "entry_bg":        "#0d1220",
        "header_bg":       "#0d1321",

        # Accent colors
        "accent":          "#c0392b",
        "accent_hover":    "#e74c3c",
        "accent_light":    "#ff6b6b",
        "green":           "#00b894",
        "green_hover":     "#00d4aa",
        "green_dark":      "#00896e",
        "yellow":          "#fdcb6e",
        "orange":          "#e67e22",
        "blue":            "#0984e3",
        "blue_hover":      "#2d9cef",
        "purple":          "#6c5ce7",

        # Text
        "text":            "#e8eaf0",
        "text_secondary":  "#8892a8",
        "text_dim":        "#4a5568",
        "text_accent":     "#ff6b6b",

        # Borders & UI
        "border":          "#1e2940",
        "border_light":    "#2a3650",
        "divider":         "#1a2438",
        "error":           "#e74c3c",
        "success":         "#00b894",
        "warning":         "#fdcb6e",
        "scrollbar":       "#2a3650",

        # Buttons
        "btn_primary":     "#c0392b",
        "btn_primary_hover":"#e74c3c",
        "btn_success":     "#00b894",
        "btn_success_hover":"#00d4aa",
        "btn_danger":      "#c0392b",
        "btn_secondary":   "#1e2940",
        "btn_secondary_hover":"#2a3a55",

        # Progress
        "progress_bg":     "#1a2438",
        "progress_fill":   "#c0392b",

        # Special
        "badge_installed": "#00b894",
        "badge_update":    "#e67e22",
        "checkbox_bg":     "#1a2234",
        "checkbox_active": "#c0392b",
        "glow":            "#c0392b33",
    },
    "light": {
        "bg":              "#f5f6fa",
        "bg_secondary":    "#ffffff",
        "bg_card":         "#ffffff",
        "bg_card_hover":   "#f0f1f5",
        "bg_card_active":  "#e8eaf0",
        "sidebar_bg":      "#ebedf5",
        "sidebar_active":  "#dde0ec",
        "entry_bg":        "#ffffff",
        "header_bg":       "#ffffff",

        "accent":          "#c0392b",
        "accent_hover":    "#e74c3c",
        "accent_light":    "#ff6b6b",
        "green":           "#00b894",
        "green_hover":     "#00d4aa",
        "green_dark":      "#00896e",
        "yellow":          "#f1c40f",
        "orange":          "#e67e22",
        "blue":            "#0984e3",
        "blue_hover":      "#2d9cef",
        "purple":          "#6c5ce7",

        "text":            "#1a1a2e",
        "text_secondary":  "#555577",
        "text_dim":        "#8888aa",
        "text_accent":     "#c0392b",

        "border":          "#e0e2ea",
        "border_light":    "#eaecf2",
        "divider":         "#e8eaf0",
        "error":           "#e74c3c",
        "success":         "#00b894",
        "warning":         "#f1c40f",
        "scrollbar":       "#c0c0d0",

        "btn_primary":     "#c0392b",
        "btn_primary_hover":"#e74c3c",
        "btn_success":     "#00b894",
        "btn_success_hover":"#00d4aa",
        "btn_danger":      "#c0392b",
        "btn_secondary":   "#e8eaf0",
        "btn_secondary_hover":"#d0d4e0",

        "progress_bg":     "#e0e2ea",
        "progress_fill":   "#c0392b",

        "badge_installed": "#00b894",
        "badge_update":    "#e67e22",
        "checkbox_bg":     "#ffffff",
        "checkbox_active": "#c0392b",
        "glow":            "#c0392b22",
    },
}


def get_colors(theme: str = "dark") -> dict:
    return COLORS.get(theme, COLORS["dark"])
