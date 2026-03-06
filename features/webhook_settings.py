import logging
from colorama import Fore, Style

from core import ask, ask_choice, section_header, success, warn, error, info
from core.webhook import (
    enable, disable, is_enabled, get_url,
    test_webhook, notify_custom,
)

log = logging.getLogger(__name__)


def _mask_url(url: str) -> str:
    """Show only the last 12 chars of the webhook ID for privacy."""
    if len(url) > 40:
        return "https://discord.com/api/webhooks/..." + url[-12:]
    return url


def _setup_webhook() -> None:
    """Walk the user through entering and testing a new webhook URL."""
    print()
    info("How to get your Discord webhook URL:")
    info("  1. Open Discord → go to a channel (e.g. #bot-logs)")
    info("  2. Channel Settings → Integrations → Webhooks → New Webhook")
    info("  3. Copy Webhook URL and paste it below.")
    print()

    url = ask("Paste your Discord webhook URL")

    if not url:
        warn("No URL entered. Cancelled.")
        return

    if not (
        url.startswith("https://discord.com/api/webhooks/")
        or url.startswith("https://discordapp.com/api/webhooks/")
        or url.startswith("https://ptb.discord.com/api/webhooks/")
        or url.startswith("https://canary.discord.com/api/webhooks/")
    ):
        error("That doesn't look like a valid Discord webhook URL.")
        error("It should start with: https://discord.com/api/webhooks/")
        return

    info("Sending test ping to Discord...")
    ok = test_webhook(url)

    if not ok:
        error("Test ping failed. Check the URL and try again.")
        error("Make sure the webhook still exists in your Discord channel settings.")
        return

    enable(url)
    success("Webhook connected and saved!")
    success(f"URL: {_mask_url(url)}")
    info("You'll now receive notifications for: session start/end, feature start/done, errors, failsafe, interrupts.")


def _disable_webhook() -> None:
    if not is_enabled():
        warn("Webhook is already disabled.")
        return

    confirm = ask("Are you sure you want to disable and delete the saved webhook? (y/n)")
    if confirm.lower() == "y":
        disable()
        success("Webhook disabled. Config deleted.")
    else:
        info("Cancelled.")


def _show_status() -> None:
    print()
    if is_enabled():
        print(Fore.GREEN + Style.BRIGHT + "  Status  : ENABLED ✓")
        print(Fore.CYAN  + f"  URL     : {_mask_url(get_url())}")
    else:
        print(Fore.YELLOW + Style.BRIGHT + "  Status  : DISABLED")
        print(Fore.LIGHTBLACK_EX + "  No webhook URL configured.")
    print()


def _send_test_ping() -> None:
    if not is_enabled():
        warn("Webhook is not enabled. Set it up first.")
        return

    info("Sending test ping...")
    ok = test_webhook(get_url())
    if ok:
        success("Test ping sent successfully — check your Discord channel!")
    else:
        error("Test ping failed. Your webhook URL may have been deleted or is invalid.")
        warn("Tip: go to Discord → channel settings → Integrations → Webhooks to verify.")


def run() -> None:
    section_header("Discord Webhook Settings")
    log.info("Webhook settings opened")

    _show_status()

    print(Fore.CYAN + "  Options:")
    if is_enabled():
        print(Fore.WHITE + "    [1]  Send test ping")
        print(Fore.WHITE + "    [2]  Change webhook URL")
        print(Fore.WHITE + "    [3]  Disable webhook")
        print(Fore.WHITE + "    [4]  Back")
        print()
        choice = ask("Choose (1/2/3/4)")
        if choice == "1":
            _send_test_ping()
        elif choice == "2":
            _setup_webhook()
        elif choice == "3":
            _disable_webhook()
        else:
            info("Returning to menu.")
    else:
        print(Fore.WHITE + "    [1]  Set up webhook")
        print(Fore.WHITE + "    [2]  Back")
        print()
        choice = ask("Choose (1/2)")
        if choice == "1":
            _setup_webhook()
        else:
            info("Returning to menu.")