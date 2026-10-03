# System Architecture

## Scope

本文定义一个最小 Python 串口上位机的职责边界。它来自对现有资料的只读结构分析，不代表已发布可运行实现，也不提供设备兼容性承诺。

## Layered Model

| Layer | Responsibility | Confirmed Reference Behavior |
| --- | --- | --- |
| User Interface | 收集端口、波特率与发送文本；显示连接状态和接收内容 | PyQt5 widgets、dialog、status bar、signal / slot |
| Application Logic | 协调窗口状态、连接动作、发送动作与显示格式 | Main-window coordination and event handlers |
| Communication | 枚举串口，建立连接，执行字节流 RX / TX | `list_ports` and `serial.Serial` |
| External Device | 提供串口端点与数据 | 具体设备型号未确认 |

该结构没有足够证据支持 MVC、MVVM、插件系统或服务化通信框架等更高级模式。

## Transmit Path

```text
User text
  -> GUI event handler
  -> append CRLF
  -> GBK encode
  -> serial write
  -> external serial device
```

## Receive Path

```text
External serial device
  -> blocking serial readline
  -> GBK decode
  -> timestamp / display formatting
  -> GUI receive area
```

资料中未发现长度字段、帧头、帧尾、checksum 或 CRC。因此这个路径只描述行导向文本传输。

## Threading Boundary

参考代码使用 `threading.Thread` 执行端口扫描和串口读取。静态审查发现两类工程风险：

1. 串口读取使用阻塞式 `readline()`，但没有可确认的 timeout 与退出条件。
2. 后台线程直接更新 Qt widget；Qt GUI 通常要求通过 signal / slot 将跨线程数据切回 GUI 线程。

这些是当前设计边界，不是已通过测试的问题修复。未来可运行实现需要增加可停止 worker、明确 timeout、错误传播和 GUI-thread handoff，并通过主机测试与运行验证证明行为。

## Capability Boundary

| Area | Status |
| --- | --- |
| Runtime port enumeration | Present in reviewed source |
| Serial open / close | Present in reviewed source |
| Text TX / RX | Present in reviewed source |
| Configurable data bits / parity / stop bits | UI values exist; end-to-end application to `Serial` is incomplete |
| Bluetooth | Placeholder UI only |
| TCP / UDP | Separate training examples exist; not part of the host-application candidate |
| Protocol parser | Not present |
| CRC / checksum | Not present |
| Automatic reconnect | Not present |
| Data plotting | Not present |
| Device-specific control | Not confirmed |
