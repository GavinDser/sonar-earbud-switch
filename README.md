# sonar-earbud-switch

[English](#english) | [中文](#中文)

Automatically switch **SteelSeries Sonar** output/mic when you take wireless earbuds out of their case — and switch back when you put them away. Built for the **ROG Cetra Open Wireless** (2.4 GHz receiver), with a small driver interface for adding other earbuds.

> Not affiliated with SteelSeries or ASUS/ROG. Uses Sonar's undocumented local API and HID reports observed on real hardware; either may change with software/firmware updates.

## English

### Why

Sonar auto-switches to SteelSeries headsets (e.g. Arctis Nova Pro) because their base station reports on/off. Third-party earbuds with a USB receiver look "always connected" to Windows, so Sonar never switches back. This tool reads the receiver's own status reports instead.

### Features

- **Take earbuds out → switch to them**; **put them back → restore** whatever Sonar was using before (e.g. your Arctis). Falls back to a configured device if unknown.
- Opening the case lid alone does **not** switch.
- **Volume keys → Sonar Master** while the earbuds are active (Windows volume keys otherwise only change Sonar's *Game* channel, so Discord/Chat stays loud). Shows a small on-screen indicator.
- Devices matched **by name**, not by ID, so changing USB ports is fine.
- Starts with Windows; single instance; logs to `switch.log`.

### Requirements

- Windows 10/11, SteelSeries GG with Sonar in **Classic** mode
- Python 3.11+ (with tcl/tk, the default in the python.org installer)
- A supported receiver plugged in: ROG Cetra Open Wireless

### Install

```powershell
git clone https://github.com/GavinDser/sonar-earbud-switch.git
cd sonar-earbud-switch
powershell -ExecutionPolicy Bypass -File install.ps1
```

The installer creates a virtual environment, **auto-detects** Sonar, your receiver and your audio devices, asks which output/mic to fall back to (Enter = your current Sonar device), writes `config.toml`, adds a startup shortcut and starts it.

Re-run detection any time: `.venv\Scripts\python.exe -m sonar_earbud_switch setup`.
Uninstall: `powershell -ExecutionPolicy Bypass -File uninstall.ps1`.

### Configuration

`config.toml` (generated): earbud/fallback device name keywords, timings, volume-key step, on-screen indicator position. Restart after editing (re-run `install.ps1`, or sign out/in).

### Known limitations

- Sonar **Classic** mode only.
- No wear detection — the Cetra Open does not report it. "Taken out of case" is the trigger.
- If the earbuds connect without reporting their in-case state, the tool falls back to "connected for 6 s".
- Sonar's UI does not refresh Master volume changed via its API; reopen the window to see it.
- While active, Windows' own volume flyout does not appear (keys are intercepted).

### Adding other earbuds

Add a module in `sonar_earbud_switch/drivers/` exporting `DISPLAY_NAME`, `DEVICE_KEYWORD`, `detect()` and a `Driver` class (`open` / `read` / `close`, see `drivers/__init__.py`), then list it in `DRIVERS`. Use a HID listener to find which reports change when you open the case, take buds out, and put them back. PRs welcome.

## 中文

### 解决什么问题

Sonar 能自动切换 SteelSeries 耳机（如 Arctis Nova Pro），因为它们的基座会上报开/关机状态。第三方带 USB 接收器的耳机，在 Windows 看来永远是“已连接”，所以 Sonar 不会切回去。这个工具直接读接收器自己上报的状态。

### 功能

- **从仓里取出耳机 → 切过去**；**放回仓 → 还原**之前在用的设备（比如 Arctis）；不知道之前是什么时切到配置的回退设备。
- 只打开仓盖**不会**切换。
- 耳机在用时，**音量键改调 Sonar Master**（否则 Windows 音量键只会动 Game 通道，Discord 声音降不下来），并在屏幕左上角显示音量。
- 设备**按名称匹配**，换 USB 口不受影响。
- 开机自启，只运行一个实例，日志在 `switch.log`。

### 环境要求

- Windows 10/11，SteelSeries GG，Sonar 使用 **Classic** 模式
- Python 3.11+（python.org 安装包默认带 tcl/tk）
- 插着受支持的接收器：ROG Cetra Open Wireless

### 安装

```powershell
git clone https://github.com/GavinDser/sonar-earbud-switch.git
cd sonar-earbud-switch
powershell -ExecutionPolicy Bypass -File install.ps1
```

安装脚本会建虚拟环境，**自动检测** Sonar、接收器和本机音频设备，让你选放回仓时切回哪个输出/麦克风（回车 = Sonar 当前设备），生成 `config.toml`，加入开机自启并启动。

重新检测：`.venv\Scripts\python.exe -m sonar_earbud_switch setup`
卸载：`powershell -ExecutionPolicy Bypass -File uninstall.ps1`

### 配置

`config.toml`（自动生成）：耳机/回退设备名称关键字、各种等待时间、音量步进、提示框位置。改完重新运行 `install.ps1` 或注销重登生效。

### 已知限制

- 只支持 Sonar **Classic** 模式。
- 没有佩戴检测（Cetra Open 不上报），以“从仓里取出”为准。
- 如果耳机连上时没报仓内状态，退回“连上满 6 秒才切”。
- 通过接口改的 Master 音量，Sonar 界面不会实时刷新，重开窗口可见。
- 接管期间按音量键不会弹出 Windows 自带的音量框。

### 支持其他耳机

在 `sonar_earbud_switch/drivers/` 加一个模块，导出 `DISPLAY_NAME`、`DEVICE_KEYWORD`、`detect()` 和 `Driver` 类（`open` / `read` / `close`，见 `drivers/__init__.py`），再加进 `DRIVERS`。用 HID 监听找出开盖、取出、放回时变化的报文即可。欢迎 PR。

## License

MIT
