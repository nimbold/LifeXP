# LifeXP

LifeXP is a small Python Tkinter desktop app that turns everyday tasks into RPG-style progress.

You create quests, complete them for XP, level up five attributes, unlock trophies, and review your activity in Chronicles.

## What It Does

- Manage active quests in the Quest Log.
- Add one quest or queue several quests at once.
- Multi-select active quests to complete, edit, or abandon them together.
- Give each quest an attribute and XP reward.
- Level up Strength, Agility, Intelligence, Charisma, and Vitality.
- Use Elden Ring-inspired XP scaling for attributes and total character level.
- Show total account rank, title, avatar ring, and XP-to-next-rank.
- Animate account rank-ups in the header with a glowing ring and level text.
- Unlock trophy milestones at attribute levels 5, 10, 25, 50, and 100.
- Draw responsive trophy art with attribute symbols, disabled locked states, and upgraded tier visuals.
- Use cleaner navigation icons for the three main tabs.
- Show daily, weekly, and monthly activity reports.
- Save progress locally in `lifexp_data.json`.
- Support multiple color themes from Settings.

## Screens

- `Quest Log`: add, batch edit, complete, or abandon quests.
- `Character Info`: view attributes, XP bars, total rank, and responsive trophies.
- `Chronicles`: review completed activity by day, week, or month.
- `Settings`: change theme, reset progress, and view app info.

## Run

Requirements:

- Python 3
- Tkinter, usually included with Python

Start the app:

```bash
python3 main.py
```

## Files

```text
main.py              Main app code
README.md            Project overview
BEGINNER_GUIDE.md    Short guide for learning the code
```

LifeXP creates `lifexp_data.json` automatically when you use the app. It stores your tasks, levels, history, trophies, theme, and custom activity names. The file is ignored by Git because it is personal local progress, not source code.

The app normalizes older saved activity suggestions when it loads. For example, close duplicates like separate reading or meal-prep activities can be merged into cleaner names.

## Learning Focus

This project is useful for learning:

- Tkinter widgets, layout, and callbacks
- Saving and loading JSON
- Dictionaries and lists as app data
- Object-oriented programming with one main class
- XP and level calculations
- Canvas drawing for trophies, icons, progress rings, and effects
- Batch actions and multi-selection in Tkinter
- Small animations with `root.after(...)`

Start with [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) if you are new to the code.

## Version

```text
1.01
```
