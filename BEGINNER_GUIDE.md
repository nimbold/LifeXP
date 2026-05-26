# LifeXP Beginner Guide

This guide explains `main.py` for a new programmer. It is written to help you read the code, understand the app, and safely make small changes.

You do not need to memorize everything. Read the "First Reading Path" first, then use the method map when you want to understand a specific part of the file.

## First Reading Path

Read `main.py` in this order:

1. Constants at the top: app version, XP numbers, animation timing.
2. `__init__`: creates the app object, loads data, builds the UI.
3. `get_theme_definitions` and `apply_modern_theme`: define and apply the colors.
4. `setup_header`, `setup_ui`, `setup_tasks_tab`, `setup_character_tab`, `setup_summary_tab`, `setup_settings_tab`: build the screens.
5. `load_data` and `save_data`: read and write the local JSON save file.
6. `add_task_dialog`, `complete_task`, `gain_xp`, `get_xp_needed`: main quest and XP logic.
7. `update_stats_display`, `update_header`, `show_summary`: refresh the visible app.
8. Animation methods near the bottom: popups, particles, trophy messages, and rank-up feedback.

## The Big Idea

LifeXP is one class:

```python
class LifeXPApp:
    def __init__(self, root):
        self.root = root
```

A class groups data and behavior together. In this app, the class stores the window, the saved data, the widgets, colors, animations, and helper methods.

`self` means "this app object." If one method writes `self.data`, another method can read it later.

Examples:

```python
self.data
self.attributes
self.current_theme_name
self.task_tree
self.trophy_canvases
```

These values are called attributes of the object. They are not the same as LifeXP's RPG attributes like Strength or Intelligence.

## The Main Data Shape

The app saves most user progress in `self.data`.

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

### User Info

`user_info` stores preferences and account-level display data.

Examples:

```python
"theme": "Tokyo Night"
"font_size": 11
"animations_enabled": True
```

### Stats

Each RPG attribute stores a level and XP inside the current level:

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

## Python Concepts Used In This App

### Variables

A variable stores a value.

```python
total_xp = 120
theme_name = "OLED Black"
```

The app uses variables for XP numbers, colors, widget references, and temporary calculations.

### Lists

A list stores ordered items.

```python
self.attributes = ["Strength", "Agility", "Intelligence", "Charisma", "Vitality"]
```

Lists are useful when you want to loop through many items.

### Dictionaries

A dictionary stores named values.

```python
theme = {
    "bg_dark": "#1A1B26",
    "bg_light": "#24283B",
    "accent": "#7AA2F7"
}
```

LifeXP uses dictionaries for themes, stats, tasks, history records, and button palettes.

### For Loops

A `for` loop repeats code for every item in a list or dictionary.

Example from the app:

```python
for attr, color in self.attr_colors.items():
    self.style.configure(
        f"{attr}.Horizontal.TProgressbar",
        background=color
    )
```

Plain English:

1. Look at each attribute color.
2. Get the attribute name and its color.
3. Create a progress-bar style for that attribute.

Another example:

```python
for style_name, background in action_button_styles.items():
    foreground = self.get_action_text_color(background)
    self.style.configure(style_name, background=background, foreground=foreground)
```

Plain English:

1. Look at each button style.
2. Pick readable text for that button's background.
3. Apply the style.

### If Statements

An `if` statement chooses between paths.

```python
if theme_name not in self.themes:
    return
```

Plain English: if the requested theme does not exist, stop the method before it crashes.

### Functions And Methods

A function is a reusable block of code.

```python
def get_readable_text_color(self, background, preferred=None):
    ...
```

Inside a class, functions are usually called methods. Methods in this app often do one job: calculate XP, draw a trophy, save data, or update one part of the UI.

### Return Values

`return` sends a result back to whoever called the method.

```python
return self.get_readable_text_color(background, "#0F172A")
```

Here the method calculates a readable text color and gives it back.

### Callbacks

A callback is a function that runs later, often after a click.

