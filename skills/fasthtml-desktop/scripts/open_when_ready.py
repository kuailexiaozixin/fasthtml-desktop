#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""等待本地 HTTP 服务就绪后打开默认浏览器。

用法：python scripts/open_when_ready.py http://127.0.0.1:5025 [timeout_seconds]
"""
from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
import webbrowser


def wait_for_http(url: str, timeout: float = 60.0) -> bool:
    deadline = time.monotonic() + timeout
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < deadline:
        try:
            with opener.open(url, timeout=2):
                return True
        except urllib.error.HTTPError:
            return True
        except (OSError, urllib.error.URLError):
            time.sleep(0.4)
    return False


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("用法: python scripts/open_when_ready.py <url> [timeout_seconds]", file=sys.stderr)
        return 2
    url = args[0]
    try:
        timeout = float(args[1]) if len(args) > 1 else 60.0
    except ValueError:
        print(f"无效超时值: {args[1]!r}", file=sys.stderr)
        return 2
    if not wait_for_http(url, timeout):
        print(f"服务未在 {timeout:g}s 内就绪: {url}", file=sys.stderr)
        return 1
    webbrowser.open(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())