import logging
import time
import socket
import struct
import threading
import subprocess
import sys
import os
import re
from collections import deque
from colorama import Fore, Style

from core import (
    ask, ask_int, ask_float, ask_choice,
    wait_if_paused, countdown,
    success, warn, error, info, section_header,
)
from core import webhook

log = logging.getLogger(__name__)


from features.sentinel_cfg import SHARED as _SHARED_CFG, NETWATCH as _NW_CFG

_SAMPLE_INTERVAL   = _SHARED_CFG.sample_interval_sec       
_HISTORY_LEN       = _SHARED_CFG.history_len            
_PING_TIMEOUT      = _NW_CFG.ping_timeout_sec            
_LOSS_ALERT_THRESH = _NW_CFG.loss_alert_threshold         
_DOWN_HOLD_SECS    = _NW_CFG.down_hold_consecutive        

_DEFAULT_HOSTS = [
    (h.ip, h.label) for h in _NW_CFG.default_hosts
]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)

_ICMP_CODE  = socket.getprotobyname("icmp")
_ECHO_ID    = os.getpid() & 0xFFFF

def _checksum(data: bytes) -> int:
    s = 0
    for i in range(0, len(data) - 1, 2):
        s += (data[i] << 8) + data[i + 1]
    if len(data) % 2:
        s += data[-1] << 8
    s  = (s >> 16) + (s & 0xFFFF)
    s += (s >> 16)
    return ~s & 0xFFFF


def _build_packet(seq: int) -> bytes:
    header = struct.pack("bbHHh", 8, 0, 0, _ECHO_ID, seq)
    payload = b"autoARC-netwatch" * 3
    chk    = _checksum(header + payload)
    return struct.pack("bbHHh", 8, 0, chk, _ECHO_ID, seq) + payload


def _raw_ping(host: str, timeout: float = _PING_TIMEOUT, seq: int = 1) -> float | None:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, _ICMP_CODE)
        sock.settimeout(timeout)
        packet = _build_packet(seq)
        t_send = time.perf_counter()
        sock.sendto(packet, (host, 0))

        while True:
            try:
                data, _ = sock.recvfrom(1024)
                t_recv  = time.perf_counter()
                icmp_hdr = data[20:28]
                icmp_type, _, _, recv_id, _ = struct.unpack("bbHHh", icmp_hdr)
                if icmp_type == 0 and recv_id == _ECHO_ID:
                    return (t_recv - t_send) * 1000
            except socket.timeout:
                return None
    except PermissionError:
        return None       
    except Exception:
        return None
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _os_ping(host: str, timeout: float = _PING_TIMEOUT) -> float | None:
    try:
        if os.name == "nt":
            cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 2,
        )
        out = result.stdout + result.stderr

        m = re.search(r"[Tt]ime[=<](\d+\.?\d*)\s*ms", out)
        if m:
            return float(m.group(1))
        return None
    except Exception:
        return None


def ping(host: str, seq: int = 1) -> float | None:
    rtt = _raw_ping(host, seq=seq)
    if rtt is None:
        rtt = _os_ping(host)
    return rtt



def _net_io():
    try:
        import psutil
        c = psutil.net_io_counters()
        return c.bytes_sent, c.bytes_recv
    except Exception:
        return None

class _HostProbe:
    def __init__(self, ip: str, label: str) -> None:
        self.ip      = ip
        self.label   = label
        self.rtt_hist: deque  = deque(maxlen=_HISTORY_LEN)
        self.loss_hist: deque = deque(maxlen=_HISTORY_LEN) 
        self._seq    = 0
        self._down_streak = 0
        self._alert_fired = False

    def sample(self) -> float | None:
        self._seq += 1
        rtt = ping(self.ip, seq=self._seq)
        self.rtt_hist.append(rtt)
        self.loss_hist.append(0 if rtt is not None else 1)

        if rtt is None:
            self._down_streak += 1
        else:
            self._down_streak = 0
            self._alert_fired = False

        return rtt

    @property
    def avg_rtt(self) -> float | None:
        vals = [v for v in self.rtt_hist if v is not None]
        return sum(vals) / len(vals) if vals else None

    @property
    def loss_pct(self) -> float:
        if not self.loss_hist:
            return 0.0
        return sum(self.loss_hist) / len(self.loss_hist) * 100

    @property
    def last_rtt(self) -> float | None:
        return self.rtt_hist[-1] if self.rtt_hist else None

    @property
    def down_streak(self) -> int:
        return self._down_streak

    @property
    def alert_fired(self) -> bool:
        return self._alert_fired

    @alert_fired.setter
    def alert_fired(self, v: bool) -> None:
        self._alert_fired = v

