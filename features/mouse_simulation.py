import logging
import random
import time
import pyautogui

from core import ask_int, jitter, jitter_sleep, wait_if_paused, countdown, success, warn, section_header

log = logging.getLogger(__name__)


def run() -> None:
    section_header("Mouse Simulation")
    log.info("Mouse simulation started")

    duration = ask_int("Duration (seconds)", min_val=1)

    warn("Switch to your target window now.")
    countdown(4)

    sw, sh   = pyautogui.size()
    end_time = time.time() + duration
    moves    = 0

    while time.time() < end_time:
        wait_if_paused()
        x        = random.randint(60, sw - 60)
        y        = random.randint(60, sh - 60)
        dur      = jitter(0.75, 0.25)
        pyautogui.moveTo(x, y, duration=dur, tween=pyautogui.easeInOutQuad)
        moves   += 1
        log.debug(f"Mouse → ({x}, {y})")
        jitter_sleep(0.3, 0.1)

    success(f"Mouse simulation complete — {moves} moves in {duration}s.")
    log.info(f"Mouse simulation done. Moves={moves}")
