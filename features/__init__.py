from . import (
    autotyper,
    automove,
    mouse_simulation,
    screen_capture,
    timed_execution,
    custom_key_sequence,
    mouse_360,
    auto_clicker,
    webhook_settings,
    sys_sentinel,
    net_watch,
)

FEATURE_MAP = {
    1:  autotyper,
    2:  automove,
    3:  mouse_simulation,
    4:  screen_capture,
    5:  timed_execution,
    6:  custom_key_sequence,
    7:  mouse_360,
    8:  auto_clicker,
    9:  webhook_settings,
    10: sys_sentinel,
    11: net_watch,
}