```python
ttk.Button(parent, text="Complete", command=self.complete_task)
```

Clicking the button calls `complete_task`.

### Nested Functions

Some methods define smaller functions inside them.

Example from `add_task_dialog`:

```python
def refresh_selected_list():
    selected_list.delete(0, tk.END)
```

This helper only matters inside the Accept Quest window, so it lives inside `add_task_dialog`.

### Caches

A cache stores a calculated result so the app does not repeat the same work.

```python
self.xp_needed_cache[level] = value
```

The XP methods use caches because the same level calculations happen many times.

### Algorithms

An algorithm is a step-by-step process. LifeXP has small algorithms, not one giant one.

Examples:

- Calculate XP needed for a level.
- Convert total XP into account level progress.
- Pick readable text for a color.
- Resize trophy art based on the window.
- Group history records into daily, weekly, or monthly reports.

## Tkinter Concepts Used Here

### Widgets

Widgets are visible UI objects.

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

- `pack`: stack large sections.
- `grid`: arrange rows and columns.
- `place`: exact positions, mostly for animations.

### ttk Styles

`ttk` widgets use named styles.

```python
self.style.configure("QuestAccept.TButton", background=background)
```

This lets the app recolor many buttons by changing one style.

### Canvas Drawing

`tk.Canvas` draws shapes, text, icons, trophies, and particles.

```python
canvas.create_oval(...)
canvas.create_line(...)
canvas.create_text(...)
```

The app draws its own trophies and tab icons instead of loading image files.

## How A Quest Gets Completed

This is the most important flow in the app:

1. You select one or more quests in the table.
2. `complete_task` reads the selected rows.
3. Each quest gives XP to its matching attribute.
4. Completed quests are removed from `self.data["tasks"]`.
5. History records are added to `self.data["history"]`.
6. `gain_xp` adds XP and handles level-ups.
7. `check_trophies` awards milestone trophies.
8. `save_data` writes the JSON file.
9. `refresh_task_list` redraws the quest table.
10. `update_stats_display` refreshes bars, trophies, and account rank.
11. Reward animations play.

If you understand this flow, you understand the heart of LifeXP.

## Accepting Quests

`add_task_dialog` builds the Accept Quest window.

Important values:

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

The active quest table supports multi-select. Complete and abandon work on all selected quests. Edit opens a batch editor when more than one quest is selected.

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

The curve is inspired by Elden Ring's level-cost formula. It starts gently and gets harder over time without becoming as extreme as a simple fixed 25 percent exponential growth.

Useful methods:

```python
get_xp_needed(level)
get_total_xp_before_level(level)
get_total_xp_for_stat(stat)
get_account_xp_needed(level)
get_account_level_progress(total_xp)
```

## Themes And Readability

Themes are dictionaries of colors.

```python
"Tokyo Night": {
    "bg_dark": "#1A1B26",
    "bg_light": "#24283B",
    "accent": "#7AA2F7",
    "text": "#C0CAF5",
    "card_text": "#C0CAF5",
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

The app also checks contrast. Contrast means the difference between text color and background color. If text would be too hard to read, helpers like `get_readable_text_color`, `get_action_text_color`, and `get_attribute_text_color` choose a safer color.

Action buttons use meanings instead of hard-coded colors:

```python
"accept": Intelligence color
"complete": Vitality color
"edit": Agility color
"abandon": Strength color
```

This prevents the Accept and Complete buttons from becoming the same color in themes such as OLED Black.

If you add a new theme, copy an existing theme block and change the colors. Make sure `bg_dark`, `bg_light`, `accent`, `text`, `card_text`, and all five `attr_colors` exist.

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

The normalize methods protect old save files. If a new version of the app expects a new field, normalization fills in a default instead of crashing.

## Drawing Trophies

Trophies are drawn on a `Canvas`.

Important methods:

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

## Animations

Tkinter animations use `after`.

```python
def animate(step=0):
    # change position, color, or opacity
    self.root.after(16, animate, step + 1)
