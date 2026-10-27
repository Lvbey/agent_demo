"""Interactive command-line entry point for Web File Agent."""
from pathlib import Path

from openai import OpenAI

from agent import new_conversation, run_turn
from config import API_KEY, BASE_URL, MODEL, REQUEST_TIMEOUT, WORKSPACE


def approve_change(name, arguments):
    """Require an explicit affirmative response for every workspace mutation."""
    path = arguments.get("path", "")
    print("\n[需要确认] Agent 请求执行文件操作：{}".format(name))
    print("目标路径（相对于 workspace）：{}".format(path or "(未提供)"))

    if name == "write_file":
        content = arguments.get("content", "")
        print("内容长度：{} 个字符".format(len(content)))
        preview = content[:1200]
        if preview:
            print("内容预览：\n{}".format(preview))
            if len(content) > len(preview):
                print("……（预览已截断）")
        print("注意：如果目标文件已存在，本次操作会覆盖它。")

    answer = input("确认执行？输入 y 或 yes 才会继续 [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def main():
    if not API_KEY:
        print("配置缺失：请复制 .env.example 为 .env，并设置 OPENAI_API_KEY。")
        return 2
    if not MODEL:
        print("配置缺失：请在 .env 中设置 OPENAI_MODEL。")
        return 2

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )
    messages = new_conversation()

    print("Web File Agent 已启动")
    print("模型：{}".format(MODEL))
    print("API Base URL：{}".format(BASE_URL))
    print("工作目录：{}".format(WORKSPACE))
    print("可读取公开网页，并在 workspace 内列出、读取和修改文本文件。")
    print("修改文件前会询问确认；输入 /clear 清空对话，输入 /exit 退出。\n")

    while True:
        try:
            user_input = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return 0

        if not user_input:
            continue
        command = user_input.lower()
        if command in ("/exit", "/quit", "exit", "quit"):
            print("再见。")
            return 0
        if command == "/clear":
            messages = new_conversation()
            print("对话已清空。\n")
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            answer = run_turn(client, messages, approve_change)
            print("\nAgent> {}\n".format(answer))
        except KeyboardInterrupt:
            print("\n本次请求已中断。\n")
        except Exception as exc:
            # Avoid dumping a traceback or environment values into the terminal by default.
            print("\n请求失败：{}".format(str(exc)[:1000]))
            print("请检查模型名称、API 地址、网络连接和服务端错误信息。\n")


if __name__ == "__main__":
    raise SystemExit(main())
