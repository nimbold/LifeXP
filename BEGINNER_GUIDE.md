# LifeXP Beginner Guide

This guide explains the LifeXP code for new programmers.

Read it when you want to understand how the app works, why the code is arranged this way, and what each method does.

You do not need to memorize everything. Start with the first sections, then use the method map when you find a method name in the code.

## Reading Path

Read the files in this order:

1. `lifexp/constants.py`, which stores shared numbers and text values.
2. `lifexp/runtime.py`, which stores small startup helper functions.
3. `main.py`, starting with the imports.
4. `__init__`, which starts the app object.
5. Theme methods, such as `get_theme_definitions` and `apply_modern_theme`.
6. UI setup methods, such as `setup_tasks_tab` and `setup_character_tab`.
7. Save/load methods, such as `load_data` and `save_data`.
8. Quest methods, such as `add_task_dialog` and `complete_task`.
9. XP methods, such as `gain_xp` and `get_xp_needed`.
10. Report and animation methods near the bottom.

## Big Picture

LifeXP is a Tkinter app mostly stored in one class:

```python
class LifeXPApp:
    def __init__(self, root):
        self.root = root
```

A class groups related data and behavior together.

In this app, the class stores:

- the main window
- saved data
- widgets
- colors
- XP logic
- trophy logic
- popup animations

`self` means "this app object."

If one method writes this:

```python
self.data = self.load_data()
```

another method can read `self.data` later.

## Project Files

The app has started to split into a few files:

```text
main.py
lifexp/
    __init__.py
    constants.py
    runtime.py
```

`main.py` is still the main file. It creates the window, defines `LifeXPApp`,
builds the screens, handles quests, saves data, calculates XP, and plays
animations.

`lifexp/constants.py` stores values that many parts of the app reuse, such as
the app version, XP settings, font limits, and popup timing.

`lifexp/runtime.py` stores helper functions that do not need to be methods on
`LifeXPApp`, such as finding app folders, detecting packaged builds, configuring
macOS scaling, and creating the HTTPS context for update checks.

This is a gradual split. The app does not need every method in its own file.
Files become useful when they collect related code with a clear responsibility.

## Main Data

Most progress is stored in `self.data`.

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

### `user_info`

Stores app preferences and account display data.

Example:

```python
"theme": "Tokyo Night"
"font_size": 11
"animations_enabled": True
```

### `stats`

Stores each RPG attribute.

Example:

```python
"Strength": {
    "level": 7,
    "xp": 75
}
```

This means Strength is level 7 with 75 XP inside that level.

### `tasks`

Stores active quests.

Example:

```python
{
    "name": "Coding",
    "attribute": "Intelligence",
    "subcategory": "Coding",
    "xp": 50
}
```

### `history`

Stores completed quests.

Example:

```python
{
    "name": "Coding",
    "attribute": "Intelligence",
    "subcategory": "Coding",
    "xp": 50,
    "date": "2026-05-24T10:30:00"
}
```

Chronicles reads this list to make reports.

### `subcategories`

Stores saved activity suggestions.

Example:

```python
"Intelligence": ["Coding", "Reading", "Research"]
```

The Accept Quest window uses these names for autocomplete.

## Python Ideas Used Here

### Variables

A variable stores a value.

```python
total_xp = 120
theme_name = "Tokyo Night"
```

LifeXP uses variables for XP numbers, colors, widget references, and short calculations.

### Constants

A constant is a value that is meant to be reused.

```python
BASE_XP_NEEDED = 100
ACCOUNT_BASE_XP_NEEDED = 500
```

LifeXP constants live in `lifexp/constants.py`. Changing a constant changes app
behavior in one place.

### Lists

A list stores ordered items.

```python
self.attributes = ["Strength", "Agility", "Intelligence", "Charisma", "Vitality"]
```

Lists are useful when the app needs to repeat work for each item.

### Dictionaries

A dictionary stores named values.

```python
theme = {
    "bg_dark": "#1A1B26",
    "bg_light": "#24283B",
    "accent": "#7AA2F7"
}
```

LifeXP uses dictionaries for themes, stats, tasks, history records, and colors.

### For Loops

A `for` loop repeats code for each item.

Example from the app:

