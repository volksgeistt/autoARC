import json
import logging
import os
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime
from colorama import Fore, Style

log = logging.getLogger(__name__)

_CFG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "webhook.cfg")
_CFG_FILE = os.path.normpath(_CFG_FILE)

_webhook_url: str  = ""
_enabled: bool     = False
_session_start: float = time.time()

_COLOURS = {
    "session_start":  0x57F287,  
    "session_end":    0xED4245,   
    "feature_start":  0x5865F2,   
    "feature_done":   0x57F287,  
    "feature_error":  0xED4245,  
    "failsafe":       0xFEE75C, 
    "interrupted":    0xEB459E,  
    "custom":         0x99AAB5,  
}

_EMOJIS = {
    "session_start":  "🚀",
    "session_end":    "👋",
    "feature_start":  "▶️",
    "feature_done":   "✅",
    "feature_error":  "❌",
    "failsafe":       "🛑",
    "interrupted":    "⏹️",
    "custom":         "📢",
}

def _save_cfg(url: str) -> None:
    try:
        with open(_CFG_FILE, "w") as f:
            json.dump({"url": url}, f)
    except Exception as e:
        log.warning(f"Could not save webhook config: {e}")


def _load_cfg() -> str:
    try:
        if os.path.exists(_CFG_FILE):
            with open(_CFG_FILE) as f:
                data = json.load(f)
                return data.get("url", "")
    except Exception as e:
        log.warning(f"Could not load webhook config: {e}")
    return ""


def _delete_cfg() -> None:
    try:
        if os.path.exists(_CFG_FILE):
            os.remove(_CFG_FILE)
    except Exception:
        pass

def _is_valid_url(url: str) -> bool:
    return (
        url.startswith("https://discord.com/api/webhooks/")
        or url.startswith("https://discordapp.com/api/webhooks/")
        or url.startswith("https://ptb.discord.com/api/webhooks/")
        or url.startswith("https://canary.discord.com/api/webhooks/")
    )

def _send_payload(payload: dict) -> bool:
    if not _webhook_url:
        return False
    try:
        data    = json.dumps(payload).encode("utf-8")
        req     = urllib.request.Request(
            _webhook_url,
            data    = data,
            headers = {"Content-Type": "application/json", "User-Agent": "AutoARC/1.0"},
            method  = "POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status in (200, 204)
    except urllib.error.HTTPError as e:
        log.warning(f"Webhook HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        log.warning(f"Webhook URL error: {e.reason}")
    except Exception as e:
        log.warning(f"Webhook send failed: {e}")
    return False


def _build_embed(event: str, title: str, description: str, fields: dict = None) -> dict:
    now     = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    elapsed = int(time.time() - _session_start)
    emoji   = _EMOJIS.get(event, "📢")
    colour  = _COLOURS.get(event, 0x99AAB5)

    embed = {
        "title":       f"{emoji}  {title}",
        "description": description,
        "color":       colour,
        "footer":      {"text": f"Auto ARC  ·  {now}  ·  session uptime {elapsed}s"},
    }

    if fields:
        embed["fields"] = [
            {"name": k, "value": str(v), "inline": True}
            for k, v in fields.items()
        ]

    return {"embeds": [embed]}


def _fire(event: str, title: str, description: str, fields: dict = None) -> None:
    if not _enabled or not _webhook_url:
        return

    payload = _build_embed(event, title, description, fields)

    def _task():
        ok = _send_payload(payload)
        if not ok:
            log.debug(f"Webhook notification failed silently (event={event})")

    threading.Thread(target=_task, daemon=True).start()

def notify_session_start() -> None:
    _fire(
        "session_start",
        "Auto ARC Started",
        "A new automation session has begun.",
        {"Status": "Running", "Uptime": "0s"},
    )


def notify_session_end() -> None:
    elapsed = int(time.time() - _session_start)
    _fire(
        "session_end",
        "Auto ARC Exited",
        "The session has ended.",
        {"Total uptime": f"{elapsed}s"},
    )


def notify_feature_start(feature_name: str) -> None:
    _fire(
        "feature_start",
        f"Feature Started — {feature_name}",
        f"**{feature_name}** is now running.",
        {"Feature": feature_name},
    )


def notify_feature_done(feature_name: str, stats: dict = None) -> None:
    fields = {"Feature": feature_name}
    if stats:
        fields.update({k.replace("_", " ").title(): str(v) for k, v in stats.items()})
    _fire(
        "feature_done",
        f"Feature Complete — {feature_name}",
        f"**{feature_name}** finished successfully.",
        fields,
    )


def notify_feature_error(feature_name: str, err: str) -> None:
    _fire(
        "feature_error",
        f"Error in {feature_name}",
        f"An error occurred:\n```\n{err[:300]}\n```",
        {"Feature": feature_name},
    )


def notify_failsafe(feature_name: str) -> None:
    _fire(
        "failsafe",
        "⚠ Emergency Stop Triggered",
        f"FailSafe activated during **{feature_name}**.\nMouse was moved to the top-left corner.",
        {"Feature": feature_name},
    )


def notify_interrupted(feature_name: str) -> None:
    _fire(
        "interrupted",
        f"Interrupted — {feature_name}",
        f"**{feature_name}** was stopped with Ctrl+C.",
        {"Feature": feature_name},
    )


def notify_custom(title: str, message: str, fields: dict = None) -> None:
    _fire("custom", title, message, fields)


def is_enabled() -> bool:
    return _enabled


def get_url() -> str:
    return _webhook_url


def enable(url: str) -> bool:
    global _webhook_url, _enabled

    url = url.strip()
    if not _is_valid_url(url):
        return False

    _webhook_url = url
    _enabled     = True
    _save_cfg(url)
    log.info("Discord webhook enabled.")
    return True


def disable() -> None:
    global _webhook_url, _enabled
    _webhook_url = ""
    _enabled     = False
    _delete_cfg()
    log.info("Discord webhook disabled and config deleted.")


def try_load_saved() -> bool:
    global _session_start
    _session_start = time.time()

    url = _load_cfg()
    if url and _is_valid_url(url):
        return enable(url)
    return False


def test_webhook(url: str) -> bool:
    payload = _build_embed(
        "custom",
        "🔔  Auto ARC — Test Notification",
        "Webhook connected successfully! You will receive notifications here.",
        {"Status": "Connected"},
    )
    global _webhook_url
    old = _webhook_url
    _webhook_url = url
    ok = _send_payload(payload)
    _webhook_url = old
    return ok