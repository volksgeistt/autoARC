<div align="center">
<img width="1810" height="869" alt="image" src="https://github.com/user-attachments/assets/50e5c5af-930f-45f3-9439-d7a4a6978b10" />
<br>
  
**Advanced automation toolkit for keyboard, mouse, and screen interaction.**
</div>

---
# autoARC

A modular, production-grade automation toolkit for keyboard and mouse control. Built for preventing AFK kicks in games like VALORANT or CS:GO, automating repetitive typing, running timed key sequences, simulating realistic human-like mouse movement — with **anti-detection jitter** baked in at every level.

No game files are modified. No server communication is touched. autoARC operates entirely at the OS input layer.

---

## Features

### Automation

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

### Monitoring Suite

| # | Feature | Description |
|---|---------|-------------|
| 10 | **SysSentinel** | Real-time CPU, RAM, GPU temp/load, Disk I/O, and Network I/O monitor with configurable alert rules and optional process kill on threshold breach |
| 11 | **NetWatch** | Live ping graph to custom hosts, packet loss detection, bandwidth usage, and Discord alerts when a host goes down |

### Configuration & Notifications

| # | Feature | Description |
|---|---------|-------------|
| 9 | **Discord Webhook** | Optional real-time embeds to your Discord channel on every key event |

---

## Monitoring Config — `sentinel_config.json`

All monitoring thresholds and defaults are driven by a single JSON file at the project root — **no Python editing required** to tune the monitoring suite.

```json
{
  "shared": {
    "sample_interval_sec": 1.0,
    "history_len": 60
  },
  "sys_sentinel": {},
  "net_watch": {
    "ping_timeout_sec": 3.0,
    "loss_alert_threshold": 20.0,
    "down_hold_consecutive": 5,
    "default_hosts": [
      { "ip": "8.8.8.8", "label": "Google DNS" },
      { "ip": "1.1.1.1", "label": "Cloudflare" }
    ]
  }
}
```

The config is loaded once at startup via `features/sentinel_cfg.py` into typed dataclass objects. If the file is missing, all values fall back to safe built-in defaults — the app never crashes over a bad config.

---

## SysSentinel

Watches the whole machine in real time with a live terminal dashboard:

- **CPU** — usage % with sparkline trend
- **RAM** — usage % + used / total GB
- **GPU** — temperature + load % + VRAM used/total (NVIDIA via `pynvml`, AMD/Intel via WMI on Windows, `lspci` on Linux)
- **Disk I/O** — read / write MB/s with sparkline
- **Network I/O** — recv / send KB/s with sparkline
- **System Specs panel** — OS, CPU name / cores / threads / max frequency, RAM total, GPU name / VRAM / driver, disk total / free — shown at the top of the dashboard on every refresh

**Alert rules** — set a threshold (e.g. CPU > 90%) and a hold duration (e.g. 10s). If the metric stays breached for that long, a Discord webhook fires. Optionally specify a process name to kill automatically when the rule fires.

GPU detection priority:
1. `pynvml` — NVIDIA Management Library (temp, load, VRAM used, driver)
2. `wmi` Win32_VideoController — AMD / Intel on Windows (name, VRAM, driver)
3. OpenHardwareMonitor WMI namespace — real-time temp + load for any GPU if OHM is running
4. `lspci` — Linux fallback (name, vendor inference)

---

## NetWatch

Monitors network health in real time:

- **ICMP ping** to each host — raw socket first, OS `ping` fallback if permissions are denied
- **RTT bar** per host — color-coded green / yellow / red by latency
- **Sparkline trend** — 60-sample rolling RTT history per host
- **Packet loss %** — rolling average, alert fires when it crosses your configured threshold
- **Bandwidth** — system-wide recv / send KB/s via psutil
- **Host-down alert** — fires after N consecutive timeouts (configurable in JSON), sends Discord embed

Default hosts (Google DNS, Cloudflare, Quad9, OpenDNS) and all thresholds come from `sentinel_config.json`.

