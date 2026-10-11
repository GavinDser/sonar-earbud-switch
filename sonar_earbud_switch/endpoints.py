"""隐藏/显示 Windows 音频端点（不需要管理员权限）。

端点隐藏后，Sonar 认为设备断开，按它自己的设备优先级列表回退；
重新显示后，Sonar 也会按列表决定是否切回来。

用的是 Windows 未公开的 IPolicyConfig::SetEndpointVisibility（音频设置工具常用）。
"""
import ctypes
import json
import os
from ctypes import wintypes as wt

from . import config

STATE_PATH = os.path.join(config.ROOT, "hidden_endpoints.json")

CLSID_PolicyConfigClient = "{870af99c-171d-4f9e-af0d-e63df40c2bc9}"
IID_IPolicyConfig = "{f8679f50-850a-41cf-9c72-430f290290c8}"
VTBL_SET_ENDPOINT_VISIBILITY = 14  # IUnknown(3) + 11 个方法之后

ole32 = ctypes.OleDLL("ole32")


class GUID(ctypes.Structure):
    _fields_ = [("d1", wt.DWORD), ("d2", wt.WORD), ("d3", wt.WORD), ("d4", ctypes.c_ubyte * 8)]


def _guid(s):
    g = GUID()
    ole32.CLSIDFromString(ctypes.c_wchar_p(s), ctypes.byref(g))
    return g


def set_visible(endpoint_id, visible):
    ole32.CoInitializeEx(None, 0x2)  # COINIT_APARTMENTTHREADED；同线程重复调用无害
    ptr = ctypes.c_void_p()
    clsid, iid = _guid(CLSID_PolicyConfigClient), _guid(IID_IPolicyConfig)
    ole32.CoCreateInstance(ctypes.byref(clsid), None, 1, ctypes.byref(iid), ctypes.byref(ptr))
    try:
        vtbl = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        fn = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int)(
            vtbl[VTBL_SET_ENDPOINT_VISIBILITY]
        )
        fn(ptr, endpoint_id, 1 if visible else 0)
    finally:
        release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtbl[2])
        release(ptr)


# 隐藏的端点记到文件里：程序崩溃或被结束后，下次启动先恢复，避免设备一直“消失”


def _load():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def _save(ids):
    if ids:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(ids, f)
    elif os.path.exists(STATE_PATH):
        os.remove(STATE_PATH)


def hide(ids):
    _save(sorted(set(_load()) | set(ids)))
    for i in ids:
        set_visible(i, False)


def show_all():
    for i in _load():
        set_visible(i, True)
    _save([])