```

Plain English:

1. Draw something.
2. Wait a few milliseconds.
3. Update it.
4. Repeat until the animation ends.

LifeXP uses this for:

- XP popups
- Level-up messages
- Header rank-up glow
- Trophy messages
- Firework particles
- Button feedback
- Tab hover and tab change feedback

## Method Map

This section lists every method in `LifeXPApp` and describes its job in simple language.

### Startup And Configuration

- `__init__`: prepares the app window, default values, themes, saved data, and all screens.
- `get_theme_definitions`: returns the full dictionary of available themes.
- `_hex_to_rgb`: converts a hex color like `#FFFFFF` into red, green, and blue numbers.
- `get_contrast_ratio`: measures how readable one color is on top of another.
- `get_readable_text_color`: chooses a text color that can be read on a background.
- `get_action_color`: chooses semantic action colors for accept, complete, edit, abandon, and danger.
- `get_action_text_color`: chooses readable text for a colored action button.
- `get_action_hover_color`: creates a slightly lighter hover color for an action button.
- `scaled_font_size`: scales a font number from the user's font-size setting.
- `ui_space`: scales padding and row heights from the user's font-size setting.
- `ui_font`: returns a Tkinter font tuple with the current font-size setting.
- `coerce_bool`: safely converts saved values like `"false"` or `0` into real booleans.
- `apply_modern_theme`: applies colors and styles to Tkinter and ttk widgets.

### Windows, Recoloring, And Display Preferences

- `fit_window_to_content`: sizes a popup window so its contents fit on screen.
- `show_fitted_window`: fits a popup, then shows it with the app's open animation.
- `animate_window_open`: fades and moves a popup into view.
- `recolor_widget_tree`: walks through child widgets and replaces old theme colors with new ones.
- `rescale_widget_tree`: walks through child widgets and updates fonts/padding after font-size changes.
- `apply_display_preferences`: saves and applies font size, animation, particle, and popup settings.
- `configure_notebook_tab_style`: sets the selected and hover colors for tabs.
- `handle_tab_hover_motion`: notices when the mouse moves over the tab area.
- `set_tab_hover`: starts or stops the tab hover animation.
- `play_tab_change_animation`: briefly animates the selected tab color.
- `handle_notebook_tab_changed`: reacts when the user changes tabs.

### Header, Rank, Tabs, And Icons

- `setup_header`: builds the top header with app title, avatar, account rank, and XP.
- `get_title_info`: chooses the current rank title and color from total level.
- `get_title_shape`: chooses the avatar shape for the current rank tier.
- `update_avatar`: redraws the avatar ring and symbol.
- `format_account_level_text`: turns account level and XP into a short label.
- `update_header`: refreshes the header and optionally plays rank-up feedback.
- `setup_ui`: creates the notebook tabs and calls each tab setup method.
- `create_pixel_icon`: builds a tiny pixel-art image from a text pattern.
- `build_tab_icons`: creates the pixel icons used in the tab bar.
- `create_level_up_arrow_icon`: creates the arrow icon used in level-up popups.

### Quest Action Buttons

- `get_quest_action_palette`: returns fill, hover, text, border, and glow colors for a quest action.
- `create_quest_action_button`: creates one custom action button in the Quest Log.
- `configure_quest_surface`: recolors a custom action button and its labels.
- `pointer_inside_widget`: checks whether the mouse pointer is inside a widget.
- `handle_quest_hover_enter`: starts hover feedback for a custom quest button.
- `handle_quest_hover_leave`: stops hover feedback after the pointer really leaves.
- `set_quest_button_hover`: animates a quest button between normal and hover colors.
- `refresh_quest_action_buttons`: rebuilds custom quest button colors after a theme change.
- `run_quest_action`: runs a quest action with click feedback.
- `play_quest_button_miss`: flashes the Complete button if no quest is selected.
- `play_quest_button_feedback`: plays the click pulse before running an action.

### Chronicles And Scrolling

