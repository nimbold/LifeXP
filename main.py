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
XP_GROWTH_RATE = 1.25
ACCOUNT_XP_PER_LEVEL = 500
POPUP_FRAME_INTERVAL_SECONDS = 1 / 60
XP_POPUP_STEPS = 125
XP_POPUP_FADE_STEPS = 42
LEVEL_UP_POPUP_STEPS = 420
LEVEL_UP_POPUP_FADE_STEPS = 140
RANK_UP_POPUP_STEPS = 420
RANK_UP_POPUP_FADE_STEPS = 140
TROPHY_POPUP_STEPS = 260
TROPHY_POPUP_FADE_STEPS = 90

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
        self.root.geometry("850x700")

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
        self.current_theme_name = "Nord RPG"
        self.settings_window = None

        # Popup sequence gives simultaneous reward messages small vertical offsets so
        # they fade independently instead of covering the exact same screen position.
        self.popup_sequence = 0
        self._subcategory_cache = None
        self._subcategory_owner_cache = None
        self._tiers_cache = None
        self._tiers_cache_expanded = None
        self._last_rendered_tiers = None
        self._max_stat_level = 1

        # Visual configuration lives near the top so the rest of the app can reuse it.
        # Each attribute gets one color, which is later used in bars, graphs, and art.
        self.attr_colors = self.themes[self.current_theme_name]["attr_colors"].copy()

        # Pixel art is represented as strings. A "1" means draw a square; a "0" means
        # leave that position empty. This is data, not drawing code yet.
        self.pixel_shapes = {
            "Strength": [
                "0000110000",
                "0001111000",
                "0000110000",
                "0000110000",
                "0000110000",
                "0000110000",
                "0000110000",
                "0111111110",
                "0000110000",
                "0000110000"
            ],
            "Agility": [
                "1000000000",
                "1100000000",
                "1110000000",
                "1111000000",
                "0111100000",
                "0011110000",
                "0001111000",
                "0000111100",
                "0000011110",
                "0000001111"
            ],
            "Intelligence": [
                "0000000000",
                "0011111100",
                "0100000010",
                "1111111111",
                "1111111111",
                "1111111111",
                "1111111111",
                "1111111111",
                "0100000010",
                "0011111100"
            ],
            "Charisma": [
                "0000000000",
                "1000110001",
                "1100110011",
                "1110110111",
                "1111111111",
                "1111111111",
                "0111111110",
                "0111111110",
                "0111111110",
                "0000000000"
            ],
            "Vitality": [
                "0000000000",
                "0011001100",
                "0111111110",
                "1111111111",
                "1111111111",
                "0111111110",
                "0011111100",
                "0001111000",
                "0000110000",
                "0000000000"
            ]
        }

        # Boot order matters: styles must exist before widgets are built, and data must
        # load before labels can show the current name, XP, tasks, and levels.
        self.apply_modern_theme()
        self.data = self.load_data()
        self._max_stat_level = self._calculate_max_level()
        self.current_theme_name = self.data["user_info"].get("theme", self.current_theme_name)
        if self.current_theme_name not in self.themes:
            self.current_theme_name = "Nord RPG"
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
        self.text_color = theme["text"]
        self.card_text_color = theme["card_text"]
        self.attr_colors = theme["attr_colors"].copy()

        # The root window is a normal tk widget, so it is configured directly rather
        # than through ttk.Style.
        self.root.configure(bg=self.bg_dark)

        # These style rules define the default look for common ttk widgets. configure()
        # sets normal values, while map() sets values for states like selected/active.
        self.style.configure('TFrame', background=self.bg_dark)
        self.style.configure('TNotebook', background=self.bg_dark, borderwidth=0)
        self.style.configure('TNotebook.Tab', background=self.bg_light, foreground=self.text_color, padding=[18, 9], font=('{San Francisco}', 11, 'bold'))
        self.style.map('TNotebook.Tab', background=[('selected', self.accent_green)], foreground=[('selected', self.bg_dark)])

        self.style.configure('TButton', background=self.bg_light, foreground=self.text_color, font=('{San Francisco}', 11), padding=6)
        self.style.map('TButton', background=[('active', self.accent_green)], foreground=[('active', self.bg_dark)])
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

        self.style.configure('TLabel', background=self.bg_dark, foreground=self.text_color, font=('{San Francisco}', 11))
        self.style.configure('Horizontal.TProgressbar', background=self.accent_green, troughcolor=self.bg_light, bordercolor=self.bg_dark, lightcolor=self.accent_green, darkcolor=self.accent_green)

        # Each RPG attribute gets its own progress-bar style. The loop prevents writing
        # five nearly identical style.configure() calls by hand.
        for attr, color in self.attr_colors.items():
            self.style.configure(f'{attr}.Horizontal.TProgressbar', background=color, troughcolor=self.bg_light, bordercolor=self.bg_dark, lightcolor=color, darkcolor=color)

        # Treeview is the table widget used for the quest list. Its heading, row color,
        # selection color, and row height are styled separately from other widgets.
        self.style.configure('Treeview', background=self.bg_light, foreground=self.text_color, fieldbackground=self.bg_light, borderwidth=0, rowheight=34, font=('{San Francisco}', 11))
        self.style.map('Treeview', background=[('selected', self.accent_green)], foreground=[('selected', self.bg_dark)])
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
        for option in ("bg", "fg", "background", "foreground", "insertbackground"):
            try:
                current = widget.cget(option)
            except tk.TclError:
                continue
            current = str(current)
            if current in color_map:
                try:
                    widget.configure(**{option: color_map[current]})
                except tk.TclError:
                    pass

        for child in widget.winfo_children():
            self.recolor_widget_tree(child, color_map)

    def setup_header(self):
        """Builds the User Account bar at the top right of the application."""
        # The header is a horizontal profile area at the top. It holds the avatar icon
        # and the account title/level labels.
        self.header_frame = tk.Frame(self.root, bg=self.bg_light)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(16, 0))

        self.settings_button = ttk.Button(self.header_frame, text="⚙ Settings", command=self.open_settings_page)
        self.settings_button.pack(side=tk.LEFT, padx=14, pady=12)

        # The app title anchors the toolbar so the top of the window feels like one
        # intentional surface instead of loose widgets floating on the background.
        self.app_title_frame = tk.Frame(self.header_frame, bg=self.bg_light)
        self.app_title_frame.pack(side=tk.LEFT, padx=(4, 0))
        self.app_title_label = tk.Label(
            self.app_title_frame,
            text="LifeXP",
            font=("{San Francisco}", 18, "bold"),
            bg=self.bg_light,
            fg=self.text_color
        )
        self.app_title_label.pack(anchor=tk.W)

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

    def update_avatar(self, tier_index, color, progress):
        """Draws the user title icon and a circular progress bar around it."""
        # Redrawing starts by clearing the canvas. Canvas drawings are not widgets;
        # they are items that stay until explicitly deleted.
        self.avatar_canvas.delete("all")

        # The ring is inset by a small padding value so its stroke does not touch the
        # edge of the canvas.
        pad = 4
        s = self.avatar_size

        # The avatar progress ring is two pieces: a full background oval and then a
        # colored arc that covers only the completed percentage.
        self.avatar_canvas.create_oval(pad, pad, s-pad, s-pad, outline=self.bg_light, width=4)

        angle = int(360 * progress)
        if angle > 0:
            self.avatar_canvas.create_arc(pad, pad, s-pad, s-pad, start=90, extent=-angle, outline=color, style=tk.ARC, width=4)

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
                    self.avatar_canvas.create_rectangle(x1, y1, x1+pixel_size, y1+pixel_size, fill=color, outline="")

    def update_header(self, animate_rank=True):
        """Calculates total global XP and Level and updates the UI."""
        # Total account XP is reconstructed from every attribute. Stored XP only keeps
        # the current level's remainder, so previous level costs are added back in.
        total_xp = sum(self.get_total_xp_for_stat(stat) for stat in self.data["stats"].values())

        # The global account level is simpler than attribute levels: every fixed chunk
        # of total XP adds one account level, and the remainder becomes ring progress.
        total_level = (total_xp // ACCOUNT_XP_PER_LEVEL) + 1
        progress = (total_xp % ACCOUNT_XP_PER_LEVEL) / float(ACCOUNT_XP_PER_LEVEL)

        # Once the total level is known, the header labels and avatar can be updated
        # with the matching title, color, and icon.
        title, color, tier_index = self.get_title_info(total_level)
        self.user_name_label.config(text=title, fg=color)
        self.user_level_label.config(text=f"Total Lvl: {total_level}  |  {total_xp} Total XP", fg=self.accent_green)

        # This block plays a rank-up animation only after startup. current_total_level
        # starts at 0 so loading an existing save does not trigger old animations.
        rank_event = None
        if self.current_total_level != 0 and total_level > self.current_total_level:
            rank_event = {"title": title, "color": color}
            if animate_rank:
                self.play_rank_up_animation(title, color)

        self.current_total_level = total_level
        self.update_avatar(tier_index, color, progress)
        return rank_event

    def setup_ui(self):
        """Initializes the main tabbed interface of the application."""
        # The Notebook widget creates tabs. Each tab is just a Frame that later receives
        # its own controls.
        self.notebook = ttk.Notebook(self.root)
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
        """Creates generated pixel icons for the main navigation tabs."""
        # Color meaning follows common UI guidance: blue for active work/logs, green for
        # character growth, and gold for history/records.
        patterns = {
            "tasks": [
                "..BBBBBB..",
                ".BWWWWWWB.",
                ".BWBBBBWB.",
                ".BWWWWWWB.",
                ".BWBBBBWB.",
                ".BWWWWWWB.",
                ".BWBBBBWB.",
                ".BWWWWWWB.",
                "..BBBBBB..",
                ".........."
            ],
            "character": [
                "....GG....",
                "...GWWG...",
                "..GWWWWG..",
                ".GWWGGWWG.",
                ".GWGGGGWG.",
                "..GGGGGG..",
                "..G.GG.G..",
                ".G..GG..G.",
                "....GG....",
                ".........."
            ],
            "chronicles": [
                "..YYYYYY..",
                ".YWWWWWWY.",
                ".YWYYYYWY.",
                ".YWWWWWWY.",
                ".YWYYYYWY.",
                ".YWWWWWWY.",
                ".YWYYYYWY.",
                ".YWWWWWWY.",
                "..YYYYYY..",
                ".........."
            ]
        }

        palettes = {
            "tasks": {"B": "#0A84FF", "W": "#EAF3FF"},
            "character": {"G": "#34C759", "W": "#EFFFF3"},
            "chronicles": {"Y": "#FFCC00", "W": "#FFF8D6"}
        }

        return {
            name: self.create_pixel_icon(pattern, palettes[name])
            for name, pattern in patterns.items()
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
        self.task_tree = ttk.Treeview(table_frame, columns=("Task", "Attribute", "XP"), show="headings")
        self.task_tree.heading("Task", text="Quest Name")
        self.task_tree.heading("Attribute", text="Scaling Attribute")
        self.task_tree.heading("XP", text="XP")

        self.task_tree.column("Task", width=250, anchor=tk.W)
        self.task_tree.column("Attribute", width=220, anchor=tk.CENTER)
        self.task_tree.column("XP", width=100, anchor=tk.CENTER)

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # The scrollbar and table are connected in both directions: the scrollbar moves
        # the table, and the table tells the scrollbar what portion is visible.
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.task_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        # Buttons call methods instead of doing work directly. This is an event-driven
        # style: Tkinter waits for a click, then runs the command function.
        control_frame = tk.Frame(page, bg=self.bg_light, width=190)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        control_frame.pack_propagate(False)

        tk.Label(
            control_frame,
            text="Quest Actions",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 14, "bold")
        ).pack(anchor=tk.W, padx=16, pady=(16, 4))

        # Color now carries the button meaning: neutral white for creating, green for
        # success, yellow for editing/caution, and red for destructive abandon.
        ttk.Button(control_frame, text="Accept Quest", style="QuestAccept.TButton", command=self.add_task_dialog).pack(fill=tk.X, padx=16, pady=(8, 8))
        ttk.Button(control_frame, text="Complete Quest", style="QuestComplete.TButton", command=self.complete_task).pack(fill=tk.X, padx=16, pady=8)
        ttk.Button(control_frame, text="Edit Quest", style="QuestEdit.TButton", command=self.edit_task_dialog).pack(fill=tk.X, padx=16, pady=8)
        ttk.Button(control_frame, text="Abandon Quest", style="QuestAbandon.TButton", command=self.delete_task).pack(fill=tk.X, padx=16, pady=8)

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

    def rebuild_trophy_room(self):
        # Rebuilding means clearing the old trophy widgets, then creating a fresh grid
        # that matches the current tier list.
        for widget in self.trophies_frame.winfo_children():
            widget.destroy()

        self.trophy_canvases = {}
        tiers = self.get_tiers()
        self._last_rendered_tiers = tiers

        # More tiers means more rows, so icons and labels shrink slightly to keep the
        # trophy room from taking too much space.
        icon_size = 30 if len(tiers) > 3 else 50
        font_size = 8 if len(tiers) > 3 else 9

        # The outer loop creates one column per attribute. The inner loop creates one
        # trophy cell per tier inside that attribute column.
        for col_idx, attr in enumerate(self.attributes):
            tk.Label(
                self.trophies_frame,
                text=attr,
                bg=self.bg_light,
                fg=self.attr_colors[attr],
                font=("{San Francisco}", 10, "bold")
            ).grid(row=0, column=col_idx, pady=(5, 0))
            self.trophies_frame.columnconfigure(col_idx, weight=1)

            for row_idx, (tier_name, level_req) in enumerate(tiers):
                cell_frame = tk.Frame(self.trophies_frame, bg=self.bg_light)
                cell_frame.grid(row=row_idx+1, column=col_idx, pady=2)

                c = tk.Canvas(cell_frame, width=icon_size, height=icon_size, bg=self.bg_light, highlightthickness=0)
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
                fg=self.card_text_color
            )
            title.pack(fill=tk.X, padx=6, pady=(8, 2))

            body = tk.Text(
                card,
                wrap=tk.WORD,
                font=("{San Francisco}", 9),
                bg=self.attr_colors[attr],
                fg=self.card_text_color,
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

        surface = tk.Frame(self.settings_window, bg=self.bg_dark)
        surface.pack(fill=tk.BOTH, expand=True, padx=22, pady=20)

        header = tk.Label(
            surface,
            text="Settings",
            font=("{San Francisco}", 22, "bold"),
            bg=self.bg_dark,
            fg=self.text_color
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
        previous_card_text = self.card_text_color
        previous_attr_colors = self.attr_colors.copy()

        # Update the active theme name and re-run the styling method.
        # This will instantly alter the appearance of many default ttk widgets.
        self.current_theme_name = theme_name
        self.apply_modern_theme()

        color_map = {
            previous_bg_dark: self.bg_dark,
            previous_bg_light: self.bg_light,
            previous_accent: self.accent_green,
            previous_text: self.text_color,
            previous_card_text: self.card_text_color
        }
        for attr, previous_color in previous_attr_colors.items():
            color_map[previous_color] = self.attr_colors[attr]

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

        if hasattr(self, "summary_title_label"):
            self.summary_title_label.configure(bg=self.bg_light, fg=self.text_color)
            for attr, widgets in self.summary_cards.items():
                widgets["title"].master.configure(bg=self.attr_colors[attr])
                widgets["title"].configure(bg=self.attr_colors[attr], fg=self.card_text_color)
                widgets["body"].configure(bg=self.attr_colors[attr], fg=self.card_text_color)

        if hasattr(self, "trophies_frame"):
            self.rebuild_trophy_room()
            self.update_stats_display()

        if hasattr(self, "summary_cards"):
            self.show_summary("daily")

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
                    "Strength Training",
                    "Bodyweight Exercise",
                    "Home Repairs",
                    "Gardening",
                    "Carrying Groceries",
                    "Moving Furniture",
                    "Deep Cleaning",
                    "Standing Desk Time",
                    "Posture Practice",
                    "Sports Practice"
                ],
                "Agility": [
                    "Walking",
                    "Running",
                    "Cycling",
                    "Stretching",
                    "Yoga",
                    "Cleaning",
                    "Sweeping",
                    "Decluttering",
                    "Typing Practice",
                    "Inbox Zero",
                    "Errands",
                    "Meal Prep Cleanup"
                ],
                "Intelligence": [
                    "Coding",
                    "Bug Fixing",
                    "Reading Book",
                    "Reading Docs",
                    "Studying",
                    "Online Course",
                    "Language Practice",
                    "Writing Notes",
                    "Planning",
                    "Budget Review",
                    "Learning a Framework",
                    "Research"
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
                    "Thank You Note"
                ],
                "Vitality": [
                    "Cooking Lunch",
                    "Healthy Breakfast",
                    "Meal Prep",
                    "Meditation",
                    "Drinking Water",
                    "Sleeping 8 Hours",
                    "Eye Rest",
                    "Skincare",
                    "Medication",
                    "Doctor Appointment",
                    "Therapy",
                    "Breathing Exercise",
                    "Outdoor Sunlight",
                    "No Junk Food"
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

                    # This loop patches missing top-level sections into older or partial save files.
                    # It prevents simple KeyError crashes later in the UI.
                    for key in default_data:
                        if key not in data:
                            data[key] = default_data[key]

                    data["stats"] = self.normalize_stats(data.get("stats"), default_data["stats"])
                    data["tasks"] = self.normalize_tasks(data.get("tasks"))
                    data["history"] = self.normalize_history(data.get("history"))
                    data["trophies"] = [
                        trophy for trophy in data.get("trophies", [])
                        if isinstance(trophy, str)
                    ] if isinstance(data.get("trophies"), list) else []

                    # Subcategories power the task-name autocomplete. This block removes old
                    # narrow suggestions and injects the broader daily-life catalogue.
                    if "subcategories" in data:
                        retired_subcategories = [
                            "Weightlifting",
                            "Pushups / Core",
                            "Stretching Routine",
                            "Yoga Break",
                            "Workout"
                        ]
                        for attr in data["subcategories"]:
                            if not isinstance(data["subcategories"][attr], list):
                                data["subcategories"][attr] = []
                            data["subcategories"][attr] = [
                                str(sub).strip() for sub in data["subcategories"][attr]
                                if isinstance(sub, str) and sub.strip() and sub not in retired_subcategories
                            ]

                        for attr, new_subs in default_data["subcategories"].items():
                            if attr not in data["subcategories"]:
                                data["subcategories"][attr] = new_subs
                            else:
                                for sub in new_subs:
                                    if sub not in data["subcategories"][attr]:
                                        data["subcategories"][attr].append(sub)

                    if not isinstance(data.get("user_info"), dict):
                        data["user_info"] = default_data["user_info"]
                    else:
                        data["user_info"].setdefault("theme", self.current_theme_name)

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
        # Refreshing the task table is done by clearing every visible row, then inserting
        # one row for each task currently stored in self.data.
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        for i, task in enumerate(self.data["tasks"]):
            self.task_tree.insert("", tk.END, iid=i, values=(task["name"], task["attribute"], f"{task['xp']} XP"))

    def add_task_dialog(self):
        """Pops up a window to create a new task. Features global autocomplete!"""
        # A Toplevel creates a second window for adding a quest. grab_set() makes it
        # modal, meaning the user should finish this dialog before returning to the app.
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title("Accept Quest")
        dialog.configure(bg=self.bg_dark)
        dialog.transient(self.root)

        surface = tk.Frame(dialog, bg=self.bg_dark)
        surface.pack(fill=tk.BOTH, expand=True, padx=24, pady=22)

        header = tk.Frame(surface, bg=self.bg_dark)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Accept Quest",
            bg=self.bg_dark,
            fg=self.text_color,
            font=("{San Francisco}", 22, "bold")
        ).pack(anchor=tk.W)
        tk.Label(
            header,
            text="Choose an attribute, find or type an activity, then set its XP.",
            bg=self.bg_dark,
            fg=self.accent_green,
            font=("{San Francisco}", 11)
        ).pack(anchor=tk.W, pady=(4, 0))

        # Attribute chips keep quest categories visible without forcing an extra field.
        attr_var = tk.StringVar(value=self.attributes[0])
        category_section = tk.Frame(surface, bg=self.bg_dark)
        category_section.pack(fill=tk.X, pady=(22, 0))
        tk.Label(
            category_section,
            text="Target Attribute",
            bg=self.bg_dark,
            fg=self.text_color,
            font=("{San Francisco}", 11, "bold")
        ).pack(anchor=tk.W)

        chip_row = tk.Frame(category_section, bg=self.bg_dark)
        chip_row.pack(fill=tk.X, pady=(8, 8))
        chip_widgets = {}

        def refresh_category_chips():
            # The selected chip gets the attribute color. The others stay neutral so the
            # user can quickly tell which attribute a new custom activity will use.
            for attr, chip in chip_widgets.items():
                selected = attr_var.get() == attr
                chip.config(
                    bg=self.attr_colors[attr] if selected else self.bg_light,
                    fg=self.card_text_color if selected else self.text_color,
                    relief=tk.FLAT if selected else tk.GROOVE,
                    bd=0 if selected else 1
                )

        def choose_attribute(attr):
            attr_var.set(attr)
            refresh_category_chips()
            update_suggestions()

        for index, attr in enumerate(self.attributes):
            chip = tk.Label(
                chip_row,
                text=attr,
                bg=self.bg_light,
                fg=self.text_color,
                padx=12,
                pady=7,
                cursor="hand2",
                font=("{San Francisco}", 10, "bold")
            )
            # grid() makes the chips wrap into rows. This prevents long names like
            # "Intelligence" or "Vitality" from disappearing off the right edge.
            chip.grid(row=index // 3, column=index % 3, sticky="ew", padx=(0, 8), pady=(0, 8))
            chip.bind("<Button-1>", lambda event, selected_attr=attr: choose_attribute(selected_attr))
            chip_widgets[attr] = chip

        # Equal column weights make the chip grid feel intentional instead of letting
        # each label pick a different width based only on its text length.
        for column in range(3):
            chip_row.grid_columnconfigure(column, weight=1, uniform="attribute_chips")

        search_section = tk.Frame(surface, bg=self.bg_dark)
        search_section.pack(fill=tk.BOTH, expand=True, pady=(18, 0))
        tk.Label(
            search_section,
            text="Activity",
            bg=self.bg_dark,
            fg=self.text_color,
            font=("{San Francisco}", 11, "bold")
        ).pack(anchor=tk.W)
        tk.Label(
            search_section,
            text="Tip: You can type an activity directly; saved activities choose their matching attribute automatically.",
            bg=self.bg_dark,
            fg=self.accent_green,
            font=("{San Francisco}", 10),
            justify=tk.LEFT,
            wraplength=500
        ).pack(anchor=tk.W, fill=tk.X, pady=(4, 0))
        activity_var = tk.StringVar()
        activity_entry = ttk.Entry(search_section, textvariable=activity_var, font=("{San Francisco}", 12))
        activity_entry.pack(fill=tk.X, pady=(8, 0), ipady=6)

        hint_label = tk.Label(
            search_section,
            text="Suggestions update as you type.",
            bg=self.bg_dark,
            fg=self.accent_green,
            font=("{San Francisco}", 10)
        )
        hint_label.pack(anchor=tk.W, pady=(6, 0))

        listbox_frame = tk.Frame(search_section, bg=self.bg_light, height=170)
        listbox_frame.pack_propagate(False)
        listbox_frame.pack(pady=(10, 0), fill=tk.BOTH, expand=True)

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
            yscrollcommand=suggestion_scrollbar.set
        )
        suggestion_scrollbar.config(command=suggestion_list.yview)
        suggestion_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        suggestion_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Nested helper functions are useful when logic belongs only inside one dialog.
        # This one rebuilds autocomplete suggestions whenever the text changes.
        def update_suggestions(*args):
            suggest_after_id[0] = None
            typed = activity_var.get().lower()
            selected_attr = attr_var.get()
            selected_subs = self.data["subcategories"].get(selected_attr, [])
            selected_subs_set = set(selected_subs)
            # Suggestions from the selected attribute are listed first. Suggestions from
            # other attributes are still searchable so typing "Meditation" can switch
            # the quest to Vitality automatically.
            other_subs = [
                sub
                for sub in self.get_all_subcategories()
                if sub not in selected_subs_set
            ]
            all_subs = dict.fromkeys(selected_subs + sorted(other_subs))
            owner_map = self.get_subcategory_owner_map()

            suggestion_list.delete(0, tk.END)

            # An exact match hides suggestions and auto-selects the matching attribute.
            # Partial matches stay visible so the user can click one.
            exact_matches = [sub for sub in all_subs if sub.lower() == typed]
            if exact_matches:
                owning_attr = owner_map.get(exact_matches[0])
                if owning_attr and attr_var.get() != owning_attr:
                    attr_var.set(owning_attr)
                    refresh_category_chips()
                suggestion_list.insert(tk.END, f"• {exact_matches[0]}")
                hint_label.config(text="Exact match found.")
                return

            hits = all_subs if not typed else [sub for sub in all_subs if typed in sub.lower()]

            if hits:
                for hit in list(hits)[:80]:
                    # A dot means the suggestion belongs to the currently selected
                    # attribute. A chevron means choosing it will switch attributes.
                    owning_attr = owner_map.get(hit, selected_attr)
                    prefix = "•" if owning_attr == selected_attr else "›"
                    suggestion_list.insert(tk.END, f"{prefix} {hit}")
                hint_label.config(text=f"{len(hits)} matching activities")
            else:
                hint_label.config(text="No saved activity yet. This will become a new suggestion.")

        suggest_after_id = [None]

        def update_suggestions_debounced(*args):
            if suggest_after_id[0] is not None:
                dialog.after_cancel(suggest_after_id[0])
            suggest_after_id[0] = dialog.after(120, update_suggestions)

        # When the user clicks a suggestion, this handler copies the text into the entry
        # and switches the selected attribute chip to the suggestion's saved category.
        def on_suggestion_select(event=None):
            if suggestion_list.curselection():
                index = suggestion_list.curselection()[0]
                selected_text = suggestion_list.get(index)[2:]

                owning_attr = self.get_subcategory_owner_map().get(selected_text)
                if owning_attr:
                    attr_var.set(owning_attr)
                    refresh_category_chips()

                activity_var.set(selected_text)
                activity_entry.icursor(tk.END)

        # trace_add connects variable changes to code. bind connects listbox selection
        # events to code. Together they make the autocomplete interactive.
        activity_var.trace_add("write", update_suggestions_debounced)
        suggestion_list.bind("<<ListboxSelect>>", on_suggestion_select)
        suggestion_list.bind("<Double-Button-1>", on_suggestion_select)

        divider = tk.Frame(surface, bg=self.bg_light, height=1)
        divider.pack(fill=tk.X, pady=(18, 16))

        slider_card = tk.Frame(surface, bg=self.bg_light)
        slider_card.pack(fill=tk.X)
        slider_card.grid_columnconfigure(0, weight=1)

        slider_header = tk.Frame(slider_card, bg=self.bg_light)
        slider_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        slider_header.grid_columnconfigure(0, weight=1)
        tk.Label(
            slider_header,
            text="Difficulty",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 12, "bold")
        ).grid(row=0, column=0, sticky="w")

        difficulty_var = tk.IntVar(value=5)
        val_label = tk.Label(
            slider_header,
            text="5 / 10",
            bg=self.bg_light,
            fg=self.accent_green,
            font=("{San Francisco}", 12, "bold")
        )
        val_label.grid(row=0, column=1, sticky="e")

        # The difficulty slider stores a simple 1-10 value. The app multiplies it by 10
        # to turn difficulty into an XP reward.
        slider_canvas = tk.Canvas(slider_card, height=58, bg=self.bg_light, highlightthickness=0)
        slider_canvas.grid(row=1, column=0, sticky="ew", padx=16)

        xp_label = tk.Label(
            slider_card,
            text="Yields 50 XP",
            bg=self.bg_light,
            fg=self.text_color,
            font=("{San Francisco}", 11)
        )
        xp_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))

        # This helper updates the difficulty label and color as the slider moves. The
        # RGB math blends from light to the accent green.
        def difficulty_color(v):
            # Difficulty 1 starts almost white, while difficulty 10 lands on the theme's
            # green-ish reward color. The intermediate values are simple RGB blends.
            ratio = (v - 1) / 9.0
            r = int(255 + (163 - 255) * ratio)
            g = int(255 + (190 - 255) * ratio)
            b = int(255 + (140 - 255) * ratio)
            return f'#{r:02x}{g:02x}{b:02x}'

        def draw_difficulty_slider():
            # The slider is drawn on a Canvas because Tk's built-in Scale widget is hard
            # to style nicely. Redrawing from scratch is cheap here because the canvas
            # only contains a track, ten ticks, two labels, and one thumb.
            slider_canvas.delete("all")
            width = max(slider_canvas.winfo_width(), 320)
            left = 18
            right = width - 18
            center_y = 22
            track_height = 8
            value = difficulty_var.get()
            ratio = (value - 1) / 9.0
            thumb_x = left + (right - left) * ratio
            color_hex = difficulty_color(value)

            slider_canvas.create_line(
                left,
                center_y,
                right,
                center_y,
                fill=self.bg_dark,
                width=track_height,
                capstyle=tk.ROUND
            )
            slider_canvas.create_line(
                left,
                center_y,
                thumb_x,
                center_y,
                fill=color_hex,
                width=track_height,
                capstyle=tk.ROUND
            )

            for tick in range(1, 11):
                tick_ratio = (tick - 1) / 9.0
                tick_x = left + (right - left) * tick_ratio
                slider_canvas.create_oval(
                    tick_x - 2,
                    center_y - 2,
                    tick_x + 2,
                    center_y + 2,
                    fill=self.text_color if tick > value else self.bg_dark,
                    outline=""
                )

            slider_canvas.create_oval(
                thumb_x - 12,
                center_y - 12,
                thumb_x + 12,
                center_y + 12,
                fill="#FFFFFF",
                outline=color_hex,
                width=3
            )
            slider_canvas.create_text(left, 46, text="1", fill=self.text_color, font=("{San Francisco}", 9))
            slider_canvas.create_text(right, 46, text="10", fill=self.text_color, font=("{San Francisco}", 9))
            val_label.config(text=f"{value} / 10", fg=color_hex)
            xp_label.config(text=f"Yields {value * 10} XP")

        def set_difficulty_from_event(event):
            # Mouse x-position becomes a 0..1 ratio along the track, then that ratio is
            # converted to one of the ten whole-number difficulty values.
            width = max(slider_canvas.winfo_width(), 320)
            left = 18
            right = width - 18
            ratio = min(1.0, max(0.0, (event.x - left) / (right - left)))
            difficulty_var.set(round(1 + ratio * 9))
            draw_difficulty_slider()

        slider_canvas.bind("<Configure>", lambda event: draw_difficulty_slider())
        slider_canvas.bind("<Button-1>", set_difficulty_from_event)
        slider_canvas.bind("<B1-Motion>", set_difficulty_from_event)

        # The save helper validates the dialog, remembers new activity names for future
        # autocomplete, appends the task, saves data, refreshes the table, and closes.
        def save():
            activity_name = activity_var.get().strip()
            attr = attr_var.get()
            xp = difficulty_var.get() * 10

            if not activity_name:
                messagebox.showerror("Hold up, Hero!", "Your quest needs an activity name.", parent=dialog)
                return

            if activity_name not in self.data["subcategories"][attr]:
                self.data["subcategories"][attr].append(activity_name)
                self._invalidate_subcategory_cache()

            self.data["tasks"].append({
                "name": activity_name,
                "attribute": attr,
                "subcategory": activity_name,
                "xp": xp
            })

            # After the new quest is added to memory, save the JSON file and
            # refresh the visible table so the UI matches the saved data.
            self.save_data()
            self.refresh_task_list()
            if suggest_after_id[0] is not None:
                dialog.after_cancel(suggest_after_id[0])
                suggest_after_id[0] = None
            dialog.destroy()

            cx, cy = self.get_center()
            self.play_floating_text("✨ QUEST ADDED", self.accent_green, cx, cy)

        def close_dialog():
            if suggest_after_id[0] is not None:
                dialog.after_cancel(suggest_after_id[0])
                suggest_after_id[0] = None
            dialog.destroy()

        action_row = tk.Frame(surface, bg=self.bg_dark)
        action_row.pack(fill=tk.X, pady=(18, 0))
        ttk.Button(action_row, text="Cancel", command=close_dialog).pack(side=tk.LEFT)
        ttk.Button(action_row, text="Accept Quest", style="QuestAccept.TButton", command=save).pack(side=tk.RIGHT)

        refresh_category_chips()
        update_suggestions()
        draw_difficulty_slider()
        self.show_fitted_window(dialog, min_width=560, min_height=660)
        dialog.grab_set()
        activity_entry.focus_set()
        dialog.bind("<Return>", lambda event: save())
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.bind("<Escape>", lambda event: close_dialog())

    def edit_task_dialog(self):
        """Allows editing a currently selected task."""
        # Most task actions begin by reading the selected row. If nothing is selected,
        # the method exits early or shows a helpful message.
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("Notice", "Select a quest from the log to edit it.")
            return

        index = int(selected[0])
        task = self.data["tasks"][index]

        # Editing uses simple popup dialogs instead of a custom window. The current task
        # values are passed in as initial values for the user to modify.
        new_name = simpledialog.askstring("Edit Quest", "New Quest Name:", initialvalue=task["name"])
        if new_name is None:
            return

        try:
            new_xp_str = simpledialog.askstring("Edit Quest", "New XP Reward:", initialvalue=str(task["xp"]))
            if new_xp_str is None:
                return
            new_xp = int(new_xp_str)
        except ValueError:
            messagebox.showerror("Error", "XP must be a numeric value.")
            return

        if new_xp < 1:
            messagebox.showerror("Error", "XP must be at least 1.")
            return

        new_name = new_name.strip()
        if not new_name:
            messagebox.showerror("Error", "Quest name cannot be blank.")
            return

        self.data["tasks"][index]["name"] = new_name
        self.data["tasks"][index]["subcategory"] = new_name
        self.data["tasks"][index]["xp"] = new_xp
        if new_name not in self.data["subcategories"][task["attribute"]]:
            self.data["subcategories"][task["attribute"]].append(new_name)
            self._invalidate_subcategory_cache()
        self.save_data()
        self.refresh_task_list()

        cx, cy = self.get_center()
        self.play_floating_text("✏️ QUEST UPDATED", "#88C0D0", cx, cy)

    def delete_task(self):
        """Removes a task from memory without giving XP."""
        selected = self.task_tree.selection()
        if not selected:
            return

        # Deleting asks for confirmation because it removes the quest without XP. After
        # deletion, the saved file and visible table are both refreshed.
        if messagebox.askyesno("Abandon Quest?", "Are you sure you want to abandon this quest? No XP will be awarded."):
            index = int(selected[0])
            del self.data["tasks"][index]
            self.save_data()
            self.refresh_task_list()

            cx, cy = self.get_center()
            self.play_floating_text("💀 QUEST ABANDONED", "#BF616A", cx, cy)
            self.play_particles("#BF616A", cx, cy, count=15, gravity=True)

    def complete_task(self):
        """The main gameplay loop: Finish task -> Grant XP -> Save History -> Redraw."""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("Notice", "Select a quest to complete it.")
            return

        index = int(selected[0])

        # Completing a quest removes it from active tasks, then reads its attribute and
        # XP reward so the character can gain progress.
        task = self.data["tasks"].pop(index)
        attr = task["attribute"]
        xp_gain = task["xp"]

        level_events = self.gain_xp(attr, xp_gain)

        # History records are separate from active tasks. They preserve what happened,
        # which attribute gained XP, and when completion occurred.
        completion_record = {
            "name": task["name"],
            "attribute": attr,
            "subcategory": task.get("subcategory", "General"),
            "xp": xp_gain,
            "date": datetime.now().isoformat()
        }
        self.data["history"].append(completion_record)

        self.save_data()
        self.refresh_task_list()
        rank_event = self.update_stats_display(animate_rank=False)

        cx, cy = self.get_center()
        # XP gain always gets a fixed readable duration. If level-up popups are also
        # needed, they are scheduled after it rather than shortening this popup.
        # play_floating_text() now returns the final popup box position. The XP particles
        # use that box as their source so sparks appear to come from the reward label,
        # while physics=True keeps the older gravity/falling feel.
        popup_box = self.play_floating_text(f"+{xp_gain} XP!", "#EBCB8B", cx, cy, size=30, duration_steps=XP_POPUP_STEPS, fade_steps=XP_POPUP_FADE_STEPS)
        self.play_firework_particles("#EBCB8B", popup_box, count=34, palette=["#EBCB8B", "#FFD166", "#F59E0B", "#F97316"], physics=True)

        if level_events or rank_event:
            self.schedule_level_up_sequence(level_events, rank_event)

    def get_xp_needed(self, level):
        """Returns the XP required to pass the given level. Increases by 25% each level."""
        # Attribute XP requirements grow by 25 percent per level. int() rounds the
        # calculated requirement down to a whole number.
        if level not in self.xp_needed_cache:
            self.xp_needed_cache[level] = int(BASE_XP_NEEDED * (XP_GROWTH_RATE ** (level - 1)))
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

    def get_all_subcategories(self):
        """Returns every known activity name once, sorted for autocomplete."""
        if self._subcategory_cache is None:
            # dict.fromkeys keeps the first copy of each activity while removing
            # duplicates. Sorting afterward gives the suggestion list a stable order.
            all_subs = dict.fromkeys(
                sub
                for subs in self.data["subcategories"].values()
                for sub in subs
            )
            self._subcategory_cache = sorted(all_subs)
        return self._subcategory_cache

    def get_subcategory_owner_map(self):
        """Returns the first saved attribute for each known activity name."""
        if self._subcategory_owner_cache is None:
            owner_map = {}
            for attr, subs in self.data["subcategories"].items():
                for sub in subs:
                    owner_map.setdefault(sub, attr)
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

    def draw_trophy(self, canvas, progress, color, shape_grid, is_gold=False, is_shiny=False):
        """Draws an 8-bit shape, filling it from bottom to top based on progress."""
        # Trophy drawing starts clean, measures the canvas, then converts the pixel-art
        # grid into rectangles sized to fit that canvas.
        canvas.delete("all")

        c_width = int(canvas['width'])
        c_height = int(canvas['height'])

        rows = len(shape_grid)
        cols = len(shape_grid[0])

        pixel_size = max(1, (c_width - 10) // max(rows, cols))

        offset_x = (c_width - (cols * pixel_size)) // 2
        offset_y = (c_height - (rows * pixel_size)) // 2

        # The fill effect works like a waterline: progress determines the vertical cutoff,
        # and pixels below that cutoff are colored while pixels above are dim.
        total_height = rows * pixel_size
        fill_height = total_height * progress
        cutoff_y = offset_y + total_height - fill_height

        base_color = "#FFD700" if is_gold else ("#00FFFF" if is_shiny else color)

        # The nested loops visit every cell in the trophy shape. Only "1" cells are
        # drawn, and each drawn cell chooses filled or dim color based on progress.
        for r in range(rows):
            for c in range(cols):
                if shape_grid[r][c] == "1":
                    x1 = offset_x + (c * pixel_size)
                    y1 = offset_y + (r * pixel_size)
                    x2 = x1 + pixel_size
                    y2 = y1 + pixel_size

                    pixel_center_y = y1 + (pixel_size / 2)

                    if pixel_center_y >= cutoff_y:
                        fill_color = base_color
                    else:
                        fill_color = "#4C566A"

                    canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="")

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

            shape = self.pixel_shapes[attr]

            for tier_name, level_req in current_tiers:
                canvas = self.trophy_canvases[f"{attr}_{tier_name}"]
                progress = min(lvl / float(level_req), 1.0)
                is_gold = (level_req == 50)
                is_shiny = (level_req == 100)
                self.draw_trophy(canvas, progress, self.attr_colors[attr], shape, is_gold, is_shiny)

        return self.update_header(animate_rank=animate_rank)

    def show_summary(self, timeframe):
        """Reads the history memory and filters it by date to generate a report."""
        # The timeframe string controls the report window: today, the last 7 days, or
        # the last 30 days. The result is a target_date cutoff.
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
                xp = record.get("xp", 0)
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

    def popup_overlap_start_ms(self, duration_steps):
        """Returns the moment when the next reward popup should begin."""
        # The next reward starts when the previous popup has finished 75 percent of its
        # life. That lets the last 25 percent overlap with the next popup's entrance.
        return int(self.popup_duration_ms(duration_steps) * 0.75)

    def schedule_level_up_sequence(self, level_events, rank_event=None):
        """Plays completion rewards after the XP popup has had a short moment."""
        # Reward chains are read in order: XP gain first, then attribute level-ups,
        # then account rank-ups. Each next popup starts at 75 percent of the previous
        # popup's lifetime, while each popup's own duration stays fixed.
        delay = self.popup_overlap_start_ms(XP_POPUP_STEPS)
        level_start_gap = self.popup_overlap_start_ms(LEVEL_UP_POPUP_STEPS)

        for index, event in enumerate(level_events):
            start_delay = delay + (index * level_start_gap)
            self.root.after(start_delay, lambda e=event: self.play_level_up_animation(e))

        if rank_event:
            rank_delay = delay + (len(level_events) * level_start_gap)
            self.root.after(rank_delay, lambda: self.play_rank_up_animation(rank_event["title"], rank_event["color"]))

    def play_level_up_animation(self, event):
        """Shows a delayed, extra-bright level-up celebration."""
        cx, cy = self.get_center()
        attr = event["attribute"]
        level = event["level"]

        popup_box = self.play_floating_text(f"{attr} leveled up {level}", "#B48EAD", cx, cy + 55, size=28, shake=True, duration_steps=LEVEL_UP_POPUP_STEPS, fade_steps=LEVEL_UP_POPUP_FADE_STEPS, trailing_icon=self.create_level_up_arrow_icon("#FF9E00"))
        # Level-up celebrations use more sparks and a later fade than XP rewards. They
        # still run in one shared animation loop so the larger burst does not tank FPS.
        self.play_firework_particles(self.attr_colors[attr], popup_box, count=112, rainbow=True, life_range=(76, 118), fade_start_ratio=0.52)

        if event["trophy"]:
            self.root.after(self.popup_overlap_start_ms(LEVEL_UP_POPUP_STEPS), lambda: self.play_trophy_animation(event["trophy"], cx, cy + 112))

    def play_rank_up_animation(self, title, color):
        """Celebrates account rank-ups with a wide rainbow burst."""
        x_pos = self.root.winfo_width() - 80 if self.root.winfo_width() > 1 else 750
        popup_box = self.play_floating_text(f"RANK UP: {title.upper()}!", color, x_pos, 80, size=28, duration_steps=RANK_UP_POPUP_STEPS, fade_steps=RANK_UP_POPUP_FADE_STEPS, trailing_icon=self.create_level_up_arrow_icon("#FFD700"))
        # Rank-up is the biggest reward, so it gets the largest and slowest fading
        # burst. The parameters keep that intensity without launching extra loops.
        self.play_firework_particles(color, popup_box, count=124, rainbow=True, life_range=(82, 128), fade_start_ratio=0.56)

    def play_trophy_animation(self, trophy_name, x, y):
        """Shows a trophy reward after the level-up burst."""
        self.play_floating_text(f"🏆 {trophy_name.upper()} EARNED! 🏆", "#EBCB8B", x, y, size=25, duration_steps=TROPHY_POPUP_STEPS, fade_steps=TROPHY_POPUP_FADE_STEPS)
        self.play_particles("#EBCB8B", x, y, count=50, gravity=True, rainbow=True)

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
                    particle["widget"].destroy()
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
                    p["widget"].destroy()
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
