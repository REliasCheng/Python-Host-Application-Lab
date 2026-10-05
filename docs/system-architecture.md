# System Architecture

## Scope

本项目实现一个面向行式串口设备的最小上位机。设计目标是让协议、状态和通信生命周期可以脱离 GUI 与真实硬件进行测试，同时保留连接实际串口的明确扩展点。

## Layered Model

| Layer | Responsibility | Implementation |
| --- | --- | --- |
| GUI | 端口选择、连接控制、命令输入、收发显示 | `host_app.gui` |
| Application Core | 协调连接、发送、轮询、消息记录和错误状态 | `HostApplication` |
| Protocol | 命令验证、编码、增量行解析、长度边界 | `host_app.protocol` |
| Communication | 抽象后端、Mock 行为、可选真实串口适配 | `host_app.communication` |
| Models | 连接状态、端口信息、终端消息 | `host_app.models` |

依赖方向从 GUI 指向核心接口；核心不导入 PyQt5 或 pyserial。`PySerialBackend` 在运行时才加载 pyserial，因此主机测试无需 GUI 或串口依赖。

## Connection Lifecycle

```text
DISCONNECTED
     ↓ connect
CONNECTING ── failure ──→ ERROR
     ↓ success              ↓ retry / disconnect
CONNECTED ── failure ───→ ERROR
     ↓ disconnect
DISCONNECTED
```

非法转换由 `ConnectionStateMachine` 拒绝。通信或协议错误会进入 `ERROR`，显式断开会关闭后端、清空解析缓冲并回到 `DISCONNECTED`。

## Transmit Path

```text
GUI command
  → validate command and token count
  → normalize arguments
  → UTF-8 encode and append CRLF
  → SerialBackend.write
  → record TX message
```

命令不允许嵌入换行，编码后的长度受 `max_line_bytes` 限制。部分写入会被视为通信错误，而不是静默成功。

## Receive Path

```text
SerialBackend.read
  → incremental LineParser buffer
  → split LF / trim optional CR
  → strict UTF-8 decode
  → record RX messages
  → GUI terminal output
```

无数据和预期超时返回空消息列表。断连、解码错误或超长行会进入错误状态；超长行被丢弃到下一个换行符后，解析器才恢复。

## GUI Boundary

GUI 使用 50 ms `QTimer` 在 Qt 主线程轮询核心，未创建后台线程，也不会从 worker 直接修改 widget。该实现适合低吞吐命令终端实验；高吞吐设备、长耗时操作和生产级并发模型不在当前验证范围内。

## Hardware Boundary

`PySerialBackend` 实现端口枚举、打开、关闭、读写和超时映射，但未使用真实设备验证。仓库没有声明设备兼容性、持续运行稳定性或特定 MCU 协议支持。
