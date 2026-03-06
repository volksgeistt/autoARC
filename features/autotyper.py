import logging
import time
import pyautogui
import pyperclip
from colorama import Fore

from core import ask, ask_int, ask_float, jitter_sleep, wait_if_paused, countdown, success, warn, section_header

log = logging.getLogger(__name__)


def run() -> None:
    section_header("AutoTyper")
    log.info("AutoTyper started")

    message  = ask("Message to spam (supports Unicode / emoji)")
    count    = ask_int("Number of times to send", min_val=1)
    interval = ask_float("Interval between sends (seconds, e.g. 1.0)", min_val=0.0)

    warn("Switch to your target window now.")
    countdown(5)

    original_clipboard = ""
    try:
        original_clipboard = pyperclip.paste()
    except Exception:
        pass

    sent = 0
    try:
        for i in range(count):
            wait_if_paused()
            pyperclip.copy(message)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(jitter_sleep.__wrapped__(0.05, 0.02) if hasattr(jitter_sleep, "__wrapped__") else 0.05)
            pyautogui.press("enter")
            sent += 1
            log.debug(f"Sent {sent}/{count}")
            jitter_sleep(interval, max(0.03, interval * 0.1))

        success(f"AutoTyper complete — {sent} message(s) sent.")
        log.info(f"AutoTyper done. Sent={sent}")
    finally:
        try:
            pyperclip.copy(original_clipboard)
        except Exception:
            pass
