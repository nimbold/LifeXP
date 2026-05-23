# LifeXP Beginner Code Guide

This guide explains the Python ideas used in `main.py` and gives you a map of every method in the app. Read it beside the code. The goal is not to memorize everything at once. The goal is to recognize the patterns when you see them.

## How To Read This Project

Start with these sections in `main.py`:

1. Imports and constants at the top.
2. `LifeXPApp.__init__`, which creates the app's starting state.
3. `setup_header`, `setup_ui`, and the `setup_*_tab` methods, which build the visible app.
4. `load_data` and `save_data`, which explain the JSON save file.
5. `complete_task` and `gain_xp`, which are the main RPG logic.
6. The animation methods near the bottom.

## Python Building Blocks Used In This App

### Imports

Imports bring code from Python or another library into this file.

```python
import json
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
```

In LifeXP:

- `tkinter` draws the desktop window.
- `ttk`, `messagebox`, and `simpledialog` provide nicer widgets and popups.
- `datetime` and `timedelta` filter history into daily, weekly, and monthly reports.
- `json` saves and loads `lifexp_data.json`.
- `math`, `random`, and `time` help with animations.
- `os` finds the save file path.

### Constants

Constants are values near the top of the file that the rest of the app reuses.

```python
BASE_XP_NEEDED = 100
XP_GROWTH_RATE = 1.25
```

In LifeXP, these make XP balancing easier because you change one value instead of hunting through the whole file.

### Class

A class groups data and behavior together.

```python
class LifeXPApp:
    def __init__(self, root):
        self.root = root
```

`LifeXPApp` owns the window, save data, colors, widgets, XP rules, and animation helpers.

### `def` Methods

`def` creates a function. Inside a class, it is usually called a method.

```python
def get_xp_needed(self, level):
    return int(BASE_XP_NEEDED * (XP_GROWTH_RATE ** (level - 1)))
```

`self` means "this app object." It lets one method use data created by another method.

### Variables

Variables store values.

```python
xp_gain = task["xp"]
attr = task["attribute"]
```

In LifeXP, variables often hold the selected quest, XP amount, widget, color, or current level.

### Lists

Lists store ordered items.

```python
self.attributes = ["Strength", "Agility", "Intelligence", "Charisma", "Vitality"]
```

LifeXP uses lists for attributes, active tasks, completion history, trophies, theme names, and pixel-art rows.

### Dictionaries

Dictionaries store named values using keys.

```python
task = {
    "name": "Read Docs",
    "attribute": "Intelligence",
    "xp": 50
}
```

LifeXP uses dictionaries for saved data, themes, stats, task records, history records, and cached lookup tables.

### Nested Dictionaries

A dictionary can contain more dictionaries.

```python
self.data["stats"]["Strength"]["level"]
```

This means: from the saved data, get stats, then Strength, then its level.

### For Loops

A `for` loop repeats work for every item in a collection.

```python
for attr in self.attributes:
    print(attr)
```

In LifeXP, loops build five stat rows, draw every trophy, check every history record, and create particles.

### While Loops

A `while` loop repeats while a condition is true.

```python
while stat["xp"] >= xp_needed:
    stat["xp"] -= xp_needed
    stat["level"] += 1
```

LifeXP uses this in `gain_xp` so one big quest can level up an attribute more than once.

### If, Elif, Else

Conditionals choose between paths.

```python
if timeframe == "daily":
    title = "Daily Report"
elif timeframe == "weekly":
    title = "Weekly Report"
else:
    title = "Monthly Report"
```

LifeXP uses conditionals for validation, theme checks, date filtering, level-up checks, and animation choices.

### Try And Except

`try` runs code that might fail. `except` handles the failure.

```python
try:
    new_xp = int(new_xp_str)
except ValueError:
    messagebox.showerror("Error", "XP must be a numeric value.")
```

LifeXP uses this to avoid crashing when JSON is damaged, a date is invalid, or the user enters bad XP.

### With Open

`with open(...)` safely opens a file and closes it when finished.

```python
with open(self.data_file, "r", encoding="utf-8") as f:
    data = json.load(f)
```

LifeXP uses this to read and write the save file.

### JSON

JSON is a text format for saving dictionaries and lists.

```python
json.dump(self.data, f, indent=4)
data = json.load(f)
```

LifeXP saves progress, tasks, history, trophies, themes, and custom activity names in `lifexp_data.json`.

### List Comprehensions

A list comprehension builds a list in one line.

```python
hits = [sub for sub in all_subs if typed in sub.lower()]
```

LifeXP uses this pattern for filtering suggestions, cleaning save data, and collecting matching records.

### Dictionary Comprehensions

A dictionary comprehension builds a dictionary in one line.

```python
{attr: {"level": 1, "xp": 0} for attr in self.attributes}
```

