# LifeXP Beginner Guide

This guide explains the parts of `main.py` that matter most when you are learning the project.

You do not need to understand every method at once. Focus on how data moves through the app.

## First Reading Path

Read `main.py` in this order:

1. Constants at the top: app version, XP numbers, animation timing.
2. `__init__`: creates the app object, loads data, builds the UI.
3. `setup_header`, `setup_ui`, `setup_tasks_tab`, `setup_character_tab`, `setup_summary_tab`: builds the screens.
4. `load_data` and `save_data`: handles the JSON save file.
5. `complete_task`, `gain_xp`, `get_xp_needed`: main RPG logic.
6. `update_stats_display` and `update_header`: refreshes labels, bars, trophies, and account rank.
7. `add_task_dialog`: creates quests, activity suggestions, and the quest queue.

## The Big Idea

LifeXP is one class:

```python
class LifeXPApp:
    def __init__(self, root):
        self.root = root
```

`self` means "this app." It lets methods share the same window, data, colors, widgets, and caches.

For example:

```python
self.data
self.attributes
self.stat_labels
self.trophy_canvases
```

These are available to all methods in the class.

## The Most Important Data

The app saves almost everything in `self.data`.

Simple shape:

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

### Stats

Each attribute stores a level and XP inside the current level:

```python
"Strength": {
    "level": 7,
    "xp": 75
}
```

This means Strength is level 7 and has 75 XP toward level 8.

### Tasks

Active quests live in `self.data["tasks"]`.

```python
{
    "name": "Coding",
    "attribute": "Intelligence",
    "subcategory": "Coding",
    "xp": 50
}
```

### History

Completed quests move into `self.data["history"]`.

```python
{
    "name": "Coding",
    "attribute": "Intelligence",
    "subcategory": "Coding",
    "xp": 50,
    "date": "2026-05-24T10:30:00"
}
```

Chronicles reads this list to build reports.

### Subcategories

Saved activity suggestions live in `self.data["subcategories"]`.

```python
"Intelligence": ["Reading", "Coding", "Research"]
```

The app cleans old suggestions in `normalize_subcategories`. It removes noisy entries, merges close duplicates, and adds the current default activity list.

## How A Quest Gets Completed

This is the most important flow in the app:

1. You select one or more quests in the table.
2. `complete_task` reads the selected quests.
3. Each quest gives XP to its matching attribute.
4. Completed quests are removed from `self.data["tasks"]`.
5. History records are added to `self.data["history"]`.
6. If enough XP exists, attributes level up.
7. `check_trophies` awards milestone trophies.
8. `save_data` writes the JSON file.
9. `refresh_task_list` redraws the quest table.
10. `update_stats_display` refreshes bars, trophies, and rank.
11. Reward animations play.

If you understand this flow, you understand the heart of LifeXP.

## Accepting Quests

`add_task_dialog` builds the Accept Quest window.

Important pieces:

```python
attr_var
activity_var
difficulty_var
pending_quests
```

What they mean:

- `attr_var`: selected activity filter or attribute.
- `activity_var`: text typed by the user.
- `difficulty_var`: 1 to 10 difficulty.
- `pending_quests`: quests waiting to be accepted.

The `All` filter shows every activity alphabetically. Attribute filters show only their own activities. If the user types a brand-new activity while `All` is selected, the app asks which attribute it belongs to.

The active quest table also supports multi-select. Complete and abandon work on all selected quests. Edit opens a batch editor when more than one quest is selected.

## XP Scaling

There are two kinds of levels:

- Attribute level: Strength, Agility, Intelligence, Charisma, Vitality.
- Account level: total character rank calculated from all lifetime attribute XP.

Both use:

```python
get_scaled_xp_needed(level, base_xp)
```

Attributes use:

```python
BASE_XP_NEEDED = 100
```

Account level uses:

```python
ACCOUNT_BASE_XP_NEEDED = 500
```

The curve is inspired by Elden Ring's level-cost formula. It starts gently and gets harder over time without becoming as extreme as the old fixed 25 percent exponential growth.

Useful methods:

```python
get_xp_needed(level)
get_total_xp_before_level(level)
get_total_xp_for_stat(stat)
get_account_xp_needed(level)
get_account_level_progress(total_xp)
```

