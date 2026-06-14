import json
import logging
import os
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

_HERE       = os.path.dirname(os.path.abspath(__file__))
_ROOT       = os.path.dirname(_HERE)
_CFG_PATH   = os.path.join(_ROOT, "sentinel_config.json")


@dataclass
class SharedCfg:
    sample_interval_sec: float = 1.0
    history_len:         int   = 60

@dataclass
class SysSentinelCfg:
    pass

@dataclass
class HostEntry:
    ip:    str
    label: str

@dataclass
class NetWatchCfg:
    ping_timeout_sec:      float            = 3.0
    loss_alert_threshold:  float            = 20.0
    down_hold_consecutive: int              = 5
    default_hosts:         list[HostEntry]  = field(default_factory=list)

def _load() -> tuple[SharedCfg, SysSentinelCfg, NetWatchCfg]:
    raw: dict = {}

    if os.path.exists(_CFG_PATH):
        try:
            with open(_CFG_PATH, encoding="utf-8") as f:
                raw = json.load(f)
            log.info(f"sentinel_cfg: loaded {_CFG_PATH}")
        except Exception as e:
            log.warning(f"sentinel_cfg: could not parse {_CFG_PATH} — using defaults. ({e})")
    else:
        log.warning(f"sentinel_cfg: {_CFG_PATH} not found — using defaults.")

    s = raw.get("shared", {})
    shared = SharedCfg(
        sample_interval_sec = float(s.get("sample_interval_sec", SharedCfg.sample_interval_sec)),
        history_len         = int  (s.get("history_len",         SharedCfg.history_len)),
    )

    sentinel = SysSentinelCfg()

    n = raw.get("net_watch", {})

    raw_hosts = n.get("default_hosts", [])
    hosts = [
        HostEntry(ip=h.get("ip", ""), label=h.get("label", h.get("ip", "")))
        for h in raw_hosts
        if h.get("ip")
    ]
    if not hosts:
        hosts = [
            HostEntry("8.8.8.8",        "Google DNS"),
            HostEntry("1.1.1.1",        "Cloudflare"),
            HostEntry("9.9.9.9",        "Quad9"),
            HostEntry("208.67.222.222", "OpenDNS"),
        ]

    netwatch = NetWatchCfg(
        ping_timeout_sec      = float(n.get("ping_timeout_sec",      NetWatchCfg.ping_timeout_sec)),
        loss_alert_threshold  = float(n.get("loss_alert_threshold",  NetWatchCfg.loss_alert_threshold)),
        down_hold_consecutive = int  (n.get("down_hold_consecutive", NetWatchCfg.down_hold_consecutive)),
        default_hosts         = hosts,
    )

    return shared, sentinel, netwatch

SHARED, SYSSENTINEL, NETWATCH = _load()