LifeXP uses this to create default stats for every attribute.

### Generator Expressions

A generator expression is like a compact loop used inside another function.

```python
total_xp = sum(self.get_total_xp_for_stat(stat) for stat in self.data["stats"].values())
```

LifeXP uses these for totals without creating a temporary list.

### Lambda

`lambda` creates a tiny one-line function.

```python
command=lambda: self.show_summary("daily")
```

LifeXP uses lambdas for buttons and delayed animation callbacks.

### Events And Callbacks

Tkinter waits for events, then calls your function.

```python
button = ttk.Button(parent, text="Complete Quest", command=self.complete_task)
```

Clicking the button calls `complete_task`.

### Tkinter Widgets

Widgets are visible UI objects.

```python
frame = tk.Frame(self.root)
label = tk.Label(frame, text="LifeXP")
button = ttk.Button(frame, text="Accept Quest")
```

LifeXP uses frames, labels, buttons, notebooks, tree tables, scrollbars, text boxes, canvases, and popup windows.

### Pack, Grid, And Place

Tkinter has layout systems:

```python
label.pack()
label.grid(row=0, column=0)
particle.place(x=100, y=200)
```

LifeXP uses:

- `pack` for stacking big UI areas.
- `grid` for rows and columns.
- `place` for animation particles at exact coordinates.

### Canvas Drawing

A canvas lets you draw shapes.

```python
canvas.create_oval(4, 4, 52, 52)
canvas.create_rectangle(10, 10, 20, 20)
```

LifeXP uses canvases for avatar rings, pixel icons, difficulty slider, trophies, and simple effects.

### String Formatting

F-strings insert values into text.

```python
f"Lvl {level} ({xp} / {xp_needed} XP)"
```

LifeXP uses this for labels, report titles, reward popups, and saved display values.

### Return Values

`return` sends a result back to the caller.

```python
return trophy_name
```

LifeXP methods return colors, levels, popup positions, rank events, trophy names, and calculated XP values.

### Caches

A cache stores a result so the app does not recalculate it every time.

```python
if level not in self.xp_needed_cache:
    self.xp_needed_cache[level] = ...
```

LifeXP caches XP requirements, total XP before levels, autocomplete suggestions, and trophy tiers.

## Important Data Shapes

### The Main Save Data

`self.data` is the app's memory.

```python
self.data = {
    "user_info": {},
    "stats": {},
    "tasks": [],
    "history": [],
    "trophies": [],
    "subcategories": {}
}
```

### A Stat

```python
{"level": 3, "xp": 42}
```

This means the attribute is level 3 and has 42 XP toward level 4.

### A Task

```python
{
    "name": "Coding",
    "attribute": "Intelligence",
    "subcategory": "Coding",
    "xp": 50
}
```

This is an active quest waiting to be completed.

### A History Record

```python
{
    "name": "Coding",
    "attribute": "Intelligence",
    "subcategory": "Coding",
    "xp": 50,
    "date": "2026-05-23T14:30:00"
}
```

This is a completed quest used by Chronicles reports.

### A Theme

```python
"Nord RPG": {
    "bg_dark": "#2E3440",
    "bg_light": "#3B4252",
    "accent": "#A3BE8C",
    "text": "#ECEFF4",
    "attr_colors": {"Strength": "#BF616A"}
}
```

Themes are dictionaries of color tokens.

## Method Map

This section lists every method in `LifeXPApp` and explains what it does.

### Startup

| Method | What it does |
| --- | --- |
| `__init__(self, root)` | Starts the app object, stores the root window, creates app state, loads data, applies the theme, builds the UI, and refreshes the first display. |

### UI Setup, Painting, And Styling

| Method | What it does |
| --- | --- |
| `get_theme_definitions` | Returns all available themes as a large dictionary. |
| `apply_modern_theme` | Configures Tkinter and ttk colors, fonts, buttons, tabs, tables, and progress bars. |
| `fit_window_to_content` | Measures a popup window and sizes it so its content fits on screen. |
| `show_fitted_window` | Fits a hidden popup window, then shows it with animation. |
| `animate_window_open` | Makes a popup fade and slide into place. |
| `recolor_widget_tree` | Walks through child widgets and swaps old theme colors for new theme colors. |
| `setup_header` | Builds the top header with Settings, app title, username/rank, and avatar canvas. |
| `get_title_info` | Converts total account level into a title like `Novice I` and a color. |
| `get_title_shape` | Returns the small pixel-art shape for the current account title tier. |
| `update_avatar` | Draws the account title icon and circular progress ring. |
| `update_header` | Calculates total account XP, updates rank labels, updates the avatar, and detects rank-ups. |
| `setup_ui` | Creates the tab notebook and calls each tab setup method. |
| `create_pixel_icon` | Turns string-based pixel art into a `PhotoImage`. |
| `build_tab_icons` | Builds the pixel icons for Quest Log, Character Info, and Chronicles tabs. |
| `create_level_up_arrow_icon` | Builds a pixel arrow icon used by level-up and rank-up popups. |
| `setup_tasks_tab` | Builds the Quest Log table and action buttons. |
| `get_tiers` | Returns trophy milestone tiers, expanding the list after higher levels. |
| `rebuild_trophy_room` | Clears and rebuilds the trophy grid. |
| `setup_character_tab` | Builds attribute progress bars and the visual trophy room. |
| `setup_summary_tab` | Builds the Chronicles report buttons and activity cards. |
| `open_settings_page` | Opens the Settings popup for themes, reset, and About info. |
| `set_theme` | Applies a selected theme, saves it, and recolors existing widgets. |
| `reset_progress` | Confirms and clears stats, tasks, history, trophies, and caches. |
| `refresh_theme_widgets` | Refreshes older theme-dependent widgets after theme changes. |

