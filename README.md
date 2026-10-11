# sonar-earbud-switch

[English](#english) | [中文](#中文)

Automatically switch **SteelSeries Sonar** output/mic when you take wireless earbuds out of their case — and switch back when you put them away. Built for the **ROG Cetra Open Wireless** (2.4 GHz receiver), with a small driver interface for adding other earbuds.

> Not affiliated with SteelSeries or ASUS/ROG. Uses Sonar's undocumented local API and HID reports observed on real hardware; either may change with software/firmware updates.

## English

### Why

Sonar has a device priority list and falls back along it when a device disconnects. Third-party earbuds with a USB receiver look "always connected" to Windows, so Sonar never falls back. This tool reads the receiver's own status reports and, when the earbuds are put away, **hides their audio devices in Windows** (no admin needed) — Sonar sees a disconnect and picks the next device on **its own list**. Take them out and the devices reappear; Sonar decides again.

Example list `Arctis > earbuds > speakers`: put the earbuds away → Arctis if it's on, otherwise speakers.

### Features

- **Take earbuds out → their devices appear**; **put them back → they disappear** and Sonar falls back per its priority list (output and mic).
- Optional `force_on_takeout`: always switch to the earbuds on take-out, even if a higher-priority device is on.
- Opening the case lid alone does **not** switch.
- **Volume keys scale all Sonar channels together** while the earbuds are active, via Sonar's API master value (Windows volume keys otherwise only change Sonar's *Game* channel, so Discord/Chat stays loud). Channel ratios are kept. Shows a small on-screen indicator.
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

The installer creates a virtual environment, **auto-detects** Sonar and your receiver, writes `config.toml`, adds a startup shortcut and starts it. Then order Sonar's device priority list the way you want.

Re-run detection any time: `.venv\Scripts\python.exe -m sonar_earbud_switch setup`.
Uninstall: `powershell -ExecutionPolicy Bypass -File uninstall.ps1`.

### Configuration

`config.toml` (generated): earbud device name keyword, `force_on_takeout`, timings, volume-key step, on-screen indicator position. Restart after editing (re-run `install.ps1`, or sign out/in).

If the tool is killed while the earbuds are hidden, it restores them on next start; `uninstall.ps1` restores them too. Manual fix: Windows Sound settings → enable the device.

### Known limitations

- Sonar **Classic** mode only.
- No wear detection — the Cetra Open does not report it. "Taken out of case" is the trigger.
- If the earbuds connect without reporting their in-case state, the tool falls back to "connected for 6 s".
- The API master value is not the master slider shown in Sonar's UI: it scales the channel volumes (visible on the "SteelSeries Sonar - Gaming/Chat/…" devices in Windows), so the UI master slider does not move.
- While active, Windows' own volume flyout does not appear (keys are intercepted).

### Adding other earbuds

Add a module in `sonar_earbud_switch/drivers/` exporting `DISPLAY_NAME`, `DEVICE_KEYWORD`, `detect()` and a `Driver` class (`open` / `read` / `close`, see `drivers/__init__.py`), then list it in `DRIVERS`. Use a HID listener to find which reports change when you open the case, take buds out, and put them back. PRs welcome.

## 中文

### 解决什么问题

Sonar 有设备优先级列表，设备断开时会按列表回退。第三方带 USB 接收器的耳机在 Windows 看来永远“已连接”，所以 Sonar 从不回退。这个工具读取接收器自己上报的状态，耳机放回仓时**在 Windows 里隐藏它的音频设备**（不需要管理员权限），Sonar 认为它断开了，就按**自己的列表**选下一个设备；取出时设备重新出现，再由 Sonar 决定。

例如列表 `Arctis > 耳机 > 音箱`：耳机放回仓 → Arctis 开着就回 Arctis，关着就回音箱。

### 功能

- **取出耳机 → 设备出现**；**放回仓 → 设备消失**，Sonar 按优先级列表回退（输出和麦克风都是）。
- 可选 `force_on_takeout`：取出时强制切到耳机，即使列表里更高优先级的设备开着。
- 只打开仓盖**不会**切换。
- 耳机在用时，**音量键让 Sonar 所有通道一起按比例变**（通过 Sonar 接口的 master 值；否则 Windows 音量键只会动 Game 通道，Discord 声音降不下来），并在屏幕左上角显示音量。
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

安装脚本会建虚拟环境，**自动检测** Sonar 和接收器，生成 `config.toml`，加入开机自启并启动。之后在 Sonar 里按你想要的顺序排好设备优先级列表。

重新检测：`.venv\Scripts\python.exe -m sonar_earbud_switch setup`
卸载：`powershell -ExecutionPolicy Bypass -File uninstall.ps1`

### 配置

`config.toml`（自动生成）：耳机设备名称关键字、`force_on_takeout`、各种等待时间、音量步进、提示框位置。改完重新运行 `install.ps1` 或注销重登生效。

如果程序在耳机被隐藏时被结束，下次启动会自动恢复；`uninstall.ps1` 也会恢复。手动恢复：Windows 声音设置 → 启用该设备。

### 已知限制

- 只支持 Sonar **Classic** 模式。
- 没有佩戴检测（Cetra Open 不上报），以“从仓里取出”为准。
- 如果耳机连上时没报仓内状态，退回“连上满 6 秒才切”。
- 接口里的 master 值不是 Sonar 界面上的“主控”滑块：它按比例缩放各通道音量（在 Windows 的 “SteelSeries Sonar - Gaming/Chat/…” 设备上能看到变化），所以界面上的主控不会动。
- 接管期间按音量键不会弹出 Windows 自带的音量框。

### 支持其他耳机

在 `sonar_earbud_switch/drivers/` 加一个模块，导出 `DISPLAY_NAME`、`DEVICE_KEYWORD`、`detect()` 和 `Driver` 类（`open` / `read` / `close`，见 `drivers/__init__.py`），再加进 `DRIVERS`。用 HID 监听找出开盖、取出、放回时变化的报文即可。欢迎 PR。

## License

MIT
