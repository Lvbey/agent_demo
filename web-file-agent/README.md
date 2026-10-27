# Web File Agent

一个用于测试 Agent Tool Calling 的最小 Python 3 示例。

## 功能

- `read_webpage`：读取网页并提取文本
- `list_files`：列出目录中的文件
- `read_file`：读取文本文件
- `write_file`：创建或覆盖文本文件
- 使用 OpenAI 兼容的 Chat Completions API 选择和调用工具

## 运行

建议使用 Python 3.10+。

```bash
cd web-file-agent
python -m venv .venv
```

Windows：

```powershell
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

macOS/Linux：

```bash
source .venv/bin/activate
cp .env.example .env
```

安装依赖：

```bash
pip install -r requirements.txt
```

修改 `.env`：

```dotenv
OPENAI_API_KEY=你的API_KEY
OPENAI_MODEL=你的模型名称
OPENAI_BASE_URL=https://api.openai.com/v1
```

启动：

```bash
python main.py
```

## 示例

- 读取 https://example.com 并总结
- 列出 workspace 目录的文件
- 在 workspace 下创建 hello.txt，内容为 Hello Agent
- 读取 hello.txt

默认文件目录是 `workspace/`。这是用于本地测试的简化示例，不适合直接作为生产服务使用。
