import logging
import time
import threading
import subprocess
import sys
import os
import re
import platform
from collections import deque
from colorama import Fore, Style

from core import (
    ask, ask_int, ask_float, ask_choice,
    wait_if_paused,
    success, warn, error, info, section_header,
)
from core import webhook

log = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)

def _ensure_psutil() -> bool:
    try:
        import psutil
        return True
    except ImportError:
        warn("psutil not found — installing...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "psutil", "--quiet"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            success("psutil installed.")
            return True
        except Exception as e:
            error(f"Could not install psutil: {e}")
            return False

class _GPUInfo:
    name:       str   = "Unknown"
    vendor:     str   = "Unknown"
    vram_total: int   = 0      
    vram_used:  int   = 0     
    temp:       float | None = None
    usage:      float | None = None  
    driver:     str   = ""
    source:     str   = "none" 

    def __init__(self):
        self.name = "Unknown"; self.vendor = "Unknown"
        self.vram_total = 0; self.vram_used = 0
        self.temp = None; self.usage = None
        self.driver = ""; self.source = "none"


_gpu_static: _GPUInfo | None = None 
_gpu_lock = threading.Lock()


def _detect_gpu_static() -> _GPUInfo:
    g = _GPUInfo()

    try:
        import pynvml
        pynvml.nvmlInit()
        handle   = pynvml.nvmlDeviceGetHandleByIndex(0)
        g.name   = pynvml.nvmlDeviceGetName(handle).decode("utf-8", errors="replace")
        g.vendor = "NVIDIA"
        mem      = pynvml.nvmlDeviceGetMemoryInfo(handle)
        g.vram_total = mem.total // 1024 // 1024
        g.vram_used  = mem.used  // 1024 // 1024
        try:
            g.driver = pynvml.nvmlSystemGetDriverVersion().decode()
        except Exception:
            pass
        g.source = "nvml"
        log.info(f"GPU detected via NVML: {g.name}")
        return g
    except Exception:
        pass

    try:
        import wmi
        w      = wmi.WMI()
        gpus   = w.Win32_VideoController()
        if gpus:
            gpu      = gpus[0]
            g.name   = gpu.Name or "Unknown"
            g.vendor = _infer_vendor(g.name)
            try:
                g.vram_total = int(gpu.AdapterRAM or 0) // 1024 // 1024
            except Exception:
                g.vram_total = 0
            try:
                g.driver = gpu.DriverVersion or ""
            except Exception:
                pass
            g.source = "wmi"
            log.info(f"GPU detected via WMI: {g.name}")
            return g
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["lspci"], capture_output=True, text=True, timeout=4
        )
        for line in result.stdout.splitlines():
            if "VGA" in line or "3D" in line or "Display" in line:
                g.name   = line.split(":")[-1].strip()
                g.vendor = _infer_vendor(g.name)
                g.source = "lspci"
                log.info(f"GPU detected via lspci: {g.name}")
                return g
    except Exception:
        pass

    g.source = "none"
    return g


def _infer_vendor(name: str) -> str:
    nl = name.lower()
    if "nvidia" in nl or "geforce" in nl or "quadro" in nl or "rtx" in nl or "gtx" in nl:
        return "NVIDIA"
    if "amd" in nl or "radeon" in nl or "rx " in nl:
        return "AMD"
    if "intel" in nl or "iris" in nl or "uhd" in nl or "hd graphics" in nl:
        return "Intel"
    return "Unknown"


def _sample_gpu_dynamic(g: _GPUInfo) -> None:
    if g.source == "nvml":
        try:
            import pynvml
            handle      = pynvml.nvmlDeviceGetHandleByIndex(0)
            g.temp      = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
            util        = pynvml.nvmlDeviceGetUtilizationRates(handle)
            g.usage     = float(util.gpu)
            mem         = pynvml.nvmlDeviceGetMemoryInfo(handle)
            g.vram_used = mem.used // 1024 // 1024
        except Exception:
            pass
        return

    if g.source == "wmi":
        try:
            import wmi
            ohm = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            sensors = ohm.Sensor()
            for s in sensors:
                if s.SensorType == "Temperature" and "gpu" in s.Name.lower():
                    g.temp = float(s.Value)
                    break
            for s in sensors:
                if s.SensorType == "Load" and "gpu core" in s.Name.lower():
                    g.usage = float(s.Value)
                    break
        except Exception:
            pass
        if g.temp is None:
            try:
                import wmi
                w = wmi.WMI(namespace="root\\wmi")
                zones = w.MSAcpi_ThermalZoneTemperature()
                if zones:
                    g.temp = round((zones[0].CurrentTemperature / 10.0) - 273.15, 1)
            except Exception:
                pass
        return

    if g.source in ("lspci", "none") and os.path.exists("/sys/class/hwmon"):
        try:
            for hwmon in os.listdir("/sys/class/hwmon"):
                name_path = f"/sys/class/hwmon/{hwmon}/name"
                if os.path.exists(name_path):
                    with open(name_path) as f:
                        hw_name = f.read().strip()
                    if hw_name in ("amdgpu", "radeon", "nvidia"):
                        temp_path = f"/sys/class/hwmon/{hwmon}/temp1_input"
                        if os.path.exists(temp_path):
                            with open(temp_path) as f:
                                g.temp = int(f.read().strip()) / 1000
                        break
        except Exception:
            pass


