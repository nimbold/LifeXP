# ==============================================================================
# LIFEXP - LEARNING MAP
# This file is a small desktop app. It mixes four ideas:
# 1. UI widgets from Tkinter, 2. saved JSON data, 3. RPG-style XP logic,
# and 4. simple canvas animations. Comments explain chunks, not every line.
# ==============================================================================
#
# IMPORTS
# Tkinter draws the window, datetime handles reports, JSON saves progress,
# os checks for the save file, random makes effects less uniform, and time keeps
# longer popup animations on a steady frame clock.
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import json
import math
import os
import random
import time

# APP_VERSION is shown in Settings. The constants below collect progression and popup
# timing knobs so later balancing changes do not require hunting through raw numbers.
APP_VERSION = "1.01"
BASE_XP_NEEDED = 100
ACCOUNT_BASE_XP_NEEDED = 500
ACCOUNT_LEVEL_CURVE_OFFSET = 81
ACCOUNT_LEVEL_CURVE_FLOOR = 92
ACCOUNT_LEVEL_CURVE_BASE_MULTIPLIER = 0.1
ACCOUNT_LEVEL_CURVE_UPGRADE_MULTIPLIER = 0.02
POPUP_FRAME_INTERVAL_SECONDS = 1 / 60
XP_POPUP_STEPS = 125
XP_POPUP_FADE_STEPS = 42
LEVEL_UP_POPUP_STEPS = 138
LEVEL_UP_POPUP_FADE_STEPS = 36
RANK_UP_HEADER_FRAMES = 92
TROPHY_POPUP_STEPS = 116
TROPHY_POPUP_FADE_STEPS = 32
XP_TO_REWARD_START_RATIO = 0.68
REWARD_CHAIN_START_RATIO = 0.50
RANK_UP_GLOW_COLOR = "#FFB020"
MAX_ACTIVE_PARTICLES = 180

