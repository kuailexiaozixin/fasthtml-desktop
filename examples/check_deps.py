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
  6. 全部已装时秒退（pip 输出 "Requirement already satisfied"），无实质开销。
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


def pip_install(pkgs_or_args: list[str], extra_args: list[str] = []) -> bool:
    """用镜像链 pip install。返回成功/失败。"""
    for i, (mirror, trust) in enumerate(MIRRORS):
        cmd = [sys.executable, "-m", "pip", "install", "-q"] + extra_args + [
            "-i", mirror
        ] + trust + pkgs_or_args
        print(f"  [deps] pip install（源 {i + 1}/{len(MIRRORS)}）...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
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
        ok = pip_install(["-r", str(req_path)])
        if ok:
            # 验证：import 入口模块
            _verify_import(search_dir, example_id)
            return 0
        return 1

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
                ok = pip_install(deps)
                if ok:
                    _verify_import(search_dir, example_id)
                    return 0
                return 1
        except Exception as e:
            print(f"  [deps] pyproject 解析失败: {e}")

    # 模式 3: 内置清单
    pkgs = HARDCODED_DEPS.get(example_id, DEFAULT_DEPS)
    print(f"  [deps] {example_id}: 检查内置清单（{len(pkgs)} 项）…")
    ok = pip_install(pkgs)
    if ok:
        _verify_import(search_dir, example_id)
        return 0
    return 1


def _verify_import(search_dir: Path, example_id: str):
    """轻量验证：尝试 import 入口模块，失败仅警告不阻断。"""
    import importlib
    candidates = ["web_app", "api_app", "main", "app", "server"]
    found = None
    for c in candidates:
        if (search_dir / f"{c}.py").is_file():
            found = c
            break
    if not found:
        return
    try:
        sys_path_backup = list(sys.path)
        sys.path.insert(0, str(search_dir))
        importlib.import_module(found)
        sys.path[:] = sys_path_backup
        # import 成功说明依赖完整
    except ModuleNotFoundError as e:
        print(f"  [deps] 警告: import {found} 缺 {e.name}，请手动安装")
    except Exception:
        # 非 import 错误（DB 连接失败等）→ 可忽略
        pass
    finally:
        sys.path[:] = sys_path_backup


if __name__ == "__main__":
    sys.exit(main())
