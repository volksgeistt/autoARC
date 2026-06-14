import logging
import pyautogui
from colorama import Fore

from core import (
    ask, ask_int, validate_keys,
    jitter_sleep, wait_if_paused,
    countdown, success, warn, error, info, section_header,
)

log = logging.getLogger(__name__)


def run() -> None:
    section_header("Custom Key Sequence")
    log.info("Custom key sequence started")

    while True:
        raw  = ask("Key sequence (comma-separated, e.g. w,a,s,d,space,ctrl,f)")
        keys = [k.strip().lower() for k in raw.split(",") if k.strip()]

        valid, invalid = validate_keys(keys)

        if invalid:
            error(f"Unrecognised key(s): {', '.join(invalid)}")
            info("Examples: w  a  s  d  space  ctrl  shift  enter  tab  f1…f12  1…9  backspace")
            retry = ask("Re-enter sequence? (y/n)")
            if retry.lower() != "y":
                return
            continue
        break

    repetitions = ask_int("Number of repetitions", min_val=1)

    warn("Switch to your target window now.")
    countdown(7)

    for rep in range(repetitions):
        wait_if_paused()
        for key in valid:
            wait_if_paused()
            pyautogui.press(key)
            log.debug(f"Rep {rep + 1}/{repetitions} — pressed '{key}'")
            jitter_sleep(0.1, 0.04)
        jitter_sleep(0.2, 0.06)

    success(f"Custom key sequence complete — {repetitions} repetition(s), {len(valid)} keys each.")
    log.info(f"Key sequence done. Reps={repetitions}, Keys={valid}")
