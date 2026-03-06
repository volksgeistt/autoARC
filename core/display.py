import os
import re
import time
import pyfiglet
from colorama import Fore, Style

AUTHOR = "volksgeistt"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)

def terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 100

def center(text: str) -> str:
    visible = len(_strip_ansi(text))
    pad     = max(0, (terminal_width() - visible) // 2)
    return " " * pad + text

def _center_plain(text: str) -> str:
    return text.center(terminal_width())

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def loading_screen() -> None:
    clear()
    title = pyfiglet.figlet_format("Auto ARC", font="slant")
    for line in title.split("\n"):
        print(Fore.CYAN + Style.BRIGHT + _center_plain(line))
        time.sleep(0.06)

    print()
    print(Fore.YELLOW + Style.BRIGHT + _center_plain(f"Developed by {AUTHOR}"))
    print(Fore.YELLOW + Style.BRIGHT + _center_plain(f"github.com/{AUTHOR}"))
    print(Fore.GREEN  + Style.BRIGHT + _center_plain("Support: unrealvolksgeist@gmail.com"))
    print()
    print(Fore.MAGENTA + Style.BRIGHT + _center_plain(
        "Anti-detection jitter active  |  F8 = Pause/Resume  |  TOP-LEFT = Emergency Stop"
    ))
    print()

    total = 24
    for i in range(total + 1):
        bar = f"[{'█' * i}{'░' * (total - i)}]  {int(i / total * 100)}%"
        print(Fore.CYAN + Style.BRIGHT + _center_plain(bar), end="\r")
        time.sleep(0.055)

    print(Fore.GREEN + Style.BRIGHT + _center_plain(f"[{'█' * total}]  100% — Ready!   "))
    time.sleep(0.7)


MENU_ITEMS = [
    ("1", "AutoTyper",           "Unicode message spammer via clipboard"),
    ("2", "Anti-AFK Movement",   "Random WASD to prevent idle kicks"),
    ("3", "Mouse Simulation",    "Random mouse movement across screen"),
    ("4", "Screen Capture",      "Screenshot + OpenCV edge analysis"),
    ("5", "Timed Execution",     "Movement actions for a fixed duration"),
    ("6", "Custom Key Sequence", "Repeat any validated key combo"),
    ("7", "360° Mouse Path",     "Smooth circular mouse movement"),
    ("8", "Auto-Clicker",        "Burst / single / double / hold + CPS"),
    ("9", "Discord Webhook",     "Notifications to your Discord channel"),
    ("0", "Exit",                "Quit Auto ARC"),
]

_LABEL_W = 22   
_DESC_W  = 40   
_BOX_W   = 71
_INNER_W = _BOX_W - 4  


def _menu_row(key: str, label: str, desc: str) -> str:
    """Return one colored, fixed-width menu row (no border)."""
    if key == "0":
        kc = Fore.RED   + Style.BRIGHT
        lc = Fore.RED   + Style.BRIGHT
    elif key == "9":
        kc = Fore.YELLOW + Style.BRIGHT
        lc = Fore.YELLOW
    else:
        kc = Fore.CYAN  + Style.BRIGHT
        lc = Fore.WHITE + Style.BRIGHT

    key_part   = f"{kc}[{key}]{Style.RESET_ALL}"
    label_part = f"{lc}{label:<{_LABEL_W}}{Style.RESET_ALL}"
    desc_part  = f"{Fore.LIGHTBLACK_EX}{desc}{Style.RESET_ALL}"
    return f"{key_part}  {label_part}   {desc_part}"


def _boxed(row_content: str) -> str:
    """Wrap a colored row inside ║ … ║, padding to _BOX_W exactly."""
    visible_len = len(_strip_ansi(row_content))
    padding     = max(0, _INNER_W - visible_len)
    return (
        f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}"
        f" {row_content}{' ' * padding} "
        f"{Fore.CYAN}{Style.BRIGHT}║"
    )



def display_menu() -> None:
    from core import webhook as _wh

    clear()

    title = pyfiglet.figlet_format("Auto ARC", font="slant")
    for line in title.split("\n"):
        print(Fore.CYAN + Style.BRIGHT + _center_plain(line))

    print()
    print(center(
        f"{Fore.YELLOW}{Style.BRIGHT}dev @ {AUTHOR}"
        f"{Fore.LIGHTBLACK_EX}  ·  "
        f"{Fore.YELLOW}{Style.BRIGHT}github.com/{AUTHOR}"
    ))
    print(center(
        f"{Fore.MAGENTA}F8{Fore.LIGHTBLACK_EX} = Pause/Resume"
        f"  ·  "
        f"{Fore.MAGENTA}Top-Left{Fore.LIGHTBLACK_EX} = Emergency Stop"
    ))

    if _wh.is_enabled():
        badge = (
            f"{Fore.GREEN}{Style.BRIGHT}●{Style.RESET_ALL}"
            f"{Fore.GREEN} Discord Webhook"
            f"{Fore.LIGHTBLACK_EX}  ENABLED"
        )
    else:
        badge = (
            f"{Fore.LIGHTBLACK_EX}○ Discord Webhook  disabled"
            f"  {Fore.YELLOW}→ [9] to configure"
        )
    print(center(badge))
    print()

    TOP = f"{Fore.CYAN}{Style.BRIGHT}╔{'═' * (_BOX_W - 2)}╗"
    BOT = f"{Fore.CYAN}{Style.BRIGHT}╚{'═' * (_BOX_W - 2)}╝"
    SEP = f"{Fore.CYAN}{Style.BRIGHT}╠{'─' * (_BOX_W - 2)}╣"

    hdr_content = (
        f"  {Fore.CYAN}{Style.BRIGHT}{'#':<3}"
        f"  {Fore.WHITE}{Style.BRIGHT}{'FEATURE':<{_LABEL_W}}"
        f"   {Fore.LIGHTBLACK_EX}DESCRIPTION"
    )

    print(center(TOP))
    print(center(_boxed(hdr_content)))
    print(center(SEP))

    for key, label, desc in MENU_ITEMS:
        print(center(_boxed(_menu_row(key, label, desc))))
        if key == "8":
            print(center(SEP))  

    print(center(BOT))
    print()


def section_header(title: str) -> None:
    bar = "─" * min(50, terminal_width() - 4)
    print()
    print(center(Fore.CYAN + Style.BRIGHT + bar))
    print(center(Fore.CYAN + Style.BRIGHT + f"  {title}  "))
    print(center(Fore.CYAN + Style.BRIGHT + bar))
    print()

def success(msg: str) -> None:
    print(Fore.GREEN  + Style.BRIGHT + f"  ✓  {msg}" + Style.RESET_ALL)

def warn(msg: str) -> None:
    print(Fore.YELLOW + Style.BRIGHT + f"  ⚠  {msg}" + Style.RESET_ALL)

def error(msg: str) -> None:
    print(Fore.RED    + Style.BRIGHT + f"  ✗  {msg}" + Style.RESET_ALL)

def info(msg: str) -> None:
    print(Fore.CYAN   +               f"  ·  {msg}" + Style.RESET_ALL)