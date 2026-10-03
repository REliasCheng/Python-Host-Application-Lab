# Communication Flow

## Connection Setup

可确认的参考流程如下：

```text
Enumerate host serial ports
  -> choose port
  -> choose baud rate
  -> open serial connection
  -> expose connection status to the GUI
```

配置对话框还展示 data bits、parity、stop bits 和 flow control 选项，但静态审查没有确认这些值被完整传递到最终 `serial.Serial` 实例。因此它们不能被描述为已经生效的通信能力。

## Transmit

发送路径从 GUI 文本框取得字符串，追加 `\r\n`，再按 GBK 编码后写入串口。该行为意味着：

- 对端应按行读取，或能接受 CRLF 后缀。
- 非 GBK 文本的互操作性未验证。
- 没有 binary-frame builder、sequence number 或 retry policy。

## Receive

接收路径通过 `readline()` 等待一行字节，按 GBK 解码，再追加到 GUI 记录区域。可选时间戳只影响显示，不属于协议字段。

## Error and Lifecycle Boundary

当前资料没有形成可验证的完整错误处理模型：

- 未确认 open failure 的用户提示与恢复路径。
- 未确认 decode failure 的处理。
- 未确认设备断开后的自动重连。
- 未确认 worker thread 的停止与回收。
- 未确认持续高吞吐下的缓冲和背压。

因此本仓库把连接、收发和线程生命周期作为后续实现目标，而不把它们写成已通过验证的能力。

## Protocol Boundary

| Item | Confirmed State |
| --- | --- |
| Transport | Serial / UART through `pyserial` |
| Payload | Text lines |
| Encoding | GBK |
| TX terminator | CRLF |
| Byte order | Not applicable to confirmed text path |
| Frame header / length / tail | Not present |
| Checksum / CRC | Not present |
| Request / response model | Not formally defined |
| Device target | Unknown |
