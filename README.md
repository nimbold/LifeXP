# RPG Task Master

RPG Task Master is a Python Tkinter desktop app that turns everyday tasks into a small role-playing game. You add quests, complete them for XP, level up five character attributes, unlock visual trophies, and review your activity in daily, weekly, and monthly Chronicles.

This is also a first-project learning course. The code is intentionally commented in block-level notes so it explains how the app works without making every line unreadable.

## Features

- Quest Log for accepting, completing, editing, and abandoning quests
- Five RPG attributes: Strength, Agility, Intelligence, Charisma, and Constitution
- XP rewards, attribute levels, account rank titles, and trophy milestones
- Chronicles page with colored attribute cards and activity combo multipliers
- Theme settings with Apple-inspired and famous developer/game palettes
- Pixel-style visual identity with lightweight animations
- Local JSON save file for progress, history, settings, and task data

## Requirements

- Python 3
- Tkinter, included with most standard Python installations

## Run The App

```bash
python3 main.py
```

The app saves progress in:

```text
rpg_tasks_data.json
```

## Project Files

```text
main.py              Main Tkinter application
rpg_tasks_data.json  Local save data
README.md            Project overview
```

## Learning Goals

This project is useful for practicing:

- Object-oriented programming with a main app class
- Event-driven UI programming with Tkinter
- Saving and loading structured data with JSON
- Separating UI setup, data management, game logic, and animation logic
- Iterating on design through small, visible improvements

## Origin

The first version was generated with Gemini. It is now being reviewed, refactored, commented, and expanded as a hands-on programming learning project.
