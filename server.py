import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Set


HISTORY_FILE = Path("history.log")
HOST = "0.0.0.0"
PORT = 9999


class ChatServer:
    """
    现代化异步聊天室服务端：
    - 基于 asyncio streams
    - JSON 行协议：每条消息为一行 JSON
    - 结构化历史记录写入 history.log（JSON Lines）

    默认使用明文 TCP。
    如需开启 TLS，请参考 main() 里的注释，配置 ssl.SSLContext 并传给 start_server。
    """

    def __init__(self) -> None:
        self._clients: Set[asyncio.StreamWriter] = set()

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        addr = writer.get_extra_info("peername")
        client_id = f"{addr[0]}:{addr[1]}" if addr else "unknown"

        self._clients.add(writer)
        await self._broadcast(
            {
                "type": "system",
                "from": "server",
                "text": f"{client_id} joined the chat",
                "timestamp": self._now(),
            }
        )
        print(f"Client {client_id} connected")

        try:
            while True:
                line = await reader.readline()
                if not line:
                    break

                try:
                    data = json.loads(line.decode("utf-8").strip())
                except json.JSONDecodeError:
                    # 忽略非法数据
                    continue

                # 标准化消息
                message = {
                    "type": data.get("type", "message"),
                    "from": data.get("from", client_id),
                    "text": data.get("text", ""),
                    "timestamp": self._now(),
                }

                await self._broadcast(message)
                self._append_history(message)

        except Exception as exc:  # noqa: BLE001
            print(f"Error handling client {client_id}: {exc}")
        finally:
            self._clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            print(f"Client {client_id} disconnected")
            await self._broadcast(
                {
                    "type": "system",
                    "from": "server",
                    "text": f"{client_id} left the chat",
                    "timestamp": self._now(),
                }
            )

    async def _broadcast(self, message: Dict) -> None:
        """
        将 JSON 消息广播给所有在线客户端。
        """
        if not self._clients:
            return

        data = (json.dumps(message) + "\n").encode("utf-8")
        dead_clients: Set[asyncio.StreamWriter] = set()

        for writer in self._clients:
            try:
                writer.write(data)
                await writer.drain()
            except Exception:  # noqa: BLE001
                dead_clients.add(writer)

        for writer in dead_clients:
            self._clients.discard(writer)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    @staticmethod
    def _append_history(message: Dict) -> None:
        """
        将消息以 JSON Lines 形式写入历史文件。
        """
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat() + "Z"


async def main() -> None:
    server = ChatServer()

    srv = await asyncio.start_server(
        server.handle_client,
        host=HOST,
        port=PORT,
        # 如需开启 TLS：
        # 1. 导入 ssl 模块
        #    import ssl
        # 2. 创建 SSL 上下文并加载证书
        #    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        #    ssl_ctx.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
        # 3. 把下面一行改为 ssl=ssl_ctx
        # ssl=ssl_ctx,
    )

    addr = ", ".join(str(sock.getsockname()) for sock in srv.sockets or [])
    print(f"Chat server started on {addr}")

    async with srv:
        await srv.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
