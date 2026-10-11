"""自动检测本机环境并生成 config.toml。

    python -m sonar_earbud_switch setup        # 交互，回车用默认值
    python -m sonar_earbud_switch setup --yes  # 全用默认值
"""
import os
import sys

from . import config, drivers, sonar


def _short(friendly):
    # "Speakers (Logitech G560 Gaming Speaker)" -> "Logitech G560 Gaming Speaker"
    # 去掉 Windows 加的 "4- " 这类编号前缀，编号会变
    name = friendly
    if "(" in name:
        name = name[name.find("(") + 1 : name.rfind(")")]
    head, sep, tail = name.partition("- ")
    return tail if sep and head.strip().isdigit() else name


def _choose(title, options, default_idx, assume_yes):
    print(f"\n{title}")
    for i, name in enumerate(options, 1):
        mark = "  <- 默认" if i - 1 == default_idx else ""
        print(f"  {i}. {name}{mark}")
    if assume_yes:
        return default_idx
    while True:
        ans = input(f"选择 1-{len(options)}（回车 = {default_idx + 1}）: ").strip()
        if not ans:
            return default_idx
        if ans.isdigit() and 1 <= int(ans) <= len(options):
            return int(ans) - 1
        print("  输入无效")


def run(argv):
    assume_yes = "--yes" in argv
    print("== sonar-earbud-switch 自动配置 ==")

    # 1. Sonar
    try:
        m = sonar.mode()
    except Exception as e:
        print(f"[x] 连不上 SteelSeries Sonar：{e}\n    请先启动 SteelSeries GG 并打开 Sonar。")
        return 1
    print(f"[ok] Sonar 在运行，模式：{m}")
    if m != "classic":
        print("[!] 目前只支持 Classic 模式，请在 Sonar 里切到 Classic 后再运行。")
        return 1

    # 2. 耳机接收器
    found = drivers.detect_all()
    if not found:
        names = ", ".join(drivers.module(n).DISPLAY_NAME for n in drivers.DRIVERS)
        print(f"[x] 没检测到支持的耳机接收器。请插上接收器后重试。\n    支持：{names}")
        return 1
    if len(found) == 1:
        drv_name = found[0]
    else:
        idx = _choose("检测到多个耳机接收器：", [drivers.module(n).DISPLAY_NAME for n in found], 0, assume_yes)
        drv_name = found[idx]
    drv = drivers.module(drv_name)
    print(f"[ok] 检测到耳机接收器：{drv.DISPLAY_NAME}")

    kw = drv.DEVICE_KEYWORD
    if not sonar.find_device(kw, "render"):
        print(f"[!] Sonar 设备列表里没找到名称含 “{kw}” 的输出设备，切换可能失败。")

    # 3. 回退设备（不知道之前用什么时，放回仓切到这里）
    devs = [d for d in sonar.devices() if not d.get("isVad") and kw.lower() not in d["friendlyName"].lower()]
    routes = sonar.routes()
    cfg = {k: dict(v) for k, v in config.DEFAULTS.items()}
    cfg["earbuds"].update(driver=drv_name, output=kw, mic=kw)

    for flow, role, label in (("render", "game", "输出"), ("capture", "mic", "麦克风")):
        opts = [d for d in devs if d["dataFlow"] == flow]
        if not opts:
            print(f"[!] 没找到其他{label}设备，回退{label}留空（放回仓时只还原之前的设备）。")
            continue
        cur = routes.get(role, "").lower()
        default = next((i for i, d in enumerate(opts) if d["id"].lower() == cur), 0)
        idx = _choose(f"耳机放回仓时切回哪个{label}设备？", [d["friendlyName"] for d in opts], default, assume_yes)
        cfg["fallback"]["output" if flow == "render" else "mic"] = _short(opts[idx]["friendlyName"])

    # 4. 写配置
    if os.path.exists(config.CONFIG_PATH) and not assume_yes:
        if input("\nconfig.toml 已存在，覆盖？[y/N] ").strip().lower() != "y":
            print("未修改。")
            return 0
    config.write(cfg)
    print(f"\n[ok] 已写入 {config.CONFIG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