class _SystemSpecs:
    cpu_name:    str = ""
    cpu_cores:   int = 0
    cpu_threads: int = 0
    cpu_freq_max: float = 0.0   
    ram_total:   int = 0        
    os_name:     str = ""
    disk_total:  int = 0       
    disk_free:   int = 0      

def _collect_specs() -> _SystemSpecs:
    import psutil
    s = _SystemSpecs()

    s.os_name = f"{platform.system()} {platform.release()}"

    try:
        import cpuinfo
        s.cpu_name = cpuinfo.get_cpu_info().get("brand_raw", "")
    except Exception:
        pass
    if not s.cpu_name:
        s.cpu_name = platform.processor() or "Unknown CPU"

    s.cpu_cores   = psutil.cpu_count(logical=False) or 1
    s.cpu_threads = psutil.cpu_count(logical=True)  or 1
    freq = psutil.cpu_freq()
    s.cpu_freq_max = round((freq.max if freq and freq.max else (freq.current if freq else 0)) / 1000, 2)

    s.ram_total = psutil.virtual_memory().total // 1024 // 1024 // 1024

    try:
        disk = psutil.disk_usage("/")
        s.disk_total = disk.total // 1024 // 1024 // 1024
        s.disk_free  = disk.free  // 1024 // 1024 // 1024
    except Exception:
        try:
            disk = psutil.disk_usage("C:\\")
            s.disk_total = disk.total // 1024 // 1024 // 1024
            s.disk_free  = disk.free  // 1024 // 1024 // 1024
        except Exception:
            pass

    return s

class _Alert:
    def __init__(self, metric: str, threshold: float, hold_secs: float, kill_proc: str = "") -> None:
        self.metric     = metric
        self.threshold  = threshold
        self.hold_secs  = hold_secs
        self.kill_proc  = kill_proc.strip().lower()
        self._breach_start: float | None = None
        self._fired     = False

    def evaluate(self, value: float) -> bool:
        if value >= self.threshold:
            if self._breach_start is None:
                self._breach_start = time.time()
            if time.time() - self._breach_start >= self.hold_secs and not self._fired:
                self._fired = True
                return True
        else:
            self._breach_start = None
            self._fired        = False
        return False

    def label(self) -> str:
        unit = "°C" if self.metric == "gpu_temp" else "%"
        return f"{self.metric.upper()} > {self.threshold}{unit} for {self.hold_secs}s"


from features.sentinel_cfg import SHARED as _SHARED_CFG

_SAMPLE_INTERVAL = _SHARED_CFG.sample_interval_sec   
_HISTORY_LEN     = _SHARED_CFG.history_len          


