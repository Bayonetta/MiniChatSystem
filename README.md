ZSChatSystem
============

 * 基于 Python asyncio 的异步聊天室
 * JSON 行协议（每条消息一行 JSON）
 * 本地结构化存储聊天历史（JSON Lines）
 * 可选的 TLS 加密支持（示例代码留有注释口子）


============

运行方式（Python 3.9+）:

1. 启动服务器:

   ```bash
   python server.py
   ```

2. 启动一个或多个客户端:

   ```bash
   python client.py
   python client.py
   # 根据需要多开几个终端
   ```

3. 查看历史记录:

   ```bash
   python check.py
   ```

说明：

- 服务端会把每条消息（包括系统消息）以 JSON Lines 方式写入 `history.log`。
- 默认使用明文 TCP 连接，便于本地学习和测试。
- 如需开启 TLS：
  - 在 `server.py` 中按照注释创建 `ssl_ctx` 并传给 `asyncio.start_server`；
  - 在 `client.py` 中按照注释创建客户端 `ssl_ctx` 并传给 `asyncio.open_connection`。
