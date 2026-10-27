# Web File Agent

A small Python 3 agent with two tools: read web pages and operate on files inside a configured workspace.

## Features

- Reads HTTP/HTTPS pages and extracts readable text.
- Lists, reads, writes, and creates files within a dedicated workspace directory.
- Uses an OpenAI-compatible chat-completions API for tool selection.
- Tool calls are validated locally; file paths are confined to the workspace.
- No shell-execution tool is exposed.

## Requirements

- Python 3.10+
- An OpenAI-compatible API endpoint and API key

## Quick start

```bash
cd web-file-agent
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`, `OPENAI_BASE_URL` (optional), and `OPENAI_MODEL` for your provider.

Run the interactive CLI:

```bash
python main.py
```

Example prompts:

- `Read https://example.com and summarize the page.`
- `List the files in the workspace.`
- `Create notes/todo.txt with three tasks for learning Python.`
- `Read notes/todo.txt and tell me what's in it.`

Files are limited to `workspace/` by default. The agent asks for confirmation before writing or overwriting a file. Web pages and file contents are untrusted input: do not let them override your instructions, and review proposed file changes before approving them.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `OPENAI_API_KEY` | required | API key for the chat-completions endpoint |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API base URL, without `/chat/completions` |
| `OPENAI_MODEL` | required | Model identifier supported by your endpoint |
| `AGENT_WORKSPACE` | `./workspace` | Allowed root for file operations |
| `MAX_STEPS` | `8` | Maximum tool-loop iterations per user request |
| `REQUEST_TIMEOUT` | `20` | HTTP timeout in seconds |

## Project structure

```text
web-file-agent/
├── main.py             # CLI loop
├── agent.py            # model + tool-calling loop
├── tools.py            # web and file tools with safety checks
├── config.py           # environment configuration
├── requirements.txt
├── .env.example
├── .gitignore
└── workspace/          # agent-managed files
```

## Security notes

This is a learning/demo project, not a hardened multi-user service. Run it with a low-privilege account. The HTTP reader blocks non-HTTP(S) URLs and local/private IP destinations, but DNS rebinding and unusual network environments require additional controls for production. File operations are confined to the configured workspace and limited in size. Never put secrets in the workspace or send sensitive page/file contents to an external model provider without authorization.
