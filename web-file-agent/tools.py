"""Web and filesystem tools exposed to the agent.

The tools intentionally do not provide shell execution or arbitrary filesystem access.
"""
import ipaddress
import socket
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import MAX_FILE_BYTES, MAX_WEB_BYTES, REQUEST_TIMEOUT, WORKSPACE


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Fetch a public HTTP(S) page and return its title and readable text. Use this to research or summarize a URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "Absolute public HTTP or HTTPS URL"}},
                "required": ["url"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List entries in a directory inside the agent workspace. Use '.' for the workspace root.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Workspace-relative directory path"}},
                "required": ["path"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file from inside the agent workspace.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Workspace-relative file path"}},
                "required": ["path"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or replace a UTF-8 text file inside the workspace. The user must explicitly approve each write before this tool is executed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Workspace-relative file path"},
                    "content": {"type": "string", "description": "Complete UTF-8 text to write"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_directory",
            "description": "Create a directory inside the agent workspace. The user must approve before this tool is executed.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Workspace-relative directory path"}},
                "required": ["path"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
]


def _inside_workspace(user_path: str) -> Path:
    """Resolve a user-supplied path and ensure the final path stays under WORKSPACE."""
    if not isinstance(user_path, str) or not user_path.strip():
        raise ValueError("A non-empty relative path is required.")
    if "\x00" in user_path:
        raise ValueError("NUL bytes are not allowed in paths.")

    supplied = Path(user_path)
    if supplied.is_absolute():
        raise ValueError("Use a workspace-relative path, not an absolute path.")

    root = WORKSPACE.resolve()
    candidate = (root / supplied).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError("Path escapes the allowed workspace.")
    return candidate


def _validate_public_url(url: str) -> str:
    """Validate a URL and reject local/private destinations before each request."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL is required.")
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL must include a hostname and must not contain credentials.")
    if parsed.port is not None and parsed.port not in (80, 443):
        raise ValueError("For safety, only the standard HTTP/HTTPS ports 80 and 443 are allowed.")

    hostname = parsed.hostname.rstrip(".")
    try:
        literal_ip = ipaddress.ip_address(hostname)
        addresses = [literal_ip]
    except ValueError:
        try:
            records = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError("Could not resolve the URL hostname.") from exc
        addresses = []
        for record in records:
            try:
                addresses.append(ipaddress.ip_address(record[4][0].split("%", 1)[0]))
            except ValueError:
                continue

    if not addresses:
        raise ValueError("The URL hostname did not resolve to an IP address.")
    if any(not address.is_global for address in addresses):
        raise ValueError("Requests to private, local, link-local, or reserved IP addresses are blocked.")
    return url.strip()


def read_webpage(url: str) -> Dict[str, Any]:
    """Fetch a public HTML/text page, manually validate redirects, and return readable text."""
    current_url = url
    response = None
    try:
        for _ in range(4):  # Initial request plus at most three redirects.
            current_url = _validate_public_url(current_url)
            response = requests.get(
                current_url,
                timeout=(5, REQUEST_TIMEOUT),
                allow_redirects=False,
                stream=True,
                headers={"User-Agent": "WebFileAgentDemo/1.0"},
            )
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                response.close()
                if not location:
                    raise ValueError("Redirect response had no Location header.")
                current_url = urljoin(current_url, location)
                continue
            break
        else:
            raise ValueError("Too many redirects.")

        with response:
            if response.status_code >= 400:
                return {"ok": False, "error": "HTTP request failed with status {}".format(response.status_code)}
            content_type = response.headers.get("Content-Type", "").lower()
            if not any(kind in content_type for kind in ("text/html", "application/xhtml+xml", "text/plain")):
                return {"ok": False, "error": "Unsupported content type: {}".format(content_type or "unknown")}

            chunks: List[bytes] = []
            total = 0
            for chunk in response.iter_content(chunk_size=16384):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_WEB_BYTES:
                    return {"ok": False, "error": "Page exceeded the configured size limit."}
                chunks.append(chunk)
            raw = b"".join(chunks)
            encoding = response.encoding or "utf-8"
            html = raw.decode(encoding, errors="replace")

        if "text/plain" in content_type:
            title = current_url
            text = html
        else:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else current_url
            for node in soup(["script", "style", "noscript", "svg"]):
                node.decompose()
            text = soup.get_text("\n", strip=True)

        # Avoid passing huge documents into the model context.
        text = text[:30000]
        return {"ok": True, "url": current_url, "title": title[:500], "text": text}
    except (requests.RequestException, ValueError, OSError) as exc:
        if response is not None:
            response.close()
        return {"ok": False, "error": str(exc)[:1000]}


def list_files(path: str = ".") -> Dict[str, Any]:
    """List a workspace directory without following paths outside the root."""
    try:
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        target = _inside_workspace(path)
        if not target.exists():
            return {"ok": False, "error": "Directory does not exist."}
        if not target.is_dir():
            return {"ok": False, "error": "Path is not a directory."}
        entries = []
        for item in sorted(target.iterdir(), key=lambda value: value.name.lower()):
            entries.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size_bytes": item.stat().st_size if item.is_file() else None,
            })
        return {"ok": True, "path": str(target.relative_to(WORKSPACE)), "entries": entries[:500]}
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc)[:1000]}


def read_file(path: str) -> Dict[str, Any]:
    """Read a small UTF-8 text file that is confined to the workspace."""
    try:
        target = _inside_workspace(path)
        if not target.exists() or not target.is_file():
            return {"ok": False, "error": "File does not exist or is not a regular file."}
        if target.stat().st_size > MAX_FILE_BYTES:
            return {"ok": False, "error": "File exceeds the configured size limit."}
        content = target.read_text(encoding="utf-8")
        return {"ok": True, "path": str(target.relative_to(WORKSPACE)), "content": content}
    except (OSError, UnicodeError, ValueError) as exc:
        return {"ok": False, "error": str(exc)[:1000]}


def write_file(path: str, content: str) -> Dict[str, Any]:
    """Write UTF-8 text to a workspace file; caller is responsible for user approval."""
    try:
        if not isinstance(content, str):
            raise ValueError("File content must be a string.")
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_FILE_BYTES:
            raise ValueError("Content exceeds the configured file size limit.")
        target = _inside_workspace(path)
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Resolve again after making parent directories to catch symlink traversal.
        target = _inside_workspace(path)
        if target.exists() and target.is_dir():
            raise ValueError("Cannot write text content to a directory.")
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(target.relative_to(WORKSPACE)), "bytes_written": len(encoded)}
    except (OSError, UnicodeError, ValueError) as exc:
        return {"ok": False, "error": str(exc)[:1000]}


def make_directory(path: str) -> Dict[str, Any]:
    """Create a workspace directory; caller is responsible for user approval."""
    try:
        target = _inside_workspace(path)
        target.mkdir(parents=True, exist_ok=True)
        target = _inside_workspace(path)
        return {"ok": True, "path": str(target.relative_to(WORKSPACE))}
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc)[:1000]}


def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a tool request after it has passed schema validation."""
    if name == "read_webpage":
        return read_webpage(arguments["url"])
    if name == "list_files":
        return list_files(arguments["path"])
    if name == "read_file":
        return read_file(arguments["path"])
    if name == "write_file":
        return write_file(arguments["path"], arguments["content"])
    if name == "make_directory":
        return make_directory(arguments["path"])
    return {"ok": False, "error": "Unknown tool: {}".format(name)}
