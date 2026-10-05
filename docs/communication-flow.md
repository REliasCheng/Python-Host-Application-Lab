# Communication Flow

## Backend Selection

应用核心只依赖 `SerialBackend` 接口：

- `MockSerialBackend` 提供确定性的内存通信，用于主机测试和错误注入。
- `PySerialBackend` 是可选真实串口适配器，pyserial 不随仓库源码分发。

## Connection Setup

```text
Enumerate ports
  → choose port and baud rate
  → validate SerialConfig
  → DISCONNECTED → CONNECTING
  → open selected backend
  → CONNECTED or ERROR
```

当前配置支持端口、波特率、文本编码、行结束符、读取大小、读取超时和最大行长度。数据位、校验位、停止位及流控制尚未暴露为项目配置能力。

## Transmit

默认发送流程为：

```text
Command text
  → reject empty or malformed command
  → normalize shell-style arguments
  → encode as UTF-8
  → append CRLF
  → backend write
```

这是一条通用行式文本通道，不是 Modbus、CAN、MQTT、BLE 或自定义二进制帧协议。命令语法只定义名称和参数边界，不赋予设备特定语义。

## Receive

`LineParser` 接受任意分段字节输入并保存未完成行。LF 结束一行，前置 CR 会被移除；空行保留。无效 UTF-8、超长行和非字节输入都会产生明确错误。

## Timeout and Disconnect

| Event | Core Behavior |
| --- | --- |
| No bytes available | 返回空消息列表，保持连接状态 |
| Expected read timeout | 返回空消息列表，保持连接状态 |
| Backend disconnect | 抛出通信错误并进入 `ERROR` |
| Decode or line-length failure | 抛出协议错误并进入 `ERROR` |
| Explicit disconnect | 关闭后端、重置解析器并进入 `DISCONNECTED` |

Mock 后端对超时和断连路径提供了自动化测试证据；真实设备上的电气、驱动和热插拔行为尚未验证。

## Protocol Boundary

| Item | Current Implementation |
| --- | --- |
| Transport | Serial byte stream through a backend interface |
| Payload | Line-oriented text |
| Default encoding | UTF-8 |
| TX terminator | CRLF |
| RX terminator | LF, with optional CR removal |
| Maximum line | Configurable; default 256 bytes |
| Frame header / length / CRC | Not implemented |
| Automatic reconnect | Not implemented |
| Device target | Not specified or validated |