class _StatsCollector:
    def __init__(self, gpu: _GPUInfo) -> None:
        import psutil
        self._ps  = psutil
        self._gpu = gpu

        self.cpu_hist:    deque = deque(maxlen=_HISTORY_LEN)
        self.ram_hist:    deque = deque(maxlen=_HISTORY_LEN)
        self.gpu_t_hist:  deque = deque(maxlen=_HISTORY_LEN)
        self.gpu_u_hist:  deque = deque(maxlen=_HISTORY_LEN)
        self.disk_r_hist: deque = deque(maxlen=_HISTORY_LEN)
        self.disk_w_hist: deque = deque(maxlen=_HISTORY_LEN)
        self.net_d_hist:  deque = deque(maxlen=_HISTORY_LEN)
        self.net_u_hist:  deque = deque(maxlen=_HISTORY_LEN)

        self._running  = False
        self._lock     = threading.Lock()

        self._last_disk  = self._ps.disk_io_counters()
        self._last_net   = self._ps.net_io_counters()
        self._last_t     = time.time()

    def _last(self, dq: deque, default=0.0):
        with self._lock:
            return dq[-1] if dq else default

    @property
    def cpu(self):    return self._last(self.cpu_hist)
    @property
    def ram(self):    return self._last(self.ram_hist)
    @property
    def gpu_t(self):  return self._last(self.gpu_t_hist, None)
    @property
    def gpu_u(self):  return self._last(self.gpu_u_hist, None)
    @property
    def disk_r(self): return self._last(self.disk_r_hist)
    @property
    def disk_w(self): return self._last(self.disk_w_hist)
    @property
    def net_d(self):  return self._last(self.net_d_hist)
    @property
    def net_u(self):  return self._last(self.net_u_hist)

    def _sample(self) -> None:
        cpu = self._ps.cpu_percent(interval=None)
        ram = self._ps.virtual_memory().percent

        _sample_gpu_dynamic(self._gpu)
        gpu_temp  = self._gpu.temp
        gpu_usage = self._gpu.usage

        now  = time.time()
        dt   = max(0.001, now - self._last_t)

        disk = self._ps.disk_io_counters()
        dr   = (disk.read_bytes  - self._last_disk.read_bytes)  / dt / 1024 / 1024
        dw   = (disk.write_bytes - self._last_disk.write_bytes) / dt / 1024 / 1024
        self._last_disk = disk

        net = self._ps.net_io_counters()
        nd  = (net.bytes_recv - self._last_net.bytes_recv) / dt / 1024
        nu  = (net.bytes_sent - self._last_net.bytes_sent) / dt / 1024
        self._last_net = net

        self._last_t = now

        with self._lock:
            self.cpu_hist.append(cpu)
            self.ram_hist.append(ram)
            if gpu_temp  is not None: self.gpu_t_hist.append(gpu_temp)
            if gpu_usage is not None: self.gpu_u_hist.append(gpu_usage)
            self.disk_r_hist.append(max(0.0, dr))
            self.disk_w_hist.append(max(0.0, dw))
            self.net_d_hist.append(max(0.0, nd))
            self.net_u_hist.append(max(0.0, nu))

    def start(self) -> None:
        self._running = True
        self._ps.cpu_percent(interval=None) 
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        while self._running:
            try:
                self._sample()
            except Exception as e:
                log.debug(f"Stats sample error: {e}")
            time.sleep(_SAMPLE_INTERVAL)

def _bar(value: float, total: float = 100.0, width: int = 18) -> str:
    pct    = min(1.0, value / (total or 1))
    filled = int(pct * width)
    empty  = width - filled
    color  = Fore.GREEN if pct < 0.5 else Fore.YELLOW if pct < 0.8 else Fore.RED
    return f"{color}{'█' * filled}{Fore.LIGHTBLACK_EX}{'░' * empty}{Style.RESET_ALL}"


def _spark(dq: deque, width: int = 24) -> str:
    blocks = " ▁▂▃▄▅▆▇█"
    data   = [v for v in dq if v is not None]
    if not data:
        return Fore.LIGHTBLACK_EX + "─" * width + Style.RESET_ALL
    mx     = max(data) or 1
    tail   = list(dq)[-width:]
    result = ""
    for v in tail:
        if v is None:
            result += "─"
        else:
            result += blocks[int((v / mx) * (len(blocks) - 1))]
    avg   = sum(data) / len(data)
    color = Fore.GREEN if avg < 50 else Fore.YELLOW if avg < 80 else Fore.RED
    return color + result.ljust(width) + Style.RESET_ALL



_W       = 66     
_BOX_W   = _W + 4 


def _box_row(content: str) -> None:
    vis = len(_strip_ansi(content))
    pad = max(0, _W - vis)
    bc  = Fore.CYAN + Style.BRIGHT
    print(f"{bc}║{Style.RESET_ALL} {content}{' ' * pad} {bc}║{Style.RESET_ALL}")


def _box_edge(l: str, f: str, r: str) -> None:
    bc = Fore.CYAN + Style.BRIGHT
    print(f"{bc}{l}{f * (_BOX_W - 2)}{r}{Style.RESET_ALL}")


