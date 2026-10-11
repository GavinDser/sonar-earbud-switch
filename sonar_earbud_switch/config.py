import os
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.toml")

DEFAULTS = {
    "earbuds": {"driver": "rog_cetra_open", "output": "", "mic": ""},
    "fallback": {"output": "", "mic": ""},
    "timing": {
        "takeout_debounce": 0.5,
        "unknown_state_delay": 6.0,
        "putback_debounce": 1.0,
        "retry": 3.0,
    },
    "volume_keys": {"enabled": True, "step": 0.02},
    "osd": {"enabled": True, "x": 50, "y": 50, "duration": 1.5},
}


def load(path=CONFIG_PATH):
    with open(path, "rb") as f:
        user = tomllib.load(f)
    cfg = {k: dict(v) for k, v in DEFAULTS.items()}
    for section, values in user.items():
        cfg.setdefault(section, {}).update(values)
    return cfg


def _q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def write(cfg, path=CONFIG_PATH):
    e, f, t, v, o = cfg["earbuds"], cfg["fallback"], cfg["timing"], cfg["volume_keys"], cfg["osd"]
    text = f"""# sonar-earbud-switch 配置（由 setup 生成，可手改）
# 设备按名称关键字匹配：不区分大小写，取 Sonar 设备列表里第一个名称包含该关键字的物理设备。

[earbuds]            # 要自动切换的耳机
driver = {_q(e["driver"])}
output = {_q(e["output"])}
mic = {_q(e["mic"])}

[fallback]           # 放回仓时，如果不知道之前用的是什么设备，就切到这里
output = {_q(f["output"])}
mic = {_q(f["mic"])}

[timing]             # 秒
takeout_debounce = {t["takeout_debounce"]}     # 取出耳塞后多久切过去
unknown_state_delay = {t["unknown_state_delay"]}  # 不知道耳塞在不在仓里时，连上多久才切
putback_debounce = {t["putback_debounce"]}     # 放回仓/断开后多久切回
retry = {t["retry"]}                # Sonar 调用失败后多久重试

[volume_keys]        # 耳机在用时，系统音量键改调 Sonar Master
enabled = {str(v["enabled"]).lower()}
step = {v["step"]}

[osd]                # 屏幕提示
enabled = {str(o["enabled"]).lower()}
x = {o["x"]}
y = {o["y"]}
duration = {o["duration"]}
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