```python
for attr, color in self.attr_colors.items():
    self.style.configure(
        f"{attr}.Horizontal.TProgressbar",
        background=color
    )
```

Plain English:

1. Take one attribute and color.
2. Create a progress-bar style for it.
3. Repeat until every attribute has a style.

Another example:

```python
for quest in pending_quests:
    self.data["tasks"].append(quest.copy())
```

Plain English:

1. Take one draft quest from the queue.
2. Copy it into the real task list.
3. Repeat for every queued quest.

### While Loops

A `while` loop repeats while a condition is true.

Example:

```python
while stat["xp"] >= xp_needed:
    stat["xp"] -= xp_needed
    stat["level"] += 1
```

Plain English:

1. If the stat has enough XP, spend XP.
2. Increase the level.
3. Check again, because one big reward might give more than one level.

### If Statements

An `if` statement chooses a path.

```python
if theme_name not in self.themes:
    return
```

Plain English: if the theme does not exist, stop before the app crashes.

### Functions And Methods

A function is reusable code.

```python
def get_readable_text_color(self, background, preferred=None):
    ...
```

A function inside a class is called a method.

Most methods in LifeXP do one job: draw something, calculate something, save data, or react to a click.

### Parameters

Parameters are values passed into a method.

```python
def get_xp_needed(self, level):
```

Here `level` tells the method which level to calculate.

### Return Values

`return` sends a result back.

```python
return self.xp_needed_cache[level]
```

The caller can use that returned value.

### Callbacks

A callback is a method that runs later.

Example:

```python
ttk.Button(parent, text="Complete", command=self.complete_task)
```

Clicking the button calls `complete_task`.

### Nested Functions

A nested function is a function inside another function.

Example from `add_task_dialog`:

```python
def refresh_selected_list():
    selected_list.delete(0, tk.END)
```

This helper only matters inside the Accept Quest window, so it stays inside `add_task_dialog`.

### Caches

A cache stores a calculated answer for reuse.

```python
self.xp_needed_cache[level] = value
```

The app calculates XP requirements many times. Caching keeps that fast.

### Algorithms

An algorithm is a step-by-step process.

LifeXP uses small algorithms for:

- calculating XP needed for a level
- converting total XP into account rank
- picking readable text colors
- grouping history records into reports
- drawing trophies based on level
- animating popups frame by frame

## Tkinter Ideas Used Here

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

LifeXP uses three layout methods:

```python
widget.pack()
widget.grid(row=0, column=0)
widget.place(x=100, y=200)
```

- `pack`: stack larger sections.
- `grid`: arrange rows and columns.
- `place`: position animation widgets exactly.

### Events

Events are things the user or window does.

Examples:

```python
slider_canvas.bind("<Button-1>", set_difficulty_from_event)
dialog.bind("<Return>", lambda event: save())
```

Clicking the slider or pressing Enter runs code.

### StringVar And IntVar

Tkinter variables connect widgets to Python values.

```python
activity_var = tk.StringVar()
difficulty_var = tk.IntVar(value=5)
```

The entry box reads from `activity_var`. The difficulty slider reads from `difficulty_var`.

### Canvas Drawing

`tk.Canvas` draws shapes and text.

```python
canvas.create_oval(...)
canvas.create_line(...)
canvas.create_text(...)
```

LifeXP uses canvases for trophies, icons, graphs, sliders, and particles.

### `after`

`after` schedules code to run later.

```python
self.root.after(20, animate)
```

Animations use this pattern:

1. Draw one frame.
2. Wait a few milliseconds.
3. Draw the next frame.
4. Repeat until finished.

## Main Workflows

### Starting The App

1. `main.py` imports constants and runtime helpers from `lifexp`.
2. `root = tk.Tk()` creates the main window.
3. `configure_platform_scaling(root)` adjusts packaged macOS display scaling if needed.
4. `app = LifeXPApp(root)` creates the app object.
5. `__init__` prepares themes, loads data, and builds the UI.
6. `root.mainloop()` starts listening for clicks, typing, and timers.

### Adding A Quest

1. `add_task_dialog` opens the Accept Quest window.
2. The user types or selects activities.
3. Draft quests go into `pending_quests`.
4. `save` copies draft quests into `self.data["tasks"]`.
5. `save_data` writes the JSON file.
6. `refresh_task_list` redraws the table.

