"""ROG Cetra Open Wireless（2.4 GHz 接收器）。

接收器 VID 0B05 / PID 1CAC，厂商 HID 接口 usage page 0xFF00 会主动上报（实测）：

    cc 22 01 00 00 <mask>          耳塞连接位掩码；00 = 断开（盖上仓盖）
    cc 22 11 00 00 <mask> <xx>     仓内耳塞位掩码；03 = 两只都在仓里，00 = 都取出
    cc 22 12 00 00 <L> <仓> <R>    电量百分比（未使用）

开盖时耳塞就会连上，所以单看连接状态分不出“开盖”和“取出”。没有佩戴检测。
"""
import hid

VID, PID, USAGE_PAGE = 0x0B05, 0x1CAC, 0xFF00
BOTH_IN_CASE = 0x03

DISPLAY_NAME = "ROG Cetra Open Wireless"
DEVICE_KEYWORD = "ROG CETRA OPEN WIRELESS"  # Sonar/Windows 里输出和麦克风名称都含这个


def detect():
    return any(i["usage_page"] == USAGE_PAGE for i in hid.enumerate(VID, PID))


class Driver:
    def __init__(self):
        self.dev = None

    def open(self):
        for info in hid.enumerate(VID, PID):
            if info["usage_page"] == USAGE_PAGE:
                self.dev = hid.device()
                self.dev.open_path(info["path"])
                return True
        return False

    def read(self, timeout_ms):
        r = self.dev.read(64, timeout_ms)
        if len(r) < 7 or r[0] != 0xCC or r[1] != 0x22:
            return None
        if r[2] == 0x01:
            return {"connected": r[5] != 0, "raw": f"conn={r[5]:02x}"}
        if r[2] == 0x11:
            return {"in_case": r[5] == BOTH_IN_CASE, "raw": f"incase={r[5]:02x}"}
        return None

    def close(self):
        if self.dev is not None:
            self.dev.close()
            self.dev = None
