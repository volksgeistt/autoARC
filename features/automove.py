import logging
import random
import time
import pyautogui
from colorama import Fore

from core import (
    ask, validate_keys, jitter, jitter_sleep,
    wait_if_paused, countdown,
    success, warn, info, section_header,
)

log = logging.getLogger(__name__)

MOVE_KEYS = ["w", "s", "a", "d"]


def run() -> None:
    section_header("Anti-AFK Movement")
    log.info("Anti-AFK movement started")

    raw = ask("Weapon/action keys to cycle (comma-separated, e.g. 2,3,4,e  — leave blank to skip)")
    weapon_keys, invalid = validate_keys(
        [k.strip().lower() for k in raw.split(",") if k.strip()]
    )
    if invalid:
        warn(f"Skipping unrecognised keys: {', '.join(invalid)}")
    if weapon_keys:
        info(f"Weapon keys: {', '.join(weapon_keys)}")
    else:
        info("No weapon keys configured — movement only.")

    warn("Switch to your target window now.")
    countdown(5)

    move_count   = 0
    switch_count = 0
    print(Fore.GREEN + "  Anti-AFK running — F8 to pause, Ctrl+C to stop.\n")

    while True:
        wait_if_paused()

        key  = random.choice(MOVE_KEYS)
        hold = jitter(0.2, 0.08)
        pyautogui.keyDown(key)
        time.sleep(hold)
        pyautogui.keyUp(key)
        move_count += 1

        if weapon_keys and random.random() < 0.4:
            wkey = random.choice(weapon_keys)
            jitter_sleep(0.05, 0.02)
            pyautogui.press(wkey)
            switch_count += 1

        log.debug(f"Moves={move_count}  Switches={switch_count}  last_key={key}")
        jitter_sleep(0.5, 0.15)