### Completing A Quest

1. The user selects quests in the table.
2. `complete_task` reads selected rows.
3. Each quest moves into `self.data["history"]`.
4. Each quest gives XP through `gain_xp`.
5. `gain_xp` handles level-ups.
6. `check_trophies` checks milestone rewards.
7. `save_data` saves progress.
8. UI refresh methods redraw the app.
9. Popup animations show the reward.

### Saving And Loading

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

The app writes to a temporary file first, then replaces the real save file. That is safer than writing directly over the old file.

### XP Scaling

There are two level systems:

- attribute levels for Strength, Agility, Intelligence, Charisma, and Vitality
- account rank from total lifetime XP

Both use:

```python
get_scaled_xp_needed(level, base_xp)
```

Attributes use:

```python
BASE_XP_NEEDED = 100
```

Account rank uses:

```python
ACCOUNT_BASE_XP_NEEDED = 500
```

The formula starts easy and becomes harder over time.

### Reports

`show_summary` builds Chronicles.

It:

1. Chooses a date range.
2. Reads `self.data["history"]`.
3. Counts matching records.
4. Groups XP by attribute and activity.
5. Updates metric labels.
6. Draws the graph.
7. Fills each report card.

## Method Map

This section lists the small helper functions outside the class, then every
method in `LifeXPApp`.

### Helper Functions

These functions live outside `LifeXPApp` because they do not need `self`.

#### `lifexp/runtime.py`

- `get_resource_dir`: returns the folder where bundled read-only app assets live.
- `get_user_data_dir`: returns the folder where packaged builds write user progress.
- `is_packaged_app`: checks whether LifeXP is running as a packaged app.
- `configure_platform_scaling`: keeps packaged macOS font rendering close to normal Python runs.
- `get_https_context`: creates an HTTPS context that works in packaged builds.

### Startup And Theme Helpers

- `__init__`: prepares the window, default values, themes, saved data, and screens.
- `get_theme_definitions`: returns all available color themes.
- `_hex_to_rgb`: converts a color like `#FFFFFF` into red, green, and blue numbers.
- `get_contrast_ratio`: measures text/background readability.
- `get_readable_text_color`: chooses a readable text color for a background.
- `get_action_color`: chooses colors for accept, complete, edit, abandon, and danger actions.
- `get_action_text_color`: chooses readable text for an action button.
- `get_action_hover_color`: creates a lighter hover color.
- `scaled_font_size`: scales a font size from the Settings value.
- `ui_space`: scales spacing from the Settings font size.
- `ui_font`: returns a Tkinter font tuple.
- `coerce_bool`: converts saved boolean-like values into real booleans.
- `apply_modern_theme`: applies Tkinter and ttk colors, fonts, and styles.

### Windows, Tabs, And Display Preferences

- `fit_window_to_content`: sizes a popup so its contents fit.
- `show_fitted_window`: fits a popup, then displays it.
- `animate_window_open`: fades and moves a popup into view.
- `recolor_widget_tree`: updates normal Tk widget colors after a theme change.
- `rescale_widget_tree`: updates already-created widget fonts after font-size changes.
- `apply_display_preferences`: applies font, animation, particle, and popup settings.
- `configure_notebook_tab_style`: sets selected and hover tab colors.
- `handle_tab_hover_motion`: detects mouse movement over the tab bar.
- `set_tab_hover`: starts or stops tab hover animation.
- `play_tab_change_animation`: briefly animates the selected tab.
- `handle_notebook_tab_changed`: reacts when the selected tab changes.

### Header And Icons

- `setup_header`: builds the top app header.
- `get_title_info`: chooses the account title and color.
- `get_title_shape`: chooses the avatar shape.
- `update_avatar`: redraws the avatar ring.
- `format_account_level_text`: formats account level text.
- `update_header`: refreshes rank, title, avatar, and XP text.
- `setup_ui`: creates the main notebook tabs.
- `create_pixel_icon`: creates a pixel icon from a text pattern.
- `build_tab_icons`: draws tab icons.
- `create_level_up_arrow_icon`: creates the level-up arrow icon.

