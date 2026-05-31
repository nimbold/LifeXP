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


RAW_BASE_XP_CURVE = (
    ACCOUNT_LEVEL_CURVE_BASE_MULTIPLIER
    * ((1 + ACCOUNT_LEVEL_CURVE_OFFSET) ** 2)
) + 1


class EngineMixin:
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
        suggest_after_id = None
        # pending_quests is a temporary queue. Nothing is saved until the user clicks
        # Accept Quest, so the dialog can add and remove draft quests freely.

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
            # A chip is a clickable label. This refresh makes the selected chip colorful
            # and returns the other chips to the normal card color.
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
            selectmode=tk.EXTENDED
        )
        suggestion_scrollbar = self.create_modern_scrollbar(listbox_frame, suggestion_list)
        suggestion_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        suggestion_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))

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
        selected_list = tk.Listbox(
            selected_list_frame,
            font=("{San Francisco}", 10),
            bg=self.bg_light,
            fg=self.text_color,
            selectbackground=self.accent_green,
            selectforeground=self.bg_dark,
            activestyle="none",
            bd=0,
            highlightthickness=0
        )
        selected_scrollbar = self.create_modern_scrollbar(selected_list_frame, selected_list)
        selected_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        selected_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))

        selected_actions = tk.Frame(selected_card, bg=self.bg_light)
        selected_actions.grid(row=2, column=0, sticky="ew", padx=14, pady=(8, 12))
        remove_button = ttk.Button(selected_actions, text="Remove Selected")
        remove_button.pack(side=tk.LEFT)

        def difficulty_color(v):
            # Higher difficulty shifts the slider color toward the current accent color.
            ratio = (v - 1) / 9.0
            target_r, target_g, target_b = self._hex_to_rgb(self.accent_green)
            r = int(255 + (target_r - 255) * ratio)
            g = int(255 + (target_g - 255) * ratio)
            b = int(255 + (target_b - 255) * ratio)
            return f'#{r:02x}{g:02x}{b:02x}'

        def draw_difficulty_slider():
            # The slider is custom-drawn on a Canvas so its colors match the active theme.
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
            # event.x is the mouse position on the slider. Convert it to a 1-10 value.
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
            # Activity suggestions can be colored by attribute. We adjust the color
            # first so it remains readable on light and dark list backgrounds.
            color = self.get_attribute_text_color(attr, self.bg_light) if use_attr_color and attr else self.text_color
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
            # Redraw the queue preview from pending_quests every time the queue changes.
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
            # This creates or updates a draft quest in the queue. If the same activity
            # is already queued for the same attribute, only the XP value is updated.
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
            # Autocomplete is rebuilt from saved activities. The All filter searches
            # every attribute; a specific attribute searches only that attribute's list.
            nonlocal suggest_after_id
            suggest_after_id = None
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
            # Debouncing waits briefly after typing before refreshing suggestions. This
            # avoids rebuilding the list on every single keystroke during fast typing.
            nonlocal suggest_after_id
            if suggest_after_id is not None:
                dialog.after_cancel(suggest_after_id)
            suggest_after_id = dialog.after(120, update_suggestions)

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
            # When the user accepts the queue, copy each draft quest into real app data
            # and remember each activity as a future autocomplete suggestion.
            if not pending_quests and not add_current_to_selection(show_error=True):
                return

            for quest in pending_quests:
                self.add_saved_subcategory(quest["attribute"], quest["name"])
                self.data["tasks"].append(quest.copy())

            added_count = len(pending_quests)
            self.save_data()
            self.refresh_task_list()
            close_dialog()

            cx, cy = self.get_center()
            self.play_floating_text(f"✨ {added_count} QUEST{'S' if added_count != 1 else ''} ADDED", self.accent_green, cx, cy)

        def close_dialog():
            nonlocal suggest_after_id
            if suggest_after_id is not None:
                dialog.after_cancel(suggest_after_id)
                suggest_after_id = None
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
        self.add_saved_subcategory(task_attr, new_name)
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

            for index, name, attr, xp in updates:
                if not 0 <= index < len(self.data["tasks"]):
                    self.refresh_task_list()
                    messagebox.showinfo("Notice", "The quest list changed. Please reopen the editor.", parent=dialog)
                    return

                self.data["tasks"][index]["attribute"] = attr
                self.data["tasks"][index]["name"] = name
                self.data["tasks"][index]["subcategory"] = name
                self.data["tasks"][index]["xp"] = xp
                self.add_saved_subcategory(attr, name)

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
        level_events = self.summarize_level_events(level_events)

        cx, cy = self.get_center()
        # XP gain always gets a fixed readable duration. If level-up popups are also
        # needed, they are scheduled after it rather than shortening this popup.
        # play_floating_text() now returns the final popup box position. The XP particles
        # use that box as their source so sparks appear to come from the reward label,
        # while physics=True keeps the older gravity/falling feel.
        popup_text = f"+{total_xp_gain} XP!" if len(tasks) == 1 else f"{len(tasks)} QUESTS  +{total_xp_gain} XP!"
        popup_box = self.play_floating_text(popup_text, "#EBCB8B", cx, cy, size=30, duration_steps=XP_POPUP_STEPS, fade_steps=XP_POPUP_FADE_STEPS)
        self.play_firework_particles("#EBCB8B", popup_box, count=34, palette=["#EBCB8B", "#FFD166", "#F59E0B", "#F97316"], physics=True, life_range=(42, 58), fade_start_ratio=0.42)

        if level_events or rank_event:
            self.schedule_level_up_sequence(level_events, rank_event)

    def get_scaled_xp_needed(self, level, base_xp):
        """Returns an Elden Ring-style level cost normalized to this app's base XP."""
        # The raw formula gives a curve shape. Dividing by raw_base normalizes the curve
        # so level 1 starts at the base XP chosen for this app.
        raw_base = RAW_BASE_XP_CURVE
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

    def _get_total_xp_before_level_generic(self, level, cache, single_needed_func):
        """Helper to compute and cache cumulative XP required to reach a given level."""
        highest_cached_level = max(cache)
        total = cache[highest_cached_level]
        for next_level in range(highest_cached_level + 1, level + 1):
            total += single_needed_func(next_level - 1)
            cache[next_level] = total
        return cache[level]

    def get_total_xp_before_level(self, level):
        """Returns cumulative XP needed to reach a level, cached by level."""
        return self._get_total_xp_before_level_generic(
            level, self.total_xp_before_level_cache, self.get_xp_needed
        )

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
        return self._get_total_xp_before_level_generic(
            level, self.account_total_xp_before_level_cache, self.get_account_xp_needed
        )

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

    def summarize_level_events(self, level_events):
        """Collapses many level crossings into one final-level event per attribute."""
        summarized = {}
        for event in level_events:
            attr = event["attribute"]
            summary = summarized.setdefault(attr, {
                "attribute": attr,
                "level": event["level"],
                "trophies": []
            })
            summary["level"] = max(summary["level"], event["level"])
            if event["trophy"]:
                summary["trophies"].append(event["trophy"])

        return [
            summarized[attr]
            for attr in self.attributes
            if attr in summarized
        ]

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
            if self._trophy_room_built:
                self.rebuild_trophy_room()
            current_tiers = self._last_rendered_tiers or current_tiers

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

        if self._trophy_room_built:
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
                record_date = self.parse_history_date(record["date"])
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
            text=title
        )
        if hasattr(self, "summary_metric_labels"):
            self.summary_metric_labels["activities"].config(text=str(unique_activities))
            self.summary_metric_labels["quests"].config(text=str(completed_tasks))
            self.summary_metric_labels["xp"].config(text=f"{total_xp} XP")

        self.update_summary_timeframe_buttons()
        self.summary_attribute_totals = {
            attr: sum(details["xp"] for details in activities.values())
            for attr, activities in activity_by_attribute.items()
        }
        self.draw_summary_graph(self.summary_attribute_totals)

        # Each card is a small independent report. It is temporarily unlocked, filled
        # with that attribute's activities, and then locked again.
        for attr in self.attributes:
            widgets = self.summary_cards[attr]
            body = widgets["body"]
            body.config(state=tk.NORMAL)
            body.delete(1.0, tk.END)

            activities = activity_by_attribute[attr]
            attr_xp = sum(details["xp"] for details in activities.values())
            widgets["meta"].config(text=f"{len(activities)} types | {attr_xp} XP")

            if not activities:
                body.insert(tk.END, "No activity logged in this chapter.")
            else:
                sorted_activities = sorted(
                    activities.items(),
                    key=lambda item: (-item[1]["count"], -item[1]["xp"], item[0])
                )
                for activity, details in sorted_activities:
                    count = details["count"]
                    # Repeated activities get stronger highlight tags, like a combo meter.
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

