"""自动检测本机环境并生成 config.toml。

    python -m sonar_earbud_switch setup        # 交互，回车用默认值
    python -m sonar_earbud_switch setup --yes  # 全用默认值
"""
import os
import sys

from . import config, drivers, sonar


def _choose(title, options, default_idx, assume_yes):
    print(f"\n{title}")
    for i, name in enumerate(options, 1):
        mark = "  <- 默认 / default" if i - 1 == default_idx else ""
        print(f"  {i}. {name}{mark}")
    if assume_yes:
        return default_idx
    while True:
        ans = input(f"选择 / Choose 1-{len(options)}（回车 / Enter = {default_idx + 1}）: ").strip()
        if not ans:
            return default_idx
        if ans.isdigit() and 1 <= int(ans) <= len(options):
            return int(ans) - 1
        print("  输入无效 / Invalid input")


def run(argv):
    assume_yes = "--yes" in argv
    print("== sonar-earbud-switch 自动配置 / Auto setup ==")

    # 1. Sonar
    try:
        m = sonar.mode()
    except Exception as e:
        print(f"[x] 连不上 SteelSeries Sonar / Cannot reach SteelSeries Sonar: {e}")
        print("    请先启动 SteelSeries GG 并打开 Sonar。/ Start SteelSeries GG and enable Sonar first.")
        return 1
    print(f"[ok] Sonar 在运行 / Sonar is running, mode: {m}")
    if m != "classic":
        print("[!] 目前只支持 Classic 模式，请在 Sonar 里切到 Classic 后再运行。")
        print("    Only Classic mode is supported. Switch Sonar to Classic and run again.")
        return 1

    # 2. 耳机接收器
    found = drivers.detect_all()
    if not found:
        names = ", ".join(drivers.module(n).DISPLAY_NAME for n in drivers.DRIVERS)
        print("[x] 没检测到支持的耳机接收器，请插上接收器后重试。")
        print("    No supported earbud receiver found. Plug it in and try again.")
        print(f"    支持 / Supported: {names}")
        return 1
    if len(found) == 1:
        drv_name = found[0]
    else:
        idx = _choose(
            "检测到多个耳机接收器 / Multiple receivers found:",
            [drivers.module(n).DISPLAY_NAME for n in found],
            0,
            assume_yes,
        )
        drv_name = found[idx]
    drv = drivers.module(drv_name)
    print(f"[ok] 检测到耳机接收器 / Receiver found: {drv.DISPLAY_NAME}")

    kw = drv.DEVICE_KEYWORD
    if not sonar.find_device(kw, "render"):
        print(f"[!] Sonar 设备列表里没找到名称含 “{kw}” 的输出设备，切换可能失败。")
        print(f"    No output device containing \"{kw}\" in Sonar; switching may fail.")

    cfg = {k: dict(v) for k, v in config.DEFAULTS.items()}
    cfg["earbuds"].update(driver=drv_name, output=kw, mic=kw)

    # 3. 提示设置 Sonar 的设备优先级列表（放回仓切到哪由它决定）
    print("\n[i] 放回仓时切到哪个设备由 Sonar 的设备优先级列表决定，请在 Sonar 里排好顺序，")
    print("    例如：Arctis > 本耳机 > 音箱（Arctis 开着就回 Arctis，关着就回音箱）。")
    print("    Where audio goes on put-away is decided by Sonar's device priority list. Order it in Sonar,")
    print("    e.g. Arctis > these earbuds > speakers (back to Arctis if it's on, otherwise speakers).")

    # 4. 写配置
    if os.path.exists(config.CONFIG_PATH) and not assume_yes:
        ans = input("\nconfig.toml 已存在，覆盖？/ config.toml exists, overwrite? [y/N] ")
        if ans.strip().lower() != "y":
            print("未修改 / Unchanged.")
            return 0
    config.write(cfg)
    print(f"\n[ok] 已写入 / Written: {config.CONFIG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
