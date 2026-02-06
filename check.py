import json
from pathlib import Path


HISTORY_FILE = Path("history.log")


def main() -> None:
    """
    简单的历史记录查看脚本。

    - 读取服务器写入的 JSON Lines 文件 history.log
    - 逐条打印时间、发送者和内容
    """
    if not HISTORY_FILE.exists():
        print("history.log 不存在。先运行 server.py / client.py 产生一些消息吧。")
        return

    with HISTORY_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                print(line)
                continue

            mtype = msg.get("type", "message")
            sender = msg.get("from", "unknown")
            text = msg.get("text", "")
            ts = msg.get("timestamp", "")

            if mtype == "system":
                print(f"[{ts}] [SYSTEM] {text}")
            else:
                print(f"[{ts}] <{sender}> {text}")


if __name__ == "__main__":
    main()

