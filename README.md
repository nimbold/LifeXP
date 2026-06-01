# 🎮 LifeXP

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)](https://github.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/nimbold/LifeXP/pulls)

LifeXP is a lightweight desktop productivity application that adds RPG-style character progression to your everyday tasks. Complete custom quests, earn experience points (XP) to level up core attributes, unlock trophy milestones, and track your long-term consistency through structured chronicles.

---

## 🖼️ Screens

| Quest Log | Character Info | Chronicles | Settings |
|:---:|:---:|:---:|:---:|
| <img src="screenshots/quest-log.png" alt="Quest Log" width="180"> | <img src="screenshots/character-info.png" alt="Character Info" width="180"> | <img src="screenshots/chronicles.png" alt="Chronicles" width="180"> | <img src="screenshots/settings.png" alt="Settings" width="180"> |

---

## ✨ Key Features

- **Progression System**: Link quests to 5 core attributes: *Strength*, *Agility*, *Intelligence*, *Charisma*, and *Vitality*.
- **Quest Log**: Batch add, edit, complete, or abandon active tasks.
- **Trophies**: Unlock milestone badges at levels 5, 10, 25, 50, and 100.
- **Chronicles**: Review productivity reports across daily, weekly, or monthly charts.
- **Customizable**: Choose UI themes (like *Tokyo Night*), toggle font sizes, and adjust canvas animations.
- **Local Storage**: Automatically manages secure state saving in a local `lifexp_data.json` file.

---

## 🚀 Quick Start

### Run the App
Make sure **Python 3** is installed. LifeXP uses `Tkinter` (built into Python):

```bash
# Clone and run
git clone https://github.com/nimbold/LifeXP.git
cd LifeXP
python3 main.py
```

### Syntax & Compile Check
To check the integrity of the codebase without launching the window:
```bash
python3 -m py_compile main.py lifexp/*.py
```

---

## 🛠️ Architecture Overview

The codebase is designed as a modular, package-based project utilizing a **multiple-inheritance Mixin pattern**:

- **`main.py`**: The application entry point and class initializer.
- **`lifexp/` package**:
  - `ui_mixin.py` – Layout structures, styling loops, and Tkinter UI widgets.
  - `data_mixin.py` – JSON persistent state reading, writing, and backup handling.
  - `engine_mixin.py` – Leveling curves, XP calculations, and growth reports.
  - `animation_mixin.py` – Canvas transitions, visual popups, and active particle effects.
  - `constants.py` & `runtime.py` – Shared configurations, scaling models, and paths.

Detailed code explanations and system diagrams are located in [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md).

---

## 📦 Packaging & CI/CD

An automated GitHub Actions workflow (`.github/workflows/build-macos.yml`) builds standalone, unsigned macOS ARM64 binaries (`LifeXP-macos-arm64-unsigned.zip`) using the PyInstaller configuration (`LifeXP.spec`).

---

## ❓ Frequently Asked Questions

<details>
<summary><b>🔒 Unsigned App Warning: "macOS cannot verify the developer"</b></summary>
<p>
Because the automated build artifact is unsigned, macOS may alert you. To bypass this:
<ol>
  <li>Go to <b>System Settings</b> > <b>Privacy & Security</b>.</li>
  <li>Scroll to the <b>Security</b> section.</li>
  <li>Click <b>Open Anyway</b> next to the LifeXP notice.</li>
</ol>
</p>
</details>

<details>
<summary><b>💾 Where is my progress saved?</b></summary>
<p>
Progress is saved automatically in JSON format:
<ul>
  <li><b>Standard Run:</b> Saved directly in <code>lifexp_data.json</code> in the workspace folder.</li>
  <li><b>Packaged App:</b> Saved in <code>~/Library/Application Support/LifeXP/lifexp_data.json</code>.</li>
</ul>
</p>
</details>

---

## 📄 License & Metadata

- **License**: MIT License. See [LICENSE](LICENSE) for details.
- **Version**: `1.0.4`
