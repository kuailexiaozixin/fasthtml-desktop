#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""examples 共享依赖自检与自动安装。

用法（由 启动-*.bat 调用）：
    python check_deps.py <example_id>

行为：
  1. 定位该 example 的 requirements.txt（含嵌套目录）或 pyproject.toml；
  2. 有 requirements.txt → pip install -q -r（幂等，extras 正确展开）；
  3. 无 requirements 但有 pyproject → pip install -q <提取的 deps>；
  4. 都没有 → 内置最小清单 + pip install；
  5. 镜像降级：Aliyun → 清华 → PyPI。
  6. 安装完成后直接退出；不在当前进程 import 应用入口，避免 `serve()` 在自检阶段启动服务或阻塞。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

# 镜像降级链
MIRRORS = [
    ("https://mirrors.aliyun.com/pypi/simple/", ["--trusted-host", "mirrors.aliyun.com"]),
    ("https://pypi.tuna.tsinghua.edu.cn/simple/", []),
    ("https://pypi.org/simple/", []),
]

# 无 requirements / pyproject 时的兜底清单
DEFAULT_DEPS = ["uvicorn", "python-fasthtml"]

# 各 example 的内置依赖（当无 requirements.txt 时）
HARDCODED_DEPS: dict[str, list[str]] = {
    "FastAccounts": [
        "fastapi", "uvicorn", "pydantic", "openpyxl",
        "httpx", "python-dotenv", "psycopg[binary]", "psycopg-pool",
    ],
}


def find_requirements(ex_root: Path, example_id: str) -> tuple[Path | None, Path]:
    """定位 requirements.txt，处理嵌套目录。返回 (req_path, search_dir)。"""
    ex_dir = ex_root / example_id
    if not ex_dir.is_dir():
        return None, ex_dir

    # 平铺：ex_dir/requirements.txt
    req = ex_dir / "requirements.txt"
    if req.is_file():
        return req, ex_dir

    # 嵌套：ex_dir/example_id/requirements.txt（如 FastERP/FastERP/）
    nested = ex_dir / example_id
    if nested.is_dir():
        req2 = nested / "requirements.txt"
        if req2.is_file():
            return req2, nested

    # pyproject.toml（平铺或嵌套）
    pyp = ex_dir / "pyproject.toml"
    if pyp.is_file():
        return None, ex_dir  # 标记有 pyproject
    pyp2 = nested / "pyproject.toml" if nested.is_dir() else None
    if pyp2 and pyp2.is_file():
        return None, nested

    # 无依赖文件
    return None, ex_dir


def pip_install(pkgs_or_args: list[str], extra_args: list[str] | None = None,
                cwd: Path | None = None) -> bool:
    """用镜像链 pip install；cwd 让 `-e .` 指向当前 example。返回成功/失败。"""
    extra_args = extra_args or []
    for i, (mirror, trust) in enumerate(MIRRORS):
        cmd = [sys.executable, "-m", "pip", "install", "-q",
               "--disable-pip-version-check"] + extra_args + [
            "-i", mirror
        ] + trust + pkgs_or_args
        print(f"  [deps] pip install（源 {i + 1}/{len(MIRRORS)}）...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                               cwd=str(cwd) if cwd is not None else None)
            if r.returncode == 0:
                print(f"  [deps] OK")
                return True
            # 提取关键错误
            err = r.stderr.strip().split("\n")[-1][:120] if r.stderr else ""
            print(f"  [deps] 失败: {err}")
        except subprocess.TimeoutExpired:
            print(f"  [deps] 超时（600s）")
    print(f"  [deps] 全部镜像失败，请手动安装")
    return False


def main() -> int:
    example_id = sys.argv[1] if len(sys.argv) > 1 else ""
    if not example_id:
        print("  [deps] 用法: python check_deps.py <example_id>")
        return 1

    ex_root = Path(__file__).resolve().parent
    req_path, search_dir = find_requirements(ex_root, example_id)

    if req_path and req_path.is_file():
        # 模式 1: pip install -r requirements.txt（幂等，extras 正确）
        print(f"  [deps] {example_id}: 检查 requirements.txt …")
        return 0 if pip_install(["-r", str(req_path)], cwd=search_dir) else 1

    # 模式 2: pyproject.toml → 提取 deps
    pyp = search_dir / "pyproject.toml"
    if pyp.is_file():
        import tomllib
        try:
            with open(pyp, "rb") as f:
                data = tomllib.load(f)
            deps = data.get("project", {}).get("dependencies", [])
            deps = [d for d in deps if not d.startswith(("-e ", "."))]
            if deps:
                print(f"  [deps] {example_id}: 检查 pyproject.toml（{len(deps)} deps）…")
                return 0 if pip_install(deps, cwd=search_dir) else 1
        except Exception as e:
            print(f"  [deps] pyproject 解析失败: {e}")

    # 模式 3: 内置清单
    pkgs = HARDCODED_DEPS.get(example_id, DEFAULT_DEPS)
    print(f"  [deps] {example_id}: 检查内置清单（{len(pkgs)} 项）…")
    return 0 if pip_install(pkgs) else 1


if __name__ == "__main__":
    sys.exit(main())