def _metric_row(
    label: str,
    value_str: str,
    bar: str,
    extra: str = "",
) -> None:
    lbl  = f"{Fore.WHITE}{Style.BRIGHT}{label:<7}{Style.RESET_ALL}"
    val  = f"{value_str}"
    ext  = f"  {Fore.LIGHTBLACK_EX}{extra}{Style.RESET_ALL}" if extra else ""
    _box_row(f"  {lbl} {bar}  {val}{ext}")


def _render_dashboard(
    collector: _StatsCollector,
    gpu: _GPUInfo,
    specs: _SystemSpecs,
    alerts: list[_Alert],
    elapsed: int,
) -> None:
    os.system("cls" if os.name == "nt" else "clear")

    TOP = ("╔", "═", "╗")
    BOT = ("╚", "═", "╝")
    SEP = ("╠", "─", "╣")

    _box_edge(*TOP)

    _box_row(
        f"{Fore.CYAN}{Style.BRIGHT}  SysSentinel"
        f"{Fore.LIGHTBLACK_EX}  ·  "
        f"{Fore.WHITE}uptime {elapsed}s"
        f"{Fore.LIGHTBLACK_EX}  ·  "
        f"{Fore.YELLOW}F8=pause  Ctrl+C=stop"
    )

    _box_edge(*SEP)

    _box_row(f"{Fore.CYAN}{Style.BRIGHT}  SYSTEM SPECS")
    _box_row(
        f"  {Fore.LIGHTBLACK_EX}OS     {Fore.WHITE}{specs.os_name}"
    )
    cpu_spec = f"{specs.cpu_name}"
    if len(cpu_spec) > _W - 12:
        cpu_spec = cpu_spec[:_W - 15] + "..."
    _box_row(f"  {Fore.LIGHTBLACK_EX}CPU    {Fore.WHITE}{cpu_spec}")
    _box_row(
        f"  {Fore.LIGHTBLACK_EX}       "
        f"{Fore.CYAN}{specs.cpu_cores}C / {specs.cpu_threads}T"
        f"{Fore.LIGHTBLACK_EX}  ·  "
        f"{Fore.CYAN}{specs.cpu_freq_max} GHz max"
    )
    _box_row(
        f"  {Fore.LIGHTBLACK_EX}RAM    "
        f"{Fore.WHITE}{specs.ram_total} GB total"
    )

    if gpu.source != "none":
        vram_str = f"{gpu.vram_total} MB VRAM" if gpu.vram_total else "VRAM unknown"
        drv_str  = f"  driver {gpu.driver}" if gpu.driver else ""
        gpu_spec = gpu.name
        if len(gpu_spec) > _W - 18:
            gpu_spec = gpu_spec[:_W - 21] + "..."
        _box_row(
            f"  {Fore.LIGHTBLACK_EX}GPU    "
            f"{Fore.WHITE}{gpu_spec}"
        )
        _box_row(
            f"  {Fore.LIGHTBLACK_EX}       "
            f"{Fore.CYAN}{vram_str}"
            f"{Fore.LIGHTBLACK_EX}{drv_str}"
        )
    else:
        _box_row(f"  {Fore.LIGHTBLACK_EX}GPU    {Fore.LIGHTBLACK_EX}not detected")

    _box_row(
        f"  {Fore.LIGHTBLACK_EX}Disk   "
        f"{Fore.WHITE}{specs.disk_total} GB total"
        f"{Fore.LIGHTBLACK_EX}  ·  "
        f"{Fore.CYAN}{specs.disk_free} GB free"
    )

    _box_edge(*SEP)

    _box_row(f"{Fore.CYAN}{Style.BRIGHT}  LIVE METRICS")

    cpu = collector.cpu
    c   = Fore.RED if cpu >= 90 else Fore.YELLOW if cpu >= 70 else Fore.GREEN
    _metric_row("CPU", f"{c}{Style.BRIGHT}{cpu:5.1f}%{Style.RESET_ALL}", _bar(cpu))
    _box_row(f"  {Fore.LIGHTBLACK_EX}        trend  {_spark(collector.cpu_hist)}")

    import psutil as _ps
    vm  = _ps.virtual_memory()
    ram = collector.ram
    ram_used_gb = vm.used / 1024 / 1024 / 1024
    c   = Fore.RED if ram >= 90 else Fore.YELLOW if ram >= 70 else Fore.GREEN
    _metric_row("RAM", f"{c}{Style.BRIGHT}{ram:5.1f}%{Style.RESET_ALL}", _bar(ram),
                f"{ram_used_gb:.1f}/{specs.ram_total} GB")
    _box_row(f"  {Fore.LIGHTBLACK_EX}        trend  {_spark(collector.ram_hist)}")

    gt = collector.gpu_t
    gu = collector.gpu_u
    gv = gpu.vram_used

    if gt is not None or gu is not None:
        gt_str = f"{Fore.RED if (gt or 0) >= 85 else Fore.YELLOW if (gt or 0) >= 70 else Fore.GREEN}{Style.BRIGHT}{gt:5.1f}°C{Style.RESET_ALL}" if gt is not None else f"{Fore.LIGHTBLACK_EX}  n/a  "
        bar_val = gt if gt is not None else 0
        extra_parts = []
        if gu is not None:
            extra_parts.append(f"load {gu:.0f}%")
        if gv and gpu.vram_total:
            extra_parts.append(f"VRAM {gv}/{gpu.vram_total}MB")
        extra_str = "  ".join(extra_parts)[:29] 
        _metric_row("GPU", gt_str, _bar(bar_val, total=100), extra_str)
        if collector.gpu_t_hist:
            _box_row(f"  {Fore.LIGHTBLACK_EX}        trend  {_spark(collector.gpu_t_hist)}")
    else:
        _box_row(f"  {Fore.LIGHTBLACK_EX}  GPU    no real-time data available")

    _box_edge(*SEP)

    dr = collector.disk_r
    dw = collector.disk_w
    _box_row(
        f"  {Fore.WHITE}{Style.BRIGHT}DISK I/O  "
        f"{Fore.GREEN}R {dr:7.2f} MB/s"
        f"{Fore.LIGHTBLACK_EX}  ·  "
        f"{Fore.YELLOW}W {dw:7.2f} MB/s"
    )
    _box_row(f"  {Fore.LIGHTBLACK_EX}  read   {_spark(collector.disk_r_hist)}")
    _box_row(f"  {Fore.LIGHTBLACK_EX}  write  {_spark(collector.disk_w_hist)}")

    nd = collector.net_d
    nu = collector.net_u
    _box_row(
        f"  {Fore.WHITE}{Style.BRIGHT}NETWORK   "
        f"{Fore.GREEN}▼ {nd:7.1f} KB/s"
        f"{Fore.LIGHTBLACK_EX}  ·  "
        f"{Fore.YELLOW}▲ {nu:7.1f} KB/s"
    )
    _box_row(f"  {Fore.LIGHTBLACK_EX}  recv   {_spark(collector.net_d_hist)}")
    _box_row(f"  {Fore.LIGHTBLACK_EX}  send   {_spark(collector.net_u_hist)}")

    _box_edge(*SEP)

    if alerts:
        _box_row(f"{Fore.YELLOW}{Style.BRIGHT}  ALERT RULES")
        for a in alerts:
            kill_tag = f"  {Fore.LIGHTBLACK_EX}→ kill [{a.kill_proc}]" if a.kill_proc else ""
            _box_row(f"  {Fore.LIGHTBLACK_EX}· {Fore.WHITE}{a.label()}{kill_tag}")
    else:
        _box_row(f"{Fore.LIGHTBLACK_EX}  No alert rules  (monitoring only)")

    _box_edge(*BOT)


