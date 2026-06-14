import logging
import random
import time
import pyautogui

from core import ask_int, ask_float, jitter, jitter_sleep, wait_if_paused, countdown, success, warn, info, section_header

log = logging.getLogger(__name__)

MOVE_KEYS = ["w", "s", "a", "d"]


def run() -> None:
    section_header("Timed Execution")
    log.info("Timed execution started")

    duration = ask_int("Total run duration (seconds)", min_val=1)
    interval = ask_float("Pause between actions (seconds, e.g. 0.5)", min_val=0.05)

    warn("Switch to your target window now.")
    countdown(5)

    end_time   = time.time() + duration
    action_num = 0

    info(f"Running for {duration}s — F8 to pause, Ctrl+C to stop.")

    while time.time() < end_time:
        wait_if_paused()

        key  = random.choice(MOVE_KEYS)
        hold = jitter(0.2, 0.07)
        pyautogui.keyDown(key)
        time.sleep(hold)
        pyautogui.keyUp(key)
        action_num += 1
        log.debug(f"Action #{action_num} key={key}")

        jitter_sleep(interval, interval * 0.1)

    success(f"Timed execution complete — {action_num} actions in {duration}s.")
    log.info(f"Timed execution done. Actions={action_num}")