- `create_summary_timeframe_button`: creates Daily, Weekly, or Monthly segmented controls.
- `update_summary_timeframe_buttons`: recolors those controls when the selected timeframe changes.
- `draw_summary_graph`: draws the Chronicles bar chart.
- `improve_color_contrast`: nudges a color toward black or white until it is readable.
- `get_attribute_text_color`: returns an attribute color adjusted for text readability.
- `get_summary_combo_colors`: chooses readable colors for highlighted words in Chronicles.
- `configure_summary_body_tags`: applies text styles to a Chronicles text box.
- `find_summary_body_under_pointer`: finds which Chronicles text box the pointer is over.
- `scroll_summary_body`: scrolls the Chronicles body under the pointer.
- `scroll_settings_canvas`: scrolls the Settings page.
- `create_modern_scrollbar`: creates a custom drawn scrollbar for list-like widgets.
- `route_global_scroll`: sends mouse-wheel events to the right scrollable area.
- `bind_global_scroll_events`: binds global scrolling events for the app.

### Building Tabs

- `setup_tasks_tab`: builds the Quest Log table and action rail.
- `get_tiers`: returns the trophy level tiers that should currently be shown.
- `calculate_trophy_canvas_size`: chooses a trophy canvas size from the available tiers.
- `schedule_trophy_room_resize`: delays trophy resizing until the layout is stable.
- `trophy_room_has_visible_geometry`: checks whether the trophy room has real screen size.
- `prepare_visible_trophy_room`: prepares trophy canvases once the tab is visible.
- `resize_trophy_canvases`: changes trophy canvas sizes after window resizing.
- `redraw_trophies`: redraws all existing trophy canvases.
- `rebuild_trophy_room`: rebuilds the full trophy grid.
- `setup_character_tab`: builds the Character Info tab with stats and trophies.
- `setup_summary_tab`: builds the Chronicles tab with reports, cards, and graph.
- `draw_font_size_slider`: draws the Settings font-size slider.
- `set_font_size_from_slider_event`: changes the slider value from a mouse click or drag.
- `apply_font_size_from_slider`: applies the selected font size to the app.
- `setup_settings_tab`: builds Settings for themes, display, animations, reset, and about info.

### Theme Changes And Data Normalization

- `set_theme`: applies a chosen theme, saves it, and recolors visible widgets.
- `reset_progress`: clears stats, quests, history, and trophies after confirmation.
- `refresh_theme_widgets`: updates widgets that need special theme handling.
- `_calculate_max_level`: finds the highest attribute level currently reached.
- `_invalidate_subcategory_cache`: clears cached activity suggestion data.
- `_invalidate_tier_cache`: clears cached trophy tier data.
- `normalize_user_info`: cleans saved user preferences and fills missing defaults.
- `normalize_subcategories`: cleans and merges saved activity suggestions.
- `get_default_data`: creates a complete fresh save-data structure.
- `get_attribute_rename_map`: lists old attribute names that should be migrated.
- `migrate_renamed_attributes`: updates old save files that used renamed attributes.
- `parse_history_date`: converts saved date text into a Python date object.
- `add_saved_subcategory`: remembers a user-created activity suggestion.
- `load_data`: loads `lifexp_data.json`, applies migrations, and returns app data.
- `normalize_stats`: validates the stats section of saved data.
- `normalize_tasks`: validates active quest records from saved data.
- `normalize_history`: validates completed quest history records from saved data.
- `save_data`: writes the current data to disk safely.

### Quest Data And Dialogs

- `refresh_task_list`: redraws the Quest Log table from `self.data["tasks"]`.
- `toggle_task_tree_selection`: lets Command-click or Control-click toggle task selection.
- `get_selected_task_indices`: returns all selected task indexes.
- `get_selected_task_index`: returns one selected task index.
- `add_task_dialog`: builds the Accept Quest window and creates pending quests.
- `edit_task_dialog`: edits one selected quest or opens batch edit for many.
- `edit_multiple_tasks_dialog`: edits XP and/or attribute for several selected quests.
- `delete_task`: abandons selected quests.
- `complete_task`: completes selected quests, awards XP, records history, and refreshes the app.

