<div align="center">

<img width="850" height="450" alt="image" src="https://github.com/user-attachments/assets/d06b53dc-f0e4-46e1-a415-d7721a3fefb3" /><br>
**Advanced automation toolkit for keyboard, mouse, and screen interaction.**
</div>

---

## What is autoARC?

autoARC is a modular, production-grade automation toolkit designed for keyboard and mouse control. Built for tasks like preventing AFK kicks in games like VALORANT or CS:GO, automating repetitive typing, running timed key sequences, and simulating realistic human-like mouse movement — with **anti-detection jitter** baked in at every level.

No game files are modified. No server communication is touched. autoARC operates entirely at the OS input layer.

---

## Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **AutoTyper** | Clipboard-based message spammer — supports full Unicode, emoji, and special characters |
| 2 | **Anti-AFK Movement** | Randomised WASD keypresses with configurable weapon key cycling |
| 3 | **Mouse Simulation** | Smooth random mouse movement across the screen using easeInOutQuad curves |
| 4 | **Screen Capture** | Screenshot + OpenCV edge analysis with brightness and RGB stats |
| 5 | **Timed Execution** | Run movement actions for a fixed duration with configurable intervals |
| 6 | **Custom Key Sequence** | Repeat any validated key combo N times with per-key jitter |
| 7 | **360° Mouse Path** | True smooth circular mouse movement — incremental angle, not random scatter |
| 8 | **Auto-Clicker** | Single / double / burst / hold modes with CPS limiter and session stats |
| 9 | **Discord Webhook** | Optional real-time notifications to your Discord channel |

### Safety & Anti-Detection
- **Jitter on every action** — all timing values carry random variance so no two inputs are identical
- **F8 pause/resume** — suspend any running task without killing the script
- **Emergency stop** — move mouse to the top-left corner at any time to abort instantly
- **Zero recursion** — clean loop architecture, no stack overflow on long sessions

---

## Project Structure

```
autoARC/
├── main.py                       ← Entry point
├── install.bat                   ← One-click dependency installer (Windows)
├── start.bat                     ← Start the program 
├── requirements.txt              ← pip install list
│
├── core/
│   ├── utils.py                  ← Jitter, input helpers, pause state
│   ├── display.py                ← Loading screen, menu, UI rendering
│   └── webhook.py                ← Discord webhook notification engine
│
└── features/
    ├── autotyper.py              ← [1] Unicode message spammer
    ├── automove.py               ← [2] Anti-AFK WASD movement
    ├── mouse_simulation.py       ← [3] Random mouse movement
    ├── screen_capture.py         ← [4] Screenshot + OpenCV analysis
    ├── timed_execution.py        ← [5] Timed movement execution
    ├── custom_key_sequence.py    ← [6] Validated key combo repeater
    ├── mouse_360.py              ← [7] Smooth circular mouse path
    ├── auto_clicker.py           ← [8] Multi-mode auto clicker
    └── webhook_settings.py       ← [9] Discord webhook setup UI
```

---

## Installation

### Windows — one click

Double-click **`install.bat`**. It will verify Python, upgrade pip, and install every dependency automatically.

### Manual — any platform

```bash
pip install -r requirements.txt
```

**Dependencies:**

| Package | Purpose |
|---|---|
| `pyautogui` | Mouse and keyboard automation |
| `pyperclip` | Clipboard access for Unicode typer |
| `colorama` | Colored terminal output |
| `pyfiglet` | ASCII art banner |
| `opencv-python` | Screen capture and image analysis |
| `numpy` | Required by OpenCV |
| `keyboard` | F8 pause/resume hotkey listener |

> `keyboard` is optional — without it, F8 is silently disabled. On Linux it may require `sudo`.

---

## Running

```bash
python main.py
```

On first launch you'll be asked whether to set up a Discord webhook for notifications — completely optional and skippable. After that the main menu appears.

---

## Discord Webhook (optional)

autoARC sends real-time embeds to a Discord channel on every key event — session start/end, feature start/done, errors, FailSafe triggers, interrupts.

**Setup:**
1. Discord → any channel → **Settings → Integrations → Webhooks → New Webhook**
2. Copy the webhook URL
3. In autoARC choose **[9]**, or say `y` at the first-launch prompt

---

## Adding a New Feature?

1. Create `features/my_feature.py` with a `def run() -> None:` function
2. Add it to `FEATURE_MAP` in `features/__init__.py`
3. Add a row to `MENU_ITEMS` in `core/display.py`

`main.py` never needs to be touched.

---

## Is it detectable?

autoARC operates purely at the OS input layer — it sends the same signals as a physical keyboard and mouse. It makes no changes to game files, memory, or network traffic. Anti-detection jitter ensures no two actions share the same timing fingerprint.

---

<div align="center">

If autoARC is useful to you, consider leaving a ⭐ on the repository.

*Made by [volksgeistt](https://github.com/volksgeistt)*

</div>
