"""SteelSeries Sonar 本地 Web API（非官方，GG 自带，只监听 127.0.0.1）。

地址发现：coreProps.json -> GG `/subApps` -> sonar.webServerAddress。
端口每次 GG 启动都可能变，所以每次调用前现查。仅支持 Classic 模式。
"""
import json
import os
import ssl
import urllib.parse
import urllib.request

CORE_PROPS = os.path.join(
    os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
    "SteelSeries",
    "SteelSeries Engine 3",
    "coreProps.json",
)
OUTPUT_ROLES = ("game", "chat", "media", "aux")
ALL_ROLES = OUTPUT_ROLES + ("mic",)
TIMEOUT = 5


def base_url():
    with open(CORE_PROPS, encoding="utf-8") as f:
        gg = json.load(f)["ggEncryptedAddress"]
    ctx = ssl._create_unverified_context()  # GG 本地自签证书，只连 127.0.0.1
    with urllib.request.urlopen(f"https://{gg}/subApps", context=ctx, timeout=TIMEOUT) as r:
        return json.load(r)["subApps"]["sonar"]["metadata"]["webServerAddress"]


def _get(path):
    with urllib.request.urlopen(base_url() + path, timeout=TIMEOUT) as r:
        return json.load(r)


def _put(path):
    req = urllib.request.Request(base_url() + path, method="PUT")
    urllib.request.urlopen(req, timeout=TIMEOUT).read()


def mode():
    return _get("/mode/")


def devices():
    return _get("/audioDevices")


def find_device(keyword, flow):
    """按名称关键字找物理设备（不区分大小写，跳过 Sonar 自己的虚拟设备）。

    flow: "render"（输出）或 "capture"（麦克风）。找不到返回 None。
    """
    kw = keyword.lower()
    for d in devices():
        if d.get("isVad") or d["dataFlow"] != flow:
            continue
        if kw in d["friendlyName"].lower():
            return d["id"]
    return None


def device_name(device_id):
    """"Headphones (4- Arctis Nova Pro Wireless)" -> "Arctis Nova Pro Wireless"。"""
    for d in devices():
        if d["id"].lower() == device_id.lower():
            name = d["friendlyName"]
            if "(" in name:
                name = name[name.find("(") + 1 : name.rfind(")")]
            return name.split("- ", 1)[-1]
    return device_id


def routes():
    """当前 Classic 路由：{role: deviceId}。"""
    return {x["id"]: x["deviceId"] for x in _get("/classicRedirections") if x["id"] in ALL_ROLES}


def set_routes(role_devices):
    for role, dev in role_devices.items():
        _put(f"/classicRedirections/{role}/deviceId/{urllib.parse.quote(dev, safe='')}")


def device_volume(device_id):
    """物理设备音量（Sonar 混音之后、送进设备之前的最后一级，所有通道都受影响）。"""
    for d in _get("/volumeSettings/devices/volumes"):
        if d["deviceId"].lower() == device_id.lower():
            return d["volume"]
    raise LookupError(f"no volume for device {device_id}")


def set_device_volume(device_id, v):
    _put(f"/volumeSettings/devices/{urllib.parse.quote(device_id, safe='')}/volume/{v}")