## Tkinter Basics Used Here

### Widgets

Widgets are UI objects:

```python
tk.Frame(...)
tk.Label(...)
ttk.Button(...)
ttk.Progressbar(...)
tk.Canvas(...)
```

### Layout

LifeXP uses three layout styles:

```python
widget.pack()
widget.grid(row=0, column=0)
widget.place(x=100, y=200)
```

- `pack`: stack big sections.
- `grid`: rows and columns.
- `place`: exact positions, mostly for animations.

### Callbacks

A callback is a function that runs later, usually after a click.

```python
ttk.Button(parent, text="Complete", command=self.complete_task)
```

Clicking the button calls `complete_task`.

## Saving And Loading

LifeXP saves to `lifexp_data.json`.

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

The app writes to a temporary file first, then replaces the real save file. This reduces the chance of corrupting the save if something fails while writing.

## Drawing Trophies

Trophies are drawn on a `Canvas`.

The important methods are:

```python
rebuild_trophy_room()
draw_trophy(...)
draw_attribute_symbol(...)
_trophy_material(...)
```

What they do:

- `rebuild_trophy_room`: creates the trophy grid.
- `draw_trophy`: draws the cup, handles, base, medallion, and tier upgrades.
- `draw_attribute_symbol`: draws the attribute symbol inside the medallion.
- `_trophy_material`: chooses bronze, silver, gold, platinum, or crystal-like colors.
- `resize_trophy_canvases`: resizes trophies when the window changes.

Trophy tiers:

```text
Level 5    Apprentice
Level 10   Adept
Level 25   Master
Level 50   Grandmaster
Level 100  Legend
```

The app starts by showing levels 5, 10, and 25. After an attribute passes level 25, it also shows levels 50 and 100. Locked trophies are greyed out. Earned trophies use color and shine.

## Themes

Themes are dictionaries of colors.

```python
"Tokyo Night": {
    "bg_dark": "#1A1B26",
    "bg_light": "#24283B",
    "accent": "#7AA2F7",
    "text": "#C0CAF5",
    "attr_colors": {...}
}
```

Main theme methods:

```python
get_theme_definitions()
apply_modern_theme()
set_theme()
refresh_theme_widgets()
```

If you add a new theme, copy an existing theme block and change the colors.

## Animations

Tkinter animations use `after`.

```python
def animate(step=0):
    # change position, color, or opacity
    self.root.after(16, animate, step + 1)
```

LifeXP uses this for:

- XP popups
- Level-up messages
- Header rank-up glow
- Trophy messages
- Firework particles
- Button feedback

The core idea is simple: draw something, wait a few milliseconds, update it, repeat.

Rank-up animation now happens in the header. The avatar ring fills orange, the title glows, and the account level text counts upward.

## Safe Beginner Edits

Try these one at a time:

1. Change `BASE_XP_NEEDED` to make attributes faster or slower.
2. Change `ACCOUNT_BASE_XP_NEEDED` to rebalance total rank speed.
3. Add a default activity inside `load_data`.
4. Add a new color theme in `get_theme_definitions`.
5. Change trophy milestone levels in `get_tiers`.
6. Change popup text in `play_level_up_animation`.
7. Change the report text in `show_summary`.
8. Change tab icons in `build_tab_icons`.

After each edit, run:

```bash
python3 -m py_compile main.py
python3 main.py
```

## Debugging Checklist

If something breaks:

- Read the Terminal error from top to bottom.
- Look for the file name and line number.
- Check missing commas or brackets first.
- If a button does nothing, check its `command=...`.
- If data looks wrong, inspect `lifexp_data.json`.
- If a widget is invisible, check `bg` and `fg` colors.
- If XP feels wrong, print values from `get_xp_needed` or `get_account_xp_needed`.

## Small Glossary

- Attribute: One stat, such as Strength or Intelligence.
- Quest: An active task.
- XP: Experience points from completed quests.
- Level: Progress stage for an attribute or account.
- Trophy: Visual reward for an attribute milestone.
- Chronicles: History reports.
- Widget: A visible Tkinter object.
- Callback: A function that runs after a click, timer, or event.
- Cache: Stored calculation reused later.
