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


class AnimationMixin:
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
        if not self.animations_enabled:
            return

        # XP confirms the quest first. Attribute upgrades are batched so completing
        # several quests does not spawn one popup and particle burst per level crossed.
        first_reward_delay = self.popup_overlap_start_ms(XP_POPUP_STEPS, XP_TO_REWARD_START_RATIO)
        trophy_start_gap = self.popup_overlap_start_ms(TROPHY_POPUP_STEPS)

        if rank_event:
            self.root.after(first_reward_delay, lambda event=rank_event: self.play_rank_up_animation(event))

        if level_events:
            self.root.after(first_reward_delay, lambda events=level_events: self.play_level_up_batch(events))

        next_delay = first_reward_delay + self.popup_overlap_start_ms(BATCH_LEVEL_UP_POPUP_STEPS, 0.82)
        for event in level_events:
            for trophy in event.get("trophies", []):
                self.root.after(next_delay, lambda trophy=trophy: self.play_trophy_animation_at_center(trophy))
                next_delay += trophy_start_gap

    def play_level_up_batch(self, events):
        """Shows all upgraded attributes together after a multi-quest completion."""
        if not self.animations_enabled:
            return

        cx, cy = self.get_center()
        count = max(1, len(events))
        spacing = 46
        start_y = int(cy + 48 - ((count - 1) * spacing / 2))
        popup_boxes = []

        for index, event in enumerate(events):
            popup_boxes.append(self.play_level_up_animation(
                event,
                x=cx,
                y=start_y + (index * spacing),
                duration_steps=BATCH_LEVEL_UP_POPUP_STEPS,
                fade_steps=BATCH_LEVEL_UP_POPUP_FADE_STEPS,
                particle_count=0,
                stack=False
            ))

        self.play_level_up_batch_particles(events, popup_boxes)

    def play_level_up_animation(self, event, x=None, y=None, duration_steps=LEVEL_UP_POPUP_STEPS, fade_steps=LEVEL_UP_POPUP_FADE_STEPS, particle_count=64, stack=True):
        """Shows a delayed, extra-bright level-up celebration."""
        if not self.animations_enabled:
            return

        cx, cy = self.get_center()
        x = cx if x is None else x
        y = cy + 55 if y is None else y
        attr = event["attribute"]
        level = event["level"]

        popup_box = self.play_floating_text(
            f"{attr} leveled up {level}",
            "#B48EAD",
            x,
            y,
            size=28,
            shake=True,
            duration_steps=duration_steps,
            fade_steps=fade_steps,
            trailing_icon=self.create_level_up_arrow_icon("#FF9E00"),
            stack=stack
        )
        if particle_count > 0:
            self.play_firework_particles(self.attr_colors[attr], popup_box, count=particle_count, rainbow=True, life_range=(78, 104), fade_start_ratio=0.52)
        return popup_box

    def play_level_up_batch_particles(self, events, popup_boxes):
        """Creates one shared particle burst around the full batch of level-up popups."""
        if not popup_boxes:
            return

        left = min(box["x"] - (box["width"] / 2) for box in popup_boxes)
        right = max(box["x"] + (box["width"] / 2) for box in popup_boxes)
        top = min(box["y"] - (box["height"] / 2) for box in popup_boxes)
        bottom = max(box["y"] + (box["height"] / 2) for box in popup_boxes)
        source_box = {
            "x": int((left + right) / 2),
            "y": int((top + bottom) / 2),
            "width": int(right - left),
            "height": int(bottom - top),
        }
        palette = [self.attr_colors[event["attribute"]] for event in events]
        palette.extend(["#EBCB8B", "#FFD166", "#ECEFF4"])
        self.play_firework_particles(
            "#B48EAD",
            source_box,
            count=max(72, min(120, 42 + (len(events) * 22))),
            palette=palette,
            life_range=(86, 112),
            fade_start_ratio=0.54
        )

    def play_rank_up_animation(self, rank_event):
        """Animates account rank-ups directly on the header avatar and text."""
        if not self.animations_enabled:
            return

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
        roman = rank_event.get("roman", title.rsplit(" ", 1)[-1])
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
            try:
                widgets_alive = (
                    self.root.winfo_exists()
                    and self.app_title_label.winfo_exists()
                    and self.app_level_delta_label.winfo_exists()
                    and self.user_name_label.winfo_exists()
                    and self.user_level_label.winfo_exists()
                )
            except tk.TclError:
                return
            if not widgets_alive:
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
                    roman=roman,
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
            self.update_avatar(tier_index, color, progress, roman=roman)

        animate()

    def play_trophy_animation_at_center(self, trophy_name):
        """Positions trophy rewards near the center reward stack."""
        cx, cy = self.get_center()
        self.play_trophy_animation(trophy_name, cx, cy + 112)

    def play_trophy_animation(self, trophy_name, x, y):
        """Shows a trophy reward after the level-up burst."""
        if not self.animations_enabled:
            return

        popup_box = self.play_floating_text(f"🏆 {trophy_name.upper()} EARNED! 🏆", "#EBCB8B", x, y, size=25, duration_steps=TROPHY_POPUP_STEPS, fade_steps=TROPHY_POPUP_FADE_STEPS)
        # Trophy rewards use the same box-anchored particle engine as level-ups so
        # their sparks share one steadier loop instead of the older point burst.
        self.play_firework_particles(
            "#EBCB8B",
            popup_box,
            count=64,
            palette=["#EBCB8B", "#FFD166", "#F59E0B", "#FFF4A3", "#ECEFF4"],
            physics=True,
            life_range=(50, 72),
            fade_start_ratio=0.44
        )

    def acquire_particle_widget(self, color, size):
        """Returns a reusable particle widget plus its current ownership token."""
        self.particle_widget_token += 1
        token = self.particle_widget_token

        if self.particle_widget_pool:
            widget = self.particle_widget_pool.pop()
            widget.configure(bg=color, width=size, height=size)
        else:
            widget = tk.Frame(self.root, bg=color, width=size, height=size)

        widget._lifexp_particle_token = token
        self.register_particle_widget(widget)
        self.root.after(PARTICLE_HARD_LIFETIME_MS, lambda w=widget, t=token: self.release_particle_widget(w, t))
        return widget, token

    def register_particle_widget(self, widget):
        """Tracks live particle widgets and caps burst load during rapid rewards."""
        if widget not in self.active_particle_widgets:
            self.active_particle_widgets.append(widget)
        while len(self.active_particle_widgets) > MAX_ACTIVE_PARTICLES:
            old_widget = self.active_particle_widgets.pop(0)
            self.release_particle_widget(old_widget)

    def release_particle_widget(self, widget, token=None):
        """Hides a particle widget and returns it to the reusable pool."""
        if token is not None and getattr(widget, "_lifexp_particle_token", None) != token:
            return
        if widget in self.active_particle_widgets:
            self.active_particle_widgets.remove(widget)
        if widget.winfo_exists():
            widget.place_forget()
            widget._lifexp_particle_token = None
            if len(self.particle_widget_pool) < MAX_ACTIVE_PARTICLES:
                self.particle_widget_pool.append(widget)
            else:
                widget.destroy()

    def destroy_particle_widget(self, widget, token=None):
        """Compatibility wrapper for particle cleanup."""
        self.release_particle_widget(widget, token)

    def play_floating_text(self, text, color, x, y, size=18, shake=False, duration_steps=70, fade_steps=20, trailing_icon=None, stack=True):
        """Creates retro text that pops, floats upwards, and fades out."""
        root_w = self.root.winfo_width() if self.root.winfo_width() > 1 else 850
        root_h = self.root.winfo_height() if self.root.winfo_height() > 1 else 700
        x = int(round(x))
        y = int(round(y))
        if not self.animations_enabled or not self.popups_enabled:
            return {
                "x": max(0, min(x, root_w)),
                "y": max(0, min(y, root_h)),
                "width": max(80, self.ui_space(160)),
                "height": max(34, self.ui_space(56))
            }

        # Floating feedback is shown in a tiny borderless Toplevel window. Toplevel
        # supports transparency, so the popup can feel lighter than a normal widget.
        if stack:
            self.popup_sequence = (self.popup_sequence + 1) % 5
            stack_offset = ((self.popup_sequence - 1) % 5) * 34
        else:
            stack_offset = 0
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
        safe_x = int(round(safe_x))
        safe_y = int(round(safe_y))
        popup.geometry(f"+{int(root_x + safe_x - popup_w // 2)}+{int(root_y + safe_y - popup_h // 2)}")

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
            try:
                if not popup.winfo_exists():
                    return
            except tk.TclError:
                return
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
                safe_x = int(round(safe_x))
                safe_current_y = int(round(safe_current_y))
                popup.geometry(f"+{int(root_x + safe_x - new_w // 2 + dx)}+{int(root_y + safe_current_y - new_h // 2 + dy)}")
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
        if not self.animations_enabled or not self.popups_enabled or not self.particles_enabled:
            return

        # This is separate from play_particles() because it starts from the popup box
        # instead of a single point. One combined loop per popup keeps frame rate stable.
        # Parameters:
        # - count controls how many spark widgets are created.
        # - palette overrides the colors, useful for gold/orange XP rewards.
        # - physics adds stronger downward gravity for XP-style falling sparks.
        # - life_range controls how long particles remain alive.
        # - fade_start_ratio controls how late the slow fade begins.
        particles = []
        max_frames = max(1, min(max(life_range) + 2, PARTICLE_HARD_LIFETIME_MS // 20))
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

            particle, token = self.acquire_particle_widget(p_color, size)
            particle.place(x=start_x, y=start_y)

            particles.append({
                "widget": particle,
                "token": token,
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
            if frame_count[0] >= max_frames:
                for particle in particles:
                    self.destroy_particle_widget(particle["widget"], particle["token"])
                return

            if frame_count[0] % 10 == 0:
                measured_w = self.root.winfo_width()
                measured_h = self.root.winfo_height()
                root_w = measured_w if measured_w > 1 else 850
                root_h = measured_h if measured_h > 1 else 700

            for particle in particles:
                if particle["life"] > 0:
                    widget = particle["widget"]
                    if (
                        not widget.winfo_exists()
                        or getattr(widget, "_lifexp_particle_token", None) != particle["token"]
                    ):
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
                        if fade_ratio >= PARTICLE_FADE_RELEASE_RATIO:
                            self.destroy_particle_widget(widget, particle["token"])
                            particle["life"] = -1
                            continue
                        widget.configure(bg=self._blend_color(particle["color"], self.bg_dark, self.ease_smoothstep(fade_ratio)))
                    particle["fade_tick"] += 1

                    widget.place(x=next_x, y=next_y)
                    particle["life"] -= 1
                    active = True
                elif particle["life"] == 0:
                    self.destroy_particle_widget(particle["widget"], particle["token"])
                    particle["life"] -= 1

            if active:
                self.root.after(20, animate)
            else:
                for particle in particles:
                    self.destroy_particle_widget(particle["widget"], particle["token"])

        animate()

    def play_particles(self, color, x, y, count=15, gravity=True, rainbow=False):
        """Spawns tiny squares that explode outward."""
        if not self.animations_enabled:
            return

        # Particles are tiny Frame widgets with random direction and lifetime. The list
        # keeps their widget, velocity, and remaining life together.
        particles = []
        max_frames = 36
        rainbow_colors = ["#BF616A", "#D08770", "#EBCB8B", "#A3BE8C", "#B48EAD", "#88C0D0", "#ECEFF4"]

        # This loop creates all particles at the starting point. Random dx/dy values make
        # each particle travel in a slightly different direction.
        root_w = self.root.winfo_width() if self.root.winfo_width() > 1 else 850
        root_h = self.root.winfo_height() if self.root.winfo_height() > 1 else 700
        start_x = max(0, min(x, root_w - 8))
        start_y = max(0, min(y, root_h - 8))

        for _ in range(count):
            p_color = random.choice(rainbow_colors) if rainbow else color
            p, token = self.acquire_particle_widget(p_color, 8)
            p.place(x=start_x, y=start_y)

            dx = random.randint(-12, 12)
            dy = random.randint(-12, 12)
            particles.append({
                "widget": p,
                "token": token,
                "x": start_x,
                "y": start_y,
                "dx": dx,
                "dy": dy,
                "life": random.randint(20, 32)
            })

        # The particle animation moves living particles, applies gravity if requested,
        # destroys expired particles, and repeats while anything is still active.
        frame_count = [0]

        def animate():
            nonlocal root_w, root_h
            active = False
            frame_count[0] += 1
            if frame_count[0] >= max_frames:
                for p in particles:
                    self.destroy_particle_widget(p["widget"], p["token"])
                return

            if frame_count[0] % 10 == 0:
                measured_w = self.root.winfo_width()
                measured_h = self.root.winfo_height()
                root_w = measured_w if measured_w > 1 else 850
                root_h = measured_h if measured_h > 1 else 700

            for p in particles:
                if p["life"] > 0:
                    w = p["widget"]
                    if (
                        not w.winfo_exists()
                        or getattr(w, "_lifexp_particle_token", None) != p["token"]
                    ):
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
                    self.destroy_particle_widget(p["widget"], p["token"])
                    p["life"] -= 1

            if active:
                self.root.after(35, animate)
            else:
                for p in particles:
                    self.destroy_particle_widget(p["widget"], p["token"])

        animate()

