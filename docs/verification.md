# Verification

## Evidence Rules

验证结果按层级记录，避免把代码存在、主机测试、包构建、GUI 启动和真实设备通信混为一谈。

## Reproducible Commands

```powershell
python -m pip install -e ".[test]"
python -m pytest
python -m build
```

可选 GUI 与串口依赖：

```powershell
python -m pip install -e ".[gui,serial]"
host-app
```

## Recorded Results

| Layer | Result | Evidence |
| --- | --- | --- |
| Host Test | PASSED | Python 3.10.11、pytest 9.0.3，33 / 33 tests passed |
| Core Coverage | PASSED | 96.81% statement / branch-aware combined coverage；要求至少 80% |
| Protocol Test | PASSED | 分段行、CRLF / LF、无效编码、超长行与命令校验 |
| Communication Test | PASSED | Mock 连接、发送、分段接收、空读取、超时与断连 |
| State Test | PASSED | 正常生命周期、非法转换、错误记录与恢复 |
| Build Verification | PASSED | `python -m build` 生成 sdist 与 `py3-none-any` wheel |
| GUI Launch | PASSED | PyQt5 5.15.11 在 Qt 离屏平台构造窗口，初始状态为 `disconnected` |
| Hardware Validation | NOT PROVIDED | 未连接真实串口设备或 MCU |
| Runtime Evidence | LIMITED | 仅有 Mock 集成路径和离屏 GUI 启动证据 |

## Coverage Scope

80% 门槛覆盖以下硬件无关模块：

- `host_app.core`
- `host_app.communication.mock_serial`
- `host_app.protocol`
- `host_app.models`

GUI 与 `PySerialBackend` 需要平台、Qt 或设备边界，不计入核心覆盖率门槛。CI 在 Python 3.10、3.11 和 3.12 上运行同一主机测试命令；远端工作流结果应以 GitHub Actions 实际运行状态为准。

## Unverified Boundary

当前证据不能证明：

- 任意外部串口设备能够连接或正确响应命令。
- 特定 USB-UART 驱动、端口权限或热插拔行为正常。
- 高吞吐、长时间运行或生产环境稳定性。
- 自动重连、二进制协议、CRC、数据绘图或设备专用控制能力。

只有在明确设备、连接参数和协议，并保存可复核运行证据后，才能更新 Hardware Validation 或扩展 Runtime Evidence。
