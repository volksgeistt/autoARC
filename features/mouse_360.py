import logging
import math
import time
import pyautogui

from core import ask_int, ask_float, jitter, jitter_sleep, wait_if_paused, countdown, success, warn, info, section_header

log = logging.getLogger(__name__)


def run() -> None:
    section_header("360° Mouse Path")
    log.info("360° mouse simulation started")

    duration = ask_int("Duration (seconds)", min_val=1)
    radius   = ask_int("Circle radius in pixels (e.g. 150)", min_val=10)
    speed    = ask_float("Angular speed in degrees per step (e.g. 3.0 = smooth, 10.0 = fast)", min_val=0.1)

    warn("Place your mouse at the desired circle CENTER, then switch window.")
    countdown(3)

    center_x, center_y = pyautogui.position()
    angle_rad  = 0.0
    step_rad   = math.radians(speed)
    end_time   = time.time() + duration
    step_count = 0
    sw, sh     = pyautogui.size()

    info(f"Center=({center_x},{center_y})  radius={radius}px  speed={speed}°/step")

    while time.time() < end_time:
        wait_if_paused()

        x = int(center_x + radius * math.cos(angle_rad))
        y = int(center_y + radius * math.sin(angle_rad))

        x = max(2, min(sw - 2, x))
        y = max(2, min(sh - 2, y))

        move_dur    = jitter(0.025, 0.005)
        pyautogui.moveTo(x, y, duration=move_dur)

        angle_rad   = (angle_rad + step_rad) % (2 * math.pi)
        step_count += 1

        time.sleep(jitter(0.025, 0.008))

    revolutions = round(step_count * math.degrees(step_rad) / 360, 1)
    success(f"360° path complete — {step_count} steps, ~{revolutions} full revolutions.")
    log.info(f"360° done. Steps={step_count}, Revolutions={revolutions}")
