import random
import time
import threading
import pyautogui
from colorama import Fore, Style

_paused      = False
_pause_lock  = threading.Lock()

VALID_KEYS   = set(pyautogui.KEYBOARD_KEYS)


def toggle_pause() -> None:
    global _paused
    with _pause_lock:
        _paused = not _paused
        state = "PAUSED  — press F8 to resume" if _paused else "RESUMED"
        symbol = "⏸" if _paused else "▶"
        print(Fore.YELLOW + Style.BRIGHT + f"\n  {symbol}  {state}\n")


def is_paused() -> bool:
    return _paused


def wait_if_paused() -> None:
    while _paused:
        time.sleep(0.1)


def start_pause_listener() -> threading.Thread:
    def _listen():
        try:
            import keyboard
            keyboard.add_hotkey("F8", toggle_pause)
            keyboard.wait()
        except Exception:
            pass

    t = threading.Thread(target=_listen, daemon=True)
    t.start()
    return t

def jitter(base: float, variance: float = 0.05) -> float:
    return max(0.0, base + random.uniform(-variance, variance))


def jitter_sleep(base: float, variance: float = 0.05) -> None:
    time.sleep(jitter(base, variance))


def ask(prompt: str) -> str:
    print(Fore.GREEN + Style.BRIGHT + prompt, end="")
    return input(f" :: {Fore.RESET}{Style.RESET_ALL}").strip()


def ask_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    while True:
        try:
            val = int(ask(prompt))
            if min_val is not None and val < min_val:
                print(Fore.RED + f"  ✗  Value must be ≥ {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(Fore.RED + f"  ✗  Value must be ≤ {max_val}")
                continue
            return val
        except ValueError:
            print(Fore.RED + "  ✗  Please enter a valid integer.")


def ask_float(prompt: str, min_val: float = None) -> float:
    while True:
        try:
            val = float(ask(prompt))
            if min_val is not None and val < min_val:
                print(Fore.RED + f"  ✗  Value must be ≥ {min_val}")
                continue
            return val
        except ValueError:
            print(Fore.RED + "  ✗  Please enter a valid number.")


def ask_choice(prompt: str, choices: list) -> str:
    choices_lower = [c.lower() for c in choices]
    while True:
        val = ask(f"{prompt} ({'/'.join(choices)})").lower()
        if val in choices_lower:
            return val
        print(Fore.RED + f"  ✗  Choose one of: {', '.join(choices)}")


def validate_keys(keys: list) -> tuple:
    valid   = [k for k in keys if k.lower() in VALID_KEYS]
    invalid = [k for k in keys if k.lower() not in VALID_KEYS]
    return valid, invalid

def countdown(seconds: int, message: str = "Starting in") -> None:
    for i in range(seconds, 0, -1):
        print(Fore.CYAN + f"  {message} {i}s...", end="\r")
        time.sleep(1)
    print(" " * 40, end="\r")
