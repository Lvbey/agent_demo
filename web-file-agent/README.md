# Web File Agent：网页阅读与文件操作 Agent

这是一个用于学习 Agent Tool Calling 的 Python 3 示例。模型负责理解用户意图并选择工具，Python 本地代码负责执行工具和进行安全检查。

## 功能

- **网页阅读**：读取公开 HTTP/HTTPS 网页，提取标题和正文文本。
- **文件查看**：列出工作目录内容、读取 UTF-8 文本文件。
- **文件操作**：创建或覆盖文本文件、创建目录；每次修改前都需要用户输入确认。
- **模型接入**：支持 OpenAI 及兼容 Chat Completions API 的服务。
- **安全边界**：不提供 Shell/任意代码执行；文件操作限制在 workspace/；网页读取会限制 URL 协议、目标 IP、重定向次数和响应大小。

## 环境要求

- Python 3.10 或更高版本
- 一个支持工具调用（Tool Calling）的 OpenAI 兼容模型及 API Key

## 快速开始

在终端进入本目录并创建虚拟环境：

    cd web-file-agent
    python -m venv .venv

Windows PowerShell 激活虚拟环境并复制配置文件：

    .\.venv\Scripts\Activate.ps1
    Copy-Item .env.example .env

macOS/Linux 激活虚拟环境并复制配置文件：

    source .venv/bin/activate
    cp .env.example .env

安装依赖：

    python -m pip install -r requirements.txt

编辑 .env，至少配置以下两项：

    OPENAI_API_KEY=你的API_KEY
    OPENAI_MODEL=服务支持的模型名称

如果使用兼容接口，将 OPENAI_BASE_URL 改为服务商提供的 API Base URL（不要加 /chat/completions）。

启动：

    python main.py

## 示例提问

- 读取 https://example.com 并总结网页内容
- 列出 workspace 目录下的文件
- 创建 notes/todo.txt，写入三条 Python 学习计划
- 读取 notes/todo.txt，并告诉我文件里写了什么

输入 /clear 可清空当前对话；输入 /exit 或 /quit 退出。

## 配置项

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| OPENAI_API_KEY | 必填 | 模型服务 API Key |
| OPENAI_BASE_URL | https://api.openai.com/v1 | API 基础地址 |
| OPENAI_MODEL | 必填 | 模型名称 |
| AGENT_WORKSPACE | ./workspace | Agent 可以操作的根目录 |
| MAX_STEPS | 8 | 每轮最多执行的工具调用循环次数 |
| REQUEST_TIMEOUT | 20 | 网页连接/读取超时（秒） |
| MAX_FILE_BYTES | 1000000 | 单个文件最大字节数 |
| MAX_WEB_BYTES | 1000000 | 网页最大下载字节数 |

## 目录结构

    web-file-agent/
    ├── main.py             # CLI 入口、写入确认
    ├── agent.py            # LLM 对话与工具调用循环
    ├── tools.py            # 网页阅读、文件工具及安全检查
    ├── config.py           # 环境变量配置
    ├── requirements.txt
    ├── .env.example
    ├── .gitignore
    ├── tests/
    │   └── test_tools.py   # 基础工具安全测试
    └── workspace/          # Agent 可操作的文件区域

运行基础测试：

    python -m unittest discover -s tests -v

## 安全说明

这是一个教学示例，不是经过安全审计的生产级服务。文件操作会限制在 workspace/，并在创建/覆盖文件前询问确认；不要把密钥或敏感文件放进工作目录。网页内容和本地文件内容都视为不可信数据，可能包含针对模型的提示注入文本。

网页读取会拒绝非 HTTP(S)、非公网 IP、非标准端口和过多重定向，但 DNS 重绑定、代理环境以及复杂网络配置仍可能需要额外防护。使用前请审查代码；生产环境中应使用低权限账户，并根据实际部署网络补充网络出口控制、日志和配额限制。发送到模型的网页或文件内容也可能离开本机，请先确认数据处理权限。
