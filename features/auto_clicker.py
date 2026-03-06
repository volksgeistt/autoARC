

import logging
import time
import random
import pyautogui
from colorama import Fore, Style

from core import (
    ask_int, ask_float, ask_choice,
    jitter, jitter_sleep,
    wait_if_paused, countdown,
    success, warn, error, info, section_header,
)

log = logging.getLogger(__name__)



def _cps_to_interval(cps: float) -> float:
    return 1.0 / cps if cps > 0 else 0.1


def _click(button: str) -> None:
    pyautogui.click(button=button)


def _double_click(button: str) -> None:
    pyautogui.doubleClick(button=button)


def _hold_click(button: str, duration: float) -> None:
    pyautogui.mouseDown(button=button)
    time.sleep(duration)
    pyautogui.mouseUp(button=button)



def _run_single(button: str, cps: float, run_duration: float) -> dict:
    interval = _cps_to_interval(cps)
    end_time = time.time() + run_duration
    clicks   = 0

    info(f"Single-click mode  ·  {cps} CPS  ·  button={button}  ·  {run_duration}s")

    while time.time() < end_time:
        wait_if_paused()
        _click(button)
        clicks += 1
        log.debug(f"Single click #{clicks}")
        jitter_sleep(interval, interval * 0.12)

    return {"mode": "single", "clicks": clicks, "duration": run_duration}


def _run_double(button: str, cps: float, run_duration: float) -> dict:
    interval = _cps_to_interval(cps)
    end_time = time.time() + run_duration
    events   = 0

    info(f"Double-click mode  ·  {cps} events/s  ·  button={button}  ·  {run_duration}s")

    while time.time() < end_time:
        wait_if_paused()
        _double_click(button)
        events += 1
        log.debug(f"Double-click event #{events}")
        jitter_sleep(interval, interval * 0.12)

    return {"mode": "double", "clicks": events * 2, "events": events, "duration": run_duration}


def _run_burst(
    button: str,
    burst_size: int,
    burst_cps: float,
    burst_pause: float,
    run_duration: float,
) -> dict:
    """
    burst_size  : clicks per burst
    burst_cps   : CPS within a burst
    burst_pause : seconds between bursts
    """
    intra_interval = _cps_to_interval(burst_cps)
    end_time       = time.time() + run_duration
    total_clicks   = 0
    bursts         = 0

    info(
        f"Burst mode  ·  {burst_size} clicks @ {burst_cps} CPS  ·  "
        f"{burst_pause}s pause between bursts  ·  {run_duration}s total"
    )

    while time.time() < end_time:
        wait_if_paused()

        for i in range(burst_size):
            if time.time() >= end_time:
                break
            wait_if_paused()
            _click(button)
            total_clicks += 1
            log.debug(f"Burst #{bursts + 1}  click {i + 1}/{burst_size}")
            if i < burst_size - 1:

                jitter_sleep(intra_interval, intra_interval * 0.15)

        bursts += 1

        remaining = end_time - time.time()
        if remaining <= 0:
            break
        pause = jitter(burst_pause, burst_pause * 0.15)
        time.sleep(min(pause, remaining))

    return {
        "mode": "burst",
        "clicks": total_clicks,
        "bursts": bursts,
        "burst_size": burst_size,
        "duration": run_duration,
    }


def _run_hold(button: str, hold_dur: float, release_pause: float, run_duration: float) -> dict:
    """
    hold_dur      : seconds to hold the button down per press
    release_pause : seconds between releases and next hold
    """
    end_time = time.time() + run_duration
    presses  = 0

    info(
        f"Hold mode  ·  hold={hold_dur}s  ·  release pause={release_pause}s  ·  "
        f"button={button}  ·  {run_duration}s total"
    )

    while time.time() < end_time:
        wait_if_paused()
        actual_hold = jitter(hold_dur, hold_dur * 0.1)
        _hold_click(button, actual_hold)
        presses += 1
        log.debug(f"Hold #{presses}  held={actual_hold:.3f}s")

        remaining = end_time - time.time()
        if remaining <= 0:
            break
        pause = jitter(release_pause, release_pause * 0.12)
        time.sleep(min(pause, remaining))

    return {"mode": "hold", "presses": presses, "hold_duration": hold_dur, "duration": run_duration}


def _print_stats(stats: dict) -> None:
    print()
    print(Fore.CYAN + Style.BRIGHT + "  ── Session Stats ──────────────────────")
    for k, v in stats.items():
        label = k.replace("_", " ").capitalize()
        print(Fore.CYAN + f"  {label:<22} {Fore.WHITE}{v}")

    dur = stats.get("duration", 1)
    clicks = stats.get("clicks") or stats.get("presses", 0)
    if dur > 0 and clicks > 0:
        effective_cps = round(clicks / dur, 2)
        print(Fore.CYAN + f"  {'Effective CPS':<22} {Fore.WHITE}{effective_cps}")

    print(Fore.CYAN + Style.BRIGHT + "  ────────────────────────────────────────")
    print()



def run() -> None:
    section_header("Auto-Clicker")
    log.info("Auto-Clicker started")

    button = ask_choice("Mouse button", ["left", "right", "middle"])

    print()
    info("Available modes:")
    info("  single — one click per interval")
    info("  double — double-click per interval")
    info("  burst  — N rapid clicks, then pause, repeat")
    info("  hold   — press and hold the button")
    print()
    mode = ask_choice("Click mode", ["single", "double", "burst", "hold"])

    run_duration = ask_float("Total run duration (seconds)", min_val=1.0)

    stats = {}

    if mode == "single":
        cps = ask_float("CPS — clicks per second (e.g. 8.0, max sane ~20)", min_val=0.1)
        warn("Switch to your target window now.")
        countdown(5)
        stats = _run_single(button, cps, run_duration)

    elif mode == "double":
        cps = ask_float("Double-click events per second (e.g. 4.0)", min_val=0.1)
        warn("Switch to your target window now.")
        countdown(5)
        stats = _run_double(button, cps, run_duration)

    elif mode == "burst":
        burst_size  = ask_int("Clicks per burst (e.g. 3)", min_val=1)
        burst_cps   = ask_float("CPS within each burst (e.g. 15.0)", min_val=1.0)
        burst_pause = ask_float("Pause between bursts in seconds (e.g. 0.8)", min_val=0.05)
        warn("Switch to your target window now.")
        countdown(5)
        stats = _run_burst(button, burst_size, burst_cps, burst_pause, run_duration)

    elif mode == "hold":
        hold_dur      = ask_float("Hold duration per press in seconds (e.g. 0.5)", min_val=0.05)
        release_pause = ask_float("Pause between presses in seconds (e.g. 0.3)", min_val=0.05)
        warn("Switch to your target window now.")
        countdown(5)
        stats = _run_hold(button, hold_dur, release_pause, run_duration)

    success("Auto-Clicker session complete.")
    _print_stats(stats)
    log.info(f"Auto-Clicker done. Stats={stats}")