def _kill_process(name: str) -> bool:
    try:
        import psutil
        killed = 0
        for proc in psutil.process_iter(["pid", "name"]):
            if name in proc.info["name"].lower():
                proc.kill()
                killed += 1
                log.info(f"Killed PID {proc.info['pid']} ({proc.info['name']})")
        return killed > 0
    except Exception as e:
        log.warning(f"Kill process failed: {e}")
        return False


def _evaluate_alerts(collector: _StatsCollector, alerts: list[_Alert]) -> None:
    metric_map = {
        "cpu":      lambda: collector.cpu,
        "ram":      lambda: collector.ram,
        "gpu_temp": lambda: collector.gpu_t or 0.0,
        "gpu_load": lambda: collector.gpu_u or 0.0,
    }
    for alert in alerts:
        getter = metric_map.get(alert.metric)
        if not getter:
            continue
        val = getter()
        if alert.evaluate(val):
            msg = f"ALERT: {alert.label()} — current {val:.1f}"
            warn(msg)
            log.warning(msg)
            webhook.notify_custom(
                f"🚨 SysSentinel — {alert.metric.upper()} Alert",
                f"Threshold breached: **{alert.label()}**\nCurrent: `{val:.1f}`",
                {"Metric": alert.metric.upper(), "Value": f"{val:.1f}", "Threshold": str(alert.threshold)},
            )
            if alert.kill_proc:
                killed = _kill_process(alert.kill_proc)
                result = "killed" if killed else "not found"
                info(f"Process '{alert.kill_proc}' — {result}")
                webhook.notify_custom(
                    "⚙️ SysSentinel — Process Action",
                    f"Attempted to kill `{alert.kill_proc}` — **{result}**",
                    {"Process": alert.kill_proc, "Result": result},
                )


