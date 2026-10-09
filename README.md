# Python-Host-Application-Lab

面向行式串口设备的原创 Python 上位机实验，重点展示可测试通信核心、协议边界与最小 PyQt5 交互界面。

![Python host application architecture](assets/images/architecture/python-host-application-overview.svg)

## Overview

本项目把上位机拆分为 GUI、应用协调、协议处理和可替换通信后端。核心逻辑不依赖 Qt 或真实串口，因此连接状态、命令编码、增量解析、超时和断连路径都能在主机环境中确定性测试；可选的 `pyserial` 后端负责连接真实串口，但本仓库不声明任何具体设备已经通过硬件验证。

## Platform & Technology

| Field | Value |
| --- | --- |
| Repository type | Original Python Host Application Lab |
| Language | Python 3.10+ |
| GUI | PyQt5（可选依赖） |
| Communication | 抽象串口接口、内存 Mock、可选 `pyserial` 适配器 |
| Protocol | UTF-8 行式文本、CRLF 发送结束符、增量接收解析 |
| Architecture | GUI → Application Core → Protocol / Communication Backend |
| Verification | pytest、Ruff、Mypy、覆盖率门槛、离屏 Mock GUI 收发、sdist/wheel 构建与安装 |

## Architecture

```text
User Input / Serial Bytes
          ↓
       PyQt5 GUI
          ↓
  HostApplication Core
      ↙          ↘
Command / Line   Connection State
   Protocol       Machine
          ↓
   SerialBackend Interface
      ↙          ↘
Mock Backend   pyserial Adapter
                    ↓
             External Device
```

- `HostApplication` 协调连接、发送、轮询和错误状态，不直接依赖 Qt。
- `ConnectionStateMachine` 明确区分 `DISCONNECTED`、`CONNECTING`、`CONNECTED` 和 `ERROR`。
- `LineParser` 处理分段输入、CRLF / LF、严格解码和行长度上限。
- `SerialBackend` 让测试使用确定性的内存后端，真实串口通过可选适配器接入。

详见 [System Architecture](docs/system-architecture.md) 与 [Communication Flow](docs/communication-flow.md)。

## Key Features

- 可替换串口后端：统一端口枚举、连接、关闭、收发接口。
- 可测试 Mock 通信：覆盖发送、分段接收、超时和运行时断连。
- 严格协议处理：验证命令名称、参数、编码、结束符和最大长度。
- 显式连接状态机：拒绝非法状态转换并保留错误信息。
- 最小 PyQt5 界面：端口与波特率选择、连接控制、终端收发和状态显示。
- 显式 `--mock` 演示：`MOCK0` 端口返回标注为 `MOCK ACK` 的模拟响应，不接触真实设备。
- 自动化质量门槛：主机测试要求核心模块覆盖率不低于 80%。
- 静态质量门槛：Ruff 检查源码与测试，Mypy 检查全部 22 个源文件。

## Project Structure

```text
Python-Host-Application-Lab/
├── .github/workflows/test.yml
├── assets/images/architecture/
├── docs/
│   ├── communication-flow.md
│   ├── system-architecture.md
│   └── verification.md
├── src/host_app/
│   ├── communication/
│   ├── core/
│   ├── gui/
│   ├── models/
│   └── protocol/
├── tests/
├── LICENSE
├── THIRD_PARTY_NOTICES.md
└── pyproject.toml
```

## Documentation

### Run host tests

```powershell
python -m pip install -e ".[test]"
python -m pytest
```

### Exercise the core without hardware

```python
from host_app import HostApplication, SerialConfig
from host_app.communication import MockSerialBackend

backend = MockSerialBackend()
application = HostApplication(backend)
application.connect(SerialConfig("MOCK0"))
application.send_command("status")

backend.queue_receive(b"ready\n")
print([message.text for message in application.poll()])  # ['ready']
```

### Run static checks

```powershell
python -m pip install -e ".[quality]"
python -m ruff check src tests
python -m mypy src
```

### Run the GUI

```powershell
python -m pip install -e ".[gui,serial]"
host-app
```

无硬件演示可运行 `host-app --mock`，连接 `MOCK0` 后发送 `status`，界面会显示 `MOCK ACK: status`。这是真实 Qt 窗口配合内存模拟后端的运行路径，不是设备回包或板端截图。GUI 使用非阻塞串口轮询（`read_timeout=0.0`）；真实设备的延迟和断线行为尚未测量。连接真实设备前，应确认端口、波特率、编码和命令协议均与目标设备一致。

推荐继续阅读：

1. [System Architecture](docs/system-architecture.md)：模块职责、依赖方向与状态模型。
2. [Communication Flow](docs/communication-flow.md)：发送、接收、超时和错误流程。
3. [Verification](docs/verification.md)：可复核命令、结果与未覆盖边界。

## Verification

| Verification Layer | Status | Evidence Boundary |
| --- | --- | --- |
| Host Test | PASSED locally | Python 3.10.11 下 45 项 pytest 全部通过；PR CI 以对应 SHA 为准 |
| Core Coverage | PASSED | 核心、协议、模型和 Mock 通信模块覆盖率 96.98%，门槛为 80% |
| Static Analysis | PASSED | Ruff 检查源码与测试；Mypy 检查 22 个源文件 |
| Build Verification | PASSED locally | 当前源码在隔离临时目录生成 sdist 与 wheel，Wheel 安装后运行 Mock GUI smoke |
| GUI Launch | PASSED locally | Qt 离屏窗口完成 `MOCK0` 连接、收发、断开及重连；未连接真实设备 |
| Hardware Validation | NOT PROVIDED | 未连接或声明任何真实串口设备 |
| Runtime Evidence | MOCK ONLY | 已运行 Qt 离屏 Mock 收发；没有真实串口或板端通信证据 |

完整记录见 [Verification](docs/verification.md)。

## License Boundary

根目录 MIT License 仅覆盖本仓库原创的 Python 源码、测试、Markdown 文档和 SVG。PyQt5、pyserial、pytest 等第三方依赖由用户单独安装并遵循各自许可证；仓库不包含课程源码、课件、未知来源图片、字体、安装包或外部设备固件。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
