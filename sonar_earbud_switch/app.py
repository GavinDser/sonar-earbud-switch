"""主循环：读耳机状态 -> 切换 Sonar 路由。

只在状态变化时切换一次，不和 Sonar 自己对 Arctis 等设备的自动切换抢。
切到耳机前记下当时的路由，放回仓时还原；不知道时用配置里的回退设备。
"""
import ctypes
import logging
import os
import time

from . import config, drivers, sonar
from .osd import Osd
from .volume_keys import VolumeKeys

log = logging.getLogger("sonar_earbud_switch")


def _single_instance():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, "Local\\sonar-earbud-switch")
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        return None
    return handle


def _earbud_routes(cfg):
    out = sonar.find_device(cfg["earbuds"]["output"], "render")
    mic = sonar.find_device(cfg["earbuds"]["mic"], "capture")
    if not out:
        raise RuntimeError(f"找不到耳机输出设备：{cfg['earbuds']['output']}")
    r = {role: out for role in sonar.OUTPUT_ROLES}
    if mic:
        r["mic"] = mic
    return r


def _fallback_routes(cfg):
    r = {}
    out = cfg["fallback"]["output"] and sonar.find_device(cfg["fallback"]["output"], "render")
    mic = cfg["fallback"]["mic"] and sonar.find_device(cfg["fallback"]["mic"], "capture")
    if out:
        r.update({role: out for role in sonar.OUTPUT_ROLES})
    if mic:
        r["mic"] = mic
    return r


def run():
    logging.basicConfig(
        filename=os.path.join(config.ROOT, "switch.log"),
        level=logging.INFO,
        format="%(asctime)s %(message)s",
    )
    mutex = _single_instance()  # noqa: F841  进程存活期间持有
    if mutex is None:
        log.info("already running, exit")
        return 0
    cfg = config.load()
    t = cfg["timing"]
    log.info("started, driver=%s", cfg["earbuds"]["driver"])

    osd = None
    if cfg["osd"]["enabled"]:
        osd = Osd(cfg["osd"]["x"], cfg["osd"]["y"], cfg["osd"]["duration"])
        osd.start()
    keys = None
    if cfg["volume_keys"]["enabled"]:
        keys = VolumeKeys(cfg["volume_keys"]["step"], osd)
        keys.start()

    def notify(text):
        if osd:
            osd.show(text)

    def set_active(on):
        if keys:
            (keys.active.set if on else keys.active.clear)()

    applied = False  # 当前是否已切到耳机
    before = None  # 切到耳机前的路由
    try:  # 重启时耳机可能已连着，接收器不会再报，按 Sonar 当前路由初始化
        out = sonar.find_device(cfg["earbuds"]["output"], "render")
        applied = bool(out) and sonar.routes().get("game", "").lower() == out.lower()
    except Exception as e:
        log.warning("initial state unknown: %s", e)
    set_active(applied)
    log.info("initial on=%s", applied)

    drv = drivers.load(cfg["earbuds"]["driver"])
    conn = in_case = None  # 驱动报的原始状态
    want = None  # 推出来的目标状态
    want_at = 0.0
    next_try = 0.0

    while True:
        try:
            if not drv.open():
                time.sleep(5)
                continue
            log.info("receiver opened")
            while True:
                upd = drv.read(200)
                if upd:
                    log.info("%s", upd.get("raw", upd))
                    if "connected" in upd:
                        conn = upd["connected"]
                        if not conn:
                            in_case = None  # 断开后仓内状态不再可信
                    if "in_case" in upd:
                        in_case = upd["in_case"]

                # 断开 -> 关；仓内状态已知 -> 取出就开、全放回就关；
                # 未知（开盖就会连上）-> 连上稳定一段时间才开
                new = None if conn is None else (False if not conn else (True if in_case is None else not in_case))
                if new != want:
                    want, want_at = new, time.monotonic()

                now = time.monotonic()
                if want:
                    delay = t["unknown_state_delay"] if in_case is None else t["takeout_debounce"]
                else:
                    delay = t["putback_debounce"]
                if want is None or want == applied or now - want_at < delay or now < next_try:
                    continue
                try:
                    if want:
                        target = _earbud_routes(cfg)
                        cur = sonar.routes()
                        if cur.get("game", "").lower() != target["game"].lower():
                            before = cur
                        sonar.set_routes(target)
                        notify(f"Switched to {sonar.device_name(target['game'])}")
                    else:
                        target = before or _fallback_routes(cfg)
                        if target:
                            sonar.set_routes(target)
                            notify(f"Switched back to {sonar.device_name(target['game'])}" if "game" in target else "Switched back")
                        before = None
                    applied = want
                    set_active(applied)
                    log.info("switched %s", "ON" if applied else "OFF")
                except Exception as e:
                    next_try = now + t["retry"]
                    log.warning("sonar switch failed, retrying: %s", e)
        except Exception as e:
            log.info("receiver lost: %s", e)
            set_active(False)
            if applied and before:
                try:
                    sonar.set_routes(before)
                except Exception as e2:
                    log.warning("restore failed: %s", e2)
            applied, before, conn, in_case, want = False, None, None, None, None
            time.sleep(3)
        finally:
            drv.close()