def _configure_alerts() -> list[_Alert]:
    alerts: list[_Alert] = []
    print()
    info("Alert Rule Setup — press Enter with no metric to finish.")
    info("Metrics: cpu, ram, gpu_temp, gpu_load")
    print()

    while True:
        raw = ask("Metric to watch (or blank to finish)").strip().lower()
        if not raw:
            break
        if raw not in ("cpu", "ram", "gpu_temp", "gpu_load"):
            error("Unknown metric. Choose: cpu, ram, gpu_temp, gpu_load")
            continue

        unit = "°C" if "temp" in raw else "%"
        threshold = ask_float(f"Alert when {raw.upper()} exceeds ({unit})", min_val=1.0)
        hold_secs = ask_float("Hold duration before firing (seconds)", min_val=1.0)
        kill_proc = ask("Process name to kill on alert (blank to skip)").strip()

        a = _Alert(raw, threshold, hold_secs, kill_proc)
        alerts.append(a)
        success(f"Rule added: {a.label()}")
        print()

    return alerts

def run() -> None:
    section_header("SysSentinel — System Monitor")
    log.info("SysSentinel started")

    if not _ensure_psutil():
        return

    print()
    info("Detecting hardware...")

    gpu   = _detect_gpu_static()
    specs = _collect_specs()

    if gpu.source != "none":
        success(f"GPU: {gpu.name} ({gpu.vendor})  {gpu.vram_total} MB VRAM")
    else:
        warn("GPU: not detected — install pynvml (NVIDIA) or pywmi (Windows)")

    info(f"CPU: {specs.cpu_name}  {specs.cpu_cores}C/{specs.cpu_threads}T  {specs.cpu_freq_max} GHz")
    info(f"RAM: {specs.ram_total} GB")
    print()

    mode = ask_choice("Mode", ["monitor-only", "monitor+alerts"])
    alerts: list[_Alert] = []

    if mode == "monitor+alerts":
        alerts = _configure_alerts()
        if not alerts:
            info("No rules — switching to monitor-only.")

    duration = ask_int("Monitor duration (seconds, 0 = until Ctrl+C)", min_val=0)
    info("Starting — collecting baseline...")

    collector = _StatsCollector(gpu)
    collector.start()
    time.sleep(1.5) 

    start_time = time.time()
    end_time   = (start_time + duration) if duration > 0 else float("inf")

    webhook.notify_custom(
        "📊 SysSentinel Started",
        f"System monitoring active.\nCPU: {specs.cpu_name}\nGPU: {gpu.name}",
        {"Mode": mode, "Alerts": str(len(alerts)), "Duration": f"{duration}s" if duration else "∞"},
    )

    try:
        while time.time() < end_time:
            wait_if_paused()
            elapsed = int(time.time() - start_time)
            _render_dashboard(collector, gpu, specs, alerts, elapsed)
            if alerts:
                _evaluate_alerts(collector, alerts)
            time.sleep(_SAMPLE_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        collector.stop()

    elapsed_total = int(time.time() - start_time)
    success(f"SysSentinel ended — {elapsed_total}s monitored.")

    webhook.notify_custom(
        "📊 SysSentinel Stopped",
        f"Session ended after {elapsed_total}s.",
        {
            "Peak CPU":      f"{max(collector.cpu_hist,  default=0):.1f}%",
            "Peak RAM":      f"{max(collector.ram_hist,  default=0):.1f}%",
            "Peak GPU temp": f"{max(collector.gpu_t_hist, default=0):.1f}°C" if collector.gpu_t_hist else "N/A",
            "Peak GPU load": f"{max(collector.gpu_u_hist, default=0):.1f}%" if collector.gpu_u_hist else "N/A",
        },
    )
    log.info(f"SysSentinel done. Elapsed={elapsed_total}s")