### Data Management

| Method | What it does |
| --- | --- |
| `_calculate_max_level` | Finds the highest attribute level in the save data. |
| `_invalidate_subcategory_cache` | Clears cached autocomplete data after activity names change. |
| `_invalidate_tier_cache` | Clears cached trophy tier data after level thresholds change. |
| `load_data` | Loads `lifexp_data.json`, creates defaults, migrates older saves, and normalizes data. |
| `normalize_stats` | Makes sure every attribute has a valid level and XP value. |
| `normalize_tasks` | Drops malformed active quests and returns clean task dictionaries. |
| `normalize_history` | Drops malformed completion records and returns clean history dictionaries. |
| `save_data` | Writes the current app data to `lifexp_data.json` through a temporary file. |

### Game Logic And User Actions

| Method | What it does |
| --- | --- |
| `refresh_task_list` | Clears and redraws the active quest table from saved tasks. |
| `add_task_dialog` | Opens the custom Accept Quest dialog, including attribute chips, autocomplete, difficulty slider, and save behavior. |
| `edit_task_dialog` | Lets the selected quest name and XP be changed. |
| `delete_task` | Removes the selected quest without awarding XP. |
| `complete_task` | Completes the selected quest, grants XP, records history, saves, refreshes UI, and starts reward animations. |
| `get_xp_needed` | Calculates how much XP is needed to pass a specific attribute level. |
| `get_total_xp_before_level` | Calculates lifetime XP needed to reach a level. |
| `get_total_xp_for_stat` | Calculates lifetime XP for one attribute, including previous levels. |
| `get_all_subcategories` | Returns every known activity name once for autocomplete. |
| `get_subcategory_owner_map` | Maps each activity name to the first attribute that owns it. |
| `gain_xp` | Adds XP to an attribute, handles level-ups, checks trophies, and returns level-up events. |
| `check_trophies` | Awards a trophy if a new level exactly matches a trophy milestone. |
| `draw_trophy` | Draws one trophy icon and fills it based on progress toward the milestone. |
| `update_stats_display` | Updates stat labels, progress bars, trophy icons, and account header. |
| `show_summary` | Filters completion history by timeframe and fills the Chronicles cards. |

### Animation And Visual Feedback

| Method | What it does |
| --- | --- |
| `get_center` | Returns the center point of the app window for popups and effects. |
| `clamp_widget_position` | Keeps a widget inside the visible window. |
| `clamp_box_position` | Keeps a popup box inside the visible window using explicit width and height. |
| `ease_out_cubic` | Calculates a motion curve that starts fast and slows near the end. |
| `ease_smoothstep` | Calculates a smooth opacity or fade curve. |
| `_blend_color` | Blends two hex colors together. |
| `set_popup_alpha` | Sets popup transparency when the operating system supports it. |
| `raise_popup_window` | Keeps reward popup windows above the main app. |
| `popup_duration_ms` | Converts animation steps into milliseconds. |
| `popup_overlap_start_ms` | Calculates when the next reward popup should start. |
| `schedule_level_up_sequence` | Schedules XP, level-up, trophy, and rank-up popups in order. |
| `play_level_up_animation` | Shows the attribute level-up popup and firework burst. |
| `play_rank_up_animation` | Shows the account rank-up popup and larger firework burst. |
| `play_trophy_animation` | Shows the trophy-earned popup and particles. |
| `play_floating_text` | Creates a borderless popup that floats upward, pops in size, and fades out. |
| `play_firework_particles` | Creates a radial burst of colored square particles from a popup box. |
| `play_particles` | Creates simpler square particles from one point. |

## Walkthrough: Completing A Quest

Here is the main flow when you select a quest and click `Complete Quest`:

