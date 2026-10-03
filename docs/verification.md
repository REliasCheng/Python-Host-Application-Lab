# Verification

## Evidence Rules

本仓库采用分层证据表达，避免把静态源码存在、语法成功、GUI 启动和真实设备通信混为一谈。

| Layer | Result | Evidence |
| --- | --- | --- |
| Source Review | PASSED | 对源资料中的 Python、Qt Designer、Qt resource、构建描述和资产引用进行了只读审查 |
| Source Syntax Review | 128 / 129 passed | 使用 AST 解析检查非构建目录 Python 文件；1 个临时 Code Runner 文件存在 unmatched parenthesis |
| Public Syntax Validation | NOT APPLICABLE | 公开候选没有 Python 源码 |
| Host Test | NOT PROVIDED | 源资料与公开候选均未提供 pytest、unittest 或功能测试 |
| GUI Launch | NOT PROVIDED | 未执行来源不明的课程应用或二进制文件 |
| Application Runtime | NOT PROVIDED | 公开候选是文档与架构实验 |
| Device Validation | NOT PROVIDED | 未连接串口设备、MCU、控制器或传感器 |
| Runtime Evidence | NOT PROVIDED | 未生成运行日志、帧追踪、截图或测量数据 |

## Static Findings

静态审查能够确认的内容：

- Python 3 风格源码。
- PyQt5 widgets 与 signal / slot 使用。
- `pyserial` 端口枚举及串口 open / close / read / write 调用。
- `threading.Thread` 用于端口扫描和接收循环。
- PyInstaller 构建描述与历史构建产物存在于源资料中，但均未公开。

静态审查不能证明：

- GUI 能在当前环境正常启动。
- PyQt5 与 pyserial 依赖组合可复现。
- 串口设备可连接或收发正确。
- Bluetooth、数据可视化或设备控制能力存在。
- 线程模型安全，或长时间运行稳定。

## Future Verification Gate

若未来从权利清晰的原创实现继续开发，至少应依次完成：

1. 对全部公开 Python 文件执行 syntax validation。
2. 为与 GUI 无关的状态机、编码与解析逻辑提供 host tests。
3. 在无设备模式下确认 GUI 启动与关闭。
4. 使用明确型号的串口设备验证连接、TX、RX、断开和异常路径。
5. 保存不含隐私的可复核日志或帧追踪，再更新 Runtime Evidence。
