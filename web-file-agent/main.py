"""Interactive CLI entry point."""
from openai import OpenAI

from agent import new_conversation, run_turn
from config import API_KEY, BASE_URL, MODEL, REQUEST_TIMEOUT, WORKSPACE


def main():
    if not API_KEY or not MODEL:
        print("请在 .env 中配置 OPENAI_API_KEY 和 OPENAI_MODEL。")
        return 1

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=REQUEST_TIMEOUT)
    messages = new_conversation()

    print("Web File Agent 已启动，输入 /exit 退出，输入 /clear 清空对话。")
    while True:
        try:
            user_text = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_text.lower() in ("/exit", "/quit", "exit", "quit"):
            break
        if user_text == "/clear":
            messages = new_conversation()
            print("对话已清空。")
            continue
        if not user_text:
            continue

        messages.append({"role": "user", "content": user_text})
        try:
            print("\nAgent> " + run_turn(client, messages, lambda name, args: True))
        except Exception as exc:
            print("请求失败：{}".format(exc))

    print("再见。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
