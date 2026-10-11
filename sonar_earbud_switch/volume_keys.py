"""接管系统音量键，改调 Sonar Master。

Windows 默认输出是 "Sonar - Gaming"，系统音量键只会动 Game 通道，
Chat（Discord）等不跟着变。启用时用低级键盘钩子吞掉音量加/减键。
"""
import ctypes
import ctypes.wintypes as wt
import logging
import queue
import threading

from . import sonar

log = logging.getLogger(__name__)

VK_VOLUME_DOWN, VK_VOLUME_UP = 0xAE, 0xAF
WH_KEYBOARD_LL, WM_KEYDOWN, WM_SYSKEYDOWN = 13, 0x0100, 0x0104


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wt.DWORD),
        ("scanCode", wt.DWORD),
        ("flags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wt.WPARAM, wt.LPARAM)
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD]
user32.SetWindowsHookExW.restype = wt.HHOOK
user32.CallNextHookEx.argtypes = [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t


class VolumeKeys:
    def __init__(self, step, osd=None):
        self.step = step
        self.osd = osd
        self.active = threading.Event()  # 只在耳机在用时接管
        self.q = queue.Queue()
        self._proc = HOOKPROC(self._hook)  # 保持引用，防止被回收

    def start(self):
        threading.Thread(target=self._hook_loop, daemon=True).start()
        threading.Thread(target=self._worker, daemon=True).start()

    def _hook(self, code, wparam, lparam):
        if code == 0 and self.active.is_set():
            vk = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents.vkCode
            if vk in (VK_VOLUME_UP, VK_VOLUME_DOWN):
                if wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    self.q.put(self.step if vk == VK_VOLUME_UP else -self.step)
                return 1  # 吞掉，Windows 不再改 Game
        return user32.CallNextHookEx(None, code, wparam, lparam)

    def _hook_loop(self):
        if not user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, None, 0):
            log.warning("keyboard hook failed: %s", ctypes.get_last_error())
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            pass

    def _worker(self):
        while True:
            delta = self.q.get()
            while not self.q.empty():  # 连按/旋钮快转时合并
                delta += self.q.get_nowait()
            try:
                cur = sonar.master_volume()
                new = round(min(1.0, max(0.0, cur + delta)), 2)
                sonar.set_master_volume(new)
                log.info("master %.2f -> %.2f", cur, new)
                if self.osd:
                    self.osd.show(f"Sonar Master  {round(new * 100)}%")
            except Exception as e:
                log.warning("master volume failed: %s", e)
