# ==============================================================================
# LIFEXP - LEARNING MAP
# This file is a small desktop app. It mixes four ideas:
# 1. UI widgets from Tkinter, 2. saved JSON data, 3. RPG-style XP logic,
# and 4. simple canvas animations. Comments explain chunks, not every line.
# ==============================================================================
#
# IMPORTS
# Tkinter draws the window, datetime handles reports, JSON saves progress,
# os checks for the save file, and random makes visual effects less uniform.
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os
import random

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
        self.attributes = ["Strength", "Agility", "Intelligence", "Charisma", "Constitution"]

        # Keep track of persistence and account-level animation state. The JSON file
        # is the app's memory between runs.
        self.data_file = "lifexp_data.json"
        self.current_total_level = 0
        self.themes = self.get_theme_definitions()
        self.current_theme_name = "Nord RPG"
        self.settings_window = None

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
            "Constitution": [
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
                    "Constitution": "#34C759"
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
                    "Constitution": "#30D158"
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
                    "Constitution": "#A3BE8C"
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
                    "Constitution": "#50FA7B"
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
                    "Constitution": "#A6E3A1"
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
                    "Constitution": "#B8BB26"
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
                    "Constitution": "#9ECE6A"
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
                    "Constitution": "#859900"
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
        self.style.configure('TNotebook.Tab', background=self.bg_light, foreground=self.text_color, padding=[16, 7], font=('{San Francisco}', 11, 'bold'))
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
        self.style.configure('Treeview', background=self.bg_light, foreground=self.text_color, fieldbackground=self.bg_light, borderwidth=0, rowheight=30, font=('{San Francisco}', 11))
        self.style.map('Treeview', background=[('selected', self.accent_green)], foreground=[('selected', self.bg_dark)])
        self.style.configure('Treeview.Heading', background=self.bg_dark, foreground=self.accent_green, font=('{San Francisco}', 11, 'bold'))

    def setup_header(self):
        """Builds the User Account bar at the top right of the application."""
        # The header is a horizontal profile area at the top. It holds the avatar icon
        # and the account title/level labels.
        self.header_frame = tk.Frame(self.root, bg=self.bg_dark)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(15, 0))

        self.settings_button = ttk.Button(self.header_frame, text="⚙ Settings", command=self.open_settings_page)
        self.settings_button.pack(side=tk.LEFT, pady=8)

        # The avatar is drawn on a Canvas because it needs custom shapes and an arc,
        # not just normal text or buttons.
        self.avatar_size = 56
        self.avatar_canvas = tk.Canvas(self.header_frame, width=self.avatar_size, height=self.avatar_size, bg=self.bg_dark, highlightthickness=0)
        self.avatar_canvas.pack(side=tk.RIGHT)

        # This nested frame groups the two text labels so they can sit together to the
        # left of the avatar while still being part of the header.
        self.user_info_frame = tk.Frame(self.header_frame, bg=self.bg_dark)
        self.user_info_frame.pack(side=tk.RIGHT, padx=15)

        self.user_name_label = tk.Label(self.user_info_frame, text=self.data["user_info"]["name"], font=("{San Francisco}", 16, "bold"), bg=self.bg_dark, fg=self.text_color)
        self.user_name_label.pack(anchor=tk.E)

        self.user_level_label = tk.Label(self.user_info_frame, text="Total Lvl: 1  |  0 XP", font=("{San Francisco}", 11), bg=self.bg_dark, fg=self.accent_green)
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

    def update_header(self):
        """Calculates total global XP and Level and updates the UI."""
        # Total account XP is reconstructed from every attribute. Stored XP only keeps
        # the current level's remainder, so previous level costs are added back in.
        total_xp = 0

        for stat in self.data["stats"].values():
            stat_total_xp = stat["xp"]
            for l in range(1, stat["level"]):
                stat_total_xp += self.get_xp_needed(l)
            total_xp += stat_total_xp

        # The global account level is simpler than attribute levels: every 500 total XP
        # adds one account level, and the remainder becomes ring progress.
        total_level = (total_xp // 500) + 1
        progress = (total_xp % 500) / 500.0

        # Once the total level is known, the header labels and avatar can be updated
        # with the matching title, color, and icon.
        title, color, tier_index = self.get_title_info(total_level)
        self.user_name_label.config(text=title, fg=color)
        self.user_level_label.config(text=f"Total Lvl: {total_level}  |  {total_xp} Total XP", fg=self.accent_green)

        # This block plays a rank-up animation only after startup. current_total_level
        # starts at 0 so loading an existing save does not trigger old animations.
        if self.current_total_level != 0 and total_level > self.current_total_level:
            x_pos = self.root.winfo_width() - 80 if self.root.winfo_width() > 1 else 750
            self.play_floating_text(f"🌟 RANK UP: {title.upper()}!", color, x_pos, 80, size=20)
            self.play_particles(color, x_pos + 30, 40, count=60, gravity=False, rainbow=True)

        self.current_total_level = total_level
        self.update_avatar(tier_index, color, progress)

    def setup_ui(self):
        """Initializes the main tabbed interface of the application."""
        # The Notebook widget creates tabs. Each tab is just a Frame that later receives
        # its own controls.
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=15, pady=15)

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
        width = len(pattern[0]) * pixel_size
        height = len(pattern) * pixel_size
        image = tk.PhotoImage(width=width, height=height)

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

    def setup_tasks_tab(self):
        """Paints the 'Quest Log' tab (task list and action buttons)."""
        # The Quest Log tab is split into a large table on the left and action buttons
        # on the right.
        list_frame = ttk.LabelFrame(self.tab_tasks, text=" Active Quests ")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview acts like a spreadsheet-style table. The code defines named columns,
        # then configures each heading and width.
        self.task_tree = ttk.Treeview(list_frame, columns=("Task", "Attribute", "XP"), show="headings")
        self.task_tree.heading("Task", text="Quest Name")
        self.task_tree.heading("Attribute", text="Scaling Attribute")
        self.task_tree.heading("XP", text="XP")

        self.task_tree.column("Task", width=250, anchor=tk.W)
        self.task_tree.column("Attribute", width=220, anchor=tk.CENTER)
        self.task_tree.column("XP", width=100, anchor=tk.CENTER)

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # The scrollbar and table are connected in both directions: the scrollbar moves
        # the table, and the table tells the scrollbar what portion is visible.
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.task_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        # Buttons call methods instead of doing work directly. This is an event-driven
        # style: Tkinter waits for a click, then runs the command function.
        control_frame = ttk.Frame(self.tab_tasks)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=20)

        # Color now carries the button meaning: neutral white for creating, green for
        # success, yellow for editing/caution, and red for destructive abandon.
        ttk.Button(control_frame, text="Accept Quest", style="QuestAccept.TButton", command=self.add_task_dialog).pack(fill=tk.X, pady=8)
        ttk.Button(control_frame, text="Complete Quest", style="QuestComplete.TButton", command=self.complete_task).pack(fill=tk.X, pady=8)
        ttk.Button(control_frame, text="Edit Quest", style="QuestEdit.TButton", command=self.edit_task_dialog).pack(fill=tk.X, pady=8)
        ttk.Button(control_frame, text="Abandon Quest", style="QuestAbandon.TButton", command=self.delete_task).pack(fill=tk.X, pady=8)

    def get_tiers(self):
        # Trophy tiers expand when the character gets stronger. Below level 25 the UI
        # shows three tiers; after that it reveals higher long-term goals.
        max_level = max([stat["level"] for stat in self.data["stats"].values()] + [1])
        if max_level > 25:
            return [("Apprentice", 5), ("Adept", 10), ("Master", 25), ("Grandmaster", 50), ("Legend", 100)]
        else:
            return [("Apprentice", 5), ("Adept", 10), ("Master", 25)]

    def rebuild_trophy_room(self):
        # Rebuilding means clearing the old trophy widgets, then creating a fresh grid
        # that matches the current tier list.
        for widget in self.trophies_frame.winfo_children():
            widget.destroy()

        self.trophy_canvases = {}
        tiers = self.get_tiers()

        # More tiers means more rows, so icons and labels shrink slightly to keep the
        # trophy room from taking too much space.
        icon_size = 30 if len(tiers) > 3 else 50
        font_size = 8 if len(tiers) > 3 else 9

        # The outer loop creates one column per attribute. The inner loop creates one
        # trophy cell per tier inside that attribute column.
        for col_idx, attr in enumerate(self.attributes):
            ttk.Label(self.trophies_frame, text=attr, font=("{San Francisco}", 10, "bold"), foreground=self.attr_colors[attr]).grid(row=0, column=col_idx, pady=(5, 0))
            self.trophies_frame.columnconfigure(col_idx, weight=1)

            for row_idx, (tier_name, level_req) in enumerate(tiers):
                cell_frame = tk.Frame(self.trophies_frame, bg=self.bg_dark)
                cell_frame.grid(row=row_idx+1, column=col_idx, pady=2)

                c = tk.Canvas(cell_frame, width=icon_size, height=icon_size, bg=self.bg_dark, highlightthickness=0)
                c.pack()

                tk.Label(cell_frame, text=f"Lvl {level_req}", font=("{San Francisco}", font_size), bg=self.bg_dark, fg=self.text_color).pack()

                self.trophy_canvases[f"{attr}_{tier_name}"] = c

    def setup_character_tab(self):
        """Paints the 'Character Info' tab (progress bars and pixel trophies)."""
        # The Character tab has two main parts: numeric stat progress at the top and
        # visual trophy progress at the bottom.
        stats_frame = ttk.LabelFrame(self.tab_character, text=" Hero Attributes ")
        stats_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)

        # A dictionary stores references to labels and progress bars so other methods
        # can update them later without recreating them.
        self.stat_labels = {}
        for i, attr in enumerate(self.attributes):
            ttk.Label(stats_frame, text=f"{attr}:", font=("{San Francisco}", 12, "bold")).grid(row=i, column=0, sticky=tk.W, padx=15, pady=10)

            lbl = ttk.Label(stats_frame, text="Lvl 1 (0 / 100 XP)", font=("{San Francisco}", 12))
            lbl.grid(row=i, column=1, sticky=tk.W, padx=15, pady=10)
            self.stat_labels[attr] = lbl

            pb = ttk.Progressbar(stats_frame, orient='horizontal', length=250, mode='determinate', style=f'{attr}.Horizontal.TProgressbar')
            pb.grid(row=i, column=2, padx=15, pady=10, sticky=tk.EW)
            stats_frame.columnconfigure(2, weight=1)
            self.stat_labels[f"{attr}_pb"] = pb

        # The trophy room starts empty, then rebuild_trophy_room() fills it based on
        # the current maximum level and tier rules.
        self.trophies_frame = ttk.LabelFrame(self.tab_character, text=" Visual Trophy Room ")
        self.trophies_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.trophy_canvases = {}
        self.rebuild_trophy_room()

    def setup_summary_tab(self):
        """Paints the 'Chronicles' tab (report buttons and visual data)."""
        # The Summary tab starts with three timeframe buttons. Each button passes a
        # different string into show_summary().
        control_frame = ttk.Frame(self.tab_summary)
        control_frame.pack(fill=tk.X, padx=15, pady=15)

        ttk.Button(control_frame, text="Daily Cycle", command=lambda: self.show_summary("daily")).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Weekly Cycle", command=lambda: self.show_summary("weekly")).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Monthly Cycle", command=lambda: self.show_summary("monthly")).pack(side=tk.LEFT, padx=5)

        # Chronicles now has one large report area. Inside it, each attribute gets a
        # colored square that lists completed activity subcategories for the timeframe.
        report_frame = ttk.LabelFrame(self.tab_summary, text=" Activity Report ")
        report_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.summary_title_label = tk.Label(
            report_frame,
            text="",
            font=("{San Francisco}", 15, "bold"),
            bg=self.bg_dark,
            fg=self.text_color
        )
        self.summary_title_label.pack(fill=tk.X, padx=10, pady=(10, 6))

        cards_frame = tk.Frame(report_frame, bg=self.bg_dark)
        cards_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

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
        """Opens the Settings page, currently focused on app themes."""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.geometry("560x560")
        self.settings_window.configure(bg=self.bg_dark)
        self.settings_window.transient(self.root)

        header = tk.Label(
            self.settings_window,
            text="Settings",
            font=("{San Francisco}", 18, "bold"),
            bg=self.bg_dark,
            fg=self.text_color
        )
        header.pack(fill=tk.X, padx=18, pady=(18, 8))

        # For now Settings has one field: Themes. Each row shows swatches, a short
        # personality note, and an Apply button.
        themes_frame = ttk.LabelFrame(self.settings_window, text=" Themes ")
        themes_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 18))

        for theme_name, theme in self.themes.items():
            row = tk.Frame(themes_frame, bg=self.bg_dark)
            row.pack(fill=tk.X, padx=10, pady=6)

            swatches = tk.Frame(row, bg=self.bg_dark)
            swatches.pack(side=tk.LEFT, padx=(0, 10))

            for color in [theme["bg_dark"], theme["bg_light"], theme["accent"]] + list(theme["attr_colors"].values())[:3]:
                tk.Frame(swatches, bg=color, width=14, height=24).pack(side=tk.LEFT, padx=1)

            text_frame = tk.Frame(row, bg=self.bg_dark)
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            name_text = theme_name
            if theme_name == self.current_theme_name:
                name_text += "  ✓"

            tk.Label(
                text_frame,
                text=name_text,
                font=("{San Francisco}", 12, "bold"),
                bg=self.bg_dark,
                fg=self.text_color
            ).pack(anchor=tk.W)

            tk.Label(
                text_frame,
                text=theme["description"],
                font=("{San Francisco}", 10),
                bg=self.bg_dark,
                fg=self.text_color,
                wraplength=300,
                justify=tk.LEFT
            ).pack(anchor=tk.W)

            ttk.Button(
                row,
                text="Apply",
                command=lambda selected=theme_name: self.set_theme(selected)
            ).pack(side=tk.RIGHT, padx=(10, 0))

    def set_theme(self, theme_name, save=True):
        """Applies a selected theme immediately and optionally saves it."""
        if theme_name not in self.themes:
            return

        self.current_theme_name = theme_name
        self.apply_modern_theme()

        if hasattr(self, "data"):
            self.data["user_info"]["theme"] = theme_name
            if save:
                self.save_data()

        self.refresh_theme_widgets()

        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.destroy()
            self.settings_window = None
            self.open_settings_page()

    def refresh_theme_widgets(self):
        """Recolors already-created tk widgets after a theme change."""
        self.root.configure(bg=self.bg_dark)

        if hasattr(self, "header_frame"):
            self.header_frame.configure(bg=self.bg_dark)
            self.avatar_canvas.configure(bg=self.bg_dark)
            self.user_info_frame.configure(bg=self.bg_dark)
            self.user_name_label.configure(bg=self.bg_dark)
            self.user_level_label.configure(bg=self.bg_dark, fg=self.accent_green)

        if hasattr(self, "summary_title_label"):
            self.summary_title_label.configure(bg=self.bg_dark, fg=self.text_color)
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
                "Constitution": [
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
                with open(self.data_file, 'r') as f:
                    data = json.load(f)

                    # Migration code lets old save files survive renamed attributes. The map says
                    # which old names should become which new names.
                    rename_map = {"Dexterity": "Agility", "Faith": "Charisma", "Vigor": "Constitution"}

                    # The next three blocks apply the rename map to stats, active tasks, and history.
                    # Each block checks that the section exists before touching it.
                    if "stats" in data:
                        for old, new in rename_map.items():
                            if old in data["stats"]:
                                data["stats"][new] = data["stats"].pop(old)

                    if "tasks" in data:
                        for task in data["tasks"]:
                            if task.get("attribute") in rename_map:
                                task["attribute"] = rename_map[task["attribute"]]

                    if "history" in data:
                        for record in data["history"]:
                            if record.get("attribute") in rename_map:
                                record["attribute"] = rename_map[record["attribute"]]

                    if "user_info" in data and data["user_info"].get("name") == "Ashen One":
                         data["user_info"]["name"] = "Hero"

                    # This loop patches missing top-level sections into older or partial save files.
                    # It prevents simple KeyError crashes later in the UI.
                    for key in default_data:
                        if key not in data:
                            data[key] = default_data[key]

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
                            data["subcategories"][attr] = [
                                sub for sub in data["subcategories"][attr]
                                if sub not in retired_subcategories
                            ]

                        for attr, new_subs in default_data["subcategories"].items():
                            if attr not in data["subcategories"]:
                                data["subcategories"][attr] = new_subs
                            else:
                                for sub in new_subs:
                                    if sub not in data["subcategories"][attr]:
                                        data["subcategories"][attr].append(sub)

                    if "user_info" not in data:
                        data["user_info"] = default_data["user_info"]
                    else:
                        data["user_info"].setdefault("theme", self.current_theme_name)

                    return data

            # If the JSON file is damaged or unreadable, the app does not crash. It prints
            # a warning and falls back to a clean default save structure.
            except json.JSONDecodeError:
                print("Error reading data file. Starting fresh.")
                return default_data

        return default_data

    def save_data(self):
        """Writes current data back to the hard drive."""
        # Saving is the reverse of loading: json.dump() converts the in-memory app data
        # into readable text and writes it to disk.
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)

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
        dialog.title("Add New Quest")
        dialog.geometry("350x500")
        dialog.configure(bg=self.bg_dark)
        dialog.transient(self.root)
        dialog.grab_set()

        # The first input chooses which RPG attribute the new quest will reward. A
        # readonly Combobox limits the choice to known attributes.
        ttk.Label(dialog, text="Target Attribute:", font=("{San Francisco}", 11, "bold")).pack(pady=(15, 5))
        attr_var = tk.StringVar(value=self.attributes[0])
        attr_dropdown = ttk.Combobox(dialog, textvariable=attr_var, values=self.attributes, state="readonly", font=("{San Francisco}", 11))
        attr_dropdown.pack(padx=20, fill=tk.X)

        # The activity name is free text, but the listbox below will suggest previous
        # or default subcategories as the user types.
        ttk.Label(dialog, text="Activity / Quest Name:", font=("{San Francisco}", 11, "bold")).pack(pady=(15, 5))
        activity_var = tk.StringVar()
        activity_entry = ttk.Entry(dialog, textvariable=activity_var, font=("{San Francisco}", 11))
        activity_entry.pack(padx=20, fill=tk.X)

        listbox_frame = ttk.Frame(dialog, height=100)
        listbox_frame.pack_propagate(False)
        listbox_frame.pack(padx=20, pady=5, fill=tk.X)

        suggestion_list = tk.Listbox(listbox_frame, font=("{San Francisco}", 11), bg=self.bg_light, fg=self.text_color, selectbackground=self.accent_green, bd=0, highlightthickness=0)

        # Nested helper functions are useful when logic belongs only inside one dialog.
        # This one rebuilds autocomplete suggestions whenever the text changes.
        def update_suggestions(*args):
            typed = activity_var.get().lower()

            all_subs = []
            for subs in self.data["subcategories"].values():
                for sub in subs:
                    if sub not in all_subs:
                        all_subs.append(sub)
            all_subs.sort()

            suggestion_list.delete(0, tk.END)

            # An exact match hides suggestions and auto-selects the matching attribute.
            # Partial matches stay visible so the user can click one.
            exact_matches = [sub for sub in all_subs if sub.lower() == typed]
            if exact_matches:
                suggestion_list.pack_forget()

                for attr, subs in self.data["subcategories"].items():
                    if exact_matches[0] in subs and attr_var.get() != attr:
                        attr_var.set(attr)
                        break
                return

            hits = all_subs if not typed else [sub for sub in all_subs if typed in sub.lower()]

            if hits:
                suggestion_list.pack(fill=tk.BOTH, expand=True)
                for hit in hits:
                    suggestion_list.insert(tk.END, hit)
            else:
                suggestion_list.pack_forget()

        # When the user clicks a suggestion, this handler copies the text into the entry
        # and switches the attribute dropdown to the suggestion's saved category.
        def on_suggestion_select(event):
            if suggestion_list.curselection():
                index = suggestion_list.curselection()[0]
                selected_text = suggestion_list.get(index)

                for attr, subs in self.data["subcategories"].items():
                    if selected_text in subs:
                        attr_var.set(attr)
                        break

                activity_var.set(selected_text)

        # trace_add connects variable changes to code. bind connects listbox selection
        # events to code. Together they make the autocomplete interactive.
        activity_var.trace_add("write", update_suggestions)
        suggestion_list.bind("<<ListboxSelect>>", on_suggestion_select)
        update_suggestions()

        tk.Frame(dialog, bg=self.text_color, height=1).pack(fill=tk.X, padx=20, pady=(20, 15))

        slider_frame = ttk.Frame(dialog)
        slider_frame.pack(fill=tk.X, padx=20)

        # The difficulty slider stores a simple 1-10 value. The app multiplies it by 10
        # to turn difficulty into an XP reward.
        xp_slider = tk.Scale(slider_frame, from_=1, to=10, orient=tk.HORIZONTAL, showvalue=0, bg=self.bg_dark, highlightthickness=0)
        xp_slider.set(2)
        xp_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        val_label = ttk.Label(slider_frame, text="Difficulty: 2  (Yields 20 XP)", font=("{San Francisco}", 11))
        val_label.pack(side=tk.RIGHT)

        # This helper updates the difficulty label and color as the slider moves. The
        # RGB math blends from light to the accent green.
        def update_slider_visuals(val):
            v = int(float(val))
            val_label.config(text=f"Difficulty: {v}  (Yields {v * 10} XP)")

            ratio = (v - 1) / 9.0

            r = int(255 + (163 - 255) * ratio)
            g = int(255 + (190 - 255) * ratio)
            b = int(255 + (140 - 255) * ratio)
            color_hex = f'#{r:02x}{g:02x}{b:02x}'

            xp_slider.config(troughcolor=color_hex)

        xp_slider.config(command=update_slider_visuals)
        update_slider_visuals(2)

        # The save helper validates the dialog, remembers new activity names for future
        # autocomplete, appends the task, saves data, refreshes the table, and closes.
        def save():
            activity_name = activity_var.get().strip()
            attr = attr_var.get()
            xp = xp_slider.get() * 10

            if not activity_name:
                messagebox.showerror("Hold up, Hero!", "Your quest needs an activity name.", parent=dialog)
                return

            if activity_name not in self.data["subcategories"][attr]:
                self.data["subcategories"][attr].append(activity_name)

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
            dialog.destroy()

            cx, cy = self.get_center()
            self.play_floating_text("✨ QUEST ADDED", self.accent_green, cx, cy)

        ttk.Button(dialog, text="Accept Quest", command=save).pack(pady=20)

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
        if new_name is None: return

        try:
             new_xp_str = simpledialog.askstring("Edit Quest", "New XP Reward:", initialvalue=str(task["xp"]))
             if new_xp_str is None: return
             new_xp = int(new_xp_str)
        except ValueError:
             messagebox.showerror("Error", "XP must be a numeric value.")
             return

        if new_name.strip():
            self.data["tasks"][index]["name"] = new_name
            self.data["tasks"][index]["subcategory"] = new_name
            self.data["tasks"][index]["xp"] = new_xp
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

        self.gain_xp(attr, xp_gain)

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

        cx, cy = self.get_center()
        self.play_floating_text(f"+{xp_gain} XP!", "#EBCB8B", cx, cy, size=24)
        self.play_particles("#EBCB8B", cx, cy, count=25, gravity=True)

        self.save_data()
        self.refresh_task_list()
        self.update_stats_display()

    def get_xp_needed(self, level):
        """Returns the XP required to pass the given level. Increases by 25% each level."""
        # Attribute XP requirements grow by 25 percent per level. int() rounds the
        # calculated requirement down to a whole number.
        return int(100 * (1.25 ** (level - 1)))

    def gain_xp(self, attribute, amount):
        """Calculates new XP and triggers Level Ups if necessary."""
        # XP is added to one attribute. The while loop handles large rewards that might
        # cross more than one level boundary at once.
        stat = self.data["stats"][attribute]
        stat["xp"] += amount

        while stat["xp"] >= self.get_xp_needed(stat["level"]):
            stat["xp"] -= self.get_xp_needed(stat["level"])
            stat["level"] += 1

            # Each level-up checks whether a milestone trophy was reached, then plays visual
            # feedback so progression feels immediate.
            self.check_trophies(attribute, stat["level"])

            cx, cy = self.get_center()
            self.play_floating_text(f"🌟 {attribute} LEVEL UP (LVL {stat['level']})! 🌟", "#B48EAD", cx, cy - 50, size=24)
            self.play_particles("#B48EAD", cx, cy - 50, count=60, gravity=False, rainbow=True)

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

            cx, cy = self.get_center()
            self.play_floating_text(f"🏆 {trophy_name.upper()} EARNED! 🏆", "#EBCB8B", cx, cy + 50, size=20)

    def draw_trophy(self, canvas, progress, color, shape_grid, is_gold=False, is_shiny=False):
        """Draws an 8-bit shape, filling it from bottom to top based on progress."""
        # Trophy drawing starts clean, measures the canvas, then converts the pixel-art
        # grid into rectangles sized to fit that canvas.
        canvas.delete("all")

        c_width = int(canvas['width'])
        c_height = int(canvas['height'])

        rows = len(shape_grid)
        cols = len(shape_grid[0])

        pixel_size = (c_width - 10) // max(rows, cols)
        if pixel_size < 1: pixel_size = 1

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

    def update_stats_display(self):
        """Updates the text labels, progress bars, and visual trophies on the Character tab."""

        # Stats display refreshes both numbers and artwork. If new trophy tiers are now
        # needed, the trophy room is rebuilt before drawing progress.
        current_tiers = self.get_tiers()
        if len(current_tiers) * len(self.attributes) != len(self.trophy_canvases):
            self.rebuild_trophy_room()

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

        self.update_header()

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
            record_date = datetime.fromisoformat(record["date"])

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
        self.root.update_idletasks()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
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

    def play_floating_text(self, text, color, x, y, size=18):
        """Creates retro text that pops, floats upwards, and fades out."""
        # Floating feedback is shown in a tiny borderless Toplevel window. Toplevel
        # supports transparency, so the popup can feel lighter than a normal widget.
        root_w = self.root.winfo_width() if self.root.winfo_width() > 1 else 850
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.configure(bg=self.bg_light)
        try:
            popup.attributes("-alpha", 0.86)
        except tk.TclError:
            pass

        display_size = max(11, size - 6)
        box = tk.Frame(
            popup,
            bg=self.bg_light,
            bd=0,
            relief=tk.FLAT,
            highlightthickness=0,
            highlightbackground=color
        )
        box.pack()

        lbl = tk.Label(
            box,
            text=text,
            font=("Courier", display_size, "bold"),
            fg=color,
            bg=self.bg_light,
            wraplength=max(140, root_w - 120),
            justify=tk.CENTER,
            padx=12,
            pady=8,
            bd=0,
            relief=tk.FLAT,
            highlightthickness=0
        )
        lbl.pack()

        popup.update_idletasks()
        popup_w = popup.winfo_reqwidth()
        popup_h = popup.winfo_reqheight()
        safe_x, safe_y = self.clamp_box_position(popup_w, popup_h, x, y)
        popup.geometry(f"+{self.root.winfo_rootx() + safe_x - popup_w // 2}+{self.root.winfo_rooty() + safe_y - popup_h // 2}")

        # Color fading works by converting hex colors to RGB numbers, blending each
        # channel, then converting the result back to a hex color.
        def blend_color(c1, c2, ratio):
            """Mathematically blends two hex colors together for fade effects."""
            c1, c2 = c1.lstrip('#'), c2.lstrip('#')
            r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
            r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)

            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            return f"#{r:02x}{g:02x}{b:02x}"

        # Tkinter animations usually use after(): do one tiny update, then schedule the
        # next update a few milliseconds later.
        def animate(step=0, current_size=display_size, current_y=safe_y):
            total_steps = 70

            if step < total_steps:
                new_size = current_size

                if step < 6:
                    new_size += 1
                    lbl.config(font=("Courier", new_size, "bold"))

                current_y -= 1
                popup.update_idletasks()
                popup_w = popup.winfo_reqwidth()
                popup_h = popup.winfo_reqheight()
                safe_x, safe_current_y = self.clamp_box_position(popup_w, popup_h, x, current_y)
                popup.geometry(f"+{self.root.winfo_rootx() + safe_x - popup_w // 2}+{self.root.winfo_rooty() + safe_current_y - popup_h // 2}")

                if step > total_steps - 20:
                    fade_ratio = (step - (total_steps - 20)) / 20.0
                    faded_color = blend_color(color, self.bg_dark, fade_ratio)
                    lbl.config(fg=faded_color)

                self.root.after(30, animate, step + 1, new_size, current_y)
            else:
                popup.destroy()

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
            particles.append({"widget": p, "dx": dx, "dy": dy, "life": random.randint(20, 40)})

        # The particle animation moves living particles, applies gravity if requested,
        # destroys expired particles, and repeats while anything is still active.
        def animate():
            active = False
            for p in particles:
                if p["life"] > 0:
                    w = p["widget"]
                    curr_x = int(w.place_info().get('x', start_x))
                    curr_y = int(w.place_info().get('y', start_y))

                    root_w = self.root.winfo_width() if self.root.winfo_width() > 1 else 850
                    root_h = self.root.winfo_height() if self.root.winfo_height() > 1 else 700
                    next_x = curr_x + p["dx"]
                    next_y = curr_y + p["dy"]

                    if next_x < 0 or next_x > root_w - 8:
                        p["dx"] = int(p["dx"] * -0.6)
                        next_x = max(0, min(next_x, root_w - 8))

                    if next_y < 0 or next_y > root_h - 8:
                        p["dy"] = int(p["dy"] * -0.6)
                        next_y = max(0, min(next_y, root_h - 8))

                    w.place(x=next_x, y=next_y)
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
