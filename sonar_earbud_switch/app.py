"""主循环：读耳机状态 -> 让耳机的音频设备在 Windows 里出现/消失，切换交给 Sonar。

耳机接收器一直插着，Sonar 永远认为耳机“已连接”，它的设备优先级列表不会生效。
放回仓时把耳机的输出/麦克风端点隐藏，Sonar 就按列表回退（比如 Arctis 开着就
回 Arctis，关着就回音箱）；取出时重新显示，Sonar 再按列表决定是否切回来。
"""
import ctypes
import logging
import os
import time

from . import config, drivers, endpoints, sonar
from .osd import Osd
from .volume_keys import VolumeKeys

log = logging.getLogger("sonar_earbud_switch")

SETTLE_SECS = 1.5  # 端点变化后等 Sonar 完成切换再读结果
ROUTE_POLL_SECS = 1.0


def _single_instance():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, "Local\\sonar-earbud-switch")
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        return None
    return handle


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

    endpoints.show_all()  # 上次异常退出时可能还隐藏着

    osd = None
    if cfg["osd"]["enabled"]:
        osd = Osd(cfg["osd"]["x"], cfg["osd"]["y"], cfg["osd"]["duration"])
        osd.start()
    keys = None
    if cfg["volume_keys"]["enabled"]:
        keys = VolumeKeys(cfg["volume_keys"]["step"], osd)
        keys.start()

    out_id = mic_id = None  # 耳机端点 ID，显示状态下按名称查到后缓存（隐藏后就查不到了）

    def resolve_ids():
        nonlocal out_id, mic_id
        out_id = sonar.find_device(cfg["earbuds"]["output"], "render") or out_id
        mic_id = sonar.find_device(cfg["earbuds"]["mic"], "capture") or mic_id

    def notify_current():
        time.sleep(SETTLE_SECS)
        game = sonar.routes().get("game")
        if game and osd:
            osd.show(f"Sonar: {sonar.device_name(game)}")

    try:
        resolve_ids()
    except Exception as e:
        log.warning("resolve earbud devices failed: %s", e)

    drv = drivers.load(cfg["earbuds"]["driver"])
    hidden = False  # 当前是否已隐藏耳机端点
    conn = in_case = None  # 驱动报的原始状态
    want = None  # 推出来的目标：True = 在用（显示），False = 收起（隐藏）
    want_at = 0.0
    next_try = 0.0
    next_poll = 0.0

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

                now = time.monotonic()

                # 音量键只在 Sonar 正在用耳机时接管
                if keys and now >= next_poll:
                    next_poll = now + ROUTE_POLL_SECS
                    try:
                        using = bool(out_id) and sonar.routes().get("game", "").lower() == out_id.lower()
                        (keys.active.set if using else keys.active.clear)()
                    except Exception:
                        keys.active.clear()

                # 断开 -> 收起；仓内状态已知 -> 取出就在用、全放回就收起；
                # 未知（开盖就会连上）-> 连上稳定一段时间才算在用
                new = None if conn is None else (False if not conn else (True if in_case is None else not in_case))
                if new != want:
                    want, want_at = new, now
                if want:
                    delay = t["unknown_state_delay"] if in_case is None else t["takeout_debounce"]
                else:
                    delay = t["putback_debounce"]
                if want is None or want == (not hidden) or now - want_at < delay or now < next_try:
                    continue

                try:
                    if want:
                        endpoints.show_all()
                        hidden = False
                        log.info("earbuds out: shown")
                        if cfg["switching"]["force_on_takeout"]:
                            time.sleep(SETTLE_SECS)
                            resolve_ids()
                            r = {role: out_id for role in sonar.OUTPUT_ROLES}
                            if mic_id:
                                r["mic"] = mic_id
                            sonar.set_routes(r)
                    else:
                        resolve_ids()
                        ids = [i for i in (out_id, mic_id) if i]
                        if not ids:
                            raise RuntimeError(f"找不到耳机设备：{cfg['earbuds']['output']}")
                        endpoints.hide(ids)
                        hidden = True
                        log.info("earbuds away: hidden")
                    notify_current()
                except Exception as e:
                    next_try = now + t["retry"]
                    log.warning("switch failed, retrying: %s", e)
        except Exception as e:
            log.info("receiver lost: %s", e)
            if keys:
                keys.active.clear()
            try:
                endpoints.show_all()
            except Exception as e2:
                log.warning("restore endpoints failed: %s", e2)
            hidden, conn, in_case, want = False, None, None, None
            time.sleep(3)
        finally:
            drv.close()