def _rtt_bar(rtt_ms: float | None, max_ms: float = 500.0, width: int = 16) -> str:
    if rtt_ms is None:
        return Fore.RED + Style.BRIGHT + "TIMEOUT " + "░" * (width - 8) + Style.RESET_ALL

    pct   = min(1.0, rtt_ms / max_ms)
    filled = int(pct * width)
    empty  = width - filled

    color = Fore.GREEN if rtt_ms < 50 else Fore.YELLOW if rtt_ms < 150 else Fore.RED
    return color + "█" * filled + Fore.LIGHTBLACK_EX + "░" * empty + Style.RESET_ALL


def _spark(history: deque, width: int = 20, max_val: float | None = None) -> str:
    blocks = " ▁▂▃▄▅▆▇█"
    clean  = [v for v in history if v is not None]
    if not clean:
        return Fore.LIGHTBLACK_EX + "─" * width + Style.RESET_ALL

    mx    = max_val or max(clean) or 1
    data  = list(history)[-width:]
    result = ""
    for v in data:
        if v is None:
            result += Fore.RED + "✗"
        else:
            idx = int((v / mx) * (len(blocks) - 1))
            result += blocks[idx]

    avg = sum(clean) / len(clean)
    color = Fore.GREEN if avg < 50 else Fore.YELLOW if avg < 150 else Fore.RED
    return color + result.ljust(width) + Style.RESET_ALL


def _loss_color(pct: float) -> str:
    if pct < 5:
        return Fore.GREEN
    elif pct < 20:
        return Fore.YELLOW
    return Fore.RED

def _render(
    probes: list[_HostProbe],
    elapsed: int,
    bw_down: float,
    bw_up: float,
    loss_threshold: float,
) -> None:
    os.system("cls" if os.name == "nt" else "clear")

    W = 68
    border = Fore.CYAN + Style.BRIGHT

    def box_row(content: str) -> None:
        visible = len(_strip_ansi(content))
        pad     = max(0, W - 4 - visible)
        print(border + "║" + Style.RESET_ALL + " " + content + " " * pad + " " + border + "║" + Style.RESET_ALL)

    TOP = border + "╔" + "═" * (W - 2) + "╗"
    BOT = border + "╚" + "═" * (W - 2) + "╝"
    SEP = border + "╠" + "─" * (W - 2) + "╣"

    print(TOP)
    title = (
        Fore.CYAN + Style.BRIGHT + "  NetWatch"
        + Fore.LIGHTBLACK_EX + "  ·  "
        + Fore.WHITE + f"uptime {elapsed}s"
        + Fore.LIGHTBLACK_EX + "  ·  "
        + Fore.YELLOW + "F8=pause  Ctrl+C=stop"
    )
    box_row(title)
    print(SEP)

    bw_line = (
        Fore.WHITE + Style.BRIGHT + "  Bandwidth  "
        + Fore.GREEN  + f"▼ {bw_down:7.2f} KB/s"
        + Fore.LIGHTBLACK_EX + "   "
        + Fore.YELLOW + f"▲ {bw_up:7.2f} KB/s"
    )
    box_row(bw_line)
    print(SEP)

    hdr = (
        Fore.CYAN + Style.BRIGHT
        + f"  {'HOST':<18}{'LABEL':<14}{'RTT':>8}  {'BAR':<18}{'LOSS':>6}  TREND"
    )
    box_row(hdr)
    print(SEP)

    for probe in probes:
        rtt   = probe.last_rtt
        avg   = probe.avg_rtt
        loss  = probe.loss_pct

        rtt_str  = f"{rtt:6.1f}ms" if rtt is not None else "  —  ms"
        avg_str  = f"avg {avg:.0f}ms" if avg is not None else "avg  —  "
        loss_str = _loss_color(loss) + f"{loss:5.1f}%" + Style.RESET_ALL

        rtt_color = (
            Fore.GREEN  if rtt is not None and rtt < 50 else
            Fore.YELLOW if rtt is not None and rtt < 150 else
            Fore.RED
        )

        row = (
            Fore.WHITE + Style.BRIGHT + f"  {probe.ip:<18}"
            + Fore.LIGHTBLACK_EX + f"{probe.label:<14}"
            + rtt_color + f"{rtt_str:>8}  "
            + _rtt_bar(rtt, width=16) + "  "
            + loss_str
        )
        box_row(row)

        spark_row = (
            Fore.LIGHTBLACK_EX
            + f"  {avg_str:<32}"
            + _spark(probe.rtt_hist, width=20)
        )
        box_row(spark_row)

        if probe.down_streak >= _DOWN_HOLD_SECS:
            alert_row = Fore.RED + Style.BRIGHT + f"  ⚠  {probe.ip} DOWN — {probe.down_streak} consecutive failures"
            box_row(alert_row)
        elif loss >= loss_threshold:
            alert_row = Fore.YELLOW + Style.BRIGHT + f"  ⚠  {probe.ip} high packet loss: {loss:.1f}%"
            box_row(alert_row)

        print(SEP if probe is not probes[-1] else BOT)

    if probes and not probes[-1]:
        print(BOT)


