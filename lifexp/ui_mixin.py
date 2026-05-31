import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import json
import math
import os
import random
import threading
import time
import urllib.error
import urllib.request
import webbrowser

from lifexp.constants import (
    ACCOUNT_BASE_XP_NEEDED,
    ACCOUNT_LEVEL_CURVE_BASE_MULTIPLIER,
    ACCOUNT_LEVEL_CURVE_FLOOR,
    ACCOUNT_LEVEL_CURVE_OFFSET,
    ACCOUNT_LEVEL_CURVE_UPGRADE_MULTIPLIER,
    APP_NAME,
    APP_VERSION,
    BASE_XP_NEEDED,
    BATCH_LEVEL_UP_POPUP_FADE_STEPS,
    BATCH_LEVEL_UP_POPUP_STEPS,
    DEFAULT_FONT_SIZE,
    FONT_SCALE_BASE_SIZE,
    GITHUB_LATEST_RELEASE_API,
    GITHUB_RELEASES_URL,
    LEGACY_MAX_FONT_SIZE,
    LEVEL_UP_POPUP_FADE_STEPS,
    LEVEL_UP_POPUP_STEPS,
    MAX_ACTIVE_PARTICLES,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    PARTICLE_FADE_RELEASE_RATIO,
    PARTICLE_HARD_LIFETIME_MS,
    POPUP_FRAME_INTERVAL_SECONDS,
    POPUP_MODE_WITH_PARTICLES,
    POPUP_MODE_WITHOUT_PARTICLES,
    RANK_UP_GLOW_COLOR,
    RANK_UP_HEADER_FRAMES,
    REWARD_CHAIN_START_RATIO,
    TROPHY_POPUP_FADE_STEPS,
    TROPHY_POPUP_STEPS,
    XP_POPUP_FADE_STEPS,
    XP_POPUP_STEPS,
    XP_TO_REWARD_START_RATIO,
)
from lifexp.runtime import (
    configure_platform_scaling,
    get_https_context,
    get_resource_dir,
    get_user_data_dir,
    is_packaged_app,
)


