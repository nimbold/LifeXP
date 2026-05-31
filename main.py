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

# ==============================================================================
# MAIN APP CLASS
# A class lets the app keep related data and behavior together. Every method
# below uses self to access the same window, saved data, widgets, and colors.
# ==============================================================================

from lifexp.ui_mixin import UIMixin
from lifexp.data_mixin import DataMixin
from lifexp.engine_mixin import EngineMixin
from lifexp.animation_mixin import AnimationMixin

class LifeXPApp(UIMixin, DataMixin, EngineMixin, AnimationMixin):
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
        self.base_dir = get_resource_dir()
        self.data_dir = get_user_data_dir() if is_packaged_app() else self.base_dir
        self.data_file = os.path.join(self.data_dir, "lifexp_data.json")
        os.makedirs(self.data_dir, exist_ok=True)
        self.rank_icon_images = []
        self.xp_needed_cache = {}
        self.total_xp_before_level_cache = {1: 0}
        self.current_total_level = 0
        self.themes = self.get_theme_definitions()
        self.current_theme_name = "Tokyo Night"
        self.font_size = DEFAULT_FONT_SIZE
        self.animations_enabled = True
        self.particles_enabled = True
        self.popups_enabled = True
        # Popup sequence gives simultaneous reward messages small vertical offsets so
        # they fade independently instead of covering the exact same screen position.
        self.popup_sequence = 0
        self.rank_up_animation_token = 0
        self.active_particle_widgets = []
        self.particle_widget_pool = []
        self.particle_widget_token = 0
        self.modern_scrollbars = []
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
        self._trophy_room_has_real_layout = False
        self._trophy_room_built = False
        self._max_stat_level = 1
        self.current_summary_timeframe = "daily"

        # Visual configuration lives near the top so the rest of the app can reuse it.
        # Each attribute gets one color, which is later used in bars, graphs, and art.
        self.attr_colors = self.themes[self.current_theme_name]["attr_colors"].copy()
        self.app_icon_image = self.load_app_icon_image()
        self.rank_icon_images = self.load_rank_icon_images()

        # Boot order matters: styles must exist before widgets are built, and data must
        # load before labels can show the current name, XP, tasks, and levels.
        self.apply_modern_theme()
        self.data = self.load_data()
        self._max_stat_level = self._calculate_max_level()
        self.current_theme_name = self.data["user_info"].get("theme", self.current_theme_name)
        if self.current_theme_name not in self.themes:
            self.current_theme_name = "Tokyo Night"
            self.data["user_info"]["theme"] = self.current_theme_name
        self.font_size = self.data["user_info"].get("font_size", DEFAULT_FONT_SIZE)
        self.animations_enabled = self.coerce_bool(self.data["user_info"].get("animations_enabled"), True)
        self.particles_enabled = self.coerce_bool(self.data["user_info"].get("particles_enabled"), True)
        self.popups_enabled = self.coerce_bool(self.data["user_info"].get("popups_enabled"), True)
        self.apply_modern_theme()

        self.setup_header()
        self.setup_ui()
        self.update_stats_display()
        self.refresh_task_list()
        self.apply_display_preferences(save=False)


# ==============================================================================
# POWER SWITCH
# This code runs only when main.py is launched directly. It creates the Tkinter
# window, creates the app object, and starts the event loop.
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    configure_platform_scaling(root)
    app = LifeXPApp(root)
    root.mainloop()