def _check_alerts(probes: list[_HostProbe], loss_threshold: float) -> None:
    for probe in probes:
        if probe.down_streak >= _DOWN_HOLD_SECS and not probe.alert_fired:
            probe.alert_fired = True
            msg = f"Host {probe.ip} ({probe.label}) is UNREACHABLE — {probe.down_streak} consecutive timeouts."
            warn(msg)
            log.warning(msg)
            webhook.notify_custom(
                "📡 NetWatch — Host Down",
                msg,
                {"Host": probe.ip, "Label": probe.label, "Failures": str(probe.down_streak)},
            )

        loss = probe.loss_pct
        if loss >= loss_threshold and len(probe.loss_hist) >= 10:
            older = list(probe.loss_hist)[:-1]
            older_loss = sum(older) / len(older) * 100 if older else 0
            if older_loss < loss_threshold:
                msg = f"High packet loss to {probe.ip} ({probe.label}): {loss:.1f}%"
                warn(msg)
                log.warning(msg)
                webhook.notify_custom(
                    "📡 NetWatch — Packet Loss Alert",
                    msg,
                    {"Host": probe.ip, "Label": probe.label, "Loss": f"{loss:.1f}%", "Threshold": f"{loss_threshold:.1f}%"},
                )

def _configure_hosts() -> list[_HostProbe]:
    print()
    info("Default hosts: Google DNS, Cloudflare, Quad9, OpenDNS")
    use_defaults = ask_choice("Use default hosts?", ["yes", "no", "both"])

    probes: list[_HostProbe] = []

    if use_defaults in ("yes", "both"):
        for ip, label in _DEFAULT_HOSTS:
            probes.append(_HostProbe(ip, label))
        success(f"Added {len(_DEFAULT_HOSTS)} default hosts.")

    if use_defaults in ("no", "both"):
        info("Enter custom hosts — blank IP to finish.")
        while True:
            ip = ask("Host IP or hostname (blank to finish)").strip()
            if not ip:
                break
            label = ask(f"Label for {ip} (e.g. 'My VPN')").strip() or ip
            probes.append(_HostProbe(ip, label))
            success(f"Added: {ip} ({label})")

    if not probes:
        warn("No hosts configured — using Google DNS as fallback.")
        probes.append(_HostProbe("8.8.8.8", "Google DNS"))

    return probes


class _BandwidthTracker:
    def __init__(self) -> None:
        self._last = _net_io()
        self._last_t = time.time()
        self.down_kb = 0.0
        self.up_kb   = 0.0

    def sample(self) -> None:
        now = time.time()
        cur = _net_io()
        if cur is None or self._last is None:
            return

        dt = max(0.001, now - self._last_t)
        self.up_kb   = (cur[0] - self._last[0]) / dt / 1024
        self.down_kb = (cur[1] - self._last[1]) / dt / 1024

        self._last   = cur
        self._last_t = now

def run() -> None:
    section_header("NetWatch — Network Monitor")
    log.info("NetWatch started")

    print()
    info("NetWatch pings hosts, tracks latency/loss, and alerts on drops.")
    info("Raw ICMP is used where available — OS ping fallback otherwise.")
    print()

    probes = _configure_hosts()

    loss_threshold = ask_float(
        "Packet loss % to trigger alert (e.g. 20.0)",
        min_val=1.0,
    )
    duration = ask_int("Monitor duration (seconds, 0 = until Ctrl+C)", min_val=0)

    info("Starting network monitoring...")
    time.sleep(0.5)

    bw = _BandwidthTracker()
    start_time = time.time()
    end_time   = (start_time + duration) if duration > 0 else float("inf")

    webhook.notify_custom(
        "📡 NetWatch Started",
        f"Monitoring {len(probes)} host(s).",
        {
            "Hosts":          ", ".join(p.ip for p in probes),
            "Loss threshold": f"{loss_threshold:.1f}%",
            "Duration":       f"{duration}s" if duration else "∞",
        },
    )

    try:
        while time.time() < end_time:
            wait_if_paused()

            for probe in probes:
                probe.sample()

            bw.sample()
            _check_alerts(probes, loss_threshold)

            elapsed = int(time.time() - start_time)
            _render(probes, elapsed, bw.down_kb, bw.up_kb, loss_threshold)

            time.sleep(_SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        pass

    elapsed_total = int(time.time() - start_time)
    success(f"NetWatch ended — {elapsed_total}s monitored.")

    summary_fields = {}
    for probe in probes:
        avg = probe.avg_rtt
        summary_fields[f"{probe.label} avg RTT"] = f"{avg:.1f}ms" if avg else "N/A"
        summary_fields[f"{probe.label} loss"]    = f"{probe.loss_pct:.1f}%"

    webhook.notify_custom(
        "📡 NetWatch Stopped",
        f"Network monitoring session ended after {elapsed_total}s.",
        summary_fields,
    )

    log.info(f"NetWatch done. Elapsed={elapsed_total}s, hosts={len(probes)}")