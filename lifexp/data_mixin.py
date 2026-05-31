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


class DataMixin:
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
                saved_font_size = int(user_info.get("font_size", normalized["font_size"]))
                if saved_font_size >= LEGACY_MAX_FONT_SIZE:
                    saved_font_size = max(saved_font_size, DEFAULT_FONT_SIZE)
                normalized["font_size"] = max(
                    MIN_FONT_SIZE,
                    min(MAX_FONT_SIZE, saved_font_size)
                )
            except (TypeError, ValueError):
                normalized["font_size"] = default_user_info["font_size"]
            normalized["animations_enabled"] = self.coerce_bool(
                user_info.get("animations_enabled"),
                default_user_info["animations_enabled"]
            )
            normalized["particles_enabled"] = self.coerce_bool(
                user_info.get("particles_enabled"),
                default_user_info["particles_enabled"]
            )
            normalized["popups_enabled"] = self.coerce_bool(
                user_info.get("popups_enabled"),
                default_user_info["popups_enabled"]
            )
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

    def get_default_data(self):
        """Returns a fresh, complete save-data structure."""
        return {
            "user_info": {
                "name": "Hero",
                "avatar_seed": random.randint(1, 100000),
                "theme": self.current_theme_name,
                "font_size": DEFAULT_FONT_SIZE,
                "animations_enabled": True,
                "particles_enabled": True,
                "popups_enabled": True
            },
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

    def get_attribute_rename_map(self):
        """Returns old attribute names and their current equivalents."""
        return {
            "Dexterity": "Agility",
            "Faith": "Charisma",
            "Vigor": "Vitality",
            "Constitution": "Vitality"
        }

    def migrate_renamed_attributes(self, data):
        """Updates old save-file attribute names in place."""
        rename_map = self.get_attribute_rename_map()

        if isinstance(data.get("stats"), dict):
            for old, new in rename_map.items():
                if old in data["stats"]:
                    data["stats"][new] = data["stats"].pop(old)

        if isinstance(data.get("tasks"), list):
            for task in data["tasks"]:
                if isinstance(task, dict) and task.get("attribute") in rename_map:
                    task["attribute"] = rename_map[task["attribute"]]

        if isinstance(data.get("history"), list):
            for record in data["history"]:
                if isinstance(record, dict) and record.get("attribute") in rename_map:
                    record["attribute"] = rename_map[record["attribute"]]

        if isinstance(data.get("subcategories"), dict):
            for old, new in rename_map.items():
                if old not in data["subcategories"]:
                    continue
                old_subs = data["subcategories"].pop(old)
                if not isinstance(old_subs, list):
                    continue
                data["subcategories"].setdefault(new, [])
                existing_names = {name.lower() for name in data["subcategories"][new] if isinstance(name, str)}
                for sub in old_subs:
                    if isinstance(sub, str) and sub.lower() not in existing_names:
                        data["subcategories"][new].append(sub)
                        existing_names.add(sub.lower())

        if isinstance(data.get("trophies"), list):
            for index, trophy_name in enumerate(data["trophies"]):
                if not isinstance(trophy_name, str):
                    continue
                for old, new in rename_map.items():
                    if trophy_name.startswith(f"{old} "):
                        data["trophies"][index] = trophy_name.replace(old, new, 1)
                        break

    def parse_history_date(self, date_value):
        """Parses saved history dates into comparable local naive datetimes."""
        record_date = datetime.fromisoformat(date_value)
        if record_date.tzinfo is not None:
            record_date = record_date.astimezone().replace(tzinfo=None)
        return record_date

    def add_saved_subcategory(self, attr, name):
        """Adds an activity suggestion if it is new for an attribute."""
        if attr not in self.attributes:
            return False
        name = str(name).strip()
        if not name:
            return False

        self.data["subcategories"].setdefault(attr, [])
        existing_names = {
            saved_name.lower()
            for saved_name in self.data["subcategories"][attr]
            if isinstance(saved_name, str)
        }
        if name.lower() in existing_names:
            return False

        self.data["subcategories"][attr].append(name)
        self._invalidate_subcategory_cache()
        return True

    def load_data(self):
        """Reads saved data. Includes complex migrations to prevent crashes."""
        # default_data is the safe starting shape for the app. It documents what keys
        # the rest of the program expects to exist.
        default_data = self.get_default_data()

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

                    if not isinstance(data.get("subcategories"), dict):
                        data["subcategories"] = default_data["subcategories"]
                    self.migrate_renamed_attributes(data)

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
            xp_needed = self.get_xp_needed(level)
            # Old saves might have too much XP stored in one level. This loop spends
            # extra XP on level-ups until the stat is in a valid state again.
            while xp >= xp_needed:
                xp -= xp_needed
                level += 1
                xp_needed = self.get_xp_needed(level)
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
                self.parse_history_date(date_value)
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
        try:
            with open(temp_file, 'w', encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            os.replace(temp_file, self.data_file)
        except OSError as exc:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except OSError:
                pass
            try:
                messagebox.showerror(
                    "Save Failed",
                    f"LifeXP could not save your progress:\n\n{exc}",
                    parent=self.root
                )
            except tk.TclError:
                print(f"LifeXP could not save your progress: {exc}")

