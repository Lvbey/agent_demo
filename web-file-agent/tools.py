"""Very small web and file tools for the demo agent."""
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import WORKSPACE


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Read a web page and return its title and text.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text to a file, creating or replacing it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
]


def read_webpage(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    return {"title": title, "text": soup.get_text("\n", strip=True)[:30000]}


def list_files(path="."):
    target = WORKSPACE / path
    target.mkdir(parents=True, exist_ok=True) if path == "." else None
    return {"files": [item.name for item in target.iterdir()]}


def read_file(path):
    return {"path": path, "content": (WORKSPACE / path).read_text(encoding="utf-8")}


def write_file(path, content):
    target = WORKSPACE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": path, "written": True}


def execute_tool(name, arguments):
    if name == "read_webpage":
        return read_webpage(**arguments)
    if name == "list_files":
        return list_files(**arguments)
    if name == "read_file":
        return read_file(**arguments)
    if name == "write_file":
        return write_file(**arguments)
    return {"error": "Unknown tool: " + name}