# ==============================================================================
# MAIN APP CLASS
# A class lets the app keep related data and behavior together. Every method
# below uses self to access the same window, saved data, widgets, and colors.
# ==============================================================================
class LifeXPApp:
    """
    Main application class for LifeXP.
    """

    def __init__(self, root):
        # Store the main Tkinter window and set its basic title/size. The root window
        # is the parent object that all visible widgets eventually belong to.
        self.root = root
        self.root.title("LifeXP")
        self.root.geometry("920x800")
        self.root.minsize(900, 760)

        # These are the core game stats. Tasks give XP to one of these attributes,
        # and many later dictionaries use the same names as keys.
        self.attributes = ["Strength", "Agility", "Intelligence", "Charisma", "Vitality"]

        # Keep track of persistence and account-level animation state. The JSON file
        # is the app's memory between runs.
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.base_dir, "lifexp_data.json")
        self.xp_needed_cache = {}
        self.total_xp_before_level_cache = {1: 0}
        self.current_total_level = 0
        self.themes = self.get_theme_definitions()
        self.current_theme_name = "Tokyo Night"
        self.settings_window = None

        # Popup sequence gives simultaneous reward messages small vertical offsets so
        # they fade independently instead of covering the exact same screen position.
        self.popup_sequence = 0
        self.rank_up_animation_token = 0
        self.active_particle_widgets = []
        self.tab_hover_active = False
        self.tab_hover_token = 0
        self.tab_change_token = 0
        self.tab_selected_bg = None
        self.tab_active_bg = None
        self._subcategory_cache = None
        self._subcategory_owner_cache = None
        self._tiers_cache = None
        self._tiers_cache_expanded = None
        self.account_xp_needed_cache = {}
        self.account_total_xp_before_level_cache = {1: 0}
        self._last_rendered_tiers = None
        self._trophy_canvas_size = None
        self._trophy_resize_after_id = None
        self._max_stat_level = 1
        self.current_summary_timeframe = "daily"

        # Visual configuration lives near the top so the rest of the app can reuse it.
        # Each attribute gets one color, which is later used in bars, graphs, and art.
        self.attr_colors = self.themes[self.current_theme_name]["attr_colors"].copy()

        # Boot order matters: styles must exist before widgets are built, and data must
        # load before labels can show the current name, XP, tasks, and levels.
        self.apply_modern_theme()
        self.data = self.load_data()
        self._max_stat_level = self._calculate_max_level()
        self.current_theme_name = self.data["user_info"].get("theme", self.current_theme_name)
        if self.current_theme_name not in self.themes:
            self.current_theme_name = "Tokyo Night"
            self.data["user_info"]["theme"] = self.current_theme_name
        self.apply_modern_theme()

        self.setup_header()
        self.setup_ui()
        self.update_stats_display()
        self.refresh_task_list()

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
                "card_text": "#111111",
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
                "card_text": "#2E3440",
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
                "card_text": "#282A36",
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
                "card_text": "#1E1E2E",
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
                "card_text": "#282828",
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
                "card_text": "#1A1B26",
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
                "card_text": "#002B36",
                "attr_colors": {
                    "Strength": "#DC322F",
                    "Agility": "#CB4B16",
                    "Intelligence": "#268BD2",
                    "Charisma": "#D33682",
                    "Vitality": "#859900"
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
        self.style.configure('TNotebook.Tab', background=self.bg_light, foreground=self.text_color, padding=[18, 9], font=('{San Francisco}', 11, 'bold'))
        self.configure_notebook_tab_style(selected_bg=self.accent_green, active_bg=self.bg_light)

        self.style.configure('TButton', background=self.bg_light, foreground=self.text_color, font=('{San Francisco}', 11), padding=6)
        self.style.map('TButton', background=[('active', self.accent_green)], foreground=[('active', self.accent_text_color)])
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
        self.style.configure('QuestAccept.TButton', background="#FFFFFF", foreground="#1D1D1F", font=('{San Francisco}', 11, 'bold'), padding=8)
        self.style.map('QuestAccept.TButton', background=[('active', '#E5E5EA')], foreground=[('active', '#1D1D1F')])
        self.style.configure('QuestComplete.TButton', background="#34C759", foreground="#0B2A12", font=('{San Francisco}', 11, 'bold'), padding=8)
        self.style.map('QuestComplete.TButton', background=[('active', '#30D158')], foreground=[('active', '#0B2A12')])
        self.style.configure('QuestEdit.TButton', background="#FFCC00", foreground="#2A2100", font=('{San Francisco}', 11, 'bold'), padding=8)
        self.style.map('QuestEdit.TButton', background=[('active', '#FFD60A')], foreground=[('active', '#2A2100')])
        self.style.configure('QuestAbandon.TButton', background="#FF3B30", foreground="#FFFFFF", font=('{San Francisco}', 11, 'bold'), padding=8)
        self.style.map('QuestAbandon.TButton', background=[('active', '#FF453A')], foreground=[('active', '#FFFFFF')])
        self.style.configure('Danger.TButton', background="#FF3B30", foreground="#FFFFFF", font=('{San Francisco}', 11, 'bold'), padding=8)
        self.style.map('Danger.TButton', background=[('active', '#FF453A')], foreground=[('active', '#FFFFFF')])

        self.style.configure('TLabelframe', background=self.bg_dark, foreground=self.accent_green, font=('{San Francisco}', 12, 'bold'))
        self.style.configure('TLabelframe.Label', background=self.bg_dark, foreground=self.accent_green)

        self.style.configure('TLabel', background=self.bg_dark, foreground=self.dark_surface_text_color, font=('{San Francisco}', 11))
        self.style.configure('Horizontal.TProgressbar', background=self.accent_green, troughcolor=self.bg_light, bordercolor=self.bg_dark, lightcolor=self.accent_green, darkcolor=self.accent_green)

        # Each RPG attribute gets its own progress-bar style. The loop prevents writing
        # five nearly identical style.configure() calls by hand.
        for attr, color in self.attr_colors.items():
            self.style.configure(f'{attr}.Horizontal.TProgressbar', background=color, troughcolor=self.bg_light, bordercolor=self.bg_dark, lightcolor=color, darkcolor=color)

        # Treeview is the table widget used for the quest list. Its heading, row color,
        # selection color, and row height are styled separately from other widgets.
        self.style.configure('Treeview', background=self.bg_light, foreground=self.text_color, fieldbackground=self.bg_light, borderwidth=0, rowheight=34, font=('{San Francisco}', 11))
        self.style.map('Treeview', background=[('selected', self.accent_green)], foreground=[('selected', self.accent_text_color)])
        self.style.configure('Treeview.Heading', background=self.bg_light, foreground=self.accent_green, relief=tk.FLAT, font=('{San Francisco}', 11, 'bold'))

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
        # These smaller 8x8 pixel grids are title icons for the avatar. The method
        # returns the icon matching the current title tier.
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

    def update_avatar(self, tier_index, color, progress, glow_progress=0.0, glow_color=None, ring_progress=None):
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

        # The title icon is scaled from grid coordinates into canvas pixel positions.
        # offset centers the icon after pixel_size is calculated.
        shape = self.get_title_shape(tier_index)
        grid_size = len(shape)
        pixel_size = (s - 20) // grid_size
        offset = (s - (grid_size * pixel_size)) // 2

        # Nested loops walk through every row and column of the pixel-art grid. Only
        # cells containing "1" become colored rectangles.
        for y in range(grid_size):
            for x in range(grid_size):
                if shape[y][x] == "1":
                    x1 = offset + (x * pixel_size)
                    y1 = offset + (y * pixel_size)
                    icon_color = self._blend_color(color, focus_color, glow_progress * 0.70)
                    self.avatar_canvas.create_rectangle(x1, y1, x1+pixel_size, y1+pixel_size, fill=icon_color, outline="")

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
                "progress": progress
            }
            if animate_rank:
                self.play_rank_up_animation(rank_event)

        self.current_total_level = total_level
        if not (rank_event and animate_rank):
            self.update_avatar(tier_index, color, progress)
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

        # After the tab frames exist, they are registered with the notebook and given
        # the labels the user clicks.
        self.tab_icons = self.build_tab_icons()
        self.notebook.add(self.tab_tasks, text=" Quest Log", image=self.tab_icons["tasks"], compound=tk.LEFT)
        self.notebook.add(self.tab_character, text=" Character Info", image=self.tab_icons["character"], compound=tk.LEFT)
        self.notebook.add(self.tab_summary, text=" Chronicles", image=self.tab_icons["chronicles"], compound=tk.LEFT)
        self.notebook.bind("<Motion>", self.handle_tab_hover_motion)
        self.notebook.bind("<Leave>", lambda event: self.set_tab_hover(False))
        self.notebook.bind("<<NotebookTabChanged>>", self.play_tab_change_animation)

        # Each tab is built by its own helper method. This keeps setup_ui() readable
        # and separates the three screens of the app.
        self.setup_tasks_tab()
        self.setup_character_tab()
        self.setup_summary_tab()

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

        def icon():
            return tk.PhotoImage(width=size, height=size)

        def rect(image, x1, y1, x2, y2, color):
            image.put(color, to=(int(x1), int(y1), int(x2), int(y2)))

        def dot(image, cx, cy, radius, color):
            radius = int(radius)
            for y in range(int(cy) - radius, int(cy) + radius + 1):
                for x in range(int(cx) - radius, int(cx) + radius + 1):
                    if 0 <= x < size and 0 <= y < size and ((x - cx) ** 2 + (y - cy) ** 2) <= radius ** 2:
                        image.put(color, (x, y))

        def stroke(image, x1, y1, x2, y2, color, width=2):
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

        return {
            "tasks": tasks,
            "character": character_icon,
            "chronicles": chronicles
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
        vitality = self.attr_colors["Vitality"]
        strength = self.attr_colors["Strength"]
        agility = self.attr_colors["Agility"]
        accept = self.accent_green
        dark_text = "#0F172A"

        def button_text(background):
            return dark_text if self.get_contrast_ratio(dark_text, background) >= 4.5 else self.get_readable_text_color(background)

        palettes = {
            "accept": {
                "fill": self._blend_color(accept, "#FFFFFF", 0.35),
                "fg": button_text(self._blend_color(accept, "#FFFFFF", 0.35)),
                "accent": accept,
                "hover": accept,
                "hover_fg": button_text(accept),
                "border": accept,
                "glow": accept
            },
            "complete": {
                "fill": self._blend_color(vitality, "#FFFFFF", 0.35),
                "fg": button_text(self._blend_color(vitality, "#FFFFFF", 0.35)),
                "accent": vitality,
                "hover": vitality,
                "hover_fg": button_text(vitality),
                "border": vitality,
                "glow": vitality
            },
            "edit": {
                "fill": self._blend_color(agility, "#FFFFFF", 0.35),
                "fg": button_text(self._blend_color(agility, "#FFFFFF", 0.35)),
                "accent": agility,
                "hover": agility,
                "hover_fg": button_text(agility),
                "border": agility,
                "glow": agility
            },
            "abandon": {
                "fill": self._blend_color(strength, "#FFFFFF", 0.35),
                "fg": button_text(self._blend_color(strength, "#FFFFFF", 0.35)),
                "accent": strength,
                "hover": strength,
                "hover_fg": button_text(strength),
                "border": strength,
                "glow": strength
            }
        }
        return palettes[role]

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

    def get_settings_button_palette(self):
        """Returns colors for the settings control feedback."""
        border = self._blend_color(self.bg_light, self.text_color, 0.42)
        return {
            "fill": self.bg_light,
            "fg": self.text_color,
            "hover": self.accent_green,
            "hover_fg": self.accent_text_color,
            "border": border,
            "glow": self.accent_green
        }

    def set_settings_button_hover(self, is_hovering):
        """Fills the settings control while hovered."""
        if not hasattr(self, "settings_surface") or not self.settings_surface.winfo_exists():
            return
        if self.settings_button_hovering == is_hovering:
            return
        self.settings_button_hovering = is_hovering
        self.settings_hover_token += 1
        token = self.settings_hover_token
        palette = self.get_settings_button_palette()
        start = str(self.settings_surface.cget("bg"))
        end = palette["hover"] if is_hovering else palette["fill"]
        end_fg = palette["hover_fg"] if is_hovering else palette["fg"]

        def step(index=1, frames=5):
            if not self.settings_surface.winfo_exists() or self.settings_button_hovering != is_hovering or self.settings_hover_token != token:
                return
            ratio = index / float(frames)
            color = self._blend_color(start, end, ratio)
            self.settings_surface.configure(bg=color)
            self.settings_icon_label.configure(bg=color, fg=end_fg)
            self.settings_text_label.configure(bg=color, fg=end_fg)
            if index < frames:
                self.root.after(20, step, index + 1, frames)

        step()

    def handle_settings_hover_enter(self):
        """Starts settings hover only when entering the whole control."""
        self.set_settings_button_hover(True)

    def handle_settings_hover_leave(self):
        """Leaves settings hover only after the pointer exits the whole control."""
        self.root.after(12, lambda: (
            hasattr(self, "settings_button")
            and self.settings_button.winfo_exists()
            and not self.pointer_inside_widget(self.settings_button)
            and self.set_settings_button_hover(False)
        ))

    def run_settings_action(self):
        """Runs the settings action after neon feedback."""
        self.play_settings_button_feedback(on_done=self.open_settings_page)

    def play_settings_button_feedback(self, on_done=None):
        """Pulses the settings frame like the quest action buttons."""
        if not hasattr(self, "settings_surface") or not self.settings_surface.winfo_exists():
            if on_done:
                on_done()
            return

        palette = self.get_settings_button_palette()
        base_fill = palette["hover"] if getattr(self, "settings_button_hovering", False) else palette["fill"]
        total_frames = 18
        peak_frame = total_frames // 2

        def step(index=0):
            if not self.settings_button.winfo_exists() or not self.settings_surface.winfo_exists():
                if on_done:
                    on_done()
                return
            if index <= total_frames:
                if index <= peak_frame:
                    progress = self.ease_smoothstep(index / float(peak_frame))
                else:
                    progress = 1 - self.ease_smoothstep((index - peak_frame) / float(total_frames - peak_frame))

                border_color = self._blend_color(palette["border"], self._blend_color(palette["glow"], "#FFFFFF", 0.42), progress)
                fill_color = self._blend_color(base_fill, self._blend_color(palette["hover"], "#FFFFFF", 0.16), progress * 0.75)
                fg = palette["hover_fg"] if progress > 0.08 or getattr(self, "settings_button_hovering", False) else palette["fg"]
                self.settings_button.configure(bg=border_color)
                self.settings_surface.configure(bg=fill_color)
                self.settings_icon_label.configure(bg=fill_color, fg=fg)
                self.settings_text_label.configure(bg=fill_color, fg=fg)
                self.root.after(18, step, index + 1)
                return

            self.settings_button.configure(bg=palette["border"])
            self.set_settings_button_hover(getattr(self, "settings_button_hovering", False))
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

        # The scrollbar and table are connected in both directions: the scrollbar moves
        # the table, and the table tells the scrollbar what portion is visible.
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.task_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_tree.configure(yscrollcommand=scrollbar.set)

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

        settings_row = tk.Frame(control_frame, bg=self.bg_light)
        settings_row.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(8, 16))
        self.settings_button = tk.Frame(
            settings_row,
            bg=self.get_settings_button_palette()["border"],
            height=47,
            cursor="hand2",
        )
        self.settings_button.pack_propagate(False)
        self.settings_button_hovering = False
        self.settings_hover_token = 0
        self.settings_button.pack(fill=tk.X)
        self.settings_surface = tk.Frame(
            self.settings_button,
            bg=self.bg_light,
            cursor="hand2"
        )
        self.settings_surface.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.settings_icon_label = tk.Label(
            self.settings_surface,
            text="⚙",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 11, "bold"),
            cursor="hand2"
        )
        self.settings_icon_label.pack(side=tk.LEFT, padx=(9, 7), pady=7)
        self.settings_text_label = tk.Label(
            self.settings_surface,
            text="Settings",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 10, "bold"),
            cursor="hand2"
        )
        self.settings_text_label.pack(side=tk.LEFT, pady=7)
        for widget in (self.settings_button, self.settings_surface, self.settings_icon_label, self.settings_text_label):
            widget.bind("<Button-1>", lambda event: self.run_settings_action())
            widget.bind("<Enter>", lambda event: self.handle_settings_hover_enter())
            widget.bind("<Leave>", lambda event: self.handle_settings_hover_leave())

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
        if self._trophy_resize_after_id is not None:
            self.root.after_cancel(self._trophy_resize_after_id)
        self._trophy_resize_after_id = self.root.after(60, self.resize_trophy_canvases)

    def resize_trophy_canvases(self):
        """Resizes trophy canvases and redraws art for the current room dimensions."""
        self._trophy_resize_after_id = None
        if not self.trophy_canvases:
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
        # the current maximum level and tier rules.
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
        self.rebuild_trophy_room()

    def setup_summary_tab(self):
        """Paints the 'Chronicles' tab (report buttons and visual data)."""
        page = tk.Frame(self.tab_summary, bg=self.bg_dark)
        page.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # The Summary tab starts with three timeframe buttons. Each button passes a
        # different string into show_summary().
        control_frame = tk.Frame(page, bg=self.bg_light)
        control_frame.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            control_frame,
            text="Chronicles",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 16, "bold")
        ).pack(side=tk.LEFT, padx=16, pady=14)

        button_row = tk.Frame(control_frame, bg=self.bg_light)
        button_row.pack(side=tk.RIGHT, padx=12, pady=10)

        ttk.Button(button_row, text="Daily", command=lambda: self.show_summary("daily")).pack(side=tk.LEFT, padx=4)
        ttk.Button(button_row, text="Weekly", command=lambda: self.show_summary("weekly")).pack(side=tk.LEFT, padx=4)
        ttk.Button(button_row, text="Monthly", command=lambda: self.show_summary("monthly")).pack(side=tk.LEFT, padx=4)

        # Chronicles now has one large report area. Inside it, each attribute gets a
        # colored square that lists completed activity subcategories for the timeframe.
        report_frame = tk.Frame(page, bg=self.bg_light)
        report_frame.pack(fill=tk.BOTH, expand=True)

        # Here we create a dynamic title label for the report, which will update 
        # based on the selected timeframe (Daily, Weekly, Monthly).
        self.summary_title_label = tk.Label(
            report_frame,
            text="",
            font=("{San Francisco}", 15, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        )
        self.summary_title_label.pack(fill=tk.X, padx=16, pady=(14, 8))

        # This container frame holds the summary cards side-by-side. We use a grid
        # layout inside it to evenly distribute one card per RPG attribute.
        cards_frame = tk.Frame(report_frame, bg=self.bg_light)
        cards_frame.pack(fill=tk.X, padx=12, pady=(0, 14))

        self.summary_cards = {}
        for i, attr in enumerate(self.attributes):
            cards_frame.columnconfigure(i, weight=1, uniform="summary_cards")

            card = tk.Frame(
                cards_frame,
                bg=self.attr_colors[attr],
                width=150,
                height=150,
                highlightthickness=0
            )
            card.grid(row=0, column=i, padx=5, pady=5)
            card.grid_propagate(False)

            title = tk.Label(
                card,
                text=attr,
                font=("{San Francisco}", 11, "bold"),
                bg=self.attr_colors[attr],
                fg=self.attr_text_colors[attr]
            )
            title.pack(fill=tk.X, padx=6, pady=(8, 2))

            body = tk.Text(
                card,
                wrap=tk.WORD,
                font=("{San Francisco}", 9),
                bg=self.attr_colors[attr],
                fg=self.attr_text_colors[attr],
                bd=0,
                highlightthickness=0,
                padx=6,
                pady=4
            )
            body.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 6))
            body.tag_configure("bold", font=("{San Francisco}", 9, "bold"))
            body.tag_configure("combo_blue", foreground="#1E5BFF", font=("{San Francisco}", 10, "bold"))
            body.tag_configure("combo_red", foreground="#8B0000", font=("{San Francisco}", 10, "bold"))
            body.tag_configure("combo_gold", foreground="#8A5A00", font=("{San Francisco}", 10, "bold"))
            body.config(state=tk.DISABLED)

            self.summary_cards[attr] = {"title": title, "body": body}

        self.show_summary("daily")

    def open_settings_page(self):
        """Opens the Settings page for themes, reset controls, and app info."""
        # If the settings window is already open, we don't want to create duplicates.
        # Instead, we just bring the existing window to the front and focus on it.
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        # tk.Toplevel creates a new floating window on top of the main root window.
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.withdraw()
        self.settings_window.title("Settings")
        self.settings_window.configure(bg=self.bg_dark)
        self.settings_window.transient(self.root)
        self.settings_window.option_add("*TCombobox*Listbox.background", self.bg_light)
        self.settings_window.option_add("*TCombobox*Listbox.foreground", self.text_color)
        self.settings_window.option_add("*TCombobox*Listbox.selectBackground", self.accent_green)
        self.settings_window.option_add("*TCombobox*Listbox.selectForeground", self.accent_text_color)

        surface = tk.Frame(self.settings_window, bg=self.bg_dark)
        surface.pack(fill=tk.BOTH, expand=True, padx=22, pady=20)

        header = tk.Label(
            surface,
            text="Settings",
            font=("{San Francisco}", 22, "bold"),
            bg=self.bg_dark,
            fg=self.dark_surface_text_color
        )
        header.pack(fill=tk.X)

        # Themes use a compact drop-down so the settings window has room for more app
        # controls without turning into a long scroll of palette rows.
        themes_frame = tk.Frame(surface, bg=self.bg_light)
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

        reset_frame = tk.Frame(surface, bg=self.bg_light)
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

        about_frame = tk.Frame(surface, bg=self.bg_light)
        about_frame.pack(fill=tk.X)
        tk.Label(
            about_frame,
            text="About",
            font=("{San Francisco}", 14, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        ).pack(anchor=tk.W, padx=14, pady=(12, 2))

        # The About block uses wraplength so longer text stays inside the Settings
        # window instead of forcing the user to resize it by hand.
        tk.Label(
            about_frame,
            text=(
                "LifeXP turns daily effort into RPG progress. "
                "Track quests, earn XP, level attributes, and review your growth.\n\n"
                f"Created by NimBold\nVersion {APP_VERSION}"
            ),
            font=("{San Francisco}", 11),
            bg=self.bg_light,
            fg=self.text_color,
            wraplength=490,
            justify=tk.LEFT
        ).pack(anchor=tk.W, fill=tk.X, padx=12, pady=12)

        self.show_fitted_window(self.settings_window, min_width=560, min_height=450)

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
            if self.settings_window and self.settings_window.winfo_exists():
                self.recolor_widget_tree(self.settings_window, color_map)
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
            parent=self.settings_window
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
            parent=self.settings_window
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

        if hasattr(self, "settings_button"):
            palette = self.get_settings_button_palette()
            self.settings_button.configure(
                bg=palette["border"]
            )
            self.settings_surface.configure(bg=palette["fill"])
            self.settings_icon_label.configure(bg=palette["fill"], fg=palette["fg"])
            self.settings_text_label.configure(bg=palette["fill"], fg=palette["fg"])

        self.refresh_quest_action_buttons()

        if hasattr(self, "summary_title_label"):
            self.summary_title_label.configure(bg=self.bg_light, fg=self.text_color)
            for attr, widgets in self.summary_cards.items():
                widgets["title"].master.configure(bg=self.attr_colors[attr])
                widgets["title"].configure(bg=self.attr_colors[attr], fg=self.attr_text_colors[attr])
                widgets["body"].configure(bg=self.attr_colors[attr], fg=self.attr_text_colors[attr])

        if hasattr(self, "trophies_frame"):
            self.rebuild_trophy_room()
            self.update_stats_display()

        if hasattr(self, "summary_cards"):
            self.show_summary(self.current_summary_timeframe)

    # ==============================================================================
    # GROUP B - DATA MANAGEMENT / LIBRARIANS
    # This group is responsible for memory: creating default data, loading saved
    # JSON, migrating old saves, and writing changes back to disk.
    # ==============================================================================
    def _calculate_max_level(self):
        """Returns the highest attribute level in the current save data."""
        return max((stat["level"] for stat in self.data["stats"].values()), default=1)

    def _invalidate_subcategory_cache(self):
        """Clears derived autocomplete data after activity names change."""
        self._subcategory_cache = None
        self._subcategory_owner_cache = None

    def _invalidate_tier_cache(self):
        """Clears derived trophy tier data after level thresholds may change."""
        self._tiers_cache = None
        self._tiers_cache_expanded = None
        self._last_rendered_tiers = None

    def normalize_user_info(self, user_info, default_user_info):
        """Returns safe account metadata with every key the header expects."""
        # Saved JSON can be edited by hand or come from an older app version. This
        # method fills missing account fields so UI code can read them without a
        # KeyError during startup.
        normalized = default_user_info.copy()
        if isinstance(user_info, dict):
            name = str(user_info.get("name", normalized["name"])).strip()
            normalized["name"] = name or default_user_info["name"]
            normalized["theme"] = str(user_info.get("theme", normalized["theme"])).strip() or default_user_info["theme"]
            try:
                normalized["avatar_seed"] = int(user_info.get("avatar_seed", normalized["avatar_seed"]))
            except (TypeError, ValueError):
                normalized["avatar_seed"] = default_user_info["avatar_seed"]
        return normalized

    def normalize_subcategories(self, subcategories, default_subcategories):
        """Returns clean autocomplete suggestions for every current attribute."""
        # Subcategories are just saved activity names. The app only needs current
        # attributes, so this removes malformed entries, trims spaces, deduplicates
        # names, and then adds any default beginner suggestions that are missing.
        retired_subcategories = {
            "weightlifting",
            "pushups / core",
            "stretching routine",
            "yoga break",
            "workout",
            "farting"
        }
        activity_aliases = {
            "strength training": ("Strength", "Resistance Training"),
            "deep cleaning": ("Strength", "Heavy Chores"),
            "moving furniture": ("Strength", "Heavy Chores"),
            "carrying groceries": ("Strength", "Carry Groceries"),
            "gardening": ("Strength", "Gardening / Yard Work"),
            "sports practice": ("Agility", "Sports or Active Play"),
            "standing desk time": ("Vitality", "Screen / Movement Break"),
            "stretching": ("Agility", "Stretching / Mobility"),
            "yoga": ("Agility", "Yoga / Mobility"),
            "cleaning": ("Vitality", "Home Reset"),
            "sweeping": ("Vitality", "Home Reset"),
            "decluttering": ("Vitality", "Home Reset"),
            "meal prep cleanup": ("Vitality", "Home Reset"),
            "typing practice": ("Intelligence", "Digital Skills Practice"),
            "inbox zero": ("Intelligence", "Digital Organization"),
            "reading book": ("Intelligence", "Reading"),
            "reading docs": ("Intelligence", "Reading"),
            "writing notes": ("Intelligence", "Writing / Notes"),
            "learning a framework": ("Intelligence", "Technical Learning"),
            "cooking lunch": ("Vitality", "Cook Healthy Meal"),
            "healthy breakfast": ("Vitality", "Cook Healthy Meal"),
            "meal prep": ("Vitality", "Cook Healthy Meal"),
            "drinking water": ("Vitality", "Hydration"),
            "sleeping 8 hours": ("Vitality", "Sleep Routine"),
            "skincare": ("Vitality", "Hygiene Routine"),
            "no junk food": ("Vitality", "Nutrition Choice")
        }
        source = subcategories if isinstance(subcategories, dict) else {}
        normalized = {attr: [] for attr in self.attributes}
        seen_by_attr = {attr: set() for attr in self.attributes}

        def add_activity(attr, name):
            if attr not in normalized:
                return
            key = name.lower()
            if key in seen_by_attr[attr]:
                return
            normalized[attr].append(name)
            seen_by_attr[attr].add(key)

        for source_attr in self.attributes:
            raw_items = source.get(source_attr, [])
            if not isinstance(raw_items, list):
                raw_items = []

            for item in raw_items:
                if not isinstance(item, str):
                    continue
                name = item.strip()
                key = name.lower()
                if not name or key in retired_subcategories:
                    continue
                target_attr, target_name = activity_aliases.get(key, (source_attr, name))
                add_activity(target_attr, target_name)

        for attr in self.attributes:
            for default_name in default_subcategories[attr]:
                add_activity(attr, default_name)

        return normalized

    def load_data(self):
        """Reads saved data. Includes complex migrations to prevent crashes."""
        # default_data is the safe starting shape for the app. It documents what keys
        # the rest of the program expects to exist.
        default_data = {
            "user_info": {"name": "Hero", "avatar_seed": random.randint(1, 100000), "theme": self.current_theme_name},
            "stats": {attr: {"level": 1, "xp": 0} for attr in self.attributes},
            "tasks": [],
            "history": [],
            "trophies": [],
            "subcategories": {
                "Strength": [
                    "Resistance Training",
                    "Bodyweight Exercise",
                    "Core Training",
                    "Home Repairs",
                    "Heavy Chores",
                    "Carry Groceries",
                    "Gardening / Yard Work",
                    "Posture Practice",
                    "Grip / Mobility"
                ],
                "Agility": [
                    "Walking",
                    "Running",
                    "Cycling",
                    "Stretching / Mobility",
                    "Yoga / Mobility",
                    "Balance Practice",
                    "Sports or Active Play",
                    "Dance / Cardio",
                    "Stair Climb",
                    "Errands"
                ],
                "Intelligence": [
                    "Coding",
                    "Bug Fixing",
                    "Reading",
                    "Studying",
                    "Online Course",
                    "Technical Learning",
                    "Language Practice",
                    "Writing / Notes",
                    "Planning",
                    "Budget Review",
                    "Research",
                    "Digital Organization",
                    "Creative Practice"
                ],
                "Charisma": [
                    "Team Standup",
                    "Client Meeting",
                    "Calling Family",
                    "Messaging Friends",
                    "Mentoring",
                    "Writing Emails",
                    "Networking",
                    "Date Night",
                    "Community Event",
                    "Presentation Practice",
                    "Conflict Resolution",
                    "Active Listening",
                    "Thank You Note",
                    "Shared Meal"
                ],
                "Vitality": [
                    "Cook Healthy Meal",
                    "Meditation",
                    "Hydration",
                    "Sleep Routine",
                    "Eye Rest",
                    "Screen / Movement Break",
                    "Outdoor Sunlight",
                    "Home Reset",
                    "Nutrition Choice",
                    "Hygiene Routine",
                    "Medication",
                    "Doctor Appointment",
                    "Therapy",
                    "Breathing Exercise",
                    "Digital Detox"
                ]
            }
        }

        # If the save file exists, the app tries to read it. If it does not exist, the
        # method skips to the final return and starts from defaults.
        if os.path.exists(self.data_file):
            try:
                # with open(...) safely opens the file and closes it automatically. json.load()
                # turns the file text back into Python dictionaries and lists.
                with open(self.data_file, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        return default_data

                    # Migration code lets old save files survive renamed attributes. The map says
                    # which old names should become which new names.
                    rename_map = {
                        "Dexterity": "Agility",
                        "Faith": "Charisma",
                        "Vigor": "Vitality",
                        "Constitution": "Vitality"
                    }

                    # The next three blocks apply the rename map to stats, active tasks, and history.
                    # Each block checks that the section exists before touching it.
                    if isinstance(data.get("stats"), dict):
                        for old, new in rename_map.items():
                            if old in data["stats"]:
                                data["stats"][new] = data["stats"].pop(old)

                    if isinstance(data.get("tasks"), list):
                        for task in data["tasks"]:
                            if not isinstance(task, dict):
                                continue
                            if task.get("attribute") in rename_map:
                                task["attribute"] = rename_map[task["attribute"]]

                    if isinstance(data.get("history"), list):
                        for record in data["history"]:
                            if not isinstance(record, dict):
                                continue
                            if record.get("attribute") in rename_map:
                                record["attribute"] = rename_map[record["attribute"]]

                    # Subcategories are stored under attribute names too. When an
                    # attribute is renamed, we move its activity suggestions to the new
                    # name and avoid adding duplicates if both old and new keys exist.
                    if not isinstance(data.get("subcategories"), dict):
                        data["subcategories"] = default_data["subcategories"]

                    if "subcategories" in data:
                        for old, new in rename_map.items():
                            if old in data["subcategories"]:
                                old_subs = data["subcategories"].pop(old)
                                if not isinstance(old_subs, list):
                                    continue
                                data["subcategories"].setdefault(new, [])
                                for sub in old_subs:
                                    if sub not in data["subcategories"][new]:
                                        data["subcategories"][new].append(sub)

                    # Trophy names are plain strings like "Vitality Bronze", not nested
                    # dictionaries. That means migration needs to rewrite the text prefix
                    # so old trophies still appear as unlocked after the rename.
                    if isinstance(data.get("trophies"), list):
                        for index, trophy_name in enumerate(data["trophies"]):
                            if not isinstance(trophy_name, str):
                                continue
                            for old, new in rename_map.items():
                                if trophy_name.startswith(f"{old} "):
                                    data["trophies"][index] = trophy_name.replace(old, new, 1)
                                    break

                    if isinstance(data.get("user_info"), dict) and data["user_info"].get("name") == "Ashen One":
                        data["user_info"]["name"] = "Hero"

                    # This loop patches missing top-level sections into older or partial
                    # save files. It prevents simple KeyError crashes later in the UI.
                    for key in default_data:
                        if key not in data:
                            data[key] = default_data[key]

                    data["user_info"] = self.normalize_user_info(data.get("user_info"), default_data["user_info"])
                    data["stats"] = self.normalize_stats(data.get("stats"), default_data["stats"])
                    data["tasks"] = self.normalize_tasks(data.get("tasks"))
                    data["history"] = self.normalize_history(data.get("history"))
                    data["trophies"] = [
                        trophy for trophy in data.get("trophies", [])
                        if isinstance(trophy, str)
                    ] if isinstance(data.get("trophies"), list) else []
                    data["subcategories"] = self.normalize_subcategories(
                        data.get("subcategories"),
                        default_data["subcategories"]
                    )

                    return data

            # If the JSON file is damaged or unreadable, the app does not crash. It
            # prints a warning and falls back to a clean default save structure.
            except (OSError, json.JSONDecodeError) as error:
                print(f"Error reading data file. Starting fresh. ({error})")
                return default_data

        return default_data

    def normalize_stats(self, stats, default_stats):
        """Returns valid stats for every current attribute."""
        normalized = {}
        stats = stats if isinstance(stats, dict) else {}
        for attr in self.attributes:
            raw_stat = stats.get(attr, {}) if isinstance(stats.get(attr, {}), dict) else {}
            try:
                level = max(1, int(raw_stat.get("level", default_stats[attr]["level"])))
                xp = max(0, int(raw_stat.get("xp", default_stats[attr]["xp"])))
            except (TypeError, ValueError):
                level = default_stats[attr]["level"]
                xp = default_stats[attr]["xp"]
            normalized[attr] = {"level": level, "xp": xp}
        return normalized

    def normalize_tasks(self, tasks):
        """Drops malformed active quests that would crash task actions."""
        normalized = []
        if not isinstance(tasks, list):
            return normalized

        for task in tasks:
            if not isinstance(task, dict):
                continue
            name = str(task.get("name", "")).strip()
            attr = task.get("attribute")
            if not name or attr not in self.attributes:
                continue
            try:
                xp = max(1, int(task.get("xp", 0)))
            except (TypeError, ValueError):
                continue
            normalized.append({
                "name": name,
                "attribute": attr,
                "subcategory": str(task.get("subcategory") or name).strip() or name,
                "xp": xp
            })
        return normalized

    def normalize_history(self, history):
        """Keeps only usable completion records for reports."""
        normalized = []
        if not isinstance(history, list):
            return normalized

        for record in history:
            if not isinstance(record, dict):
                continue
            attr = record.get("attribute")
            if attr not in self.attributes:
                continue
            date_value = record.get("date")
            try:
                datetime.fromisoformat(date_value)
                xp = max(0, int(record.get("xp", 0)))
            except (TypeError, ValueError):
                continue
            name = str(record.get("name") or record.get("subcategory") or "General").strip() or "General"
            normalized.append({
                "name": name,
                "attribute": attr,
                "subcategory": str(record.get("subcategory") or name).strip() or name,
                "xp": xp,
                "date": date_value
            })
        return normalized

    def save_data(self):
        """Writes current data back to the hard drive."""
        # Saving is the reverse of loading: json.dump() converts the in-memory app data
        # into readable text and writes it to disk.
        temp_file = f"{self.data_file}.tmp"
        with open(temp_file, 'w', encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)
        os.replace(temp_file, self.data_file)

    # ==============================================================================
    # GROUP C - GAME ENGINE / LOGIC AND ACTIONS
    # This group responds to user actions: adding, editing, deleting, completing
    # quests, granting XP, awarding trophies, and generating reports.
    # ==============================================================================
    def refresh_task_list(self):
        """Clears the visual list and redraws it based on current memory."""
        # Refreshing the task table is done by clearing visible rows, then inserting
        # one row for each task currently stored in self.data. Passing all existing
        # row IDs into delete() at once is faster than deleting one row at a time.
        existing_rows = self.task_tree.get_children()
        if existing_rows:
            self.task_tree.delete(*existing_rows)

        for i, task in enumerate(self.data["tasks"]):
            self.task_tree.insert("", tk.END, iid=i, values=(task["name"], task["attribute"], f"{task['xp']} XP"))

    def toggle_task_tree_selection(self, event):
        """Supports Command/Ctrl-click toggling for active quest multi-select."""
        item_id = self.task_tree.identify_row(event.y)
        if not item_id:
            return "break"

        current_selection = set(self.task_tree.selection())
        if item_id in current_selection:
            self.task_tree.selection_remove(item_id)
        else:
            self.task_tree.selection_add(item_id)
            self.task_tree.focus(item_id)
        return "break"

    def get_selected_task_indices(self, empty_message=None):
        """Returns valid selected quest indices, preserving visual row order."""
        selected = self.task_tree.selection()
        if not selected:
            if empty_message:
                messagebox.showinfo("Notice", empty_message, parent=self.root)
            return []

        indices = []
        for item_id in selected:
            try:
                index = int(item_id)
            except (TypeError, ValueError):
                self.refresh_task_list()
                return []
            if not 0 <= index < len(self.data["tasks"]):
                self.refresh_task_list()
                if empty_message:
                    messagebox.showinfo("Notice", "That quest is no longer available. Please select it again.", parent=self.root)
                return []
            indices.append(index)

        return sorted(set(indices))

    def get_selected_task_index(self, empty_message=None):
        """Returns the selected quest index, or None if the selection is unusable."""
        indices = self.get_selected_task_indices(empty_message)
        if not indices:
            return None
        return indices[0]

    def add_task_dialog(self):
        """Pops up a wider, multi-add window for accepting one or more quests."""
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title("Accept Quest")
        dialog.configure(bg=self.bg_dark)
        dialog.transient(self.root)

        surface = tk.Frame(dialog, bg=self.bg_dark)
        surface.pack(fill=tk.BOTH, expand=True, padx=22, pady=18)

        header = tk.Frame(surface, bg=self.bg_dark)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Accept Quest",
            bg=self.bg_dark,
            fg=self.dark_surface_text_color,
            font=("{San Francisco}", 20, "bold")
        ).pack(anchor=tk.W)
        tk.Label(
            header,
            text="Build your quest queue.",
            bg=self.bg_dark,
            fg=self.accent_green,
            font=("{San Francisco}", 11)
        ).pack(anchor=tk.W, pady=(4, 0))

        all_filter_label = "All"
        attr_var = tk.StringVar(value=all_filter_label)
        activity_var = tk.StringVar()
        difficulty_var = tk.IntVar(value=5)
        pending_quests = []
        suggest_after_id = [None]

        category_section = tk.Frame(surface, bg=self.bg_dark)
        category_section.pack(fill=tk.X, pady=(16, 0))
        tk.Label(
            category_section,
            text="Target Attribute",
            bg=self.bg_dark,
            fg=self.dark_surface_text_color,
            font=("{San Francisco}", 11, "bold")
        ).pack(anchor=tk.W)

        chip_row = tk.Frame(category_section, bg=self.bg_dark)
        chip_row.pack(fill=tk.X, pady=(8, 0))
        chip_widgets = {}

        def refresh_category_chips():
            for attr, chip in chip_widgets.items():
                selected = attr_var.get() == attr
                selected_bg = self.accent_green if attr == all_filter_label else self.attr_colors[attr]
                selected_fg = self.accent_text_color if attr == all_filter_label else self.attr_text_colors[attr]
                chip.config(
                    bg=selected_bg if selected else self.bg_light,
                    fg=selected_fg if selected else self.text_color,
                    relief=tk.FLAT if selected else tk.GROOVE,
                    bd=0 if selected else 1
                )

        def choose_attribute(attr):
            attr_var.set(attr)
            refresh_category_chips()
            update_suggestions()

        filter_options = [all_filter_label] + self.attributes
        for index, attr in enumerate(filter_options):
            chip = tk.Label(
                chip_row,
                text=attr,
                bg=self.bg_light,
                fg=self.text_color,
                padx=8,
                pady=7,
                cursor="hand2",
                font=("{San Francisco}", 10, "bold")
            )
            chip.grid(row=0, column=index, sticky="ew", padx=(0, 8))
            chip.bind("<Button-1>", lambda event, selected_attr=attr: choose_attribute(selected_attr))
            chip_widgets[attr] = chip
            chip_row.grid_columnconfigure(index, weight=1, uniform="attribute_chips")

        body = tk.Frame(surface, bg=self.bg_dark)
        body.pack(fill=tk.BOTH, expand=True, pady=(16, 0))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        search_section = tk.Frame(body, bg=self.bg_dark)
        search_section.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        search_section.grid_rowconfigure(4, weight=1)
        search_section.grid_columnconfigure(0, weight=1)
        tk.Label(
            search_section,
            text="Activity",
            bg=self.bg_dark,
            fg=self.dark_surface_text_color,
            font=("{San Francisco}", 11, "bold")
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            search_section,
            text="Saved Activities",
            bg=self.bg_dark,
            fg=self.accent_green,
            font=("{San Francisco}", 10),
            justify=tk.LEFT
        ).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        activity_entry = ttk.Entry(search_section, textvariable=activity_var, font=("{San Francisco}", 12))
        activity_entry.grid(row=2, column=0, sticky="ew", pady=(8, 0), ipady=6)

        hint_label = tk.Label(
            search_section,
            text="",
            bg=self.bg_dark,
            fg=self.accent_green,
            font=("{San Francisco}", 10)
        )
        hint_label.grid(row=3, column=0, sticky="w", pady=(6, 0))

        listbox_frame = tk.Frame(search_section, bg=self.bg_light)
        listbox_frame.grid(row=4, column=0, sticky="nsew", pady=(10, 0))

        suggestion_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        suggestion_list = tk.Listbox(
            listbox_frame,
            font=("{San Francisco}", 11),
            bg=self.bg_light,
            fg=self.text_color,
            selectbackground=self.accent_green,
            selectforeground=self.bg_dark,
            activestyle="none",
            bd=0,
            highlightthickness=0,
            selectmode=tk.EXTENDED,
            yscrollcommand=suggestion_scrollbar.set
        )
        suggestion_scrollbar.config(command=suggestion_list.yview)
        suggestion_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        suggestion_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        side_panel = tk.Frame(body, bg=self.bg_dark)
        side_panel.grid(row=0, column=1, sticky="nsew")
        side_panel.grid_columnconfigure(0, weight=1)
        side_panel.grid_rowconfigure(1, weight=1)

        slider_card = tk.Frame(side_panel, bg=self.bg_light)
        slider_card.grid(row=0, column=0, sticky="ew")
        slider_card.grid_columnconfigure(0, weight=1)

        slider_header = tk.Frame(slider_card, bg=self.bg_light)
        slider_header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        slider_header.grid_columnconfigure(0, weight=1)
        tk.Label(
            slider_header,
            text="Difficulty",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 12, "bold")
        ).grid(row=0, column=0, sticky="w")

        val_label = tk.Label(
            slider_header,
            text="5 / 10",
            bg=self.bg_light,
            fg=self.accent_green,
            font=("{San Francisco}", 12, "bold")
        )
        val_label.grid(row=0, column=1, sticky="e")

        slider_canvas = tk.Canvas(slider_card, height=54, bg=self.bg_light, highlightthickness=0)
        slider_canvas.grid(row=1, column=0, sticky="ew", padx=14)

        xp_label = tk.Label(
            slider_card,
            text="Yields 50 XP",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 11)
        )
        xp_label.grid(row=2, column=0, sticky="w", padx=14, pady=(0, 12))

        selected_card = tk.Frame(side_panel, bg=self.bg_light)
        selected_card.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        selected_card.grid_columnconfigure(0, weight=1)
        selected_card.grid_rowconfigure(1, weight=1)

        selected_header = tk.Frame(selected_card, bg=self.bg_light)
        selected_header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        selected_header.grid_columnconfigure(0, weight=1)
        selected_title = tk.Label(
            selected_header,
            text="Selected Quests",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 12, "bold")
        )
        selected_title.grid(row=0, column=0, sticky="w")
        selected_count_label = tk.Label(
            selected_header,
            text="0",
            bg=self.bg_light,
            fg=self.accent_green,
            font=("{San Francisco}", 12, "bold")
        )
        selected_count_label.grid(row=0, column=1, sticky="e")

        selected_list_frame = tk.Frame(selected_card, bg=self.bg_light)
        selected_list_frame.grid(row=1, column=0, sticky="nsew", padx=14)
        selected_scrollbar = ttk.Scrollbar(selected_list_frame, orient=tk.VERTICAL)
        selected_list = tk.Listbox(
            selected_list_frame,
            font=("{San Francisco}", 10),
            bg=self.bg_light,
            fg=self.text_color,
            selectbackground=self.accent_green,
            selectforeground=self.bg_dark,
            activestyle="none",
            bd=0,
            highlightthickness=0,
            yscrollcommand=selected_scrollbar.set
        )
        selected_scrollbar.config(command=selected_list.yview)
        selected_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        selected_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        selected_actions = tk.Frame(selected_card, bg=self.bg_light)
        selected_actions.grid(row=2, column=0, sticky="ew", padx=14, pady=(8, 12))
        remove_button = ttk.Button(selected_actions, text="Remove Selected")
        remove_button.pack(side=tk.LEFT)

        def difficulty_color(v):
            ratio = (v - 1) / 9.0
            target_r, target_g, target_b = self._hex_to_rgb(self.accent_green)
            r = int(255 + (target_r - 255) * ratio)
            g = int(255 + (target_g - 255) * ratio)
            b = int(255 + (target_b - 255) * ratio)
            return f'#{r:02x}{g:02x}{b:02x}'

        def draw_difficulty_slider():
            slider_canvas.delete("all")
            width = max(slider_canvas.winfo_width(), 240)
            left = 16
            right = width - 16
            center_y = 21
            track_height = 8
            value = difficulty_var.get()
            ratio = (value - 1) / 9.0
            thumb_x = left + (right - left) * ratio
            color_hex = difficulty_color(value)

            slider_canvas.create_line(left, center_y, right, center_y, fill=self.bg_dark, width=track_height, capstyle=tk.ROUND)
            slider_canvas.create_line(left, center_y, thumb_x, center_y, fill=color_hex, width=track_height, capstyle=tk.ROUND)

            for tick in range(1, 11):
                tick_ratio = (tick - 1) / 9.0
                tick_x = left + (right - left) * tick_ratio
                slider_canvas.create_oval(tick_x - 2, center_y - 2, tick_x + 2, center_y + 2, fill=self.text_color if tick > value else self.bg_dark, outline="")

            slider_canvas.create_oval(thumb_x - 12, center_y - 12, thumb_x + 12, center_y + 12, fill="#FFFFFF", outline=color_hex, width=3)
            slider_canvas.create_text(left, 45, text="1", fill=self.text_color, font=("{San Francisco}", 9))
            slider_canvas.create_text(right, 45, text="10", fill=self.text_color, font=("{San Francisco}", 9))
            val_label.config(text=f"{value} / 10", fg=color_hex)
            xp_label.config(text=f"Yields {value * 10} XP")

        def set_difficulty_from_event(event):
            width = max(slider_canvas.winfo_width(), 240)
            left = 16
            right = width - 16
            ratio = min(1.0, max(0.0, (event.x - left) / (right - left)))
            difficulty_var.set(round(1 + ratio * 9))
            draw_difficulty_slider()

        def suggestion_name_at(index):
            return suggestion_list.get(index)

        def insert_activity_item(listbox, text, attr=None, use_attr_color=True):
            listbox.insert(tk.END, text)
            item_index = listbox.size() - 1
            color = self.attr_colors.get(attr, self.text_color) if use_attr_color and attr else self.text_color
            listbox.itemconfig(item_index, foreground=color)
            return item_index

        def ask_activity_attribute(activity_name):
            chooser = tk.Toplevel(dialog)
            chooser.withdraw()
            chooser.title("Activity Attribute")
            chooser.configure(bg=self.bg_dark)
            chooser.transient(dialog)
            chooser.grab_set()

            selected_attr = tk.StringVar(value=self.attributes[0])
            surface = tk.Frame(chooser, bg=self.bg_dark)
            surface.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)

            tk.Label(
                surface,
                text="Choose Attribute",
                bg=self.bg_dark,
                fg=self.dark_surface_text_color,
                font=("{San Francisco}", 15, "bold")
            ).pack(anchor=tk.W)
            tk.Label(
                surface,
                text=activity_name,
                bg=self.bg_dark,
                fg=self.accent_green,
                font=("{San Francisco}", 11)
            ).pack(anchor=tk.W, pady=(3, 12))

            chip_frame = tk.Frame(surface, bg=self.bg_dark)
            chip_frame.pack(fill=tk.X)
            chooser_chips = {}

            def refresh_chooser_chips():
                for attr, chip in chooser_chips.items():
                    selected = selected_attr.get() == attr
                    chip.config(
                        bg=self.attr_colors[attr] if selected else self.bg_light,
                        fg=self.attr_text_colors[attr] if selected else self.text_color,
                        relief=tk.FLAT if selected else tk.GROOVE,
                        bd=0 if selected else 1
                    )

            def select_attr(attr):
                selected_attr.set(attr)
                refresh_chooser_chips()

            for index, attr in enumerate(self.attributes):
                chip = tk.Label(
                    chip_frame,
                    text=attr,
                    bg=self.bg_light,
                    fg=self.text_color,
                    padx=9,
                    pady=7,
                    cursor="hand2",
                    font=("{San Francisco}", 10, "bold")
                )
                chip.grid(row=0, column=index, sticky="ew", padx=(0, 7))
                chip.bind("<Button-1>", lambda event, selected=attr: select_attr(selected))
                chooser_chips[attr] = chip
                chip_frame.grid_columnconfigure(index, weight=1, uniform="new_activity_attr")

            result = {"attribute": None}

            def confirm():
                result["attribute"] = selected_attr.get()
                chooser.destroy()

            def cancel():
                chooser.destroy()

            action_row = tk.Frame(surface, bg=self.bg_dark)
            action_row.pack(fill=tk.X, pady=(14, 0))
            ttk.Button(action_row, text="Cancel", command=cancel).pack(side=tk.LEFT)
            ttk.Button(action_row, text="Use Attribute", style="QuestAccept.TButton", command=confirm).pack(side=tk.RIGHT)

            refresh_chooser_chips()
            self.show_fitted_window(chooser, min_width=520, min_height=190)
            chooser.bind("<Return>", lambda event: confirm())
            chooser.bind("<Escape>", lambda event: cancel())
            chooser.protocol("WM_DELETE_WINDOW", cancel)
            dialog.wait_window(chooser)
            return result["attribute"]

        def refresh_selected_list():
            selected_list.delete(0, tk.END)
            for quest in pending_quests:
                insert_activity_item(
                    selected_list,
                    f"{quest['attribute']}  ·  {quest['name']}  ·  {quest['xp']} XP",
                    quest["attribute"]
                )
            count = len(pending_quests)
            selected_count_label.config(text=str(count))
            accept_button.config(text=f"Accept {count} Quest{'s' if count != 1 else ''}" if count else "Accept Quest")
            remove_button.config(state=tk.NORMAL if count else tk.DISABLED)

        def add_pending_quest(activity_name, attr=None, refresh=True, show_error=True):
            activity_name = activity_name.strip()
            if not activity_name:
                if show_error:
                    messagebox.showerror("Hold up, Hero!", "Your quest needs an activity name.", parent=dialog)
                return False

            selected_filter = attr_var.get()
            fallback_attr = self.attributes[0] if selected_filter == all_filter_label else selected_filter
            known_owner = self.get_known_activity_owner(activity_name)
            if attr is None and known_owner is None and selected_filter == all_filter_label:
                attr = ask_activity_attribute(activity_name)
                if attr is None:
                    return False
            attr = attr or known_owner or fallback_attr
            xp = difficulty_var.get() * 10
            for quest in pending_quests:
                if quest["attribute"] == attr and quest["name"].lower() == activity_name.lower():
                    quest["xp"] = xp
                    if refresh:
                        refresh_selected_list()
                        hint_label.config(text="Updated selected quest difficulty.")
                    return True

            pending_quests.append({
                "name": activity_name,
                "attribute": attr,
                "subcategory": activity_name,
                "xp": xp
            })
            if refresh:
                refresh_selected_list()
                hint_label.config(text=f"Added {activity_name}.")
            return True

        def add_current_to_selection(show_error=True):
            return add_pending_quest(activity_var.get(), show_error=show_error)

        def add_selected_suggestions():
            selections = suggestion_list.curselection()
            if not selections:
                add_current_to_selection()
                return

            owner_map = self.get_subcategory_owner_map()
            added = 0
            for index in selections:
                selected_text = suggestion_name_at(index)
                owning_attr = owner_map.get(selected_text) or attr_var.get()
                if owning_attr == all_filter_label:
                    owning_attr = self.attributes[0]
                if add_pending_quest(selected_text, owning_attr, refresh=False, show_error=False):
                    added += 1
            refresh_selected_list()
            hint_label.config(text=f"Added {added} selected activit{'y' if added == 1 else 'ies'}.")

        def remove_selected_pending():
            selections = list(selected_list.curselection())
            if not selections:
                return
            for index in reversed(selections):
                if 0 <= index < len(pending_quests):
                    pending_quests.pop(index)
            refresh_selected_list()

        remove_button.config(command=remove_selected_pending)

        def update_suggestions(*args):
            suggest_after_id[0] = None
            typed = activity_var.get().strip().lower()
            selected_filter = attr_var.get()
            owner_map = self.get_subcategory_owner_map()
            if selected_filter == all_filter_label:
                available_subs = self.get_all_subcategories()
            else:
                available_subs = sorted(
                    dict.fromkeys(self.data["subcategories"].get(selected_filter, [])),
                    key=str.lower
                )

            suggestion_list.delete(0, tk.END)

            exact_matches = [sub for sub in available_subs if sub.lower() == typed]
            if exact_matches:
                owning_attr = owner_map.get(exact_matches[0])
                if selected_filter != all_filter_label and owning_attr and attr_var.get() != owning_attr:
                    attr_var.set(owning_attr)
                    refresh_category_chips()

            hits = available_subs if not typed else [sub for sub in available_subs if typed in sub.lower()]
            if hits:
                for hit in list(hits)[:80]:
                    owning_attr = owner_map.get(hit, selected_filter)
                    insert_activity_item(
                        suggestion_list,
                        hit,
                        owning_attr,
                        use_attr_color=selected_filter != all_filter_label
                    )
                hint_label.config(text=f"{len(hits)} matching activities")
            else:
                hint_label.config(text="New activity")

        def update_suggestions_debounced(*args):
            if suggest_after_id[0] is not None:
                dialog.after_cancel(suggest_after_id[0])
            suggest_after_id[0] = dialog.after(120, update_suggestions)

        activity_var.trace_add("write", update_suggestions_debounced)
        def toggle_suggestion_selection(event):
            index = suggestion_list.nearest(event.y)
            if index < 0 or index >= suggestion_list.size():
                return "break"
            if index in suggestion_list.curselection():
                suggestion_list.selection_clear(index)
            else:
                suggestion_list.selection_set(index)
                suggestion_list.activate(index)
            return "break"

        suggestion_list.bind("<Command-Button-1>", toggle_suggestion_selection)
        suggestion_list.bind("<Control-Button-1>", toggle_suggestion_selection)
        suggestion_list.bind("<Double-Button-1>", lambda event: add_selected_suggestions())
        slider_canvas.bind("<Configure>", lambda event: draw_difficulty_slider())
        slider_canvas.bind("<Button-1>", set_difficulty_from_event)
        slider_canvas.bind("<B1-Motion>", set_difficulty_from_event)

        action_row = tk.Frame(surface, bg=self.bg_dark)
        action_row.pack(fill=tk.X, pady=(14, 0))
        ttk.Button(action_row, text="Cancel", command=lambda: close_dialog()).pack(side=tk.LEFT)
        ttk.Button(action_row, text="Add Typed", command=add_current_to_selection).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(action_row, text="Add Selected", command=add_selected_suggestions).pack(side=tk.RIGHT, padx=(8, 0))
        accept_button = ttk.Button(action_row, text="Accept Quest", style="QuestAccept.TButton")
        accept_button.pack(side=tk.RIGHT)

        def save():
            if not pending_quests and not add_current_to_selection(show_error=True):
                return

            subcategories_changed = False
            for quest in pending_quests:
                attr = quest["attribute"]
                existing_names = {name.lower() for name in self.data["subcategories"][attr]}
                if quest["name"].lower() not in existing_names:
                    self.data["subcategories"][attr].append(quest["name"])
                    subcategories_changed = True
                self.data["tasks"].append(quest.copy())

            if subcategories_changed:
                self._invalidate_subcategory_cache()

            added_count = len(pending_quests)
            self.save_data()
            self.refresh_task_list()
            close_dialog()

            cx, cy = self.get_center()
            self.play_floating_text(f"✨ {added_count} QUEST{'S' if added_count != 1 else ''} ADDED", self.accent_green, cx, cy)

        def close_dialog():
            if suggest_after_id[0] is not None:
                dialog.after_cancel(suggest_after_id[0])
                suggest_after_id[0] = None
            dialog.destroy()

        accept_button.config(command=save)
        refresh_category_chips()
        refresh_selected_list()
        update_suggestions()
        draw_difficulty_slider()
        self.show_fitted_window(dialog, min_width=860, min_height=540)
        dialog.grab_set()
        activity_entry.focus_set()
        dialog.bind("<Return>", lambda event: save())
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.bind("<Escape>", lambda event: close_dialog())

    def edit_task_dialog(self):
        """Allows editing a currently selected task."""
        # Most task actions begin by reading the selected row. If nothing is selected,
        # the method exits early or shows a helpful message.
        indices = self.get_selected_task_indices("Select a quest from the log to edit it.")
        if not indices:
            return
        if len(indices) > 1:
            self.edit_multiple_tasks_dialog(indices)
            return

        index = indices[0]

        task = self.data["tasks"][index]

        # Editing uses simple popup dialogs instead of a custom window. The current task
        # values are passed in as initial values for the user to modify.
        new_name = simpledialog.askstring("Edit Quest", "New Quest Name:", initialvalue=task["name"], parent=self.root)
        if new_name is None:
            return

        try:
            new_xp_str = simpledialog.askstring("Edit Quest", "New XP Reward:", initialvalue=str(task["xp"]), parent=self.root)
            if new_xp_str is None:
                return
            new_xp = int(new_xp_str)
        except ValueError:
            messagebox.showerror("Error", "XP must be a numeric value.", parent=self.root)
            return

        if new_xp < 1:
            messagebox.showerror("Error", "XP must be at least 1.", parent=self.root)
            return

        new_name = new_name.strip()
        if not new_name:
            messagebox.showerror("Error", "Quest name cannot be blank.", parent=self.root)
            return

        task_attr = self.get_known_activity_owner(new_name) or task["attribute"]
        self.data["tasks"][index]["attribute"] = task_attr
        self.data["tasks"][index]["name"] = new_name
        self.data["tasks"][index]["subcategory"] = new_name
        self.data["tasks"][index]["xp"] = new_xp
        existing_names = {name.lower() for name in self.data["subcategories"][task_attr]}
        if new_name.lower() not in existing_names:
            self.data["subcategories"][task_attr].append(new_name)
            self._invalidate_subcategory_cache()
        self.save_data()
        self.refresh_task_list()

        cx, cy = self.get_center()
        self.play_floating_text("✏️ QUEST UPDATED", "#88C0D0", cx, cy)

    def edit_multiple_tasks_dialog(self, indices):
        """Opens a compact batch editor for multiple selected quests."""
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title("Edit Quests")
        dialog.configure(bg=self.bg_dark)
        dialog.transient(self.root)

        surface = tk.Frame(dialog, bg=self.bg_dark)
        surface.pack(fill=tk.BOTH, expand=True, padx=22, pady=18)

        tk.Label(
            surface,
            text=f"Edit {len(indices)} Quests",
            bg=self.bg_dark,
            fg=self.dark_surface_text_color,
            font=("{San Francisco}", 20, "bold")
        ).pack(anchor=tk.W)

        table = tk.Frame(surface, bg=self.bg_light)
        table.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        table.grid_columnconfigure(1, weight=1)

        headers = [("XP", 0), ("Activity", 1), ("Attribute", 2)]
        for text, column in headers:
            tk.Label(
                table,
                text=text,
                bg=self.bg_light,
                fg=self.text_color,
                font=("{San Francisco}", 11, "bold")
            ).grid(row=0, column=column, sticky="w", padx=10, pady=(10, 6))

        row_controls = []
        for row, index in enumerate(indices, start=1):
            task = self.data["tasks"][index]
            xp_var = tk.StringVar(value=str(task["xp"]))
            name_var = tk.StringVar(value=task["name"])
            attr_var = tk.StringVar(value=task["attribute"])

            xp_entry = ttk.Entry(table, textvariable=xp_var, width=8, font=("{San Francisco}", 11))
            xp_entry.grid(row=row, column=0, sticky="ew", padx=(10, 6), pady=5, ipady=3)

            name_entry = ttk.Entry(table, textvariable=name_var, font=("{San Francisco}", 11))
            name_entry.grid(row=row, column=1, sticky="ew", padx=6, pady=5, ipady=3)

            attr_combo = ttk.Combobox(table, textvariable=attr_var, values=self.attributes, state="readonly", width=16, font=("{San Francisco}", 11))
            attr_combo.grid(row=row, column=2, sticky="ew", padx=(6, 10), pady=5, ipady=3)

            row_controls.append({
                "index": index,
                "xp_var": xp_var,
                "name_var": name_var,
                "attr_var": attr_var
            })

        def save_edits():
            updates = []
            for row in row_controls:
                name = row["name_var"].get().strip()
                attr = row["attr_var"].get()
                try:
                    xp = int(row["xp_var"].get())
                except ValueError:
                    messagebox.showerror("Error", "XP must be numeric for every selected quest.", parent=dialog)
                    return

                if not name:
                    messagebox.showerror("Error", "Quest names cannot be blank.", parent=dialog)
                    return
                if attr not in self.attributes:
                    messagebox.showerror("Error", "Every quest needs a valid attribute.", parent=dialog)
                    return
                if xp < 1:
                    messagebox.showerror("Error", "XP must be at least 1 for every selected quest.", parent=dialog)
                    return

                updates.append((row["index"], name, attr, xp))

            subcategories_changed = False
            for index, name, attr, xp in updates:
                if not 0 <= index < len(self.data["tasks"]):
                    self.refresh_task_list()
                    messagebox.showinfo("Notice", "The quest list changed. Please reopen the editor.", parent=dialog)
                    return

                self.data["tasks"][index]["attribute"] = attr
                self.data["tasks"][index]["name"] = name
                self.data["tasks"][index]["subcategory"] = name
                self.data["tasks"][index]["xp"] = xp

                existing_names = {saved_name.lower() for saved_name in self.data["subcategories"][attr]}
                if name.lower() not in existing_names:
                    self.data["subcategories"][attr].append(name)
                    subcategories_changed = True

            if subcategories_changed:
                self._invalidate_subcategory_cache()

            self.save_data()
            self.refresh_task_list()
            dialog.destroy()

            cx, cy = self.get_center()
            self.play_floating_text(f"✏️ {len(updates)} QUESTS UPDATED", "#88C0D0", cx, cy)

        def close_dialog():
            dialog.destroy()

        action_row = tk.Frame(surface, bg=self.bg_dark)
        action_row.pack(fill=tk.X, pady=(14, 0))
        ttk.Button(action_row, text="Cancel", command=close_dialog).pack(side=tk.LEFT)
        ttk.Button(action_row, text="Save Changes", style="QuestAccept.TButton", command=save_edits).pack(side=tk.RIGHT)

        self.show_fitted_window(dialog, min_width=720, min_height=320)
        dialog.grab_set()
        dialog.bind("<Return>", lambda event: save_edits())
        dialog.bind("<Escape>", lambda event: close_dialog())
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

    def delete_task(self):
        """Removes a task from memory without giving XP."""
        indices = self.get_selected_task_indices()
        if not indices:
            return

        # Deleting asks for confirmation because it removes the quest without XP. After
        # deletion, the saved file and visible table are both refreshed.
        count = len(indices)
        quest_word = "quest" if count == 1 else "quests"
        if messagebox.askyesno("Abandon Quest?", f"Are you sure you want to abandon {count} {quest_word}? No XP will be awarded.", parent=self.root):
            for index in sorted(indices, reverse=True):
                del self.data["tasks"][index]
            self.save_data()
            self.refresh_task_list()

            cx, cy = self.get_center()
            self.play_floating_text(f"💀 {count} QUEST{'S' if count != 1 else ''} ABANDONED", "#BF616A", cx, cy)
            self.play_particles("#BF616A", cx, cy, count=min(32, 10 + (count * 5)), gravity=True)

    def complete_task(self):
        """The main gameplay loop: Finish task -> Grant XP -> Save History -> Redraw."""
        indices = self.get_selected_task_indices("Select a quest to complete it.")
        if not indices:
            return

        tasks = [self.data["tasks"][index] for index in indices]
        level_events = []
        total_xp_gain = 0

        for task in tasks:
            attr = task["attribute"]
            xp_gain = task["xp"]
            total_xp_gain += xp_gain
            level_events.extend(self.gain_xp(attr, xp_gain))

            self.data["history"].append({
                "name": task["name"],
                "attribute": attr,
                "subcategory": task.get("subcategory", "General"),
                "xp": xp_gain,
                "date": datetime.now().isoformat()
            })

        for index in sorted(indices, reverse=True):
            self.data["tasks"].pop(index)

        self.save_data()
        self.refresh_task_list()
        rank_event = self.update_stats_display(animate_rank=False)

        cx, cy = self.get_center()
        # XP gain always gets a fixed readable duration. If level-up popups are also
        # needed, they are scheduled after it rather than shortening this popup.
        # play_floating_text() now returns the final popup box position. The XP particles
        # use that box as their source so sparks appear to come from the reward label,
        # while physics=True keeps the older gravity/falling feel.
        popup_text = f"+{total_xp_gain} XP!" if len(tasks) == 1 else f"{len(tasks)} QUESTS  +{total_xp_gain} XP!"
        popup_box = self.play_floating_text(popup_text, "#EBCB8B", cx, cy, size=30, duration_steps=XP_POPUP_STEPS, fade_steps=XP_POPUP_FADE_STEPS)
        self.play_firework_particles("#EBCB8B", popup_box, count=34, palette=["#EBCB8B", "#FFD166", "#F59E0B", "#F97316"], physics=True)

        if level_events or rank_event:
            self.schedule_level_up_sequence(level_events, rank_event)

    def get_scaled_xp_needed(self, level, base_xp):
        """Returns an Elden Ring-style level cost normalized to this app's base XP."""
        raw_base = (
            ACCOUNT_LEVEL_CURVE_BASE_MULTIPLIER
            * ((1 + ACCOUNT_LEVEL_CURVE_OFFSET) ** 2)
        ) + 1
        upgrade_multiplier = max(
            0.0,
            ((level + ACCOUNT_LEVEL_CURVE_OFFSET) - ACCOUNT_LEVEL_CURVE_FLOOR)
            * ACCOUNT_LEVEL_CURVE_UPGRADE_MULTIPLIER
        )
        raw_cost = (
            (upgrade_multiplier + ACCOUNT_LEVEL_CURVE_BASE_MULTIPLIER)
            * ((level + ACCOUNT_LEVEL_CURVE_OFFSET) ** 2)
        ) + 1
        return max(1, int(base_xp * (raw_cost / raw_base)))

    def get_xp_needed(self, level):
        """Returns the XP required to pass the given attribute level."""
        # Attributes now use the same normalized Elden-style curve as account levels.
        # This keeps early levels quick while avoiding the extreme late-game wall from
        # a fixed 25 percent exponential increase.
        if level not in self.xp_needed_cache:
            self.xp_needed_cache[level] = self.get_scaled_xp_needed(level, BASE_XP_NEEDED)
        return self.xp_needed_cache[level]

    def get_total_xp_before_level(self, level):
        """Returns cumulative XP needed to reach a level, cached by level."""
        highest_cached_level = max(self.total_xp_before_level_cache)
        total = self.total_xp_before_level_cache[highest_cached_level]
        for next_level in range(highest_cached_level + 1, level + 1):
            total += self.get_xp_needed(next_level - 1)
            self.total_xp_before_level_cache[next_level] = total
        return self.total_xp_before_level_cache[level]

    def get_total_xp_for_stat(self, stat):
        """Returns lifetime XP for one attribute, including already-spent level XP."""
        # Saved stats only keep the XP inside the current level. This helper adds the
        # XP paid for previous levels so account rank can use true lifetime progress.
        return stat["xp"] + self.get_total_xp_before_level(stat["level"])

    def get_account_xp_needed(self, level):
        """Returns account XP needed to advance from this total level."""
        # This mirrors Elden Ring's shape: a small base multiplier applies early, then
        # the per-level upgrade multiplier kicks in after the floor level. The result is
        # normalized so LifeXP level 1 still costs ACCOUNT_BASE_XP_NEEDED instead of
        # Elden Ring's raw rune value.
        if level not in self.account_xp_needed_cache:
            self.account_xp_needed_cache[level] = self.get_scaled_xp_needed(level, ACCOUNT_BASE_XP_NEEDED)
        return self.account_xp_needed_cache[level]

    def get_total_account_xp_before_level(self, level):
        """Returns cumulative account XP needed to reach a total level."""
        highest_cached_level = max(self.account_total_xp_before_level_cache)
        total = self.account_total_xp_before_level_cache[highest_cached_level]
        for next_level in range(highest_cached_level + 1, level + 1):
            total += self.get_account_xp_needed(next_level - 1)
            self.account_total_xp_before_level_cache[next_level] = total
        return self.account_total_xp_before_level_cache[level]

    def get_account_level_progress(self, total_xp):
        """Returns total level, XP inside that level, and XP needed for the next one."""
        # Account progress is shown often, so avoid walking from level 1 every time.
        # First find an upper bound by doubling, then binary-search the cached totals.
        try:
            total_xp = max(0, int(total_xp))
        except (TypeError, ValueError):
            total_xp = 0
        low = 1
        high = 2
        while self.get_total_account_xp_before_level(high) <= total_xp:
            high *= 2

        while low < high:
            mid = (low + high + 1) // 2
            if self.get_total_account_xp_before_level(mid) <= total_xp:
                low = mid
            else:
                high = mid - 1

        level = low
        xp_before_level = self.get_total_account_xp_before_level(level)
        xp_needed = self.get_account_xp_needed(level)
        return level, total_xp - xp_before_level, xp_needed

    def get_all_subcategories(self):
        """Returns every known activity name once, sorted for autocomplete."""
        if self._subcategory_cache is None:
            # The save file is normalized on load, but this cache is still defensive
            # because suggestions can be added while the app is running. Case-folded
            # keys remove "Reading" / "reading" duplicates without changing display
            # capitalization.
            seen = set()
            all_subs = []
            for subs in self.data["subcategories"].values():
                if not isinstance(subs, list):
                    continue
                for sub in subs:
                    if not isinstance(sub, str):
                        continue
                    name = sub.strip()
                    key = name.lower()
                    if name and key not in seen:
                        all_subs.append(name)
                        seen.add(key)

            # Sorting once here is cheaper than sorting every time the user types in
            # the autocomplete field.
            self._subcategory_cache = sorted(all_subs, key=str.lower)
        return self._subcategory_cache

    def get_known_activity_owner(self, activity_name):
        """Returns the saved attribute for an activity name, ignoring capitalization."""
        # Exact lookup is fast for normal suggestion clicks. The lowercase fallback
        # protects users who type a known activity with different capitalization.
        owner_map = self.get_subcategory_owner_map()
        if activity_name in owner_map:
            return owner_map[activity_name]

        lowered = activity_name.lower()
        for saved_name, attr in owner_map.items():
            if saved_name.lower() == lowered:
                return attr
        return None

    def get_subcategory_owner_map(self):
        """Returns the first saved attribute for each known activity name."""
        if self._subcategory_owner_cache is None:
            owner_map = {}
            seen_lower = set()
            # Iterating in self.attributes order makes ownership predictable if the
            # same activity appears under multiple attributes.
            for attr in self.attributes:
                subs = self.data["subcategories"].get(attr, [])
                if not isinstance(subs, list):
                    continue
                for sub in subs:
                    if isinstance(sub, str) and sub.strip():
                        name = sub.strip()
                        lowered = name.lower()
                        if lowered not in seen_lower:
                            owner_map[name] = attr
                            seen_lower.add(lowered)
            self._subcategory_owner_cache = owner_map
        return self._subcategory_owner_cache

    def gain_xp(self, attribute, amount):
        """Calculates new XP and returns any level-up moments to animate later."""
        # XP is added to one attribute. The while loop handles large rewards that might
        # cross more than one level boundary at once.
        stat = self.data["stats"][attribute]
        stat["xp"] += amount
        level_events = []

        xp_needed = self.get_xp_needed(stat["level"])
        while stat["xp"] >= xp_needed:
            stat["xp"] -= xp_needed
            stat["level"] += 1
            if stat["level"] > self._max_stat_level:
                self._max_stat_level = stat["level"]

            # Each level-up checks whether a milestone trophy was reached. Animation is
            # delayed by the completion flow so the XP popup gets the first beat.
            trophy_name = self.check_trophies(attribute, stat["level"])
            level_events.append({
                "attribute": attribute,
                "level": stat["level"],
                "trophy": trophy_name
            })
            xp_needed = self.get_xp_needed(stat["level"])

        return level_events

    def check_trophies(self, attribute, new_level):
        """Awards a trophy if specific level milestones are hit."""
        # Trophy checking searches the tier list for an exact level match. If a new
        # milestone is found and not already owned, it is added to saved data.
        trophy_name = None
        for tier_name, level_req in self.get_tiers():
            if new_level == level_req:
                trophy_name = f"{attribute} {tier_name}"
                break

        if trophy_name and trophy_name not in self.data["trophies"]:
            self.data["trophies"].append(trophy_name)
            return trophy_name

        return None

    def _trophy_material(self, level_req, progress):
        """Returns tier-specific trophy colors or disabled greys while locked."""
        progress = max(0.0, min(progress, 1.0))
        if progress < 1.0:
            lift = progress * 0.42
            return (
                self._blend_color("#3E4654", "#7E8796", lift),
                self._blend_color("#262C36", "#596272", lift),
                self._blend_color("#7C8594", "#D1D6DF", lift),
                self._blend_color("#4B5563", "#9AA3B2", lift)
            )

        if level_req >= 100:
            material = ("#DDF8FF", "#7AA2F7", "#FFFFFF", "#B9F6FF")
        elif level_req >= 50:
            material = ("#F8FAFF", "#B7C4D8", "#FFFFFF", "#7AA2F7")
        elif level_req >= 25:
            material = ("#FFD700", "#B8860B", "#FFF4A3", "#F59E0B")
        elif level_req >= 10:
            material = ("#D9E2EC", "#8C99A8", "#FFFFFF", "#A7B4C4")
        else:
            material = ("#C9893D", "#7A4A20", "#FFD18A", "#9A5B2D")

        return material

    def draw_attribute_symbol(self, canvas, attr, cx, cy, size, color, line_color):
        """Draws the attribute emblem inside the trophy medallion."""
        stroke = max(2, int(size * 0.08))
        if attr == "Strength":
            bar_y = cy
            plate_w = size * 0.12
            plate_h = size * 0.34
            canvas.create_line(cx - size * 0.34, bar_y, cx + size * 0.34, bar_y, fill=line_color, width=stroke, capstyle=tk.ROUND)
            for side in (-1, 1):
                x = cx + side * size * 0.26
                canvas.create_rectangle(x - plate_w, bar_y - plate_h / 2, x + plate_w, bar_y + plate_h / 2, fill=line_color, outline="")
                canvas.create_rectangle(x + side * size * 0.13 - plate_w / 2, bar_y - plate_h * 0.42, x + side * size * 0.13 + plate_w / 2, bar_y + plate_h * 0.42, fill=line_color, outline="")
        elif attr == "Agility":
            shoe = [
                cx - size * 0.32, cy + size * 0.10,
                cx - size * 0.05, cy + size * 0.16,
                cx + size * 0.30, cy + size * 0.05,
                cx + size * 0.36, cy + size * 0.17,
                cx + size * 0.05, cy + size * 0.31,
                cx - size * 0.30, cy + size * 0.24
            ]
            canvas.create_polygon(shoe, fill=line_color, outline="")
            for index in range(3):
                y = cy - size * (0.26 - index * 0.09)
                canvas.create_arc(cx - size * (0.42 - index * 0.07), y, cx + size * 0.06, y + size * 0.28, start=18, extent=132, outline=line_color, width=max(1, stroke - 1), style=tk.ARC)
            canvas.create_line(cx - size * 0.15, cy + size * 0.10, cx + size * 0.10, cy + size * 0.04, fill=color, width=max(1, stroke - 1))
        elif attr == "Intelligence":
            canvas.create_oval(cx - size * 0.26, cy - size * 0.30, cx + size * 0.26, cy + size * 0.18, fill="", outline=line_color, width=stroke)
            canvas.create_rectangle(cx - size * 0.13, cy + size * 0.15, cx + size * 0.13, cy + size * 0.30, fill=line_color, outline="")
            for offset in (-0.16, 0.0, 0.16):
                canvas.create_arc(cx - size * 0.25 + size * offset, cy - size * 0.26, cx + size * 0.12 + size * offset, cy + size * 0.06, start=35, extent=245, outline=line_color, width=max(1, stroke - 1), style=tk.ARC)
            canvas.create_line(cx, cy - size * 0.24, cx, cy + size * 0.08, fill=line_color, width=max(1, stroke - 1))
        elif attr == "Charisma":
            crown = [
                cx - size * 0.34, cy - size * 0.05,
                cx - size * 0.22, cy - size * 0.30,
                cx - size * 0.06, cy - size * 0.08,
                cx + size * 0.10, cy - size * 0.32,
                cx + size * 0.24, cy - size * 0.07,
                cx + size * 0.34, cy - size * 0.27,
                cx + size * 0.30, cy + size * 0.16,
                cx - size * 0.28, cy + size * 0.16
            ]
            canvas.create_polygon(crown, fill=line_color, outline="")
            canvas.create_line(cx - size * 0.24, cy + size * 0.25, cx + size * 0.24, cy + size * 0.25, fill=line_color, width=stroke, capstyle=tk.ROUND)
            for x in (cx - size * 0.12, cx + size * 0.12):
                canvas.create_oval(x - size * 0.035, cy + size * 0.01, x + size * 0.035, cy + size * 0.08, fill=color, outline="")
        elif attr == "Vitality":
            heart = [
                cx, cy + size * 0.29,
                cx - size * 0.32, cy + size * 0.02,
                cx - size * 0.27, cy - size * 0.24,
                cx - size * 0.06, cy - size * 0.19,
                cx, cy - size * 0.07,
                cx + size * 0.06, cy - size * 0.19,
                cx + size * 0.27, cy - size * 0.24,
                cx + size * 0.32, cy + size * 0.02
            ]
            canvas.create_polygon(heart, fill=line_color, outline="", smooth=True)
            pulse = [
                cx - size * 0.26, cy + size * 0.02,
                cx - size * 0.10, cy + size * 0.02,
                cx - size * 0.04, cy - size * 0.10,
                cx + size * 0.04, cy + size * 0.12,
                cx + size * 0.10, cy + size * 0.02,
                cx + size * 0.26, cy + size * 0.02
            ]
            canvas.create_line(pulse, fill=color, width=max(1, stroke - 1), capstyle=tk.ROUND, joinstyle=tk.ROUND)

    def draw_trophy(self, canvas, attr, progress, color, level_req):
        """Draws a high-resolution attribute trophy with tier-specific upgrades."""
        canvas.delete("all")

        c_width = int(canvas['width'])
        c_height = int(canvas['height'])
        s = min(c_width * 0.78, c_height * 0.86)
        scale = max(0.45, s / 92.0)
        cx = c_width / 2
        y0 = max(0, (c_height - (s * 0.98)) / 2)
        left = cx - (s * 0.28)
        right = cx + (s * 0.28)
        rim_left = cx - (s * 0.34)
        rim_right = cx + (s * 0.34)
        top = y0 + (s * 0.07)
        bowl_bottom = y0 + (s * 0.48)
        base_y = y0 + (s * 0.76)

        earned = progress >= 1.0
        display_color = color if earned else self._blend_color("#586273", "#A8AFBB", progress * 0.35)
        primary, shadow, highlight, accent = self._trophy_material(level_req, progress)
        dark_line = self._blend_color(shadow, "#111827", 0.32)
        glow = self._blend_color(display_color, "#FFFFFF", 0.18 + (0.35 * progress)) if earned else self._blend_color("#4B5563", "#C3CAD5", 0.18 + (progress * 0.20))
        rim_shine = "#FFFFFF" if earned else "#9EA7B6"

        canvas.create_oval(cx - s * 0.31, base_y + s * 0.08, cx + s * 0.31, base_y + s * 0.19, fill=self._blend_color(self.bg_light, "#000000", 0.16), outline="")

        if level_req >= 50:
            for angle in range(0, 360, 45):
                radians = math.radians(angle)
                ray_cy = y0 + s * 0.39
                inner = s * 0.33
                outer = s * (0.40 if level_req < 100 else 0.43)
                canvas.create_line(
                    cx + math.cos(radians) * inner,
                    ray_cy + math.sin(radians) * inner,
                    cx + math.cos(radians) * outer,
                    ray_cy + math.sin(radians) * outer,
                    fill=glow,
                    width=max(1, int(2 * scale)),
                    capstyle=tk.ROUND
                )

        handle_width = max(3, int(4 * scale))
        canvas.create_arc(cx - s * 0.49, top + s * 0.05, cx - s * 0.12, bowl_bottom + s * 0.10, start=78, extent=214, outline=shadow, width=handle_width, style=tk.ARC)
        canvas.create_arc(cx + s * 0.12, top + s * 0.05, cx + s * 0.49, bowl_bottom + s * 0.10, start=-112, extent=214, outline=shadow, width=handle_width, style=tk.ARC)
        canvas.create_arc(cx - s * 0.45, top + s * 0.10, cx - s * 0.17, bowl_bottom + s * 0.03, start=86, extent=194, outline=highlight, width=max(1, int(2 * scale)), style=tk.ARC)
        canvas.create_arc(cx + s * 0.17, top + s * 0.10, cx + s * 0.45, bowl_bottom + s * 0.03, start=-100, extent=194, outline=highlight, width=max(1, int(2 * scale)), style=tk.ARC)

        canvas.create_oval(rim_left, top - s * 0.04, rim_right, top + s * 0.08, fill=highlight, outline=dark_line, width=max(1, int(scale)))

        bowl = [
            left, top + s * 0.01,
            right, top + s * 0.01,
            cx + s * 0.24, bowl_bottom,
            cx - s * 0.24, bowl_bottom
        ]
        canvas.create_polygon(bowl, fill=primary, outline=dark_line, width=max(1, int(2 * scale)), smooth=True)
        canvas.create_arc(rim_left, top - s * 0.04, rim_right, top + s * 0.08, start=0, extent=180, outline=rim_shine, width=max(1, int(2 * scale)), style=tk.ARC)
        canvas.create_polygon(left + s * 0.04, top + s * 0.04, cx - s * 0.07, top + s * 0.04, cx - s * 0.13, bowl_bottom - s * 0.02, left + s * 0.11, bowl_bottom - s * 0.01, fill=highlight, outline="")
        canvas.create_polygon(cx + s * 0.08, top + s * 0.04, right - s * 0.04, top + s * 0.04, right - s * 0.12, bowl_bottom - s * 0.03, cx + s * 0.16, bowl_bottom - s * 0.01, fill=self._blend_color(primary, shadow, 0.30), outline="")
        canvas.create_line(cx - s * 0.20, bowl_bottom - s * 0.02, cx + s * 0.20, bowl_bottom - s * 0.02, fill=self._blend_color(primary, shadow, 0.18), width=max(1, int(2 * scale)), capstyle=tk.ROUND)

        stem_w = s * 0.16
        canvas.create_polygon(cx - stem_w / 2, bowl_bottom - s * 0.01, cx + stem_w / 2, bowl_bottom - s * 0.01, cx + stem_w * 0.72, base_y, cx - stem_w * 0.72, base_y, fill=shadow, outline=dark_line, width=max(1, int(scale)))
        canvas.create_polygon(cx - s * 0.25, base_y - s * 0.05, cx + s * 0.25, base_y - s * 0.05, cx + s * 0.34, base_y + s * 0.08, cx - s * 0.34, base_y + s * 0.08, fill=primary, outline=dark_line, width=max(1, int(2 * scale)))
        canvas.create_rectangle(cx - s * 0.29, base_y + s * 0.04, cx + s * 0.29, base_y + s * 0.14, fill=shadow, outline=dark_line, width=max(1, int(scale)))
        canvas.create_line(cx - s * 0.22, base_y + s * 0.06, cx + s * 0.22, base_y + s * 0.06, fill=highlight, width=max(1, int(scale)), capstyle=tk.ROUND)

        medallion_r = s * 0.235
        medallion_cy = top + s * 0.14 + medallion_r
        medallion_fill = self._blend_color(display_color, "#111827", 0.14 if earned else 0.30)
        medallion_shadow = self._blend_color(medallion_fill, "#000000", 0.20)
        canvas.create_oval(cx - medallion_r, medallion_cy - medallion_r, cx + medallion_r, medallion_cy + medallion_r, fill=medallion_shadow, outline="")
        canvas.create_oval(cx - medallion_r * 0.92, medallion_cy - medallion_r * 0.92, cx + medallion_r * 0.92, medallion_cy + medallion_r * 0.92, fill=medallion_fill, outline=highlight, width=max(1, int(2 * scale)))
        canvas.create_arc(cx - medallion_r * 0.72, medallion_cy - medallion_r * 0.72, cx + medallion_r * 0.72, medallion_cy + medallion_r * 0.72, start=42, extent=98, outline=self._blend_color("#FFFFFF", highlight, 0.35), width=max(1, int(2 * scale)), style=tk.ARC)

        symbol_size = medallion_r * 1.76
        symbol_main = self.get_readable_text_color(medallion_fill, "#FFFFFF") if earned else "#D7DCE4"
        symbol_shadow = self._blend_color(medallion_fill, "#000000", 0.48)
        symbol_glow = self._blend_color(display_color, "#FFFFFF", 0.70 if earned else 0.28)
        self.draw_attribute_symbol(canvas, attr, cx + s * 0.012, medallion_cy + s * 0.014, symbol_size, display_color, symbol_shadow)
        self.draw_attribute_symbol(canvas, attr, cx, medallion_cy, symbol_size, symbol_glow, symbol_main)
        shine_color = self._blend_color(symbol_main, "#FFFFFF", 0.55 if earned else 0.18)
        canvas.create_line(cx - medallion_r * 0.43, medallion_cy - medallion_r * 0.48, cx - medallion_r * 0.12, medallion_cy - medallion_r * 0.72, fill=shine_color, width=max(1, int(2 * scale)), capstyle=tk.ROUND)
        canvas.create_line(cx + medallion_r * 0.16, medallion_cy + medallion_r * 0.55, cx + medallion_r * 0.52, medallion_cy + medallion_r * 0.20, fill=shine_color, width=max(1, int(scale)), capstyle=tk.ROUND)
        if earned:
            sparkle_x = cx + medallion_r * 0.62
            sparkle_y = medallion_cy - medallion_r * 0.58
            sparkle_r = medallion_r * 0.16
            canvas.create_line(sparkle_x - sparkle_r, sparkle_y, sparkle_x + sparkle_r, sparkle_y, fill="#FFFFFF", width=max(1, int(scale)), capstyle=tk.ROUND)
            canvas.create_line(sparkle_x, sparkle_y - sparkle_r, sparkle_x, sparkle_y + sparkle_r, fill="#FFFFFF", width=max(1, int(scale)), capstyle=tk.ROUND)

        if level_req >= 10:
            for offset in (-0.22, 0, 0.22):
                canvas.create_oval(cx + s * offset - s * 0.032, top + s * 0.02, cx + s * offset + s * 0.032, top + s * 0.084, fill=glow, outline=highlight)

        if level_req >= 25:
            for side in (-1, 1):
                for index in range(3):
                    y = bowl_bottom + s * (0.01 + index * 0.08)
                    x = cx + side * s * (0.22 + index * 0.012)
                    leaf = [x, y, x + side * s * 0.11, y - s * 0.04, x + side * s * 0.07, y + s * 0.04]
                    canvas.create_polygon(leaf, fill=accent, outline="", smooth=True)

        if level_req >= 50:
            canvas.create_arc(cx - s * 0.38, top - s * 0.04, cx + s * 0.38, top + s * 0.18, start=15, extent=150, outline=glow, width=max(1, int(2 * scale)), style=tk.ARC)

        if level_req >= 100:
            for x, y in ((cx - s * 0.32, top + s * 0.04), (cx + s * 0.32, top + s * 0.27), (cx, top + s * 0.04)):
                r = s * 0.035
                canvas.create_line(x - r, y, x + r, y, fill="#FFFFFF", width=max(1, int(2 * scale)))
                canvas.create_line(x, y - r, x, y + r, fill="#FFFFFF", width=max(1, int(2 * scale)))

    def update_stats_display(self, animate_rank=True):
        """Updates the text labels, progress bars, and visual trophies on the Character tab."""

        # Stats display refreshes both numbers and artwork. If new trophy tiers are now
        # needed, the trophy room is rebuilt before drawing progress.
        current_tiers = self.get_tiers()
        if current_tiers is not self._last_rendered_tiers:
            self.rebuild_trophy_room()
            current_tiers = self._last_rendered_tiers

        # Each attribute refreshes its label, progress bar, and every trophy icon tied
        # to that attribute.
        for attr in self.attributes:
            stat = self.data["stats"][attr]
            lvl = stat["level"]
            xp = stat["xp"]
            xp_needed = self.get_xp_needed(lvl)

            self.stat_labels[attr].config(text=f"Lvl {lvl}  ({xp} / {xp_needed} XP)")
            self.stat_labels[f"{attr}_pb"]['maximum'] = xp_needed
            self.stat_labels[f"{attr}_pb"]['value'] = xp

        self.redraw_trophies(current_tiers)

        return self.update_header(animate_rank=animate_rank)

    def show_summary(self, timeframe):
        """Reads the history memory and filters it by date to generate a report."""
        # The timeframe string controls the report window: today, the last 7 days, or
        # the last 30 days. The result is a target_date cutoff.
        if timeframe not in {"daily", "weekly", "monthly"}:
            timeframe = "daily"
        self.current_summary_timeframe = timeframe

        now = datetime.now()
        target_date = now
        title = ""

        if timeframe == "daily":
            title = f"Daily Report ({now.strftime('%b %d, %Y')})"
            target_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "weekly":
            title = "Weekly Report (Last 7 Days)"
            target_date = now - timedelta(days=7)
        elif timeframe == "monthly":
            title = "Monthly Report (Last 30 Days)"
            target_date = now - timedelta(days=30)

        total_xp = 0
        completed_tasks = 0
        activity_by_attribute = {attr: {} for attr in self.attributes}

        # The report loops through completion history and counts only records on or
        # after target_date. It groups completed subcategories under their attribute
        # so each colored card can tell one part of the story.
        for record in self.data["history"]:
            try:
                record_date = datetime.fromisoformat(record["date"])
            except (TypeError, ValueError):
                continue

            if record_date >= target_date:
                completed_tasks += 1
                try:
                    xp = max(0, int(record.get("xp", 0)))
                except (TypeError, ValueError):
                    xp = 0
                total_xp += xp
                attr = record.get("attribute")
                activity = record.get("subcategory") or record.get("name", "General")

                if attr in activity_by_attribute:
                    if activity not in activity_by_attribute[attr]:
                        activity_by_attribute[attr][activity] = {"count": 0, "xp": 0}
                    activity_by_attribute[attr][activity]["count"] += 1
                    activity_by_attribute[attr][activity]["xp"] += xp

        unique_activities = sum(len(activities) for activities in activity_by_attribute.values())
        self.summary_title_label.config(
            text=f"{title}  |  {unique_activities} activity types  |  {completed_tasks} quests  |  {total_xp} XP"
        )

        # Each card is a small independent report. It is temporarily unlocked, filled
        # with that attribute's activities, and then locked again.
        for attr in self.attributes:
            body = self.summary_cards[attr]["body"]
            body.config(state=tk.NORMAL)
            body.delete(1.0, tk.END)

            activities = activity_by_attribute[attr]
            attr_xp = sum(details["xp"] for details in activities.values())

            if not activities:
                body.insert(tk.END, "No activity yet.")
            else:
                body.insert(tk.END, f"{len(activities)} types | {attr_xp} XP\n\n")
                sorted_activities = sorted(
                    activities.items(),
                    key=lambda item: (-item[1]["count"], -item[1]["xp"], item[0])
                )
                for activity, details in sorted_activities:
                    count = details["count"]
                    if count > 10:
                        combo_tag = "combo_gold"
                    elif count >= 5:
                        combo_tag = "combo_red"
                    elif count >= 2:
                        combo_tag = "combo_blue"
                    else:
                        combo_tag = "bold"

                    body.insert(tk.END, f"{activity} ", "bold")
                    body.insert(tk.END, f"x{count}\n", combo_tag)
                    body.insert(tk.END, "   XP gained: ", "bold")
                    body.insert(tk.END, f"+{details['xp']} XP\n\n")

            body.config(state=tk.DISABLED)

    # ==============================================================================
    # GROUP D - ANIMATION / VISUAL FEEDBACK
    # This group adds motion: floating messages and particles. The core idea is to
    # create widgets, move or recolor them over time, then destroy them.
    # ==============================================================================
    def get_center(self):
        """A helper method to find the dead center of the application window."""
        # Animations need a starting point. This helper returns the current window center
        # or a reasonable fallback before Tkinter has measured the window.
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        return (w // 2, h // 2) if w > 1 else (425, 325)

    def clamp_widget_position(self, widget, x, y, padding=12):
        """Keeps an anchored widget fully inside the visible application window."""
        # update_idletasks() forces Tkinter to finish pending geometry calculations.
        # This ensures we get the most accurate current width and height of the window.
        self.root.update_idletasks()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        
        # Sometimes the window isn't fully drawn yet, giving a width/height of 1.
        # In that case, we fall back to the default app dimensions.
        if root_w <= 1 or root_h <= 1:
            root_w, root_h = 850, 700

        widget_w = widget.winfo_reqwidth()
        widget_h = widget.winfo_reqheight()

        if widget_w + (padding * 2) >= root_w:
            safe_x = root_w // 2
        else:
            half_w = widget_w // 2
            safe_x = max(padding + half_w, min(x, root_w - padding - half_w))

        if widget_h + (padding * 2) >= root_h:
            safe_y = root_h // 2
        else:
            half_h = widget_h // 2
            safe_y = max(padding + half_h, min(y, root_h - padding - half_h))

        return safe_x, safe_y

    def clamp_box_position(self, width, height, x, y, padding=12):
        """Keeps a floating popup box fully inside the visible application window."""
        # Similar to clamp_widget_position, but works with explicit width/height
        # rather than a widget object. Useful for centering temporary animations.
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        if root_w <= 1 or root_h <= 1:
            root_w, root_h = 850, 700

        if width + (padding * 2) >= root_w:
            safe_x = root_w // 2
        else:
            safe_x = max(padding + width // 2, min(x, root_w - padding - width // 2))

        if height + (padding * 2) >= root_h:
            safe_y = root_h // 2
        else:
            safe_y = max(padding + height // 2, min(y, root_h - padding - height // 2))

        return safe_x, safe_y

    def ease_out_cubic(self, progress):
        """Starts fast and slows down near the end for natural UI motion."""
        # Cubic easing keeps the animation snappy without ending in a hard stop.
        progress = max(0.0, min(progress, 1.0))
        return 1 - ((1 - progress) ** 3)

    def ease_smoothstep(self, progress):
        """Blends from 0 to 1 with soft acceleration and soft deceleration."""
        # Smoothstep is useful for opacity because it avoids both sudden starts and
        # sudden endings. That makes stacked level-up popups feel less jumpy.
        progress = max(0.0, min(progress, 1.0))
        return progress * progress * (3 - (2 * progress))

    def _blend_color(self, c1, c2, ratio):
        """Mathematically blends two hex colors together for fade effects."""
        c1, c2 = c1.lstrip('#'), c2.lstrip('#')
        r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
        r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)

        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_popup_alpha(self, popup, alpha):
        """Changes a popup's transparency when the operating system supports it."""
        # Some Tk builds do not support window alpha. The try block keeps animations
        # working everywhere, even if transparency is ignored by the platform.
        try:
            popup.attributes("-alpha", max(0.0, min(alpha, 1.0)))
        except tk.TclError:
            pass

    def raise_popup_window(self, popup):
        """Keeps a delayed reward popup above the main app window."""
        # Delayed Toplevel windows can appear behind the root window on some systems.
        # Making them transient and briefly topmost keeps text visible while particles
        # continue to live inside the root window.
        popup.transient(self.root)
        popup.lift()
        try:
            popup.attributes("-topmost", True)
            self.root.after(250, lambda: popup.attributes("-topmost", False) if popup.winfo_exists() else None)
        except tk.TclError:
            pass

    def popup_duration_ms(self, duration_steps):
        """Converts popup animation steps into milliseconds for reward scheduling."""
        # Scheduling uses the same frame clock as the popup engine. That keeps timing
        # math tied to the actual animation length.
        return int((duration_steps + 1) * POPUP_FRAME_INTERVAL_SECONDS * 1000)

    def popup_overlap_start_ms(self, duration_steps, start_ratio=REWARD_CHAIN_START_RATIO):
        """Returns the moment when the next reward popup should begin."""
        # The next reward starts before the previous one fully fades. XP waits longer
        # because it confirms the quest, while chained rewards hand off faster.
        return int(self.popup_duration_ms(duration_steps) * start_ratio)

    def schedule_level_up_sequence(self, level_events, rank_event=None):
        """Plays completion rewards after the XP popup has had a short moment."""
        # Reward chains are read in order: XP gain first, then attribute level-ups,
        # trophy unlocks, then account rank-ups. XP hands off after it is readable,
        # while later reward popups overlap sooner so the chain stays energetic.
        first_reward_delay = self.popup_overlap_start_ms(XP_POPUP_STEPS, XP_TO_REWARD_START_RATIO)
        next_delay = first_reward_delay
        level_start_gap = self.popup_overlap_start_ms(LEVEL_UP_POPUP_STEPS)
        trophy_start_gap = self.popup_overlap_start_ms(TROPHY_POPUP_STEPS)

        if rank_event:
            self.root.after(first_reward_delay, lambda event=rank_event: self.play_rank_up_animation(event))

        for event in level_events:
            self.root.after(next_delay, lambda e=event: self.play_level_up_animation(e))
            next_delay += level_start_gap

            if event["trophy"]:
                self.root.after(next_delay, lambda trophy=event["trophy"]: self.play_trophy_animation_at_center(trophy))
                next_delay += trophy_start_gap

    def play_level_up_animation(self, event):
        """Shows a delayed, extra-bright level-up celebration."""
        cx, cy = self.get_center()
        attr = event["attribute"]
        level = event["level"]

        popup_box = self.play_floating_text(f"{attr} leveled up {level}", "#B48EAD", cx, cy + 55, size=28, shake=True, duration_steps=LEVEL_UP_POPUP_STEPS, fade_steps=LEVEL_UP_POPUP_FADE_STEPS, trailing_icon=self.create_level_up_arrow_icon("#FF9E00"))
        # Level-up celebrations use more sparks and a later fade than XP rewards. They
        # still run in one shared animation loop so the larger burst does not tank FPS.
        self.play_firework_particles(self.attr_colors[attr], popup_box, count=112, rainbow=True, life_range=(76, 118), fade_start_ratio=0.52)

    def play_rank_up_animation(self, rank_event):
        """Animates account rank-ups directly on the header avatar and text."""
        self.rank_up_animation_token += 1
        token = self.rank_up_animation_token
        title = rank_event["title"]
        color = rank_event["color"]
        previous_level = rank_event["previous_level"]
        total_level = rank_event["total_level"]
        xp_into_level = rank_event["xp_into_level"]
        xp_needed = rank_event["xp_needed"]
        total_xp = rank_event["total_xp"]
        tier_index = rank_event["tier_index"]
        progress = rank_event["progress"]
        frames = RANK_UP_HEADER_FRAMES
        level_span = max(1, total_level - previous_level)
        focus_color = RANK_UP_GLOW_COLOR
        self.app_level_delta_label.config(text=f"+{level_span}", fg=focus_color)
        self.app_level_delta_label.pack(side=tk.LEFT, anchor=tk.N, padx=(2, 0), pady=(0, 0))
        started_at = time.perf_counter()

        def animate(frame=0):
            if token != self.rank_up_animation_token:
                return

            if frame <= frames:
                phase = frame / float(frames)
                rise = self.ease_out_cubic(min(phase * 1.35, 1.0))
                ring_load = self.ease_out_cubic(min(phase / 0.58, 1.0))
                hold_progress = self.ease_smoothstep(max(0.0, (phase - 0.58) / 0.42))
                icon_glow = math.sin(hold_progress * math.pi)
                ring_glow = 1 - (hold_progress * 0.55)
                title_glow = max(ring_load * 0.35, icon_glow)
                displayed_level = min(total_level, previous_level + int(round(level_span * rise)))

                self.app_title_label.config(
                    fg=self._blend_color(self.text_color, focus_color, title_glow),
                    font=("{San Francisco}", 18 + int(3 * title_glow), "bold")
                )
                self.app_level_delta_label.config(
                    fg=self._blend_color(self.bg_light, focus_color, title_glow)
                )
                self.user_name_label.config(
                    text=title,
                    fg=self._blend_color(color, focus_color, icon_glow * 0.86)
                )
                self.user_level_label.config(
                    text=self.format_account_level_text(displayed_level, xp_into_level, xp_needed, total_xp),
                    fg=self._blend_color(self.accent_green, focus_color, max(ring_load * 0.55, icon_glow * 0.92)),
                    font=("{San Francisco}", 11 + int(2 * icon_glow), "bold" if icon_glow > 0.28 else "normal")
                )
                self.update_avatar(
                    tier_index,
                    color,
                    progress,
                    glow_progress=max(ring_glow, icon_glow),
                    glow_color=focus_color,
                    ring_progress=ring_load
                )

                target_time = started_at + ((frame + 1) * POPUP_FRAME_INTERVAL_SECONDS)
                next_delay = max(1, int((target_time - time.perf_counter()) * 1000))
                self.root.after(next_delay, animate, frame + 1)
                return

            self.user_name_label.config(text=title, fg=color)
            self.user_level_label.config(
                text=self.format_account_level_text(total_level, xp_into_level, xp_needed, total_xp),
                fg=self.accent_green,
                font=("{San Francisco}", 11)
            )
            self.app_title_label.config(
                fg=self.text_color,
                font=("{San Francisco}", 18, "bold")
            )
            self.app_level_delta_label.pack_forget()
            self.update_avatar(tier_index, color, progress)

        animate()

    def play_trophy_animation_at_center(self, trophy_name):
        """Positions trophy rewards near the center reward stack."""
        cx, cy = self.get_center()
        self.play_trophy_animation(trophy_name, cx, cy + 112)

    def play_trophy_animation(self, trophy_name, x, y):
        """Shows a trophy reward after the level-up burst."""
        popup_box = self.play_floating_text(f"🏆 {trophy_name.upper()} EARNED! 🏆", "#EBCB8B", x, y, size=25, duration_steps=TROPHY_POPUP_STEPS, fade_steps=TROPHY_POPUP_FADE_STEPS)
        # Trophy rewards use the same box-anchored particle engine as level-ups so
        # their sparks share one steadier loop instead of the older point burst.
        self.play_firework_particles(
            "#EBCB8B",
            popup_box,
            count=64,
            palette=["#EBCB8B", "#FFD166", "#F59E0B", "#FFF4A3", "#ECEFF4"],
            physics=True,
            life_range=(54, 86),
            fade_start_ratio=0.45
        )

    def register_particle_widget(self, widget):
        """Tracks live particle widgets and caps burst load during rapid rewards."""
        self.active_particle_widgets.append(widget)
        while len(self.active_particle_widgets) > MAX_ACTIVE_PARTICLES:
            old_widget = self.active_particle_widgets.pop(0)
            if old_widget.winfo_exists():
                old_widget.destroy()

    def destroy_particle_widget(self, widget):
        """Destroys a particle widget and removes it from the live budget."""
        if widget in self.active_particle_widgets:
            self.active_particle_widgets.remove(widget)
        if widget.winfo_exists():
            widget.destroy()

    def play_floating_text(self, text, color, x, y, size=18, shake=False, duration_steps=70, fade_steps=20, trailing_icon=None):
        """Creates retro text that pops, floats upwards, and fades out."""
        # Floating feedback is shown in a tiny borderless Toplevel window. Toplevel
        # supports transparency, so the popup can feel lighter than a normal widget.
        root_w = self.root.winfo_width() if self.root.winfo_width() > 1 else 850
        root_h = self.root.winfo_height() if self.root.winfo_height() > 1 else 700
        self.popup_sequence = (self.popup_sequence + 1) % 5
        stack_offset = ((self.popup_sequence - 1) % 5) * 34
        stack_direction = 1 if y < root_h * 0.3 else -1
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.configure(bg=self.bg_light)
        self.set_popup_alpha(popup, 0.0)
        self.raise_popup_window(popup)

        display_size = max(14, size)
        box = tk.Frame(
            popup,
            bg=self.bg_light,
            bd=0,
            relief=tk.FLAT,
            highlightthickness=0,
            highlightbackground=color
        )
        box.pack()

        content_frame = tk.Frame(box, bg=self.bg_light)
        content_frame.pack(padx=18, pady=12)

        lbl = tk.Label(
            content_frame,
            text=text,
            font=("Courier", display_size, "bold"),
            fg=color,
            bg=self.bg_light,
            wraplength=max(140, root_w - 120),
            justify=tk.CENTER,
            bd=0,
            relief=tk.FLAT,
            highlightthickness=0
        )
        lbl.pack(side=tk.LEFT)

        # Optional trailing icons let special popups add pixel art without forcing
        # every caller to build a custom Toplevel layout.
        if trailing_icon:
            popup._trailing_icon = trailing_icon
            icon_label = tk.Label(content_frame, image=trailing_icon, bg=self.bg_light, bd=0, highlightthickness=0)
            icon_label.pack(side=tk.LEFT, padx=(10, 0))

        popup.update_idletasks()
        popup_w = popup.winfo_reqwidth()
        popup_h = popup.winfo_reqheight()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        # Top-corner popups stack downward, while center-screen reward popups stack
        # upward. This avoids edge clamping when several animations start together.
        safe_x, safe_y = self.clamp_box_position(popup_w, popup_h, x, y + (stack_offset * stack_direction))
        popup.geometry(f"+{root_x + safe_x - popup_w // 2}+{root_y + safe_y - popup_h // 2}")

        # This local clamp uses already-known window dimensions so animation frames do
        # not repeatedly ask Tkinter for geometry. That keeps long popups near 60 FPS.
        def clamp_popup_position(width, height, target_x, target_y, padding=12):
            if width + (padding * 2) >= root_w:
                clamped_x = root_w // 2
            else:
                clamped_x = max(padding + width // 2, min(target_x, root_w - padding - width // 2))

            if height + (padding * 2) >= root_h:
                clamped_y = root_h // 2
            else:
                clamped_y = max(padding + height // 2, min(target_y, root_h - padding - height // 2))

            return clamped_x, clamped_y

        # Tkinter animations usually use after(): do one tiny update, then schedule the
        # next update a few milliseconds later. This popup uses three phases:
        # fade in quickly, hover while drifting upward, then fade out smoothly.
        max_alpha = 0.94
        total_steps = max(duration_steps, fade_steps + 12)
        fade_in_steps = max(10, min(18, total_steps // 5))
        pop_steps = 12
        started_at = time.perf_counter()

        def animate(step=0, current_size=display_size, w=popup_w, h=popup_h):
            if step <= total_steps:
                progress = min(step / float(total_steps), 1.0)
                new_size = display_size
                new_w, new_h = w, h

                # The first few frames make the text pop like an RPG reward banner,
                # then settle back to its normal size for readability.
                if step < pop_steps:
                    pop_progress = step / float(pop_steps)
                    pop_amount = 4 * (1 - abs((pop_progress * 2) - 1))
                    new_size = display_size + round(pop_amount)
                elif step == pop_steps:
                    new_size = display_size

                if new_size != current_size:
                    lbl.config(font=("Courier", new_size, "bold"))
                    popup.update_idletasks()
                    new_w = popup.winfo_reqwidth()
                    new_h = popup.winfo_reqheight()

                # Drift uses easing so the popup slows as it rises. A small stack offset
                # keeps simultaneous messages from sitting exactly on top of each other.
                drift = int(54 * self.ease_out_cubic(progress))
                current_y = safe_y - drift

                if shake:
                    # Subtle, dampening retro shake effect.
                    amplitude = max(0, 3 - (step // 8))
                    dx = random.randint(-amplitude, amplitude)
                    dy = random.randint(-amplitude, amplitude)
                else:
                    dx, dy = 0, 0

                safe_x, safe_current_y = clamp_popup_position(new_w, new_h, x, current_y)
                popup.geometry(f"+{root_x + safe_x - new_w // 2 + dx}+{root_y + safe_current_y - new_h // 2 + dy}")
                if step % 30 == 0:
                    popup.lift()

                if step < fade_in_steps:
                    fade_in_ratio = self.ease_out_cubic(step / float(fade_in_steps))
                    alpha = max_alpha * fade_in_ratio
                elif step >= total_steps - fade_steps:
                    fade_ratio = (step - (total_steps - fade_steps)) / float(fade_steps)
                    eased_fade = self.ease_smoothstep(fade_ratio)
                    alpha = max_alpha * (1 - eased_fade)
                    lbl.config(fg=self._blend_color(color, self.bg_dark, eased_fade))
                else:
                    alpha = max_alpha

                self.set_popup_alpha(popup, alpha)

                # Running one final frame at alpha 0.0 prevents the popup from cutting
                # off before the fade-out has visually completed.
                target_time = started_at + ((step + 1) * POPUP_FRAME_INTERVAL_SECONDS)
                next_delay = max(1, int((target_time - time.perf_counter()) * 1000))
                self.root.after(next_delay, animate, step + 1, new_size, new_w, new_h)
            else:
                popup.destroy()

        animate()
        # Returning the box lets particle effects use the actual popup bounds instead
        # of guessing from the requested x/y point. That makes sparks feel attached to
        # the reward label even when clamping or stacking moves the popup.
        return {"x": safe_x, "y": safe_y, "width": popup_w, "height": popup_h}

    def play_firework_particles(self, color, source_box, count=80, rainbow=False, palette=None, physics=False, life_range=(40, 68), fade_start_ratio=0.35):
        """Spawns radial burst particles for level-up and rank-up celebrations."""
        # This is separate from play_particles() because it starts from the popup box
        # instead of a single point. One combined loop per popup keeps frame rate stable.
        # Parameters:
        # - count controls how many spark widgets are created.
        # - palette overrides the colors, useful for gold/orange XP rewards.
        # - physics adds stronger downward gravity for XP-style falling sparks.
        # - life_range controls how long particles remain alive.
        # - fade_start_ratio controls how late the slow fade begins.
        particles = []
        rainbow_colors = ["#BF616A", "#D08770", "#EBCB8B", "#A3BE8C", "#B48EAD", "#88C0D0", "#ECEFF4"]
        active_palette = palette or (rainbow_colors if rainbow else [color])
        root_w = self.root.winfo_width() if self.root.winfo_width() > 1 else 850
        root_h = self.root.winfo_height() if self.root.winfo_height() > 1 else 700
        box_x = source_box["x"]
        box_y = source_box["y"]
        half_w = max(18, source_box["width"] // 2)
        half_h = max(14, source_box["height"] // 2)

        for i in range(count):
            # Evenly stepping around the circle gives the burst a clear firework ring.
            # A small random offset keeps it from looking mathematically perfect.
            angle = ((i / float(count)) * math.tau) + random.uniform(-0.18, 0.18)
            direction_x = math.cos(angle)
            direction_y = math.sin(angle)
            # edge_scale finds a point on the popup rectangle in the particle's travel
            # direction. Starting from the box edge sells the idea that sparks burst out
            # of the quote box instead of appearing from the middle of the screen.
            edge_scale = min(
                half_w / max(abs(direction_x), 0.18),
                half_h / max(abs(direction_y), 0.18)
            )
            start_x = max(0, min(box_x + (direction_x * edge_scale * random.uniform(0.55, 1.0)), root_w - 12))
            start_y = max(0, min(box_y + (direction_y * edge_scale * random.uniform(0.55, 1.0)), root_h - 12))
            speed = random.uniform(3.2, 9.6) if physics else random.uniform(3.8, 10.8)
            size = random.randint(3, 10)
            life = random.randint(*life_range)
            p_color = random.choice(active_palette)

            particle = tk.Frame(self.root, bg=p_color, width=size, height=size)
            particle.place(x=start_x, y=start_y)
            self.register_particle_widget(particle)

            particles.append({
                "widget": particle,
                "x": float(start_x),
                "y": float(start_y),
                "dx": speed * math.cos(angle),
                "dy": speed * math.sin(angle),
                "size": size,
                "life": life,
                "max_life": life,
                "color": p_color,
                "fade_tick": 0
            })

        frame_count = [0]

        def animate():
            nonlocal root_w, root_h
            active = False
            frame_count[0] += 1
            if frame_count[0] % 10 == 0:
                measured_w = self.root.winfo_width()
                measured_h = self.root.winfo_height()
                root_w = measured_w if measured_w > 1 else 850
                root_h = measured_h if measured_h > 1 else 700

            for particle in particles:
                if particle["life"] > 0:
                    widget = particle["widget"]
                    if not widget.winfo_exists():
                        particle["life"] = -1
                        continue

                    # Drag slows the burst over time. A tiny gravity pull makes late
                    # sparks drift down like fireworks instead of freezing in place.
                    # XP rewards use a stronger gravity term through physics=True.
                    particle["x"] += particle["dx"]
                    particle["y"] += particle["dy"]
                    particle["dx"] *= 0.94 if physics else 0.955
                    particle["dy"] = (particle["dy"] * (0.94 if physics else 0.955)) + (0.34 if physics else 0.08)

                    size = particle["size"]
                    next_x = max(0, min(int(particle["x"]), root_w - size))
                    next_y = max(0, min(int(particle["y"]), root_h - size))

                    # Tkinter Frame widgets do not support opacity, so the fade is a
                    # color fade toward the current background. Updating every third
                    # frame keeps the fade smooth enough without extra per-frame cost.
                    age = particle["max_life"] - particle["life"]
                    fade_start = int(particle["max_life"] * fade_start_ratio)
                    if age >= fade_start and particle["fade_tick"] % 3 == 0:
                        fade_ratio = (age - fade_start) / float(max(1, particle["max_life"] - fade_start))
                        widget.configure(bg=self._blend_color(particle["color"], self.bg_dark, self.ease_smoothstep(fade_ratio)))
                    particle["fade_tick"] += 1

                    widget.place(x=next_x, y=next_y)
                    particle["life"] -= 1
                    active = True
                elif particle["life"] == 0:
                    self.destroy_particle_widget(particle["widget"])
                    particle["life"] -= 1

            if active:
                self.root.after(20, animate)

        animate()

    def play_particles(self, color, x, y, count=15, gravity=True, rainbow=False):
        """Spawns tiny squares that explode outward."""
        # Particles are tiny Frame widgets with random direction and lifetime. The list
        # keeps their widget, velocity, and remaining life together.
        particles = []
        rainbow_colors = ["#BF616A", "#D08770", "#EBCB8B", "#A3BE8C", "#B48EAD", "#88C0D0", "#ECEFF4"]

        # This loop creates all particles at the starting point. Random dx/dy values make
        # each particle travel in a slightly different direction.
        root_w = self.root.winfo_width() if self.root.winfo_width() > 1 else 850
        root_h = self.root.winfo_height() if self.root.winfo_height() > 1 else 700
        start_x = max(0, min(x, root_w - 8))
        start_y = max(0, min(y, root_h - 8))

        for _ in range(count):
            p_color = random.choice(rainbow_colors) if rainbow else color
            p = tk.Frame(self.root, bg=p_color, width=8, height=8)
            p.place(x=start_x, y=start_y)
            self.register_particle_widget(p)

            dx = random.randint(-12, 12)
            dy = random.randint(-12, 12)
            particles.append({
                "widget": p,
                "x": start_x,
                "y": start_y,
                "dx": dx,
                "dy": dy,
                "life": random.randint(20, 40)
            })

        # The particle animation moves living particles, applies gravity if requested,
        # destroys expired particles, and repeats while anything is still active.
        frame_count = [0]

        def animate():
            nonlocal root_w, root_h
            active = False
            frame_count[0] += 1
            if frame_count[0] % 10 == 0:
                measured_w = self.root.winfo_width()
                measured_h = self.root.winfo_height()
                root_w = measured_w if measured_w > 1 else 850
                root_h = measured_h if measured_h > 1 else 700

            for p in particles:
                if p["life"] > 0:
                    w = p["widget"]
                    if not w.winfo_exists():
                        p["life"] = -1
                        continue
                    next_x = p["x"] + p["dx"]
                    next_y = p["y"] + p["dy"]

                    if next_x < 0 or next_x > root_w - 8:
                        p["dx"] = int(p["dx"] * -0.6)
                        next_x = max(0, min(next_x, root_w - 8))

                    if next_y < 0 or next_y > root_h - 8:
                        p["dy"] = int(p["dy"] * -0.6)
                        next_y = max(0, min(next_y, root_h - 8))

                    p["x"], p["y"] = next_x, next_y
                    w.place(x=int(next_x), y=int(next_y))
                    p["life"] -= 1

                    if gravity:
                        p["dy"] += 1

                    active = True
                elif p["life"] == 0:
                    self.destroy_particle_widget(p["widget"])
                    p["life"] -= 1

            if active:
                self.root.after(35, animate)

        animate()

# ==============================================================================
# POWER SWITCH
# This code runs only when main.py is launched directly. It creates the Tkinter
# window, creates the app object, and starts the event loop.
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = LifeXPApp(root)
    root.mainloop()