### Quest Buttons

- `get_quest_action_palette`: returns colors for a custom quest button.
- `create_quest_action_button`: builds one custom quest action button.
- `configure_quest_surface`: recolors a custom quest button.
- `pointer_inside_widget`: checks whether the mouse is inside a widget.
- `handle_quest_hover_enter`: starts custom button hover feedback.
- `handle_quest_hover_leave`: stops hover feedback.
- `set_quest_button_hover`: animates a custom quest button.
- `refresh_quest_action_buttons`: rebuilds quest action button colors.
- `run_quest_action`: runs a quest action after click feedback.
- `play_quest_button_miss`: flashes Complete when no quest is selected.
- `play_quest_button_feedback`: plays button press feedback.

### Chronicles And Scrolling

- `create_summary_timeframe_button`: creates a Daily, Weekly, or Monthly selector.
- `update_summary_timeframe_buttons`: recolors timeframe selectors.
- `draw_summary_graph`: draws the Chronicles bar chart.
- `improve_color_contrast`: adjusts a color until it is readable.
- `get_attribute_text_color`: returns a readable color for an attribute label.
- `get_summary_combo_colors`: chooses highlight colors for report text.
- `configure_summary_body_tags`: sets styles inside report text boxes.
- `find_summary_body_under_pointer`: finds the report body under the mouse.
- `scroll_summary_body`: scrolls the report body under the mouse.
- `scroll_settings_canvas`: scrolls the Settings page.
- `create_modern_scrollbar`: creates a custom scrollbar.
- `route_global_scroll`: sends mouse-wheel events to the correct area.
- `bind_global_scroll_events`: connects mouse-wheel events to the app.

### Building Screens

- `setup_tasks_tab`: builds the Quest Log.
- `get_tiers`: returns the trophy tiers currently shown.
- `calculate_trophy_canvas_size`: chooses trophy canvas size.
- `schedule_trophy_room_resize`: waits briefly before resizing trophies.
- `trophy_room_has_visible_geometry`: checks whether the trophy area has real size.
- `prepare_visible_trophy_room`: prepares trophies when the Character tab is visible.
- `resize_trophy_canvases`: resizes trophy canvases.
- `redraw_trophies`: redraws existing trophies.
- `rebuild_trophy_room`: rebuilds the trophy grid.
- `setup_character_tab`: builds Character Info.
- `setup_summary_tab`: builds Chronicles.
- `draw_font_size_slider`: draws the Settings font-size slider.
- `set_font_size_from_slider_event`: changes font size from mouse position.
- `apply_font_size_from_slider`: applies the selected font size.
- `setup_settings_tab`: builds Settings.

### Theme Changes And Save Cleanup

- `set_theme`: changes theme, saves it, and recolors the app.
- `reset_progress`: clears progress after confirmation.
- `refresh_theme_widgets`: refreshes widgets that need special theme handling.
- `_calculate_max_level`: finds the highest current attribute level.
- `_invalidate_subcategory_cache`: clears saved activity caches.
- `_invalidate_tier_cache`: clears trophy tier caches.
- `normalize_user_info`: validates saved preferences.
- `normalize_subcategories`: validates, merges, and cleans activity suggestions.
- `get_default_data`: creates a fresh save-data structure.
- `get_attribute_rename_map`: lists old attribute names and new names.
- `migrate_renamed_attributes`: updates old saves that used old attribute names.
- `parse_history_date`: converts saved date text into a `datetime`.
- `add_saved_subcategory`: saves a new activity suggestion.
- `load_data`: loads JSON, migrates old data, and fills missing fields.
- `normalize_stats`: validates stats and fixes overfilled XP.
- `normalize_tasks`: keeps only valid active quests.
- `normalize_history`: keeps only valid completed quest records.
- `save_data`: writes the current data to disk.

### Quest Actions

- `refresh_task_list`: redraws the active quest table.
- `toggle_task_tree_selection`: toggles table selection with Command or Control click.
- `get_selected_task_indices`: returns selected quest indexes.
- `get_selected_task_index`: returns one selected quest index.
- `add_task_dialog`: opens the Accept Quest window.
- `edit_task_dialog`: edits one quest or starts batch editing.
- `edit_multiple_tasks_dialog`: edits several quests in one popup.
- `delete_task`: abandons selected quests.
- `complete_task`: completes selected quests, awards XP, saves history, and refreshes the UI.

