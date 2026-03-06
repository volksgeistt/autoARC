import sys
import time
import logging
import pyautogui
from colorama import Fore, Style, init

init(autoreset=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("AutoARC")

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0

from core import (
    display_menu, loading_screen,
    start_pause_listener,
    ask_int, success, error, info, warn, center,
    webhook,
)
from features import FEATURE_MAP

_FEATURE_NAMES = {
    1: "AutoTyper",
    2: "Anti-AFK Movement",
    3: "Mouse Simulation",
    4: "Screen Capture",
    5: "Timed Execution",
    6: "Custom Key Sequence",
    7: "360° Mouse Path",
    8: "Auto-Clicker",
    9: "Discord Webhook Settings",
}



def _prompt_webhook_setup() -> None:
    print()
    print(Fore.YELLOW + Style.BRIGHT + "  🔔  Discord Webhook  (optional)")
    print(Fore.WHITE  + "  Get notified on your phone when tasks start, finish, or error.")
    print()
    ans = input(Fore.GREEN + Style.BRIGHT + "  Set up now? (y/n) :: " + Fore.RESET).strip().lower()
    if ans == "y":
        _quick_webhook_setup()
    else:
        info("Skipped — set it up later via menu option [9].")
    print()


def _quick_webhook_setup() -> None:
    url = input(Fore.GREEN + Style.BRIGHT + "  Paste your Discord webhook URL :: " + Fore.RESET).strip()
    if not url:
        warn("No URL entered. Skipping.")
        return
    info("Testing connection...")
    ok = webhook.test_webhook(url)
    if not ok:
        error("Could not reach that webhook. Check the URL and try option [9] later.")
        return
    webhook.enable(url)
    success("Webhook saved! Notifications are now active.")



def main() -> None:
    log.info("Auto ARC starting.")

    start_pause_listener()

    saved = webhook.try_load_saved()
    if saved:
        log.info("Webhook loaded from saved config.")

    loading_screen()

    if not webhook.is_enabled():
        _prompt_webhook_setup()

    webhook.notify_session_start()

    max_choice = max(FEATURE_MAP.keys())

    while True:
        display_menu()

        try:
            choice = ask_int(f"Enter your choice (0–{max_choice})", min_val=0, max_val=max_choice)
        except KeyboardInterrupt:
            print(Fore.RED + "\n  Ctrl+C — returning to menu.\n")
            time.sleep(0.8)
            continue

        if choice == 0:
            webhook.notify_session_end()
            print(Fore.MAGENTA + Style.BRIGHT + center("Goodbye!  o7"))
            log.info("Auto ARC exited by user.")
            sys.exit(0)

        feature      = FEATURE_MAP.get(choice)
        feature_name = _FEATURE_NAMES.get(choice, f"Feature {choice}")

        if feature is None:
            error(f"No feature mapped to choice {choice}.")
            continue

        if choice != 9:
            webhook.notify_feature_start(feature_name)

        try:
            feature.run()
            if choice != 9:
                webhook.notify_feature_done(feature_name)

        except pyautogui.FailSafeException:
            print(Fore.RED + Style.BRIGHT + "\n  🛑  Emergency stop triggered. Returning to menu.\n")
            webhook.notify_failsafe(feature_name)
            log.warning("FailSafe triggered.")

        except KeyboardInterrupt:
            print(Fore.RED + "\n  Interrupted — returning to menu.\n")
            webhook.notify_interrupted(feature_name)
            log.info("Feature interrupted.")

        except Exception as e:
            error(f"Unexpected error: {e}")
            webhook.notify_feature_error(feature_name, str(e))
            log.exception(e)

        print()
        input(Fore.CYAN + "  Press ENTER to return to menu...")


if __name__ == "__main__":
    main()