---

## Safety & Anti-Detection

- **Jitter on every action** — all timing values carry random variance so no two inputs are identical
- **F8 pause/resume** — suspend any running task without killing the script
- **Emergency stop** — move the mouse to the top-left corner at any time to abort instantly (pyautogui FailSafe)
- **Zero recursion** — clean loop architecture, no stack overflow on long sessions

---

## Project Structure

```
autoARC/
├── main.py                       ← Entry point
├── install.bat                   ← One-click dependency installer (Windows)
├── start.bat                     ← Launches with correct terminal size (120×36)
├── sentinel_config.json          ← Monitoring thresholds & defaults (edit freely)
│
├── core/
│   ├── utils.py                  ← Jitter, input helpers, pause state, F8 listener
│   ├── display.py                ← Loading screen, menu, UI rendering, terminal resize
│   └── webhook.py                ← Discord webhook notification engine
│
└── features/
    ├── __init__.py               ← FEATURE_MAP — registers all features
    ├── sentinel_cfg.py           ← Typed config loader for sentinel_config.json
    │
    ├── autotyper.py              ← [1]  Unicode message spammer
    ├── automove.py               ← [2]  Anti-AFK WASD movement
    ├── mouse_simulation.py       ← [3]  Random mouse movement
    ├── screen_capture.py         ← [4]  Screenshot + OpenCV analysis
    ├── timed_execution.py        ← [5]  Timed movement execution
    ├── custom_key_sequence.py    ← [6]  Validated key combo repeater
    ├── mouse_360.py              ← [7]  Smooth circular mouse path
    ├── auto_clicker.py           ← [8]  Multi-mode auto clicker
    ├── webhook_settings.py       ← [9]  Discord webhook setup UI
    ├── sys_sentinel.py           ← [10] System monitor + alerter
    └── net_watch.py              ← [11] Network monitor + alerter
```

---

## Installation

### Windows — one click

Double-click **`install.bat`**. It will verify Python, upgrade pip, and install every dependency automatically.

### Manual — any platform

```bash
pip install -r requirements.txt
```

**Core dependencies:**

| Package | Purpose |
|---|---|
| `pyautogui` | Mouse and keyboard automation |
| `pyperclip` | Clipboard access for Unicode typer |
| `colorama` | Colored terminal output |
| `pyfiglet` | ASCII art banner |
| `opencv-python` | Screen capture and image analysis |
| `numpy` | Required by OpenCV |
| `keyboard` | F8 pause/resume hotkey listener |
| `psutil` | System stats for SysSentinel and NetWatch (auto-installed on first run if missing) |

**Optional — enhanced GPU monitoring:**

| Package | Purpose |
|---|---|
| `pynvml` | NVIDIA GPU temperature, load, and VRAM (recommended for NVIDIA users) |
| `pywin32` | WMI access for AMD/Intel GPU info on Windows |

> `keyboard` may require `sudo` on Linux. `pynvml` requires an NVIDIA GPU and driver. Without optional packages, features degrade gracefully — the app always runs.

---

## Running

```bash
# Recommended — sets terminal to 120×36 automatically
start.bat

# Or directly
python main.py
```

On first launch you'll be asked whether to set up a Discord webhook — completely optional and skippable. After that the main menu appears.

---

## Discord Webhook (optional)

autoARC sends real-time embeds to a Discord channel on every key event:

- Session start / end
- Feature start / done
- Errors and exceptions
- FailSafe emergency stop
- Keyboard interrupt
- SysSentinel alert rule triggers
- NetWatch host-down and packet loss alerts

**Setup:**
1. Discord → any channel → **Settings → Integrations → Webhooks → New Webhook**
2. Copy the webhook URL
3. In autoARC choose **[9]**, or say `y` at the first-launch prompt

---

## Adding a New Feature

1. Create `features/my_feature.py` with a `def run() -> None:` function
2. Register it in `features/__init__.py` → `FEATURE_MAP`
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