### XP, Activities, And Trophies

- `get_scaled_xp_needed`: calculates XP needed for a level.
- `get_xp_needed`: returns XP needed for the next attribute level.
- `get_total_xp_before_level`: returns total XP needed before an attribute level.
- `get_total_xp_for_stat`: calculates lifetime XP for one attribute.
- `get_account_xp_needed`: returns XP needed for the next account level.
- `get_total_account_xp_before_level`: returns total account XP needed before a level.
- `get_account_level_progress`: converts total XP into account level progress.
- `get_all_subcategories`: returns all saved activity names once.
- `get_known_activity_owner`: finds which attribute owns an activity.
- `get_subcategory_owner_map`: builds an activity-to-attribute lookup.
- `gain_xp`: adds XP to an attribute and creates level-up events.
- `check_trophies`: awards trophy milestones.
- `_trophy_material`: chooses trophy colors for a milestone.
- `draw_attribute_symbol`: draws the symbol inside a trophy.
- `draw_trophy`: draws one trophy cup.
- `update_stats_display`: refreshes stat labels, bars, trophies, header, and summary.
- `show_summary`: builds the daily, weekly, or monthly report.

### Animation And Popup Helpers

- `get_center`: returns the center of the app window.
- `clamp_widget_position`: keeps a popup widget inside the window.
- `clamp_box_position`: keeps a popup box inside the window.
- `ease_out_cubic`: makes movement start fast and slow down.
- `ease_smoothstep`: makes movement start and end softly.
- `_blend_color`: blends two colors.
- `set_popup_alpha`: changes popup transparency when supported.
- `raise_popup_window`: keeps a popup above the main window.
- `popup_duration_ms`: converts animation steps into milliseconds.
- `popup_overlap_start_ms`: chooses when chained popups may overlap.
- `schedule_level_up_sequence`: schedules rank, level, and trophy popups.
- `play_level_up_animation`: shows an attribute level-up popup.
- `play_rank_up_animation`: plays the header rank-up animation.
- `play_trophy_animation_at_center`: starts a trophy popup at the window center.
- `play_trophy_animation`: shows trophy text and particles.
- `acquire_particle_widget`: gets a particle widget from the pool or creates one.
- `register_particle_widget`: tracks an active particle.
- `release_particle_widget`: hides and stores a particle for reuse.
- `destroy_particle_widget`: safely releases a particle widget.
- `play_floating_text`: creates floating reward text.
- `play_firework_particles`: creates larger firework-style particles.
- `play_particles`: creates smaller burst particles.

## Beginner Edits To Try

Try one change at a time:

1. Change `BASE_XP_NEEDED` in `lifexp/constants.py`.
2. Add a default activity in `get_default_data`.
3. Add a theme in `get_theme_definitions`.
4. Change trophy levels in `get_tiers`.
5. Change popup text in `play_level_up_animation`.
6. Change report text in `show_summary`.

After each edit, run:

```bash
python3 -m py_compile main.py lifexp/*.py
python3 main.py
```

## Debugging Checklist

If something breaks:

- Read the Terminal error from top to bottom.
- Find the file name and line number.
- Check commas, brackets, and indentation.
- If a button does nothing, check its `command=...`.
- If data looks wrong, inspect `lifexp_data.json`.
- If a widget is invisible, check `bg` and `fg`.
- If XP feels wrong, check `get_xp_needed` and `gain_xp`.
- If reports look wrong, check `show_summary`.

## Glossary

- Attribute: one RPG stat, such as Strength.
- Object attribute: a value stored on `self`.
- Quest: an active task.
- XP: experience points from completed quests.
- Level: progress stage for an attribute or account.
- Trophy: reward for an attribute milestone.
- Chronicles: history reports.
- Widget: a visible Tkinter object.
- Callback: code that runs after a click, timer, or event.
- Cache: stored calculation reused later.
- Method: a function that belongs to a class.
- Dictionary: named values.
- List: ordered values.
- Loop: repeated code.
- Theme: a named group of colors.