1. `complete_task` checks which row is selected in the quest table.
2. It removes that task from `self.data["tasks"]`.
3. It reads the task's attribute and XP reward.
4. It calls `gain_xp(attr, xp_gain)`.
5. `gain_xp` adds XP and may increase the attribute level.
6. `check_trophies` may add a trophy if a level milestone was reached.
7. `complete_task` appends a record to `self.data["history"]`.
8. `save_data` writes the updated data to `lifexp_data.json`.
9. `refresh_task_list` redraws the table.
10. `update_stats_display` updates progress bars, trophies, and rank info.
11. Animation methods show XP, level-up, rank-up, and trophy feedback.

## Walkthrough: Adding A Quest

The `add_task_dialog` method is long because it builds a complete custom popup.

Important pieces:

- `tk.Toplevel` creates the popup window.
- `StringVar` and `IntVar` store live form values.
- Attribute chips are clickable `Label` widgets.
- The activity entry uses autocomplete suggestions from `self.data["subcategories"]`.
- The difficulty slider is drawn manually on a `Canvas`.
- The nested `save` function validates the form, appends a task, saves data, refreshes the table, and closes the popup.

Small simplified version:

```python
def save():
    activity_name = activity_var.get().strip()
    attr = attr_var.get()
    xp = difficulty_var.get() * 10

    self.data["tasks"].append({
        "name": activity_name,
        "attribute": attr,
        "subcategory": activity_name,
        "xp": xp
    })

    self.save_data()
    self.refresh_task_list()
```

## Walkthrough: Saving And Loading

LifeXP saves data in one JSON file.

Loading:

```python
with open(self.data_file, "r", encoding="utf-8") as f:
    data = json.load(f)
```

Saving:

```python
with open(temp_file, "w", encoding="utf-8") as f:
    json.dump(self.data, f, indent=4)
os.replace(temp_file, self.data_file)
```

The app writes to a temporary file first, then replaces the real save file. That is safer than writing directly to the save file.

## Walkthrough: Themes

Themes are dictionaries of color names.

```python
theme = self.themes[self.current_theme_name]
self.bg_dark = theme["bg_dark"]
self.bg_light = theme["bg_light"]
self.accent_green = theme["accent"]
```

`apply_modern_theme` applies those colors to ttk styles. `recolor_widget_tree` updates normal Tkinter widgets that do not automatically follow ttk styles.

## Walkthrough: Pixel Art

Pixel art is stored as strings.

```python
pattern = [
    "....Y....",
    "...YYY...",
    "..YYYYY.."
]
```

The drawing code loops through every row and column. If a character is not `.`, it draws a colored square.

```python
for y, row in enumerate(pattern):
    for x, cell in enumerate(row):
        if cell != ".":
            image.put(color, to=(x * pixel_size, y * pixel_size, ...))
```

The same idea appears in tab icons, level-up icons, avatar icons, and trophies.

## Walkthrough: Animations

Tkinter animations use repeated `after` calls.

```python
def animate(step=0):
    # move or recolor something
    self.root.after(16, animate, step + 1)
```

LifeXP uses this pattern for:

- Floating XP text.
- Fade-in and fade-out popup windows.
- Level-up and rank-up effects.
- Square particle movement.
- Firework bursts.

## Good Beginner Experiments

Try these small changes one at a time:

1. Change `BASE_XP_NEEDED` from `100` to `50` and see leveling become faster.
2. Add a new default activity under one attribute in `load_data`.
3. Add a new theme to `get_theme_definitions`.
4. Change a tab icon pattern in `build_tab_icons`.
5. Change trophy milestone levels in `get_tiers`.
6. Change the text shown by `play_floating_text` when a quest is completed.
7. Add a new report button that calls `show_summary` with a new timeframe.

## Debugging Tips

- If the app will not start, run `python3 main.py` from Terminal so you can see the error.
- If the save file seems broken, inspect `lifexp_data.json`.
- If a widget is invisible, check its `bg` and `fg` colors.
- If a button does nothing, check its `command=...`.
- If a popup appears in the wrong place, check `get_center`, `clamp_box_position`, or the `x, y` values passed to the animation.
- If autocomplete is stale, check `_invalidate_subcategory_cache`.

## Glossary

- Attribute: One RPG stat, such as Strength or Intelligence.
- Quest: An active task waiting to be completed.
- XP: Experience points gained from completed quests.
- Level: Progress stage for one attribute.
- Account rank: Total level calculated from all attribute lifetime XP.
- Trophy: Pixel-art milestone reward for an attribute level.
- Chronicles: The report screen for daily, weekly, and monthly history.
- Widget: A visible Tkinter UI object.
- Callback: A function that runs after a click, key press, timer, or other event.
- Cache: Stored calculated data reused later for speed.
