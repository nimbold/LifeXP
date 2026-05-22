# LifeXP

LifeXP is a Python Tkinter desktop app that turns everyday tasks into a small role-playing game. You accept quests, complete them for XP, level up five character attributes, unlock pixel trophies, and review your activity through daily, weekly, and monthly Chronicles.

This is also a first-project learning course. The code is intentionally commented in block-level notes so it explains how the app works without making every line unreadable.

## Features

- Quest Log for accepting, completing, editing, and abandoning quests.
- Autocomplete activity names built from default and previously used subcategories.
- Difficulty slider that converts everyday task difficulty into XP rewards.
- Five RPG attributes: Strength, Agility, Intelligence, Charisma, and Vitality.
- Attribute levels, total account level, rank titles, roman numerals, and avatar progress ring.
- Visual Trophy Room with pixel trophies for milestone levels.
- Chronicles page with daily, weekly, and monthly activity reports.
- Colored activity cards with XP totals and combo-style repeat counters.
- Settings page for themes, progress reset, and app information.
- Apple-inspired and developer/game-inspired themes, including Nord, Dracula, Catppuccin, Gruvbox, Tokyo Night, and Solarized Dark.
- Smooth RPG-style popup animations for XP, quest actions, level-ups, rank-ups, trophies, and particle bursts.
- Local JSON save file for progress, history, settings, tasks, trophies, and custom subcategories.
- Save-file migration logic for older attribute names and older subcategory lists.

## App Screens

- `Quest Log`: manage active quests and XP rewards.
- `Character Info`: inspect attribute levels, progress bars, trophies, account rank, and avatar art.
- `Chronicles`: review activity history by day, week, or month.
- `Settings`: change themes, reset progress, and view app version details.

## Requirements

- Python 3
- Tkinter, included with most standard Python installations

## Run The App

```bash
python3 main.py
```

The app saves progress in:

```text
lifexp_data.json
```

This file is normal app data. It changes when you complete quests, change themes, unlock trophies, or reset progress.

## Project Files

```text
main.py              Main Tkinter application
lifexp_data.json     Local save data
README.md            Project overview
```

## Learning Goals

This project is useful for practicing:

- Object-oriented programming with a main app class
- Event-driven UI programming with Tkinter
- Saving and loading structured data with JSON
- Separating UI setup, data management, game logic, and animation logic
- Designing small reusable helpers for XP math, autocomplete, themes, and popup motion
- Using canvas drawing for pixel art, avatar icons, progress rings, trophies, and particles
- Iterating on design through small, visible improvements

## Current Version

```text
1.01
```

## About

LifeXP is built as both a personal productivity tool and a programming practice project. The app uses RPG feedback to make repeated daily effort visible: quests become XP, XP becomes attribute growth, and history becomes a record of what you actually spent time improving.

The project is intentionally kept small, readable, and heavily commented so each feature can teach a practical programming idea without hiding the logic behind a large framework.
