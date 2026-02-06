import asyncio
import json
#import ssl
import sys
from typing import Optional

HOST = "localhost"
PORT = 9999


def _format_message(msg: dict) -> str:
    mtype = msg.get("type", "message")
    sender = msg.get("from", "unknown")
    text = msg.get("text", "")
    ts = msg.get("timestamp", "")
    if mtype == "system":
        return f"[{ts}] [SYSTEM] {text}\n"
    return f"[{ts}] <{sender}> {text}\n"


async def read_server(reader: asyncio.StreamReader) -> None:
    while True:
        line = await reader.readline()
        if not line:
            print("\nDisconnected from chat server")
            # 退出整个进程
            sys.exit(0)
        try:
            data = json.loads(line.decode("utf-8").strip())
        except json.JSONDecodeError:
            # 打印原始行以便调试
            print(line.decode("utf-8", errors="replace"))
            continue

        sys.stdout.write(_format_message(data))
        sys.stdout.flush()


async def read_stdin_and_send(
    writer: asyncio.StreamWriter, username: str
) -> None:
    loop = asyncio.get_running_loop()
    while True:
        # 在线程池中同步读取一行 stdin，避免阻塞整个事件循环
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        text = line.rstrip("\n")
        if not text:
            continue

        payload = {
            "type": "message",
            "from": username,
            "text": text,
        }
        writer.write((json.dumps(payload) + "\n").encode("utf-8"))
        try:
            await writer.drain()
        except Exception:
            print("Error sending message, connection may be closed.")
            break


async def main(
    host: str = HOST, port: int = PORT, username: Optional[str] = None
) -> None:
    if not username:
        username = input("请输入你的昵称: ").strip() or "anonymous"

    try:
        # 默认使用明文 TCP。
        # 如需启用 TLS，请参考下面注释：
        #
        # import ssl
        # ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        # ssl_ctx.load_verify_locations("cert.pem")  # 信任的 CA 或自签证书
        # ssl_ctx.check_hostname = False            # 自签证书一般没有合法主机名
        # ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        # reader, writer = await asyncio.open_connection(
        #     host=host, port=port, ssl=ssl_ctx, server_hostname=host
        # )
        #
        # 不需要 TLS 时，只保留下面这一行即可：
        reader, writer = await asyncio.open_connection(host=host, port=port)
    except Exception as exc:  # noqa: BLE001
        print(f"Unable to connect: {exc}")
        sys.exit(1)

    print("Connected to remote host. Start sending messages.")
    print("Ctrl+C 退出。")

    # 并发执行：一边收消息，一边从 stdin 读入消息发送
    tasks = [
        asyncio.create_task(read_server(reader)),
        asyncio.create_task(read_stdin_and_send(writer, username)),
    ]

    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for t in tasks:
            t.cancel()
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye.")