### XP, Account Level, Activities, And Trophies

- `get_scaled_xp_needed`: calculates XP needed for a level from a base number.
- `get_xp_needed`: returns XP needed for the next attribute level.
- `get_total_xp_before_level`: returns total attribute XP required before a level.
- `get_total_xp_for_stat`: calculates lifetime XP for one attribute.
- `get_account_xp_needed`: returns XP needed for the next account level.
- `get_total_account_xp_before_level`: returns total account XP required before a level.
- `get_account_level_progress`: converts total XP into account level, current XP, and needed XP.
- `get_all_subcategories`: returns all saved activity suggestions in one sorted list.
- `get_known_activity_owner`: finds which attribute owns a saved activity name.
- `get_subcategory_owner_map`: builds a lookup from activity name to attribute.
- `gain_xp`: adds XP to an attribute and handles level-up events.
- `check_trophies`: awards trophies when an attribute reaches milestone levels.
- `_trophy_material`: chooses trophy material colors for each milestone.
- `draw_attribute_symbol`: draws the small symbol for an attribute.
- `draw_trophy`: draws one trophy cup on a canvas.
- `update_stats_display`: refreshes stat labels, bars, trophies, header, and summary.
- `show_summary`: builds the daily, weekly, or monthly Chronicles report.

### Animation And Popup Helpers

- `get_center`: returns the center point of the app window.
- `clamp_widget_position`: keeps a popup widget inside the window bounds.
- `clamp_box_position`: keeps a box position inside the window bounds.
- `ease_out_cubic`: makes an animation start fast and slow down smoothly.
- `ease_smoothstep`: makes an animation start and end softly.
- `_blend_color`: blends two hex colors together.
- `set_popup_alpha`: changes popup transparency when the system supports it.
- `raise_popup_window`: keeps a popup visible above the main window.
- `popup_duration_ms`: converts animation steps into milliseconds.
- `popup_overlap_start_ms`: decides when chained popup animations can overlap.
- `schedule_level_up_sequence`: schedules multiple reward animations in order.
- `play_level_up_animation`: shows an attribute level-up popup.
- `play_rank_up_animation`: plays the header account-rank animation.
- `play_trophy_animation_at_center`: plays a trophy popup at the window center.
- `play_trophy_animation`: shows the trophy earned popup and particles.
- `acquire_particle_widget`: reuses or creates a widget for one particle.
- `register_particle_widget`: tracks a particle widget as active.
- `release_particle_widget`: hides and stores a particle widget for reuse.
- `destroy_particle_widget`: safely destroys a particle widget.
- `play_floating_text`: creates floating reward text.
- `play_firework_particles`: creates firework-style particles from a popup.
- `play_particles`: creates smaller burst particles.

## Safe Beginner Edits

Try these one at a time:

1. Change `BASE_XP_NEEDED` to make attributes faster or slower.
2. Change `ACCOUNT_BASE_XP_NEEDED` to rebalance total rank speed.
3. Add a default activity inside `get_default_data`.
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
- If a theme looks wrong, check `get_theme_definitions`, `get_action_color`, and `get_readable_text_color`.

## Small Glossary

- Attribute: One RPG stat, such as Strength or Intelligence.
- Object attribute: A value stored on `self`, such as `self.data`.
- Quest: An active task.
- XP: Experience points from completed quests.
- Level: Progress stage for an attribute or account.
- Trophy: Visual reward for an attribute milestone.
- Chronicles: History reports.
- Widget: A visible Tkinter object.
- Callback: A function that runs after a click, timer, or event.
- Cache: Stored calculation reused later.
- Method: A function that belongs to a class.
- Dictionary: A group of named values.
- List: An ordered group of values.
- Loop: Code that repeats for each item.
- Theme: A named group of colors.