class UIMixin:
    # ==============================================================================
    # GROUP A - UI SETUP / PAINTERS AND STYLISTS
    # This group creates the visible interface: theme colors, tabs, tables, labels,
    # progress bars, trophies, summary panels, and graph canvases.
    # ==============================================================================
    def get_theme_definitions(self):
        """Returns the available app themes and their color tokens."""
        # These palettes mix modern app ideas with famous editor/game-adjacent themes.
        # Each theme defines interface colors plus the five RPG attribute colors.
        return {
            "Apple Light": {
                "description": "Clean, bright, modern system-app feeling.",
                "bg_dark": "#F5F5F7",
                "bg_light": "#FFFFFF",
                "accent": "#007AFF",
                "text": "#1D1D1F",
                "card_text": "#1D1D1F",
                "attr_colors": {
                    "Strength": "#FF3B30",
                    "Agility": "#FF9500",
                    "Intelligence": "#007AFF",
                    "Charisma": "#AF52DE",
                    "Vitality": "#34C759"
                }
            },
            "Apple Dark": {
                "description": "Minimal dark mode with crisp system accents.",
                "bg_dark": "#1C1C1E",
                "bg_light": "#2C2C2E",
                "accent": "#30D158",
                "text": "#F2F2F7",
                "card_text": "#F2F2F7",
                "attr_colors": {
                    "Strength": "#FF453A",
                    "Agility": "#FF9F0A",
                    "Intelligence": "#0A84FF",
                    "Charisma": "#BF5AF2",
                    "Vitality": "#30D158"
                }
            },
            "Nord RPG": {
                "description": "Cool, readable, fantasy-terminal atmosphere.",
                "bg_dark": "#2E3440",
                "bg_light": "#3B4252",
                "accent": "#A3BE8C",
                "text": "#ECEFF4",
                "card_text": "#ECEFF4",
                "attr_colors": {
                    "Strength": "#BF616A",
                    "Agility": "#D08770",
                    "Intelligence": "#88C0D0",
                    "Charisma": "#EBCB8B",
                    "Vitality": "#A3BE8C"
                }
            },
            "Dracula": {
                "description": "High-contrast neon dungeon palette.",
                "bg_dark": "#282A36",
                "bg_light": "#44475A",
                "accent": "#BD93F9",
                "text": "#F8F8F2",
                "card_text": "#F8F8F2",
                "attr_colors": {
                    "Strength": "#FF5555",
                    "Agility": "#FFB86C",
                    "Intelligence": "#8BE9FD",
                    "Charisma": "#FF79C6",
                    "Vitality": "#50FA7B"
                }
            },
            "Catppuccin Mocha": {
                "description": "Soft pastel night palette with cozy contrast.",
                "bg_dark": "#1E1E2E",
                "bg_light": "#313244",
                "accent": "#A6E3A1",
                "text": "#CDD6F4",
                "card_text": "#CDD6F4",
                "attr_colors": {
                    "Strength": "#F38BA8",
                    "Agility": "#FAB387",
                    "Intelligence": "#89B4FA",
                    "Charisma": "#F5C2E7",
                    "Vitality": "#A6E3A1"
                }
            },
            "Gruvbox": {
                "description": "Retro warm adventurer palette.",
                "bg_dark": "#282828",
                "bg_light": "#3C3836",
                "accent": "#B8BB26",
                "text": "#EBDBB2",
                "card_text": "#EBDBB2",
                "attr_colors": {
                    "Strength": "#FB4934",
                    "Agility": "#FE8019",
                    "Intelligence": "#83A598",
                    "Charisma": "#D3869B",
                    "Vitality": "#B8BB26"
                }
            },
            "Tokyo Night": {
                "description": "Sleek cyber-RPG night colors.",
                "bg_dark": "#1A1B26",
                "bg_light": "#24283B",
                "accent": "#7AA2F7",
                "text": "#C0CAF5",
                "card_text": "#C0CAF5",
                "attr_colors": {
                    "Strength": "#F7768E",
                    "Agility": "#FF9E64",
                    "Intelligence": "#7AA2F7",
                    "Charisma": "#BB9AF7",
                    "Vitality": "#9ECE6A"
                }
            },
            "Solarized Dark": {
                "description": "Calm low-contrast reading palette.",
                "bg_dark": "#002B36",
                "bg_light": "#073642",
                "accent": "#859900",
                "text": "#EEE8D5",
                "card_text": "#EEE8D5",
                "attr_colors": {
                    "Strength": "#DC322F",
                    "Agility": "#CB4B16",
                    "Intelligence": "#268BD2",
                    "Charisma": "#D33682",
                    "Vitality": "#859900"
                }
            },
            "OLED Black": {
                "description": "True-black AMOLED mode with bright readable accents.",
                "bg_dark": "#000000",
                "bg_light": "#050505",
                "accent": "#00E676",
                "text": "#F5F5F5",
                "card_text": "#F5F5F5",
                "attr_colors": {
                    "Strength": "#FF5252",
                    "Agility": "#FFB74D",
                    "Intelligence": "#40C4FF",
                    "Charisma": "#E040FB",
                    "Vitality": "#00E676"
                }
            },
            "GitHub Light": {
                "description": "Familiar bright GitHub-style workspace palette.",
                "bg_dark": "#F6F8FA",
                "bg_light": "#FFFFFF",
                "accent": "#0969DA",
                "text": "#24292F",
                "card_text": "#24292F",
                "attr_colors": {
                    "Strength": "#CF222E",
                    "Agility": "#BC4C00",
                    "Intelligence": "#0969DA",
                    "Charisma": "#8250DF",
                    "Vitality": "#1A7F37"
                }
            },
            "One Dark": {
                "description": "Popular Atom-inspired dark coding palette.",
                "bg_dark": "#21252B",
                "bg_light": "#282C34",
                "accent": "#61AFEF",
                "text": "#ABB2BF",
                "card_text": "#ABB2BF",
                "attr_colors": {
                    "Strength": "#E06C75",
                    "Agility": "#D19A66",
                    "Intelligence": "#61AFEF",
                    "Charisma": "#C678DD",
                    "Vitality": "#98C379"
                }
            },
            "Monokai Pro": {
                "description": "Classic saturated editor palette with warm contrast.",
                "bg_dark": "#2D2A2E",
                "bg_light": "#403E41",
                "accent": "#A9DC76",
                "text": "#FCFCFA",
                "card_text": "#FCFCFA",
                "attr_colors": {
                    "Strength": "#FF6188",
                    "Agility": "#FC9867",
                    "Intelligence": "#78DCE8",
                    "Charisma": "#AB9DF2",
                    "Vitality": "#A9DC76"
                }
            },
            "Rose Pine Moon": {
                "description": "Muted rose-toned night palette with soft contrast.",
                "bg_dark": "#232136",
                "bg_light": "#2A273F",
                "accent": "#C4A7E7",
                "text": "#E0DEF4",
                "card_text": "#E0DEF4",
                "attr_colors": {
                    "Strength": "#EB6F92",
                    "Agility": "#F6C177",
                    "Intelligence": "#9CCFD8",
                    "Charisma": "#C4A7E7",
                    "Vitality": "#A3BE8C"
                }
            },
            "Everforest Dark": {
                "description": "Earthy low-glare forest palette.",
                "bg_dark": "#2D353B",
                "bg_light": "#343F44",
                "accent": "#A7C080",
                "text": "#D3C6AA",
                "card_text": "#D3C6AA",
                "attr_colors": {
                    "Strength": "#E67E80",
                    "Agility": "#E69875",
                    "Intelligence": "#7FBBB3",
                    "Charisma": "#D699B6",
                    "Vitality": "#A7C080"
                }
            }
        }

    def _hex_to_rgb(self, color):
        """Converts a #RRGGBB color into RGB channel values."""
        color = str(color).lstrip("#")
        if len(color) != 6:
            return 0, 0, 0
        return tuple(int(color[index:index + 2], 16) for index in (0, 2, 4))

    def get_contrast_ratio(self, foreground, background):
        """Returns the WCAG contrast ratio for two hex colors."""
        def channel(value):
            value = value / 255.0
            return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

        def luminance(color):
            red, green, blue = self._hex_to_rgb(color)
            return (0.2126 * channel(red)) + (0.7152 * channel(green)) + (0.0722 * channel(blue))

        light = max(luminance(foreground), luminance(background))
        dark = min(luminance(foreground), luminance(background))
        return (light + 0.05) / (dark + 0.05)

    def get_readable_text_color(self, background, preferred=None):
        """Keeps text readable on light and dark theme surfaces."""
        if preferred and self.get_contrast_ratio(preferred, background) >= 4.5:
            return preferred

        candidates = ["#FFFFFF", "#F4F7FF", "#111827", "#000000"]
        return max(candidates, key=lambda color: self.get_contrast_ratio(color, background))

    def get_action_color(self, role):
        """Returns semantic action colors that stay distinct across themes."""
        # Buttons use meanings, not fixed hex colors. Accept is blue/intelligence and
        # Complete is green/vitality, so they stay different even in very dark themes.
        action_colors = {
            "accept": self.attr_colors["Intelligence"],
            "complete": self.attr_colors["Vitality"],
            "edit": self.attr_colors["Agility"],
            "abandon": self.attr_colors["Strength"],
            "danger": self.attr_colors["Strength"]
        }
        return action_colors[role]

    def get_action_text_color(self, background):
        """Returns readable text for a colored action control."""
        # Dark navy text looks good on many bright action colors. If it is not readable,
        # get_readable_text_color automatically switches to a safer light or dark color.
        return self.get_readable_text_color(background, "#0F172A")

    def get_action_hover_color(self, background):
        """Returns a visible hover color for a colored action control."""
        # Hover colors are a small move toward white. This creates feedback without
        # inventing a separate hover palette for every theme.
        return self._blend_color(background, "#FFFFFF", 0.18)

    def scaled_font_size(self, base_size):
        """Scales a hard-coded font size from the user's base preference."""
        scale = self.font_size / float(FONT_SCALE_BASE_SIZE)
        return max(7, int(round(base_size * scale)))

    def ui_space(self, base_size):
        """Scales fixed padding and row heights with the readable font size."""
        scale = self.font_size / float(FONT_SCALE_BASE_SIZE)
        return max(1, int(round(base_size * scale)))

    def ui_font(self, base_size=DEFAULT_FONT_SIZE, weight=None, family="{San Francisco}"):
        """Returns a Tk font tuple adjusted by the current Settings font size."""
        size = self.scaled_font_size(base_size)
        return (family, size, weight) if weight else (family, size)

    def coerce_bool(self, value, default=True):
        """Normalizes saved boolean-like values without treating 'False' as true."""
        # JSON or hand-edited saves might store booleans as true/false, "true"/"false",
        # or 1/0. This helper turns those common forms back into real Python booleans.
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    def apply_modern_theme(self):
        """Overrides default system styling to create a cohesive dark 'RPG' look."""
        # ttk widgets use a Style object for shared appearance rules. The clam theme is
        # chosen because it is easier to recolor consistently than many system themes.
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        # Central color variables make the theme easier to change. Instead of repeating
        # hex values everywhere, later widgets reference these readable names.
        theme = self.themes[self.current_theme_name]
        self.bg_dark = theme["bg_dark"]
        self.bg_light = theme["bg_light"]
        self.accent_green = theme["accent"]
        self.text_color = self.get_readable_text_color(self.bg_light, theme["text"])
        self.dark_surface_text_color = self.get_readable_text_color(self.bg_dark, self.text_color)
        self.accent_text_color = self.get_readable_text_color(self.accent_green, self.bg_dark)
        self.card_text_color = self.get_readable_text_color(self.bg_light, theme["card_text"])
        self.attr_colors = theme["attr_colors"].copy()
        self.attr_text_colors = {
            attr: self.get_readable_text_color(color, self.card_text_color)
            for attr, color in self.attr_colors.items()
        }

        # The root window is a normal tk widget, so it is configured directly rather
        # than through ttk.Style.
        self.root.configure(bg=self.bg_dark)

        # These style rules define the default look for common ttk widgets. configure()
        # sets normal values, while map() sets values for states like selected/active.
        self.style.configure('TFrame', background=self.bg_dark)
        self.style.configure('TNotebook', background=self.bg_dark, borderwidth=0)
        self.style.layout(
            'TNotebook.Tab',
            [('Notebook.tab', {'sticky': 'nswe', 'children': [
                ('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children': [
                    ('Notebook.label', {'side': 'top', 'sticky': ''})
                ]})
            ]})]
        )
        self.style.configure('TNotebook.Tab', background=self.bg_light, foreground=self.text_color, padding=[self.ui_space(18), self.ui_space(9)], font=self.ui_font(11, 'bold'))
        self.configure_notebook_tab_style(selected_bg=self.accent_green, active_bg=self.bg_light)

        self.style.configure('TButton', background=self.bg_light, foreground=self.text_color, font=self.ui_font(11), padding=self.ui_space(6))
        self.style.map('TButton', background=[('active', self.accent_green)], foreground=[('active', self.accent_text_color)])
        self.style.layout(
            'Modern.Vertical.TScrollbar',
            [('Vertical.Scrollbar.trough', {'sticky': 'ns', 'children': [
                ('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})
            ]})]
        )
        self.style.configure(
            'Modern.Vertical.TScrollbar',
            background=self.accent_green,
            troughcolor=self._blend_color(self.bg_dark, self.text_color, 0.08),
            bordercolor=self.bg_dark,
            lightcolor=self.accent_green,
            darkcolor=self.accent_green,
            arrowcolor=self.accent_green,
            relief=tk.FLAT,
            borderwidth=0,
            width=14
        )
        self.style.map(
            'Modern.Vertical.TScrollbar',
            background=[('active', self._blend_color(self.accent_green, "#FFFFFF", 0.18))]
        )
        self.style.configure(
            'Settings.TCombobox',
            fieldbackground=self.bg_light,
            background=self.bg_light,
            foreground=self.text_color,
            arrowcolor=self.text_color,
            selectbackground=self.accent_green,
            selectforeground=self.accent_text_color
        )
        self.style.map(
            'Settings.TCombobox',
            fieldbackground=[('readonly', self.bg_light)],
            foreground=[('readonly', self.text_color)],
            selectbackground=[('readonly', self.accent_green)],
            selectforeground=[('readonly', self.accent_text_color)]
        )
        # Dialog action buttons share the same semantic colors as the Quest Log action
        # rail. The loop below creates five ttk button styles from one dictionary.
        action_button_styles = {
            "QuestAccept.TButton": self.get_action_color("accept"),
            "QuestComplete.TButton": self.get_action_color("complete"),
            "QuestEdit.TButton": self.get_action_color("edit"),
            "QuestAbandon.TButton": self.get_action_color("abandon"),
            "Danger.TButton": self.get_action_color("danger")
        }
        for style_name, background in action_button_styles.items():
            foreground = self.get_action_text_color(background)
            active_background = self.get_action_hover_color(background)
            active_foreground = self.get_action_text_color(active_background)
            self.style.configure(style_name, background=background, foreground=foreground, font=self.ui_font(11, 'bold'), padding=self.ui_space(8))
            self.style.map(style_name, background=[('active', active_background)], foreground=[('active', active_foreground)])

        self.style.configure('TLabelframe', background=self.bg_dark, foreground=self.accent_green, font=self.ui_font(12, 'bold'))
        self.style.configure('TLabelframe.Label', background=self.bg_dark, foreground=self.accent_green)

        self.style.configure('TLabel', background=self.bg_dark, foreground=self.dark_surface_text_color, font=self.ui_font(11))
        self.style.configure('Horizontal.TProgressbar', background=self.accent_green, troughcolor=self.bg_light, bordercolor=self.bg_dark, lightcolor=self.accent_green, darkcolor=self.accent_green)

        # Each RPG attribute gets its own progress-bar style. The loop prevents writing
        # five nearly identical style.configure() calls by hand.
        for attr, color in self.attr_colors.items():
            self.style.configure(f'{attr}.Horizontal.TProgressbar', background=color, troughcolor=self.bg_light, bordercolor=self.bg_dark, lightcolor=color, darkcolor=color)

        # Treeview is the table widget used for the quest list. Its heading, row color,
        # selection color, and row height are styled separately from other widgets.
        self.style.configure('Treeview', background=self.bg_light, foreground=self.text_color, fieldbackground=self.bg_light, borderwidth=0, rowheight=self.ui_space(34), font=self.ui_font(11))
        self.style.map('Treeview', background=[('selected', self.accent_green)], foreground=[('selected', self.accent_text_color)])
        self.style.configure('Treeview.Heading', background=self.bg_light, foreground=self.accent_green, relief=tk.FLAT, font=self.ui_font(11, 'bold'))

    def fit_window_to_content(self, window, min_width=360, min_height=260, center=True):
        """Sizes a Toplevel to its requested content while staying inside the screen."""
        # Tkinter calculates a widget's "requested" size only after it has had a chance
        # to lay out its children. update_idletasks() performs that layout work without
        # starting the full event loop, so the width/height below are accurate.
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # The window should be at least big enough to be usable, but it should not grow
        # beyond most of the screen. The 90% cap keeps large dialogs from opening under
        # the menu bar or outside the monitor on smaller laptops.
        width = min(max(window.winfo_reqwidth(), min_width), int(screen_width * 0.9))
        height = min(max(window.winfo_reqheight(), min_height), int(screen_height * 0.9))
        window.minsize(min(min_width, width), min(min_height, height))

        if center:
            # Centering is based on the main app window, not the whole screen. That
            # keeps dialogs visually attached to LifeXP even when the app is moved.
            parent = self.root
            parent.update_idletasks()
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            x = parent_x + max(0, (parent_width - width) // 2)
            y = parent_y + max(0, (parent_height - height) // 2)
            x = min(max(0, x), max(0, screen_width - width))
            y = min(max(0, y), max(0, screen_height - height))
            window.geometry(f"{width}x{height}+{x}+{y}")
        else:
            window.geometry(f"{width}x{height}")

    def show_fitted_window(self, window, min_width=360, min_height=260):
        """Fits a hidden Toplevel, then shows it after the geometry is final."""
        # Toplevel windows can briefly appear at a tiny default size before their
        # children finish layout. Building them while withdrawn, then deiconifying here,
        # avoids that flash.
        self.fit_window_to_content(window, min_width=min_width, min_height=min_height)
        self.animate_window_open(window)

    def animate_window_open(self, window):
        """Shows a Toplevel with a short fade-and-rise transition."""
        if not self.animations_enabled:
            window.deiconify()
            window.lift()
            self.set_popup_alpha(window, 1.0)
            return

        # Motion guidelines favor quick, subtle transitions that explain state changes
        # without making the user wait. This uses the already-final window size, then
        # starts 10 pixels lower and eases into place over about 150ms.
        geometry = window.geometry()
        try:
            size_part, x_part, y_part = geometry.split("+")
            width, height = size_part.split("x")
            final_x = int(x_part)
            final_y = int(y_part)
            width = int(width)
            height = int(height)
        except ValueError:
            window.deiconify()
            window.lift()
            return

        start_y = final_y + 10
        frames = 9
        delay_ms = 16
        self.set_popup_alpha(window, 0.0)
        window.geometry(f"{width}x{height}+{final_x}+{start_y}")
        window.deiconify()
        window.lift()

        def animate(frame=0):
            if not window.winfo_exists():
                return

            progress = min(frame / float(frames), 1.0)
            eased = self.ease_out_cubic(progress)
            current_y = int(start_y + ((final_y - start_y) * eased))
            window.geometry(f"{width}x{height}+{final_x}+{current_y}")
            self.set_popup_alpha(window, eased)

            if frame < frames:
                self.root.after(delay_ms, animate, frame + 1)
            else:
                window.geometry(f"{width}x{height}+{final_x}+{final_y}")
                self.set_popup_alpha(window, 1.0)

        animate()

    def recolor_widget_tree(self, widget, color_map):
        """Walks through normal tk widgets and swaps old theme colors for new ones."""
        # ttk widgets mostly follow ttk.Style, but tk.Frame/tk.Label/tk.Canvas/tk.Text
        # keep literal colors. This helper updates those literal colors in place so a
        # theme change does not need to destroy and rebuild the whole interface.
        # Some colors are reused for different jobs. For example, a dark background can
        # also be the best text color on a light card. Separate maps stop a background
        # from accidentally being changed into a text color during a theme switch.
        bg_options = {"bg", "background", "selectbackground", "highlightbackground"}
        fg_options = {"fg", "foreground", "insertbackground", "selectforeground"}
        if "background" in color_map or "foreground" in color_map:
            background_map = color_map.get("background", {})
            foreground_map = color_map.get("foreground", {})
        else:
            background_map = color_map
            foreground_map = color_map

        for option in bg_options | fg_options:
            try:
                current = widget.cget(option)
            except tk.TclError:
                continue
            current = str(current)
            option_map = background_map if option in bg_options else foreground_map
            if current in option_map:
                try:
                    widget.configure(**{option: option_map[current]})
                except tk.TclError:
                    pass

        for child in widget.winfo_children():
            self.recolor_widget_tree(child, color_map)

    def rescale_widget_tree(self, widget):
        """Scales already-created tk widget fonts from their original sizes."""
        # The first time a widget is resized, remember its original font. Later changes
        # scale from that original value instead of repeatedly scaling an already-scaled font.
        try:
            font_value = widget.cget("font")
        except tk.TclError:
            font_value = None

        if font_value:
            try:
                if not hasattr(widget, "_lifexp_base_font"):
                    actual = tkfont.Font(root=self.root, font=font_value).actual()
                    widget._lifexp_base_font = {
                        "family": actual.get("family") or "San Francisco",
                        "size": abs(int(actual.get("size") or DEFAULT_FONT_SIZE)),
                        "weight": actual.get("weight") or "normal",
                        "slant": actual.get("slant") or "roman"
                    }
                base = widget._lifexp_base_font
                widget.configure(
                    font=(base["family"], self.scaled_font_size(base["size"]), base["weight"], base["slant"])
                )
            except (tk.TclError, ValueError):
                pass

        if isinstance(widget, tk.Text):
            # Text widgets can have styled ranges called tags. Each tag may have its own
            # font, so the tags need the same "remember original, then scale" treatment.
            for tag in widget.tag_names():
                try:
                    tag_font = widget.tag_cget(tag, "font")
                except tk.TclError:
                    continue
                if not tag_font:
                    continue
                cache_name = f"_lifexp_tag_font_{tag}"
                try:
                    if not hasattr(widget, cache_name):
                        actual = tkfont.Font(root=self.root, font=tag_font).actual()
                        setattr(widget, cache_name, {
                            "family": actual.get("family") or "San Francisco",
                            "size": abs(int(actual.get("size") or DEFAULT_FONT_SIZE)),
                            "weight": actual.get("weight") or "normal",
                            "slant": actual.get("slant") or "roman"
                        })
                    base = getattr(widget, cache_name)
                    widget.tag_configure(
                        tag,
                        font=(base["family"], self.scaled_font_size(base["size"]), base["weight"], base["slant"])
                    )
                except (tk.TclError, ValueError):
                    continue

        for child in widget.winfo_children():
            self.rescale_widget_tree(child)

    def apply_display_preferences(self, save=True):
        """Applies persisted font and animation preferences to the live app."""
        self.font_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, int(self.font_size)))
        window_scale = 1.0 + (max(0, self.font_size - FONT_SCALE_BASE_SIZE) / float(FONT_SCALE_BASE_SIZE) * 0.35)
        min_width = int(round(900 * window_scale))
        min_height = int(round(760 * window_scale))
        self.root.minsize(min_width, min_height)
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        if current_width > 1 and current_height > 1 and (current_width < min_width or current_height < min_height):
            self.root.geometry(f"{max(current_width, min_width)}x{max(current_height, min_height)}")
        self.apply_modern_theme()
        self.rescale_widget_tree(self.root)
        if hasattr(self, "font_size_slider_var"):
            self.font_size_slider_var.set(self.font_size)
            self.draw_font_size_slider()
        if hasattr(self, "settings_canvas"):
            self.settings_canvas.configure(bg=self.bg_dark)
            self.root.after(10, lambda: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all")) if self.settings_canvas.winfo_exists() else None)
        if hasattr(self, "modern_scrollbars"):
            live_scrollbars = []
            for scrollbar in self.modern_scrollbars:
                canvas = scrollbar["canvas"]
                if canvas.winfo_exists():
                    canvas.configure(bg=self.bg_light)
                    scrollbar["draw"]()
                    live_scrollbars.append(scrollbar)
            self.modern_scrollbars = live_scrollbars
        if hasattr(self, "task_tree"):
            self.refresh_task_list()
        if hasattr(self, "summary_cards"):
            self.show_summary(self.current_summary_timeframe)
        if save and hasattr(self, "data"):
            self.data["user_info"]["font_size"] = self.font_size
            self.data["user_info"]["animations_enabled"] = bool(self.animations_enabled)
            self.data["user_info"]["particles_enabled"] = bool(self.particles_enabled)
            self.data["user_info"]["popups_enabled"] = bool(self.popups_enabled)
            self.save_data()

    def configure_notebook_tab_style(self, selected_bg=None, active_bg=None):
        """Applies selected and hover colors to notebook tabs."""
        if selected_bg is None:
            selected_bg = self.tab_selected_bg or self.accent_green
        if active_bg is None:
            active_bg = self.tab_active_bg or self.bg_light

        self.tab_selected_bg = selected_bg
        self.tab_active_bg = active_bg
        selected_fg = self.get_readable_text_color(selected_bg, self.accent_text_color)
        active_fg = self.get_readable_text_color(active_bg, self.text_color)
        self.style.map(
            'TNotebook.Tab',
            background=[('selected', selected_bg), ('active', active_bg)],
            foreground=[('selected', selected_fg), ('active', active_fg)]
        )

    def handle_tab_hover_motion(self, event):
        """Animates tab hover fill when the pointer is over a notebook tab."""
        try:
            self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            self.set_tab_hover(False)
            return

        self.set_tab_hover(True)

    def set_tab_hover(self, is_hovering):
        """Eases notebook hover color in and out."""
        if not self.animations_enabled:
            return

        if self.tab_hover_active == is_hovering:
            return

        self.tab_hover_active = is_hovering
        self.tab_hover_token += 1
        token = self.tab_hover_token
        start = self.tab_active_bg or self.bg_light
        target = self._blend_color(self.bg_light, self.accent_green, 0.78) if is_hovering else self.bg_light

        def step(index=1, frames=8):
            if self.tab_hover_token != token or self.tab_hover_active != is_hovering:
                return
            ratio = self.ease_smoothstep(index / float(frames))
            self.configure_notebook_tab_style(active_bg=self._blend_color(start, target, ratio))
            if index < frames:
                self.root.after(18, step, index + 1, frames)

        step()

    def play_tab_change_animation(self, event=None):
        """Pulses the selected tab with a smooth neon glow on tab change."""
        if not self.animations_enabled:
            return

        self.tab_change_token += 1
        token = self.tab_change_token
        base = self.accent_green
        peak = self._blend_color(self.accent_green, "#FFFFFF", 0.46)
        total_frames = 18
        peak_frame = total_frames // 2

        def step(index=0):
            if self.tab_change_token != token:
                return
            if index <= total_frames:
                if index <= peak_frame:
                    progress = self.ease_smoothstep(index / float(peak_frame))
                else:
                    progress = 1 - self.ease_smoothstep((index - peak_frame) / float(total_frames - peak_frame))
                self.configure_notebook_tab_style(selected_bg=self._blend_color(base, peak, progress))
                self.root.after(18, step, index + 1)
                return

            self.configure_notebook_tab_style(selected_bg=base)

        step()

    def handle_notebook_tab_changed(self, event=None):
        """Runs tab-change effects and prepares visible tab-specific artwork."""
        self.play_tab_change_animation(event)
        if not hasattr(self, "notebook") or not hasattr(self, "tab_character"):
            return

        try:
            selected_tab = self.notebook.nametowidget(self.notebook.select())
        except tk.TclError:
            return

        if selected_tab == self.tab_character:
            self.prepare_visible_trophy_room()

    def setup_header(self):
        """Builds the User Account bar at the top right of the application."""
        # The header is a horizontal profile area at the top. It holds the avatar icon
        # and the account title/level labels.
        self.header_frame = tk.Frame(self.root, bg=self.bg_light)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(16, 0))

        # The app title anchors the toolbar so the top of the window feels like one
        # intentional surface instead of loose widgets floating on the background.
        self.app_title_frame = tk.Frame(self.header_frame, bg=self.bg_light)
        self.app_title_frame.pack(side=tk.LEFT, padx=(18, 0), pady=12)
        self.app_title_label = tk.Label(
            self.app_title_frame,
            text="LifeXP",
            font=("{San Francisco}", 18, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        )
        self.app_title_label.pack(side=tk.LEFT, anchor=tk.W)
        self.app_level_delta_label = tk.Label(
            self.app_title_frame,
            text="",
            font=("{San Francisco}", 10, "bold"),
            bg=self.bg_light,
            fg=RANK_UP_GLOW_COLOR
        )
        self.app_level_delta_label.pack(side=tk.LEFT, anchor=tk.N, padx=(2, 0), pady=(0, 0))
        self.app_level_delta_label.pack_forget()

        # The avatar is drawn on a Canvas because it needs custom shapes and an arc,
        # not just normal text or buttons.
        self.avatar_size = 56
        self.avatar_canvas = tk.Canvas(self.header_frame, width=self.avatar_size, height=self.avatar_size, bg=self.bg_light, highlightthickness=0)
        self.avatar_canvas.pack(side=tk.RIGHT, padx=(0, 14), pady=8)

        # This nested frame groups the two text labels so they can sit together to the
        # left of the avatar while still being part of the header.
        self.user_info_frame = tk.Frame(self.header_frame, bg=self.bg_light)
        self.user_info_frame.pack(side=tk.RIGHT, padx=15)

        self.user_name_label = tk.Label(self.user_info_frame, text=self.data["user_info"]["name"], font=("{San Francisco}", 16, "bold"), bg=self.bg_light, fg=self.text_color)
        self.user_name_label.pack(anchor=tk.E)

        self.user_level_label = tk.Label(self.user_info_frame, text="Total Lvl: 1  |  0 XP", font=("{San Francisco}", 11), bg=self.bg_light, fg=self.accent_green)
        self.user_level_label.pack(anchor=tk.E)

        # After the widgets exist, update_header() calculates the real saved level and
        # fills the labels/avatar with current data.
        self.update_header()

    def get_title_info(self, total_level):
        """Returns the Title string, Roman Numeral, and Color for the user based on total level."""
        # Account titles are stored as ordered tiers. Every five total levels moves the
        # player to the next title family and color.
        titles = [
            ("Novice", "#88C0D0"),
            ("Apprentice", "#A3BE8C"),
            ("Journeyman", "#EBCB8B"),
            ("Adept", "#D08770"),
            ("Expert", "#BF616A"),
            ("Master", "#B48EAD"),
            ("Grandmaster", "#FFD700"),
            ("Champion", "#00FFFF"),
            ("Hero", "#FF00FF"),
            ("Legend", "#FFFFFF")
        ]

        # Integer division turns a level into a zero-based tier index. The clamp keeps
        # very high levels from indexing past the end of the title list.
        tier_index = (total_level - 1) // 5
        if tier_index >= len(titles):
            tier_index = len(titles) - 1

        base_title, color = titles[tier_index]

        # The modulo calculation gives the title's roman numeral inside its five-level
        # tier: I, II, III, IV, or V.
        sub_level = ((total_level - 1) % 5) + 1
        roman = ["I", "II", "III", "IV", "V"][sub_level - 1]

        return f"{base_title} {roman}", color, tier_index

    def get_title_shape(self, tier_index):
        # Fallback masks used only if the generated rank art cannot be loaded.
        shapes = [
            [ "00000000", "00011000", "00111100", "00011000", "00011000", "00011000", "01111110", "01111110" ],
            [ "00000011", "00000111", "00001100", "00011000", "00110000", "01100000", "11000000", "10000000" ],
            [ "00011100", "00011100", "00011100", "00011100", "00011100", "00011100", "00111111", "00111111" ],
            [ "01111100", "11111110", "11000110", "11000110", "11000110", "11000110", "01111111", "00111110" ],
            [ "00011000", "00011000", "00111100", "01111110", "11111111", "11111111", "11111111", "01111110" ],
            [ "00111100", "01111110", "01100110", "00111100", "00011000", "00011000", "00011000", "00011000" ],
            [ "00011000", "00111100", "01111110", "11111111", "01111110", "00111100", "00011000", "00000000" ],
            [ "00111100", "01111110", "11011011", "11011011", "11111111", "01111110", "00111100", "00000000" ],
            [ "11111111", "11011011", "11111111", "11111111", "01111110", "00111100", "00011000", "00000000" ],
            [ "10011001", "11011011", "11111111", "01111110", "11111111", "00111100", "01111110", "01000010" ]
        ]
        return shapes[tier_index] if tier_index < len(shapes) else shapes[-1]

    def load_rank_icon_images(self):
        """Loads the generated rank medallions used by the header avatar."""
        rank_names = [
            "novice",
            "apprentice",
            "journeyman",
            "adept",
            "expert",
            "master",
            "grandmaster",
            "champion",
            "hero",
            "legend",
        ]
        icon_dir = os.path.join(self.base_dir, "assets", "rank_icons")
        images = []
        for index, name in enumerate(rank_names):
            path = os.path.join(icon_dir, f"rank_{index:02d}_{name}.png")
            try:
                images.append(tk.PhotoImage(file=path))
            except tk.TclError:
                images.append(None)
        return images

    def load_app_icon_image(self):
        """Loads the app icon for Tk windows when the PNG asset is available."""
        path = os.path.join(self.base_dir, "assets", "app_icon", "lifexp_icon.png")
        try:
            image = tk.PhotoImage(file=path)
            self.root.iconphoto(True, image)
            return image
        except tk.TclError:
            return None

    def update_avatar(self, tier_index, color, progress, roman="I", glow_progress=0.0, glow_color=None, ring_progress=None):
        """Draws the user title icon and a circular progress bar around it."""
        # Redrawing starts by clearing the canvas. Canvas drawings are not widgets;
        # they are items that stay until explicitly deleted.
        self.avatar_canvas.delete("all")

        # The ring is inset by a small padding value so its stroke does not touch the
        # edge of the canvas.
        pad = 4
        s = self.avatar_size
        glow_progress = max(0.0, min(glow_progress, 1.0))
        focus_color = glow_color or color
        active_progress = progress if ring_progress is None else max(0.0, min(ring_progress, 1.0))

        # The avatar progress ring is two pieces: a full background oval and then a
        # colored arc that covers only the completed percentage.
        track_color = self._blend_color(self.bg_light, self.text_color, 0.12)
        self.avatar_canvas.create_oval(pad, pad, s-pad, s-pad, outline=track_color, width=4)

        angle = int(360 * active_progress)
        if angle > 0:
            ring_width = 4 + int(4 * glow_progress)
            ring_color = self._blend_color(color, focus_color, glow_progress)
            self.avatar_canvas.create_arc(pad, pad, s-pad, s-pad, start=90, extent=-angle, outline=ring_color, style=tk.ARC, width=ring_width)

        if glow_progress > 0:
            glow_fill = self._blend_color(self.bg_light, focus_color, min(0.45, glow_progress * 0.45))
            self.avatar_canvas.create_oval(8, 8, s - 8, s - 8, fill=glow_fill, outline="")

        rank_icon = None
        if self.rank_icon_images and 0 <= tier_index < len(self.rank_icon_images):
            rank_icon = self.rank_icon_images[tier_index]

        if rank_icon:
            self.avatar_canvas.create_image(s / 2, s / 2, image=rank_icon)
        else:
            shape = self.get_title_shape(tier_index)
            grid_size = len(shape)
            pixel_size = (s - 20) // grid_size
            offset = (s - (grid_size * pixel_size)) // 2
            for y in range(grid_size):
                for x in range(grid_size):
                    if shape[y][x] == "1":
                        x1 = offset + (x * pixel_size)
                        y1 = offset + (y * pixel_size)
                        icon_color = self._blend_color(color, focus_color, glow_progress * 0.70)
                        self.avatar_canvas.create_rectangle(x1, y1, x1+pixel_size, y1+pixel_size, fill=icon_color, outline="")

        roman = roman if roman in ("I", "II", "III", "IV", "V") else "I"
        numeral_font_size = 7 if len(roman) >= 3 else 8
        badge_fill = self._blend_color("#0F111A", color, 0.18)
        badge_outline = self._blend_color(color, "#FFFFFF", 0.28 + (glow_progress * 0.32))
        text_color = self.get_readable_text_color(badge_fill, "#FFFFFF")
        self.avatar_canvas.create_rectangle(s - 24, s - 20, s - 5, s - 6, fill=badge_fill, outline=badge_outline, width=1)
        self.avatar_canvas.create_text(
            s - 14,
            s - 13,
            text=roman,
            fill=text_color,
            font=("{San Francisco}", numeral_font_size, "bold")
        )

    def format_account_level_text(self, total_level, xp_into_level, xp_needed, total_xp):
        """Returns the compact account level text shown in the header."""
        return f"Total Lvl: {total_level}  |  {xp_into_level} / {xp_needed} XP  |  {total_xp} Total XP"

    def update_header(self, animate_rank=True):
        """Calculates total global XP and Level and updates the UI."""
        # Total account XP is reconstructed from every attribute. Stored XP only keeps
        # the current level's remainder, so previous level costs are added back in.
        total_xp = sum(self.get_total_xp_for_stat(stat) for stat in self.data["stats"].values())

        # Account levels use an Elden Ring-inspired cost curve instead of a fixed
        # 500 XP chunk. The first level still costs 500 XP, then each level uses a
        # higher multiplier so long-term rank progress slows down naturally.
        total_level, xp_into_level, xp_needed = self.get_account_level_progress(total_xp)
        progress = xp_into_level / float(xp_needed)

        # Once the total level is known, the header labels and avatar can be updated
        # with the matching title, color, and icon.
        title, color, tier_index = self.get_title_info(total_level)
        roman = title.rsplit(" ", 1)[-1]
        self.user_name_label.config(text=title, fg=color)
        self.user_level_label.config(text=self.format_account_level_text(total_level, xp_into_level, xp_needed, total_xp), fg=self.accent_green)

        # This block plays a rank-up animation only after startup. current_total_level
        # starts at 0 so loading an existing save does not trigger old animations.
        rank_event = None
        previous_level = self.current_total_level
        if self.current_total_level != 0 and total_level > self.current_total_level:
            rank_event = {
                "title": title,
                "color": color,
                "previous_level": previous_level,
                "total_level": total_level,
                "xp_into_level": xp_into_level,
                "xp_needed": xp_needed,
                "total_xp": total_xp,
                "tier_index": tier_index,
                "roman": roman,
                "progress": progress
            }
            if animate_rank and self.animations_enabled:
                self.play_rank_up_animation(rank_event)

        self.current_total_level = total_level
        if not (rank_event and animate_rank and self.animations_enabled):
            self.update_avatar(tier_index, color, progress, roman=roman)
        return rank_event

    def setup_ui(self):
        """Initializes the main tabbed interface of the application."""
        # The Notebook widget creates tabs. Each tab is just a Frame that later receives
        # its own controls.
        self.notebook = ttk.Notebook(self.root)
        self.notebook.configure(takefocus=False)
        self.notebook.pack(expand=True, fill='both', padx=20, pady=20)

        self.tab_tasks = ttk.Frame(self.notebook)
        self.tab_character = ttk.Frame(self.notebook)
        self.tab_summary = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)

        # After the tab frames exist, they are registered with the notebook and given
        # the labels the user clicks.
        self.tab_icons = self.build_tab_icons()
        self.notebook.add(self.tab_tasks, text=" Quest Log", image=self.tab_icons["tasks"], compound=tk.LEFT)
        self.notebook.add(self.tab_character, text=" Character Info", image=self.tab_icons["character"], compound=tk.LEFT)
        self.notebook.add(self.tab_summary, text=" Chronicles", image=self.tab_icons["chronicles"], compound=tk.LEFT)
        self.notebook.add(self.tab_settings, text=" Settings", image=self.tab_icons["settings"], compound=tk.LEFT)
        self.notebook.bind("<Motion>", self.handle_tab_hover_motion)
        self.notebook.bind("<Leave>", lambda event: self.set_tab_hover(False))
        self.notebook.bind("<<NotebookTabChanged>>", self.handle_notebook_tab_changed)

        # Each tab is built by its own helper method. This keeps setup_ui() readable
        # and separates the three screens of the app.
        self.setup_tasks_tab()
        self.setup_character_tab()
        self.setup_summary_tab()
        self.setup_settings_tab()
        self.bind_global_scroll_events()

    def create_pixel_icon(self, pattern, palette, pixel_size=3):
        """Turns a small character grid into a vibrant PhotoImage pixel icon."""
        # Calculate the total width and height based on the pixel grid.
        # tk.PhotoImage creates an empty image in memory that we can draw pixels onto.
        width = len(pattern[0]) * pixel_size
        height = len(pattern) * pixel_size
        image = tk.PhotoImage(width=width, height=height)

        # Loop through every row and column of the pattern to paint each "pixel" block.
        for y, row in enumerate(pattern):
            for x, cell in enumerate(row):
                if cell != ".":
                    color = palette[cell]
                    image.put(
                        color,
                        to=(
                            x * pixel_size,
                            y * pixel_size,
                            (x + 1) * pixel_size,
                            (y + 1) * pixel_size
                        )
                    )

        return image

    def build_tab_icons(self):
        """Creates consistent 24px navigation icons for the main tabs."""
        size = 24
        line = "#D8DEE9"
        muted = "#6F7A8A"
        quest = "#88C0D0"
        character = "#FFB020"
        chronicle = "#EBCB8B"
        settings = "#A3BE8C"

        # The small helper functions below draw simple shapes into a PhotoImage. They
        # work like a tiny pixel-art toolkit used only inside this method.
        def icon():
            return tk.PhotoImage(width=size, height=size)

        def rect(image, x1, y1, x2, y2, color):
            image.put(color, to=(int(x1), int(y1), int(x2), int(y2)))

        def dot(image, cx, cy, radius, color):
            # A dot is made by checking nearby pixels and filling the ones inside a circle.
            radius = int(radius)
            for y in range(int(cy) - radius, int(cy) + radius + 1):
                for x in range(int(cx) - radius, int(cx) + radius + 1):
                    if 0 <= x < size and 0 <= y < size and ((x - cx) ** 2 + (y - cy) ** 2) <= radius ** 2:
                        image.put(color, (x, y))

        def stroke(image, x1, y1, x2, y2, color, width=2):
            # A stroke walks from one point to another and places dots along the path.
            steps = max(abs(int(x2 - x1)), abs(int(y2 - y1)), 1)
            for step in range(steps + 1):
                t = step / float(steps)
                x = x1 + ((x2 - x1) * t)
                y = y1 + ((y2 - y1) * t)
                dot(image, round(x), round(y), max(1, width // 2), color)

        def rect_outline(image, x1, y1, x2, y2, color, width=2):
            stroke(image, x1, y1, x2, y1, color, width)
            stroke(image, x2, y1, x2, y2, color, width)
            stroke(image, x2, y2, x1, y2, color, width)
            stroke(image, x1, y2, x1, y1, color, width)

        def ellipse_outline(image, cx, cy, rx, ry, color, width=2):
            # This loop steps around a circle in degrees, then stretches it into an oval.
            for degrees in range(0, 360, 3):
                radians = math.radians(degrees)
                x = cx + math.cos(radians) * rx
                y = cy + math.sin(radians) * ry
                dot(image, round(x), round(y), max(1, width // 2), color)

        tasks = icon()
        rect_outline(tasks, 6, 5, 18, 21, line, 2)
        rect(tasks, 9, 3, 15, 6, quest)
        stroke(tasks, 8, 10, 10, 12, quest, 2)
        stroke(tasks, 10, 12, 14, 8, quest, 2)
        stroke(tasks, 8, 16, 10, 18, quest, 2)
        stroke(tasks, 10, 18, 15, 13, quest, 2)

        character_icon = icon()
        ellipse_outline(character_icon, 12, 12, 8, 8, character, 2)
        dot(character_icon, 12, 9, 3, line)
        stroke(character_icon, 7, 17, 10, 14, line, 2)
        stroke(character_icon, 10, 14, 14, 14, line, 2)
        stroke(character_icon, 14, 14, 17, 17, line, 2)
        stroke(character_icon, 12, 2, 12, 5, character, 2)

        chronicles = icon()
        stroke(chronicles, 6, 4, 6, 20, muted, 2)
        rect_outline(chronicles, 7, 5, 19, 20, line, 2)
        stroke(chronicles, 10, 15, 13, 12, chronicle, 2)
        stroke(chronicles, 13, 12, 15, 14, chronicle, 2)
        stroke(chronicles, 15, 14, 18, 9, chronicle, 2)
        stroke(chronicles, 10, 9, 14, 9, muted, 1)

        settings_icon = icon()
        ellipse_outline(settings_icon, 12, 12, 7, 7, settings, 2)
        ellipse_outline(settings_icon, 12, 12, 3, 3, line, 2)
        for x1, y1, x2, y2 in (
            (12, 2, 12, 5),
            (12, 19, 12, 22),
            (2, 12, 5, 12),
            (19, 12, 22, 12),
            (5, 5, 7, 7),
            (17, 17, 19, 19),
            (5, 19, 7, 17),
            (17, 7, 19, 5),
        ):
            stroke(settings_icon, x1, y1, x2, y2, settings, 2)

        return {
            "tasks": tasks,
            "character": character_icon,
            "chronicles": chronicles,
            "settings": settings_icon
        }

    def create_level_up_arrow_icon(self, color):
        """Creates a pixel arrow used by level-up reward popups."""
        # Level-up uses generated pixel icons instead of emojis so reward feedback stays
        # inside the app's generated pixel-art language.
        pattern = [
            "....Y....",
            "...YYY...",
            "..YYYYY..",
            ".YYYYYYY.",
            "...YYY...",
            "...YYY...",
            "...YYY...",
            "...YYY...",
            "...YYY...",
            "........."
        ]
        palette = {"Y": color}
        return self.create_pixel_icon(pattern, palette, pixel_size=4)

    def get_quest_action_palette(self, role):
        """Returns compact button colors for the quest action rail."""
        # The custom Quest Log buttons need several colors: normal fill, hover fill,
        # text, border, and glow. Each one starts from the same semantic action color.
        color = self.get_action_color(role)
        fill = self._blend_color(color, "#FFFFFF", 0.35)
        return {
            "fill": fill,
            "fg": self.get_action_text_color(fill),
            "accent": color,
            "hover": color,
            "hover_fg": self.get_action_text_color(color),
            "border": color,
            "glow": color
        }

    def create_quest_action_button(self, parent, icon, text, role, command, strong_feedback=False):
        """Builds an icon-led Tk button with click feedback for quest actions."""
        palette = self.get_quest_action_palette(role)
        border = tk.Frame(parent, bg=palette["border"])
        button = tk.Frame(
            border,
            bg=palette["fill"],
            cursor="hand2",
        )
        button.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        icon_label = tk.Label(
            button,
            text=icon,
            bg=palette["fill"],
            fg=palette["fg"],
            font=("{San Francisco}", 11, "bold"),
            cursor="hand2"
        )
        icon_label.pack(side=tk.LEFT, padx=(9, 7), pady=7)

        text_label = tk.Label(
            button,
            text=text,
            bg=palette["fill"],
            fg=palette["fg"],
            font=("{San Francisco}", 10, "bold"),
            cursor="hand2"
        )
        text_label.pack(side=tk.LEFT, pady=7)

        button._quest_role = role
        button._quest_palette = palette
        button._quest_hovering = False
        button._quest_hover_token = 0
        button._quest_labels = (icon_label, text_label)
        if not hasattr(self, "quest_action_buttons"):
            self.quest_action_buttons = []
        self.quest_action_buttons.append(button)

        for widget in (button, icon_label, text_label):
            widget.bind("<Button-1>", lambda event, surface=button: self.run_quest_action(surface, command, strong_feedback))
            widget.bind("<Enter>", lambda event, surface=button: self.handle_quest_hover_enter(surface))
            widget.bind("<Leave>", lambda event, surface=button: self.handle_quest_hover_leave(surface))
        return border

    def configure_quest_surface(self, button, bg, fg):
        """Colors a custom quest action surface and its labels."""
        button.configure(bg=bg)
        for label in getattr(button, "_quest_labels", ()):
            label.configure(bg=bg, fg=fg)

    def pointer_inside_widget(self, widget):
        """Returns True when the mouse pointer is inside a widget's screen box."""
        try:
            pointer_x = widget.winfo_pointerx()
            pointer_y = widget.winfo_pointery()
            left = widget.winfo_rootx()
            top = widget.winfo_rooty()
            right = left + widget.winfo_width()
            bottom = top + widget.winfo_height()
        except tk.TclError:
            return False
        return left <= pointer_x < right and top <= pointer_y < bottom

    def handle_quest_hover_enter(self, button):
        """Starts quest hover only when entering the whole control."""
        self.set_quest_button_hover(button, True)

    def handle_quest_hover_leave(self, button):
        """Leaves quest hover only after the pointer exits the whole control."""
        self.root.after(12, lambda surface=button: (
            surface.winfo_exists()
            and not self.pointer_inside_widget(surface.master)
            and self.set_quest_button_hover(surface, False)
        ))

    def set_quest_button_hover(self, button, is_hovering):
        """Fills a quest button with its action color while hovered."""
        if not button.winfo_exists():
            return
        if button._quest_hovering == is_hovering:
            return
        button._quest_hovering = is_hovering
        button._quest_hover_token += 1
        token = button._quest_hover_token
        palette = button._quest_palette
        start = str(button.cget("bg"))
        end = palette["hover"] if is_hovering else palette["fill"]
        end_fg = palette["hover_fg"] if is_hovering else palette["fg"]

        def step(index=1, frames=5):
            if not button.winfo_exists() or button._quest_hovering != is_hovering or button._quest_hover_token != token:
                return
            ratio = index / float(frames)
            self.configure_quest_surface(button, self._blend_color(start, end, ratio), end_fg)
            if index < frames:
                self.root.after(20, step, index + 1, frames)

        step()

    def refresh_quest_action_buttons(self):
        """Updates custom action buttons after a theme change."""
        if not hasattr(self, "quest_action_buttons"):
            return

        for button in self.quest_action_buttons:
            if not button.winfo_exists():
                continue
            palette = self.get_quest_action_palette(button._quest_role)
            button._quest_palette = palette
            self.configure_quest_surface(button, palette["fill"], palette["fg"])
            button.master.configure(bg=palette["border"])

    def create_summary_timeframe_button(self, parent, label, timeframe):
        """Builds one segmented Chronicles timeframe control."""
        button = tk.Label(
            parent,
            text=label,
            bg=self.bg_dark,
            fg=self.dark_surface_text_color,
            font=("{San Francisco}", 10, "bold"),
            padx=14,
            pady=8,
            cursor="hand2"
        )
        button._summary_timeframe = timeframe
        button.bind("<Button-1>", lambda event, value=timeframe: self.show_summary(value))
        button.pack(side=tk.LEFT, padx=2, pady=2)
        return button

    def update_summary_timeframe_buttons(self):
        """Highlights the active Chronicles timeframe segment."""
        if not hasattr(self, "summary_timeframe_buttons"):
            return

        for button in self.summary_timeframe_buttons:
            if not button.winfo_exists():
                continue
            active = button._summary_timeframe == self.current_summary_timeframe
            fill = self.accent_green if active else self.bg_dark
            fg = self.accent_text_color if active else self.dark_surface_text_color
            button.configure(bg=fill, fg=fg)

    def draw_summary_graph(self, totals_by_attribute):
        """Draws the Chronicles XP distribution chart."""
        if not hasattr(self, "summary_graph_canvas"):
            return

        canvas = self.summary_graph_canvas
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        if width <= 1 or height <= 1:
            width = max(320, canvas.winfo_reqwidth())
            height = max(160, canvas.winfo_reqheight())

        canvas.configure(bg=self.bg_light)
        pad_x = 34
        top = 20
        bottom = 42
        chart_h = max(30, height - top - bottom)
        baseline = top + chart_h
        muted = self._blend_color(self.text_color, self.bg_light, 0.58)
        grid = self._blend_color(self.bg_dark, self.bg_light, 0.55)

        for index in range(4):
            y = top + (chart_h * index / 3)
            canvas.create_line(pad_x, y, width - 18, y, fill=grid)

        max_xp = max([1] + [totals_by_attribute.get(attr, 0) for attr in self.attributes])
        available_w = max(1, width - pad_x - 28)
        slot_w = available_w / len(self.attributes)
        bar_w = max(18, min(46, slot_w * 0.48))

        if max_xp <= 1 and not any(totals_by_attribute.values()):
            canvas.create_text(
                width / 2,
                height / 2,
                text="No XP logged for this chapter.",
                fill=muted,
                font=("{San Francisco}", 12, "bold")
            )

        for index, attr in enumerate(self.attributes):
            xp = totals_by_attribute.get(attr, 0)
            center_x = pad_x + (slot_w * index) + (slot_w / 2)
            bar_h = 4 if xp <= 0 else max(8, (xp / max_xp) * (chart_h - 8))
            left = center_x - (bar_w / 2)
            right = center_x + (bar_w / 2)
            top_y = baseline - bar_h
            canvas.create_rectangle(left, top_y, right, baseline, fill=self.attr_colors[attr], outline="")
            canvas.create_text(center_x, top_y - 10, text=str(xp), fill=self.text_color, font=("{San Francisco}", 9, "bold"))
            canvas.create_text(center_x, baseline + 18, text=attr[:3].upper(), fill=muted, font=("{San Francisco}", 8, "bold"))

    def improve_color_contrast(self, color, background, minimum_ratio=4.5):
        """Pushes a color toward black or white until it is readable on a surface."""
        if self.get_contrast_ratio(color, background) >= minimum_ratio:
            return color

        black = "#000000"
        white = "#FFFFFF"
        target = white if self.get_contrast_ratio(white, background) > self.get_contrast_ratio(black, background) else black
        for step in range(1, 11):
            candidate = self._blend_color(color, target, step / 10.0)
            if self.get_contrast_ratio(candidate, background) >= minimum_ratio:
                return candidate
        return target

    def get_attribute_text_color(self, attr, background=None):
        """Returns an attribute color adjusted for use as text."""
        # Attribute colors are bright enough for bars and trophies, but not always for
        # text. This helper nudges them lighter or darker until the text can be read.
        background = background or self.bg_light
        return self.improve_color_contrast(self.attr_colors[attr], background)

    def get_summary_combo_colors(self, background=None):
        """Returns combo tag colors that remain readable on the ledger background."""
        background = background or self.bg_dark
        return {
            "combo_blue": self.improve_color_contrast(self.attr_colors["Intelligence"], background),
            "combo_red": self.improve_color_contrast(self.attr_colors["Strength"], background),
            "combo_gold": self.improve_color_contrast(self.attr_colors["Agility"], background)
        }

    def configure_summary_body_tags(self, body):
        """Applies the shared Chronicles text tags to one ledger body."""
        combo_colors = self.get_summary_combo_colors(body.cget("bg"))
        body.tag_configure("bold", font=("{San Francisco}", 9, "bold"))
        body.tag_configure("combo_blue", foreground=combo_colors["combo_blue"], font=("{San Francisco}", 10, "bold"))
        body.tag_configure("combo_red", foreground=combo_colors["combo_red"], font=("{San Francisco}", 10, "bold"))
        body.tag_configure("combo_gold", foreground=combo_colors["combo_gold"], font=("{San Francisco}", 10, "bold"))

    def find_summary_body_under_pointer(self):
        """Returns the Chronicles entry list currently under the mouse pointer."""
        if not hasattr(self, "summary_cards"):
            return None

        try:
            pointer_x = self.root.winfo_pointerx()
            pointer_y = self.root.winfo_pointery()
        except tk.TclError:
            return None

        for widgets in self.summary_cards.values():
            body = widgets["body"]
            if not body.winfo_exists():
                continue
            left = body.winfo_rootx()
            top = body.winfo_rooty()
            right = left + body.winfo_width()
            bottom = top + body.winfo_height()
            if left <= pointer_x < right and top <= pointer_y < bottom:
                return body
        return None

    def _generic_scroll(self, event, scroll_target, speed_units):
        """Generic mouse wheel and trackpad scroll helper for scrollable widgets."""
        if scroll_target is None or not scroll_target.winfo_exists():
            return None

        if getattr(event, "num", None) == 4:
            units = -1
        elif getattr(event, "num", None) == 5:
            units = 1
        else:
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return None
            if abs(delta) >= 120:
                units = -(delta // 120)
            else:
                units = -delta

        scroll_target.yview_scroll(units * speed_units, "units")
        return "break"

    def scroll_summary_body(self, event):
        """Scrolls the Chronicles entry list under the pointer."""
        body = self.find_summary_body_under_pointer()
        return self._generic_scroll(event, body, speed_units=4)

    def scroll_settings_canvas(self, event):
        """Scrolls the Settings tab content without resizing the main window."""
        canvas = getattr(self, "settings_canvas", None)
        return self._generic_scroll(event, canvas, speed_units=3)

    def create_modern_scrollbar(self, parent, target, width=14):
        """Creates a slim canvas scrollbar wired to a y-scrollable widget."""
        live_scrollbars = []
        for existing in self.modern_scrollbars:
            canvas = existing["canvas"]
            try:
                if canvas.winfo_exists():
                    live_scrollbars.append(existing)
            except tk.TclError:
                continue
        self.modern_scrollbars = live_scrollbars

        state = {"first": 0.0, "last": 1.0}
        scrollbar = tk.Canvas(parent, width=width, bg=self.bg_light, highlightthickness=0, cursor="sb_v_double_arrow")

        def draw(event=None):
            if not scrollbar.winfo_exists():
                return
            scrollbar.delete("all")
            canvas_width = max(1, scrollbar.winfo_width())
            canvas_height = max(1, scrollbar.winfo_height())
            first = state["first"]
            last = state["last"]
            if last - first >= 0.999:
                return

            track_x = canvas_width // 2
            track_color = self._blend_color(self.bg_light, self.text_color, 0.20)
            scrollbar.create_line(track_x, 8, track_x, canvas_height - 8, fill=track_color, width=max(4, canvas_width // 3), capstyle=tk.ROUND)

            usable_top = 8
            usable_height = max(1, canvas_height - 16)
            thumb_top = usable_top + (first * usable_height)
            thumb_bottom = usable_top + (last * usable_height)
            min_thumb = 34
            if thumb_bottom - thumb_top < min_thumb:
                center = (thumb_top + thumb_bottom) / 2
                thumb_top = max(usable_top, center - (min_thumb / 2))
                thumb_bottom = min(usable_top + usable_height, thumb_top + min_thumb)
            scrollbar.create_line(track_x, thumb_top, track_x, thumb_bottom, fill=self.accent_green, width=max(5, canvas_width // 2), capstyle=tk.ROUND)

        def set_view(first, last):
            state["first"] = float(first)
            state["last"] = float(last)
            draw()

        def jump(event):
            if not target.winfo_exists():
                return "break"
            canvas_height = max(1, scrollbar.winfo_height())
            page = max(0.01, state["last"] - state["first"])
            ratio = max(0.0, min(1.0, (event.y - 8) / float(max(1, canvas_height - 16))))
            target.yview_moveto(max(0.0, min(1.0 - page, ratio - (page / 2))))
            draw()
            return "break"

        target.configure(yscrollcommand=set_view)
        scrollbar.bind("<Configure>", draw)
        scrollbar.bind("<Button-1>", jump)
        scrollbar.bind("<B1-Motion>", jump)
        scrollbar._lifexp_draw = draw
        self.modern_scrollbars.append({"canvas": scrollbar, "draw": draw})
        return scrollbar

    def route_global_scroll(self, event):
        """Routes trackpad and wheel events to the active scrollable tab content."""
        if hasattr(self, "notebook"):
            try:
                selected_tab = self.notebook.nametowidget(self.notebook.select())
            except tk.TclError:
                selected_tab = None

            if selected_tab == getattr(self, "tab_settings", None):
                return self.scroll_settings_canvas(event)

        return self.scroll_summary_body(event)

    def bind_global_scroll_events(self):
        """Installs one app-wide scroll router for mouse wheels and trackpads."""
        for sequence in ("<MouseWheel>", "<Shift-MouseWheel>", "<Button-4>", "<Button-5>"):
            self.root.bind_all(sequence, self.route_global_scroll)

    def run_quest_action(self, button, command, strong_feedback=False):
        """Runs a quest action after immediate tactile UI feedback."""
        if strong_feedback and not self.task_tree.selection():
            self.play_quest_button_miss(button)
            command()
            return

        self.play_quest_button_feedback(button, strong=strong_feedback, on_done=command)

    def play_quest_button_miss(self, button):
        """Flashes the Complete button when no quest is selected."""
        palette = button._quest_palette
        miss_color = self.attr_colors["Strength"]
        sequence = [miss_color, palette["fill"], miss_color, palette["fill"]]

        def step(index=0):
            if index >= len(sequence) or not button.winfo_exists():
                return
            self.configure_quest_surface(button, sequence[index], palette["fg"])
            self.root.after(55, step, index + 1)

        step()

    def play_quest_button_feedback(self, button, strong=False, on_done=None):
        """Animates the button frame as a short neon pulse before running the action."""
        if not button.winfo_exists():
            if on_done:
                on_done()
            return

        palette = button._quest_palette
        border = button.master
        glow = palette["glow"]
        base_fill = palette["hover"] if button._quest_hovering else palette["fill"]
        total_frames = 18
        peak_frame = total_frames // 2

        def step(index=0):
            if not button.winfo_exists() or not border.winfo_exists():
                if on_done:
                    on_done()
                return
            if index <= total_frames:
                if index <= peak_frame:
                    progress = self.ease_smoothstep(index / float(peak_frame))
                else:
                    progress = 1 - self.ease_smoothstep((index - peak_frame) / float(total_frames - peak_frame))

                border_color = self._blend_color(palette["border"], self._blend_color(glow, "#FFFFFF", 0.42), progress)
                fill_color = self._blend_color(base_fill, self._blend_color(palette["hover"], "#FFFFFF", 0.16), progress * 0.75)
                fg = palette["hover_fg"] if progress > 0.08 or button._quest_hovering else palette["fg"]
                border.configure(bg=border_color)
                self.configure_quest_surface(button, fill_color, fg)
                self.root.after(18, step, index + 1)
                return

            border.configure(bg=palette["border"])
            self.set_quest_button_hover(button, button._quest_hovering)
            if on_done:
                on_done()

        step()

    def setup_tasks_tab(self):
        """Paints the 'Quest Log' tab (task list and action buttons)."""
        # The Quest Log tab is split into a large table on the left and an action panel
        # on the right. Each area uses the same light "surface" color as the Accept
        # Quest window so the whole app feels like one design system.
        page = tk.Frame(self.tab_tasks, bg=self.bg_dark)
        page.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        list_frame = tk.Frame(page, bg=self.bg_light)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 14), pady=0)

        tk.Label(
            list_frame,
            text="Active Quests",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 16, "bold")
        ).pack(anchor=tk.W, padx=16, pady=(14, 10))

        table_frame = tk.Frame(list_frame, bg=self.bg_light)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        # Treeview acts like a spreadsheet-style table. The code defines named columns,
        # then configures each heading and width.
        self.task_tree = ttk.Treeview(table_frame, columns=("Task", "Attribute", "XP"), show="headings", selectmode="extended")
        self.task_tree.heading("Task", text="Quest Name")
        self.task_tree.heading("Attribute", text="Scaling Attribute")
        self.task_tree.heading("XP", text="XP")

        self.task_tree.column("Task", width=250, anchor=tk.W)
        self.task_tree.column("Attribute", width=220, anchor=tk.CENTER)
        self.task_tree.column("XP", width=100, anchor=tk.CENTER)

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.task_tree.bind("<Command-Button-1>", self.toggle_task_tree_selection)
        self.task_tree.bind("<Control-Button-1>", self.toggle_task_tree_selection)

        # The custom scrollbar keeps the table controls visually consistent.
        scrollbar = self.create_modern_scrollbar(table_frame, self.task_tree)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))

        # Buttons call methods instead of doing work directly. This is an event-driven
        # style: Tkinter waits for a click, then runs the command function.
        self.quest_action_buttons = []
        control_frame = tk.Frame(page, bg=self.bg_light, width=210)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        control_frame.pack_propagate(False)

        tk.Label(
            control_frame,
            text="Quest Actions",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 14, "bold")
        ).pack(anchor=tk.W, padx=16, pady=(16, 4))

        action_stack = tk.Frame(control_frame, bg=self.bg_light)
        action_stack.pack(fill=tk.X, padx=12, pady=(8, 0))

        self.create_quest_action_button(action_stack, "+", "Accept Quest", "accept", self.add_task_dialog).pack(fill=tk.X, pady=(0, 9))
        self.create_quest_action_button(action_stack, "✓", "Complete Quest", "complete", self.complete_task, strong_feedback=True).pack(fill=tk.X, pady=(0, 9))
        self.create_quest_action_button(action_stack, "✎", "Edit Quest", "edit", self.edit_task_dialog).pack(fill=tk.X, pady=(0, 9))
        self.create_quest_action_button(action_stack, "×", "Abandon Quest", "abandon", self.delete_task).pack(fill=tk.X, pady=(0, 9))

    def get_tiers(self):
        # Trophy tiers expand when the character gets stronger. Below level 25 the UI
        # shows three tiers; after that it reveals higher long-term goals.
        tiers_expanded = self._max_stat_level > 25
        if self._tiers_cache is None or tiers_expanded != self._tiers_cache_expanded:
            self._tiers_cache_expanded = tiers_expanded
            if tiers_expanded:
                self._tiers_cache = [("Apprentice", 5), ("Adept", 10), ("Master", 25), ("Grandmaster", 50), ("Legend", 100)]
            else:
                self._tiers_cache = [("Apprentice", 5), ("Adept", 10), ("Master", 25)]
        return self._tiers_cache

    def calculate_trophy_canvas_size(self, tiers):
        """Returns trophy canvas dimensions that fit the current trophy room."""
        columns = max(1, len(self.attributes))
        rows = max(1, len(tiers))

        frame_width = self.trophies_frame.winfo_width()
        if frame_width <= 1:
            frame_width = max(420, self.root.winfo_width() - 60)

        frame_height = self.trophies_frame.winfo_height()
        if frame_height <= 1:
            frame_height = max(240, self.root.winfo_height() - 440)

        width_per_column = (frame_width - 28) / columns
        height_per_row = (frame_height - 30 - (rows * 17)) / rows

        max_width = 94 if rows <= 3 else 70
        min_width = 52 if rows <= 3 else 38
        width = int(max(min_width, min(max_width, width_per_column * 0.72)))

        preferred_height = width * 1.12
        max_height = 108 if rows <= 3 else 78
        min_height = 58 if rows <= 3 else 44
        height = int(max(min_height, min(max_height, preferred_height, height_per_row)))

        return width, height

    def schedule_trophy_room_resize(self, event=None):
        """Debounces trophy resizing while the window is being dragged."""
        if not hasattr(self, "trophies_frame"):
            return
        if not self._trophy_room_built:
            if self.trophy_room_has_visible_geometry():
                self.prepare_visible_trophy_room()
            return
        if self._trophy_resize_after_id is not None:
            self.root.after_cancel(self._trophy_resize_after_id)
        self._trophy_resize_after_id = self.root.after(60, self.resize_trophy_canvases)

    def trophy_room_has_visible_geometry(self):
        """Returns whether the trophy room has a real mapped size."""
        if not hasattr(self, "trophies_frame"):
            return False
        return (
            self.trophies_frame.winfo_ismapped()
            and self.trophies_frame.winfo_width() > 1
            and self.trophies_frame.winfo_height() > 1
        )

    def prepare_visible_trophy_room(self):
        """Builds trophy artwork only after the Character tab is visible."""
        if not hasattr(self, "trophies_frame"):
            return
        if self._trophy_resize_after_id is not None:
            self.root.after_cancel(self._trophy_resize_after_id)
            self._trophy_resize_after_id = None
        if not self.trophy_room_has_visible_geometry():
            self._trophy_resize_after_id = self.root.after(10, self.prepare_visible_trophy_room)
            return
        if not self._trophy_room_built:
            self.rebuild_trophy_room()
        else:
            self.resize_trophy_canvases()

    def resize_trophy_canvases(self):
        """Resizes trophy canvases and redraws art for the current room dimensions."""
        self._trophy_resize_after_id = None
        if not self._trophy_room_built or not self.trophy_canvases:
            return

        tiers = self.get_tiers()
        size = self.calculate_trophy_canvas_size(tiers)
        if size == self._trophy_canvas_size:
            return

        self._trophy_canvas_size = size
        width, height = size
        for canvas in self.trophy_canvases.values():
            canvas.configure(width=width, height=height)

        self.redraw_trophies(tiers)
        if self.trophy_room_has_visible_geometry():
            self._trophy_room_has_real_layout = True

    def redraw_trophies(self, tiers):
        """Draws every trophy using current levels and canvas sizes."""
        for attr in self.attributes:
            lvl = self.data["stats"][attr]["level"]
            for tier_name, level_req in tiers:
                canvas = self.trophy_canvases.get(f"{attr}_{tier_name}")
                if canvas is None:
                    continue
                progress = min(lvl / float(level_req), 1.0)
                self.draw_trophy(canvas, attr, progress, self.attr_colors[attr], level_req)

    def rebuild_trophy_room(self):
        # Rebuilding means clearing the old trophy widgets, then creating a fresh grid
        # that matches the current tier list.
        if not self.trophy_room_has_visible_geometry():
            for widget in self.trophies_frame.winfo_children():
                widget.destroy()
            self.trophy_canvases = {}
            self._trophy_room_built = False
            self._trophy_room_has_real_layout = False
            self._trophy_canvas_size = None
            self._last_rendered_tiers = None
            return

        self._trophy_room_has_real_layout = self.trophy_room_has_visible_geometry()
        for widget in self.trophies_frame.winfo_children():
            widget.destroy()

        self.trophy_canvases = {}
        tiers = self.get_tiers()
        self._last_rendered_tiers = tiers

        # More tiers means more rows, but dimensions still come from the current room
        # so resizing the window makes the trophies grow or shrink with it.
        expanded_tiers = len(tiers) > 3
        icon_width, icon_height = self.calculate_trophy_canvas_size(tiers)
        self._trophy_canvas_size = (icon_width, icon_height)
        font_size = 7 if expanded_tiers else 8
        attr_font_size = 8 if expanded_tiers else 9
        cell_pady = 1 if expanded_tiers else 2

        # The outer loop creates one column per attribute. The inner loop creates one
        # trophy cell per tier inside that attribute column.
        for col_idx, attr in enumerate(self.attributes):
            tk.Label(
                self.trophies_frame,
                text=attr,
                bg=self.bg_light,
                fg=self.attr_colors[attr],
                font=("{San Francisco}", attr_font_size, "bold")
            ).grid(row=0, column=col_idx, pady=(5, 0))
            self.trophies_frame.columnconfigure(col_idx, weight=1)

            for row_idx, (tier_name, level_req) in enumerate(tiers):
                cell_frame = tk.Frame(self.trophies_frame, bg=self.bg_light)
                cell_frame.grid(row=row_idx+1, column=col_idx, pady=cell_pady)

                c = tk.Canvas(cell_frame, width=icon_width, height=icon_height, bg=self.bg_light, highlightthickness=0)
                c.pack()

                tk.Label(cell_frame, text=f"Lvl {level_req}", font=("{San Francisco}", font_size), bg=self.bg_light, fg=self.text_color).pack()

                self.trophy_canvases[f"{attr}_{tier_name}"] = c

        self.redraw_trophies(tiers)
        self._trophy_room_built = True

    def setup_character_tab(self):
        """Paints the 'Character Info' tab (progress bars and pixel trophies)."""
        # The Character tab has two main parts: numeric stat progress at the top and
        # visual trophy progress at the bottom.
        page = tk.Frame(self.tab_character, bg=self.bg_dark)
        page.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        stats_frame = tk.Frame(page, bg=self.bg_light)
        stats_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 14))

        tk.Label(
            stats_frame,
            text="Hero Attributes",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 16, "bold")
        ).grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=16, pady=(14, 10))

        # A dictionary stores references to labels and progress bars so other methods
        # can update them later without recreating them.
        self.stat_labels = {}
        for i, attr in enumerate(self.attributes):
            row = i + 1
            tk.Frame(stats_frame, bg=self.attr_colors[attr], width=10, height=26).grid(row=row, column=0, sticky=tk.W, padx=(16, 8), pady=8)
            tk.Label(
                stats_frame,
                text=attr,
                bg=self.bg_light,
                fg=self.text_color,
                font=("{San Francisco}", 12, "bold")
            ).grid(row=row, column=1, sticky=tk.W, padx=(0, 12), pady=8)

            lbl = tk.Label(stats_frame, text="Lvl 1 (0 / 100 XP)", bg=self.bg_light, fg=self.text_color, font=("{San Francisco}", 12))
            lbl.grid(row=row, column=2, sticky=tk.W, padx=(0, 12), pady=8)
            self.stat_labels[attr] = lbl

            pb = ttk.Progressbar(stats_frame, orient='horizontal', length=250, mode='determinate', style=f'{attr}.Horizontal.TProgressbar')
            pb.grid(row=row, column=3, padx=(0, 16), pady=8, sticky=tk.EW)
            stats_frame.columnconfigure(3, weight=1)
            self.stat_labels[f"{attr}_pb"] = pb

        # The trophy room starts empty, then rebuild_trophy_room() fills it based on
        # the current maximum level and tier rules after this hidden tab is visible.
        trophy_section = tk.Frame(page, bg=self.bg_light)
        trophy_section.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        tk.Label(
            trophy_section,
            text="Visual Trophy Room",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 16, "bold")
        ).pack(anchor=tk.W, padx=16, pady=(14, 8))

        self.trophies_frame = tk.Frame(trophy_section, bg=self.bg_light)
        self.trophies_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.trophies_frame.bind("<Configure>", self.schedule_trophy_room_resize)

        self.trophy_canvases = {}
        self._trophy_room_built = False

    def setup_summary_tab(self):
        """Paints the 'Chronicles' tab (report buttons and visual data)."""
        page = tk.Frame(self.tab_summary, bg=self.bg_dark)
        page.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Chronicles uses a dashboard layout: chapter controls at the top, three quick
        # readouts, an XP distribution chart, and RPG attribute activity ledgers.
        control_frame = tk.Frame(page, bg=self.bg_light)
        control_frame.pack(fill=tk.X, pady=(0, 12))
        control_frame.grid_columnconfigure(0, weight=1)
        self.summary_light_surfaces = [control_frame]
        self.summary_dark_surfaces = []
        self.summary_primary_labels = []
        self.summary_secondary_labels = []

        heading_frame = tk.Frame(control_frame, bg=self.bg_light)
        heading_frame.grid(row=0, column=0, sticky=tk.W, padx=16, pady=(14, 12))
        self.summary_light_surfaces.append(heading_frame)

        heading_label = tk.Label(
            heading_frame,
            text="Chronicles",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 18, "bold")
        )
        heading_label.pack(anchor=tk.W)
        self.summary_primary_labels.append(heading_label)

        subtitle_label = tk.Label(
            heading_frame,
            text="Chapter records by attribute, quest chain, and XP gained",
            bg=self.bg_light,
            fg=self._blend_color(self.text_color, self.bg_light, 0.28),
            font=("{San Francisco}", 10)
        )
        subtitle_label.pack(anchor=tk.W, pady=(3, 0))
        self.summary_secondary_labels.append(subtitle_label)

        button_row = tk.Frame(control_frame, bg=self.bg_dark)
        button_row.grid(row=0, column=1, sticky=tk.E, padx=14, pady=14)
        self.summary_dark_surfaces.append(button_row)
        self.summary_timeframe_buttons = [
            self.create_summary_timeframe_button(button_row, "Daily", "daily"),
            self.create_summary_timeframe_button(button_row, "Weekly", "weekly"),
            self.create_summary_timeframe_button(button_row, "Monthly", "monthly")
        ]

        report_frame = tk.Frame(page, bg=self.bg_light)
        report_frame.pack(fill=tk.BOTH, expand=True)
        self.summary_light_surfaces.append(report_frame)

        # Here we create a dynamic title label for the report, which will update 
        # based on the selected timeframe (Daily, Weekly, Monthly).
        self.summary_title_label = tk.Label(
            report_frame,
            text="",
            font=("{San Francisco}", 13, "bold"),
            bg=self.bg_light,
            fg=self._blend_color(self.text_color, self.bg_light, 0.18)
        )
        self.summary_title_label.pack(anchor=tk.W, padx=16, pady=(14, 8))

        metrics_frame = tk.Frame(report_frame, bg=self.bg_light)
        metrics_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        self.summary_light_surfaces.append(metrics_frame)
        self.summary_metric_labels = {}
        for column, (key, label) in enumerate((
            ("activities", "Activity Types"),
            ("quests", "Quests Cleared"),
            ("xp", "XP Banked")
        )):
            metrics_frame.columnconfigure(column, weight=1, uniform="summary_metrics")
            metric = tk.Frame(metrics_frame, bg=self.bg_dark)
            metric.grid(row=0, column=column, sticky=tk.EW, padx=4)
            self.summary_dark_surfaces.append(metric)
            metric_label = tk.Label(
                metric,
                text=label,
                bg=self.bg_dark,
                fg=self._blend_color(self.dark_surface_text_color, self.bg_dark, 0.34),
                font=("{San Francisco}", 9, "bold")
            )
            metric_label.pack(anchor=tk.W, padx=12, pady=(9, 0))
            self.summary_secondary_labels.append(metric_label)
            value = tk.Label(
                metric,
                text="0",
                bg=self.bg_dark,
                fg=self.dark_surface_text_color,
                font=("{San Francisco}", 18, "bold")
            )
            value.pack(anchor=tk.W, padx=12, pady=(1, 9))
            self.summary_metric_labels[key] = value

        graph_frame = tk.Frame(report_frame, bg=self.bg_light)
        graph_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        self.summary_light_surfaces.append(graph_frame)
        graph_title = tk.Label(
            graph_frame,
            text="Attribute XP Distribution",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 12, "bold")
        )
        graph_title.pack(anchor=tk.W, pady=(0, 6))
        self.summary_primary_labels.append(graph_title)
        self.summary_graph_canvas = tk.Canvas(graph_frame, height=132, bg=self.bg_light, highlightthickness=0)
        self.summary_graph_canvas.pack(fill=tk.X)
        self.summary_attribute_totals = {attr: 0 for attr in self.attributes}
        self.summary_graph_canvas.bind("<Configure>", lambda event: self.draw_summary_graph(self.summary_attribute_totals))

        # This container frame holds the summary cards side-by-side. Each attribute
        # keeps its RPG color, but the readable text now sits on the shared surface.
        cards_frame = tk.Frame(report_frame, bg=self.bg_light)
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 14))
        self.summary_light_surfaces.append(cards_frame)

        self.summary_cards = {}
        cards_frame.rowconfigure(0, weight=1, minsize=150)
        for i, attr in enumerate(self.attributes):
            cards_frame.columnconfigure(i, weight=1, uniform="summary_cards")

            card = tk.Frame(
                cards_frame,
                bg=self.bg_dark,
                width=150,
                highlightthickness=0
            )
            card.grid(row=0, column=i, sticky=tk.NSEW, padx=5, pady=5)
            card.columnconfigure(0, weight=1)
            card.rowconfigure(3, weight=1)
            self.summary_dark_surfaces.append(card)

            strip = tk.Frame(card, bg=self.attr_colors[attr], height=5)
            strip.grid(row=0, column=0, sticky=tk.EW)

            title = tk.Label(
                card,
                text=attr,
                font=("{San Francisco}", 10, "bold"),
                bg=self.bg_dark,
                fg=self.attr_colors[attr]
            )
            title.grid(row=1, column=0, sticky=tk.W, padx=10, pady=(9, 0))

            meta = tk.Label(
                card,
                text="0 types | 0 XP",
                font=("{San Francisco}", 9),
                bg=self.bg_dark,
                fg=self._blend_color(self.dark_surface_text_color, self.bg_dark, 0.34)
            )
            meta.grid(row=2, column=0, sticky=tk.W, padx=10, pady=(1, 5))

            body_frame = tk.Frame(card, bg=self.bg_dark)
            body_frame.grid(row=3, column=0, sticky=tk.NSEW, padx=0, pady=(0, 8))
            body_frame.columnconfigure(0, weight=1)
            body_frame.rowconfigure(0, weight=1)
            self.summary_dark_surfaces.append(body_frame)

            body = tk.Text(
                body_frame,
                wrap=tk.WORD,
                height=4,
                font=("{San Francisco}", 9),
                bg=self.bg_dark,
                fg=self.dark_surface_text_color,
                bd=0,
                highlightthickness=0,
                padx=10,
                pady=6
            )
            body.grid(row=0, column=0, sticky=tk.NSEW)
            self.configure_summary_body_tags(body)
            body.config(state=tk.DISABLED)

            self.summary_cards[attr] = {
                "card": card,
                "strip": strip,
                "title": title,
                "meta": meta,
                "body_frame": body_frame,
                "body": body
            }

        self.show_summary("daily")

    def draw_font_size_slider(self):
        """Draws the Settings display-scale slider."""
        if not hasattr(self, "font_size_canvas"):
            return

        canvas = self.font_size_canvas
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        if width <= 1:
            width = max(420, canvas.winfo_reqwidth())

        height = 86
        center_y = 44
        left_label_w = 44
        right_label_w = 54
        left = left_label_w + 18
        right = max(left + 20, width - right_label_w - 18)
        values = list(range(MIN_FONT_SIZE, MAX_FONT_SIZE + 1))
        selected = int(self.font_size_slider_var.get())
        selected_index = max(0, min(len(values) - 1, values.index(selected) if selected in values else 0))
        step = (right - left) / float(max(1, len(values) - 1))
        selected_x = left + (selected_index * step)

        track_color = self._blend_color(self.text_color, self.bg_light, 0.58)
        inactive_dot = self._blend_color(self.text_color, self.bg_light, 0.30)
        glow = self._blend_color(self.accent_green, "#FFFFFF", 0.15)

        canvas.configure(bg=self.bg_light)
        canvas.create_text(14, center_y, text="Aa", anchor=tk.W, fill=self.text_color, font=("{San Francisco}", 15, "bold"))
        canvas.create_text(width - 12, center_y, text="Aa", anchor=tk.E, fill=self.text_color, font=("{San Francisco}", 22, "bold"))
        canvas.create_line(left, center_y, right, center_y, fill=track_color, width=4, capstyle=tk.ROUND)
        canvas.create_line(left, center_y, selected_x, center_y, fill=self.accent_green, width=4, capstyle=tk.ROUND)

        for index, value in enumerate(values):
            x = left + (index * step)
            radius = 7 if value != selected else 11
            if value == selected:
                canvas.create_oval(x - 20, center_y - 20, x + 20, center_y + 20, fill=self._blend_color(self.accent_green, self.bg_light, 0.70), outline="")
                fill = self.accent_green
                outline = glow
            else:
                fill = self.accent_green if value < selected else inactive_dot
                outline = fill
            canvas.create_oval(x - radius, center_y - radius, x + radius, center_y + radius, fill=fill, outline=outline, width=2)

    def set_font_size_from_slider_event(self, event):
        """Snaps the custom font-size slider to the nearest supported value."""
        if not hasattr(self, "font_size_canvas"):
            return "break"

        canvas = self.font_size_canvas
        width = max(1, canvas.winfo_width())
        left = 44 + 18
        right = max(left + 20, width - 54 - 18)
        values = list(range(MIN_FONT_SIZE, MAX_FONT_SIZE + 1))
        ratio = (event.x - left) / float(max(1, right - left))
        index = max(0, min(len(values) - 1, int(round(ratio * (len(values) - 1)))))
        self.font_size_slider_var.set(values[index])
        self.apply_font_size_from_slider()
        return "break"

    def apply_font_size_from_slider(self):
        """Applies the selected display scale after a short debounce."""
        self.font_size = int(self.font_size_slider_var.get())
        if hasattr(self, "font_value_label"):
            self.font_value_label.config(text=f"{self.font_size} pt")
        self.draw_font_size_slider()
        if getattr(self, "font_apply_after_id", None) is not None:
            self.root.after_cancel(self.font_apply_after_id)

        def commit_font_size():
            self.font_apply_after_id = None
            self.apply_display_preferences(save=True)

        self.font_apply_after_id = self.root.after(120, commit_font_size)

    def setup_settings_tab(self):
        """Paints the Settings tab for themes, display, animations, reset, and app info."""
        self.root.option_add("*TCombobox*Listbox.background", self.bg_light)
        self.root.option_add("*TCombobox*Listbox.foreground", self.text_color)
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.accent_green)
        self.root.option_add("*TCombobox*Listbox.selectForeground", self.accent_text_color)

        page = tk.Frame(self.tab_settings, bg=self.bg_dark)
        page.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.settings_canvas = tk.Canvas(
            page,
            bg=self.bg_dark,
            highlightthickness=0,
            yscrollincrement=16
        )
        settings_scrollbar = ttk.Scrollbar(
            page,
            orient=tk.VERTICAL,
            command=self.settings_canvas.yview,
            style='Modern.Vertical.TScrollbar'
        )
        self.settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        self.settings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        settings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))

        surface = tk.Frame(self.settings_canvas, bg=self.bg_dark)
        surface_window = self.settings_canvas.create_window((0, 0), window=surface, anchor=tk.NW)

        def sync_scroll_region(event=None):
            self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"))

        def sync_surface_width(event):
            self.settings_canvas.itemconfigure(surface_window, width=event.width)

        surface.bind("<Configure>", sync_scroll_region)
        self.settings_canvas.bind("<Configure>", sync_surface_width)
        self.settings_canvas.bind("<Enter>", lambda event: self.settings_canvas.focus_set())

        content = tk.Frame(surface, bg=self.bg_dark)
        content.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)

        header = tk.Label(
            content,
            text="Settings",
            font=("{San Francisco}", 22, "bold"),
            bg=self.bg_dark,
            fg=self.dark_surface_text_color
        )
        header.pack(fill=tk.X)

        # Themes use a compact drop-down so the settings tab has room for more app
        # controls without turning into a long scroll of palette rows.
        themes_frame = tk.Frame(content, bg=self.bg_light)
        themes_frame.pack(fill=tk.X, pady=(16, 14))
        tk.Label(
            themes_frame,
            text="Themes",
            font=("{San Francisco}", 14, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        ).pack(anchor=tk.W, padx=14, pady=(12, 2))

        selected_theme = tk.StringVar(value=self.current_theme_name)

        picker_row = tk.Frame(themes_frame, bg=self.bg_light)
        picker_row.pack(fill=tk.X, padx=12, pady=(12, 8))

        theme_picker = ttk.Combobox(
            picker_row,
            textvariable=selected_theme,
            values=list(self.themes.keys()),
            state="readonly",
            style="Settings.TCombobox",
            font=("{San Francisco}", 11)
        )
        theme_picker.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            picker_row,
            text="Apply",
            command=lambda: self.set_theme(selected_theme.get())
        ).pack(side=tk.RIGHT, padx=(10, 0))

        preview_row = tk.Frame(themes_frame, bg=self.bg_light)
        preview_row.pack(fill=tk.X, padx=12, pady=(0, 12))

        swatches = tk.Frame(preview_row, bg=self.bg_light)
        swatches.pack(side=tk.LEFT, padx=(0, 10))

        description_label = tk.Label(
            preview_row,
            text="",
            font=("{San Francisco}", 10),
            bg=self.bg_light,
            fg=self.text_color,
            wraplength=400,
            justify=tk.LEFT
        )
        description_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def update_theme_preview(event=None):
            for widget in swatches.winfo_children():
                widget.destroy()

            theme = self.themes[selected_theme.get()]
            colors = [theme["bg_dark"], theme["bg_light"], theme["accent"]] + list(theme["attr_colors"].values())[:3]
            for color in colors:
                tk.Frame(swatches, bg=color, width=16, height=24).pack(side=tk.LEFT, padx=1)

            description_label.config(text=theme["description"])

        theme_picker.bind("<<ComboboxSelected>>", update_theme_preview)
        update_theme_preview()

        display_frame = tk.Frame(content, bg=self.bg_light)
        display_frame.pack(fill=tk.X, pady=(0, 14))
        tk.Label(
            display_frame,
            text="Display",
            font=("{San Francisco}", 14, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        ).pack(anchor=tk.W, padx=14, pady=(12, 2))

        display_body = tk.Frame(display_frame, bg=self.bg_light)
        display_body.pack(fill=tk.X, padx=12, pady=(8, 12))

        font_header_row = tk.Frame(display_body, bg=self.bg_light)
        font_header_row.pack(fill=tk.X)

        tk.Label(
            font_header_row,
            text="Font size",
            font=("{San Francisco}", 16, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        ).pack(side=tk.LEFT)

        self.font_size_slider_var = tk.IntVar(value=self.font_size)
        self.font_value_label = tk.Label(
            font_header_row,
            text=f"{self.font_size} pt",
            font=("{San Francisco}", 10, "bold"),
            bg=self.bg_light,
            fg=self.accent_green,
            width=5
        )
        self.font_value_label.pack(side=tk.RIGHT)

        self.font_apply_after_id = None
        self.font_size_canvas = tk.Canvas(
            display_body,
            bg=self.bg_light,
            highlightthickness=0,
            height=86,
            cursor="hand2"
        )
        self.font_size_canvas.pack(fill=tk.X, pady=(6, 0))
        self.font_size_canvas.bind("<Configure>", lambda event: self.draw_font_size_slider())
        self.font_size_canvas.bind("<Button-1>", self.set_font_size_from_slider_event)
        self.font_size_canvas.bind("<B1-Motion>", self.set_font_size_from_slider_event)
        self.draw_font_size_slider()

        animation_frame = tk.Frame(content, bg=self.bg_light)
        animation_frame.pack(fill=tk.X, pady=(0, 14))
        tk.Label(
            animation_frame,
            text="Animations",
            font=("{San Francisco}", 14, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        ).pack(anchor=tk.W, padx=14, pady=(12, 2))

        animation_body = tk.Frame(animation_frame, bg=self.bg_light)
        animation_body.pack(fill=tk.X, padx=12, pady=(8, 12))

        animations_var = tk.BooleanVar(value=self.animations_enabled)
        popups_var = tk.BooleanVar(value=self.popups_enabled)
        popup_mode_var = tk.StringVar(
            value=POPUP_MODE_WITH_PARTICLES if self.particles_enabled else POPUP_MODE_WITHOUT_PARTICLES
        )
        animation_toggles = []

        def update_animation_toggle_colors():
            for toggle in animation_toggles:
                variable = toggle["variable"]
                active = bool(variable.get())
                box = toggle["box"]
                label = toggle["label"]
                box.delete("all")
                fill = self.accent_green if active else self.bg_dark
                outline = self.accent_green if active else self._blend_color(self.text_color, self.bg_light, 0.42)
                mark = self.get_readable_text_color(fill, self.accent_text_color) if active else self.text_color
                box.create_rectangle(3, 3, 19, 19, fill=fill, outline=outline, width=2)
                if active:
                    box.create_line(7, 11, 10, 15, 16, 7, fill=mark, width=3, capstyle=tk.ROUND, joinstyle=tk.ROUND)
                label.configure(fg=self.accent_green if active else self.text_color)

        self.refresh_animation_toggle_colors = update_animation_toggle_colors

        def save_animation_preferences():
            self.animations_enabled = bool(animations_var.get())
            self.popups_enabled = bool(popups_var.get())
            self.particles_enabled = popup_mode_var.get() == POPUP_MODE_WITH_PARTICLES
            popup_mode_picker.configure(state="readonly" if self.popups_enabled else "disabled")
            update_animation_toggle_colors()
            self.apply_display_preferences(save=True)

        def create_animation_toggle(label_text, variable):
            toggle = tk.Frame(animation_body, bg=self.bg_light, cursor="hand2")
            box = tk.Canvas(
                toggle,
                width=22,
                height=22,
                bg=self.bg_light,
                highlightthickness=0,
                cursor="hand2"
            )
            box.pack(side=tk.LEFT)
            label = tk.Label(
                toggle,
                text=label_text,
                bg=self.bg_light,
                fg=self.text_color,
                font=("{San Francisco}", 10),
                cursor="hand2"
            )
            label.pack(side=tk.LEFT, padx=(6, 0))
            toggle.pack(side=tk.LEFT, padx=(0, 18))

            def toggle_value(event=None):
                variable.set(not bool(variable.get()))
                save_animation_preferences()
                return "break"

            for widget in (toggle, box, label):
                widget.bind("<Button-1>", toggle_value)

            animation_toggles.append({"box": box, "label": label, "variable": variable})

        for label_text, variable in (
            ("Enable animations", animations_var),
            ("Reward popups", popups_var),
        ):
            create_animation_toggle(label_text, variable)

        popup_mode_picker = ttk.Combobox(
            animation_body,
            textvariable=popup_mode_var,
            values=[POPUP_MODE_WITH_PARTICLES, POPUP_MODE_WITHOUT_PARTICLES],
            state="readonly",
            style="Settings.TCombobox",
            font=("{San Francisco}", 10),
            width=24
        )
        popup_mode_picker.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def handle_popup_mode_selected(event=None):
            save_animation_preferences()
            def clear_popup_mode_selection():
                try:
                    popup_mode_picker.selection_clear()
                    popup_mode_picker.icursor(tk.END)
                except tk.TclError:
                    pass
                self.root.focus_set()

            self.root.after_idle(clear_popup_mode_selection)

        popup_mode_picker.bind("<<ComboboxSelected>>", handle_popup_mode_selected)
        popup_mode_picker.configure(state="readonly" if self.popups_enabled else "disabled")
        update_animation_toggle_colors()

        reset_frame = tk.Frame(content, bg=self.bg_light)
        reset_frame.pack(fill=tk.X, pady=(0, 14))
        tk.Label(
            reset_frame,
            text="Progress",
            font=("{San Francisco}", 14, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        ).pack(anchor=tk.W, padx=14, pady=(12, 2))

        reset_body = tk.Frame(reset_frame, bg=self.bg_light)
        reset_body.pack(fill=tk.X, padx=12, pady=12)

        tk.Label(
            reset_body,
            text="Reset all XP, levels, quests, history, and trophies.",
            font=("{San Francisco}", 10),
            bg=self.bg_light,
            fg=self.text_color,
            wraplength=340,
            justify=tk.LEFT
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            reset_body,
            text="Reset Progress",
            style="Danger.TButton",
            command=self.reset_progress
        ).pack(side=tk.RIGHT, padx=(10, 0))

        about_frame = tk.Frame(content, bg=self.bg_light)
        about_frame.pack(fill=tk.X)
        tk.Label(
            about_frame,
            text="About",
            font=("{San Francisco}", 12, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        ).pack(anchor=tk.W, padx=12, pady=(8, 0))

        # The About block uses wraplength so longer text stays inside the Settings tab.
        tk.Label(
            about_frame,
            text=(
                "LifeXP turns daily effort into RPG progress. "
                f"Created by NimBold. Version {APP_VERSION}."
            ),
            font=("{San Francisco}", 9),
            bg=self.bg_light,
            fg=self.text_color,
            wraplength=490,
            justify=tk.LEFT
        ).pack(anchor=tk.W, fill=tk.X, padx=12, pady=(4, 8))

        self.update_button = ttk.Button(
            about_frame,
            text="Check for Update",
            command=self.check_for_update
        )
        self.update_button.pack(anchor=tk.W, padx=12, pady=(0, 12))

        self.rescale_widget_tree(self.tab_settings)
        sync_scroll_region()

    def set_theme(self, theme_name, save=True):
        """Applies a selected theme immediately and optionally saves it."""
        # We first check if the requested theme is valid to avoid crashing.
        if theme_name not in self.themes:
            return

        previous_bg_dark = self.bg_dark
        previous_bg_light = self.bg_light
        previous_accent = self.accent_green
        previous_text = self.text_color
        previous_dark_surface_text = self.dark_surface_text_color
        previous_card_text = self.card_text_color
        previous_attr_colors = self.attr_colors.copy()

        # Update the active theme name and re-run the styling method.
        # This will instantly alter the appearance of many default ttk widgets.
        self.current_theme_name = theme_name
        self.apply_modern_theme()

        background_color_map = {
            previous_bg_dark: self.bg_dark,
            previous_bg_light: self.bg_light,
            previous_accent: self.accent_green,
        }
        foreground_color_map = {
            previous_text: self.text_color,
            previous_dark_surface_text: self.dark_surface_text_color,
            previous_card_text: self.card_text_color,
            previous_accent: self.accent_green
        }
        for attr, previous_color in previous_attr_colors.items():
            background_color_map[previous_color] = self.attr_colors[attr]
            foreground_color_map[previous_color] = self.attr_colors[attr]

        color_map = {
            "background": background_color_map,
            "foreground": foreground_color_map
        }

        # Update the saved user preferences so the theme persists on next launch.
        if hasattr(self, "data"):
            self.data["user_info"]["theme"] = theme_name
            if save:
                self.save_data()

        # Many newer UI pieces are normal tk widgets, not ttk widgets. They can be
        # recolored in place by swapping old theme colors for new ones. That avoids the
        # visible flicker caused by destroying and recreating the whole interface.
        if hasattr(self, "header_frame") and hasattr(self, "notebook"):
            self.recolor_widget_tree(self.root, color_map)
            self.update_stats_display()
            self.refresh_task_list()
            self.refresh_theme_widgets()
        else:
            self.refresh_theme_widgets()

    def reset_progress(self):
        """Clears progression data after an explicit warning confirmation."""
        confirmed = messagebox.askyesno(
            "⚠ Reset Progress?",
            "This will erase all XP, levels, quests, history, and trophies.\n\nAre you sure you want to reset your LifeXP progress?",
            icon="warning",
            parent=self.root
        )
        if not confirmed:
            return

        self.data["stats"] = {attr: {"level": 1, "xp": 0} for attr in self.attributes}
        self.data["tasks"] = []
        self.data["history"] = []
        self.data["trophies"] = []
        self.current_total_level = 0
        self._max_stat_level = 1
        self._invalidate_subcategory_cache()
        self._invalidate_tier_cache()

        self.save_data()
        self.refresh_task_list()
        self.update_stats_display()
        self.show_summary("daily")

        messagebox.showinfo(
            "Progress Reset",
            "Your LifeXP progress has been reset.",
            parent=self.root
        )

    @staticmethod
    def normalize_version_parts(version):
        """Converts a release tag like v1.2.3 into comparable integer parts."""
        cleaned = str(version or "").strip().lower()
        if cleaned.startswith("v"):
            cleaned = cleaned[1:]
        core = cleaned.split("-", 1)[0]
        parts = []
        for item in core.split("."):
            digits = ""
            for char in item:
                if char.isdigit():
                    digits += char
                else:
                    break
            parts.append(int(digits or 0))
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])

    @staticmethod
    def is_newer_version(candidate, current):
        """Returns whether candidate is newer than the current app version."""
        return LifeXPApp.normalize_version_parts(candidate) > LifeXPApp.normalize_version_parts(current)

    def check_for_update(self):
        """Checks GitHub releases and offers to open the latest release page."""
        button = getattr(self, "update_button", None)
        if button is not None:
            try:
                button.configure(text="Checking...", state=tk.DISABLED)
            except tk.TclError:
                pass

        def worker():
            try:
                request = urllib.request.Request(
                    GITHUB_LATEST_RELEASE_API,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": f"{APP_NAME}/{APP_VERSION}"
                    }
                )
                with urllib.request.urlopen(request, timeout=8, context=get_https_context()) as response:
                    release = json.loads(response.read().decode("utf-8"))
                result = {
                    "ok": True,
                    "tag": release.get("tag_name", ""),
                    "url": release.get("html_url") or GITHUB_RELEASES_URL
                }
            except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
                result = {"ok": False, "error": str(error)}

            try:
                self.root.after(0, lambda: self.finish_update_check(result))
            except tk.TclError:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def finish_update_check(self, result):
        """Shows the update-check result on the Tk main thread."""
        button = getattr(self, "update_button", None)
        if button is not None and button.winfo_exists():
            try:
                button.configure(text="Check for Update", state=tk.NORMAL)
            except tk.TclError:
                pass

        if not result.get("ok"):
            messagebox.showerror(
                "Update Check Failed",
                "LifeXP could not check GitHub releases right now.\n\n"
                f"{result.get('error', 'Unknown error')}",
                parent=self.root
            )
            return

        latest_tag = result.get("tag") or APP_VERSION
        latest_url = result.get("url") or GITHUB_RELEASES_URL
        if self.is_newer_version(latest_tag, APP_VERSION):
            open_release = messagebox.askyesno(
                "Update Available",
                f"LifeXP {latest_tag} is available.\n\n"
                f"You are using {APP_VERSION}.\n\n"
                "Open the GitHub release page?",
                parent=self.root
            )
            if open_release:
                webbrowser.open(latest_url)
        else:
            messagebox.showinfo(
                "No Update Available",
                f"You are using the latest LifeXP release ({APP_VERSION}).",
                parent=self.root
            )

    def refresh_theme_widgets(self):
        """Recolors already-created tk widgets after a theme change."""
        self.root.configure(bg=self.bg_dark)

        if hasattr(self, "header_frame"):
            self.header_frame.configure(bg=self.bg_light)
            self.avatar_canvas.configure(bg=self.bg_light)
            self.user_info_frame.configure(bg=self.bg_light)
            self.user_name_label.configure(bg=self.bg_light)
            self.user_level_label.configure(bg=self.bg_light, fg=self.accent_green)
            if hasattr(self, "app_title_frame"):
                self.app_title_frame.configure(bg=self.bg_light)
                self.app_title_label.configure(bg=self.bg_light, fg=self.text_color)
                if hasattr(self, "app_level_delta_label"):
                    self.app_level_delta_label.configure(bg=self.bg_light, fg=RANK_UP_GLOW_COLOR)

        self.refresh_quest_action_buttons()
        if hasattr(self, "refresh_animation_toggle_colors"):
            self.refresh_animation_toggle_colors()

        if hasattr(self, "summary_title_label"):
            if hasattr(self, "summary_light_surfaces"):
                for surface in self.summary_light_surfaces:
                    surface.configure(bg=self.bg_light)
            if hasattr(self, "summary_dark_surfaces"):
                for surface in self.summary_dark_surfaces:
                    surface.configure(bg=self.bg_dark)
            if hasattr(self, "summary_primary_labels"):
                for label in self.summary_primary_labels:
                    label.configure(bg=self.bg_light, fg=self.text_color)
            if hasattr(self, "summary_secondary_labels"):
                for label in self.summary_secondary_labels:
                    dark_parent = str(label.master.cget("bg")) == self.bg_dark
                    bg = self.bg_dark if dark_parent else self.bg_light
                    fg_base = self.dark_surface_text_color if dark_parent else self.text_color
                    label.configure(bg=bg, fg=self._blend_color(fg_base, bg, 0.34 if dark_parent else 0.28))
            self.summary_title_label.configure(bg=self.bg_light, fg=self._blend_color(self.text_color, self.bg_light, 0.18))
            if hasattr(self, "summary_timeframe_buttons"):
                self.update_summary_timeframe_buttons()
            if hasattr(self, "summary_metric_labels"):
                for value in self.summary_metric_labels.values():
                    value.configure(bg=self.bg_dark)
                    value.configure(fg=self.dark_surface_text_color)
            if hasattr(self, "summary_graph_canvas"):
                self.draw_summary_graph(getattr(self, "summary_attribute_totals", {attr: 0 for attr in self.attributes}))
            for attr, widgets in self.summary_cards.items():
                widgets["card"].configure(bg=self.bg_dark)
                widgets["strip"].configure(bg=self.attr_colors[attr])
                widgets["title"].configure(bg=self.bg_dark, fg=self.attr_colors[attr])
                widgets["meta"].configure(bg=self.bg_dark, fg=self._blend_color(self.dark_surface_text_color, self.bg_dark, 0.34))
                widgets["body_frame"].configure(bg=self.bg_dark)
                widgets["body"].configure(bg=self.bg_dark, fg=self.dark_surface_text_color)
                self.configure_summary_body_tags(widgets["body"])

        if hasattr(self, "trophies_frame"):
            if self._trophy_room_built:
                self.rebuild_trophy_room()
            self.update_stats_display()

        if hasattr(self, "summary_cards"):
            self.show_summary(self.current_summary_timeframe)

