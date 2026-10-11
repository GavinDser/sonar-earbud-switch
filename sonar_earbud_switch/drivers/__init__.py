"""耳机检测驱动。

每个驱动是一个模块，导出 `Driver` 类：

    class Driver:
        def open(self) -> bool            # 找到并打开设备；没插返回 False
        def read(self, timeout_ms) -> dict | None
            # 读一条状态更新，可能包含：
            #   "connected": bool  耳机是否和接收器连着
            #   "in_case":   bool  是否全部在充电仓里（不知道就不给）
            # 设备断开时抛异常
        def close(self)

模块还要导出：
    DISPLAY_NAME    人看的名字
    DEVICE_KEYWORD  Sonar 设备名里的关键字（自动配置用）
    detect() -> bool  接收器是否插在这台电脑上

新增耳机：在本目录加一个模块，并加进下面的 DRIVERS。
"""
import importlib

DRIVERS = ["rog_cetra_open"]


def module(name):
    return importlib.import_module(f"{__name__}.{name}")


def load(name):
    return module(name).Driver()


def detect_all():
    """返回插在本机上的驱动模块名列表。"""
    found = []
    for name in DRIVERS:
        try:
            if module(name).detect():
                found.append(name)
        except Exception:
            pass
    return found
