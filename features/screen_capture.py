import logging
import time
import pyautogui
import cv2
import numpy as np
from colorama import Fore

from core import ask_int, countdown, success, warn, error, info, section_header

log = logging.getLogger(__name__)


def run() -> None:
    section_header("Screen Capture & Analysis")
    log.info("Screen capture started")

    delay = ask_int("Countdown before capture (seconds, e.g. 7)", min_val=1)

    warn("Switch to your target window now.")
    countdown(delay, message="Capturing in")

    try:
        screenshot = pyautogui.screenshot()
        img_bgr    = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        gray       = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        edges      = cv2.Canny(gray, 100, 200)

        cv2.imwrite("screenshot.png", img_bgr)
        cv2.imwrite("edges.png",      edges)

        h, w         = img_bgr.shape[:2]
        mean_r       = int(img_bgr[:, :, 2].mean())
        mean_g       = int(img_bgr[:, :, 1].mean())
        mean_b       = int(img_bgr[:, :, 0].mean())
        edge_density = round(edges.sum() / (255 * w * h) * 100, 2)
        brightness   = round((0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b), 1)

        success("Captured & analysed!")
        info(f"Resolution   : {w} × {h}")
        info(f"Mean RGB     : R={mean_r}  G={mean_g}  B={mean_b}")
        info(f"Brightness   : {brightness} / 255")
        info(f"Edge density : {edge_density}%")
        info("Saved → screenshot.png  |  edges.png")

        log.info(f"Capture done. {w}×{h}, brightness={brightness}, edges={edge_density}%")
    except Exception as e:
        error(f"Capture failed: {e}")
        log.error(e)
