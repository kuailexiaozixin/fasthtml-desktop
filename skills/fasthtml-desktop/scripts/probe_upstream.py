#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe_upstream.py — examples 引入期的「上游 fasthtml API 漂移」探针。

为什么需要它：
    某些上游项目会写 `from fasthtml.common import (... picolink ...)`，但 `picolink`
    在 fasthtml 0.14.0 已被移除，全局基线是 0.14.9 → 运行时才崩 ImportError。
    这类「上游自称 >=0.12.1 却只兼容 <0.14.0」的漂移，等运行时才发现太晚。
    本脚本在克隆期就能扫出「上游 import 了但当前 fasthtml 已不存在的符号」，
    提前标红并建议走 ISOLATED_VENV。

用法：
    python scripts/probe_upstream.py <示例目录>        # 探测单个示例
    python scripts/probe_upstream.py                  # 探测 examples/ 下全部示例
    python scripts/probe_upstream.py --json <目录>    # 机器可读输出

退出码：发现「已移除符号」= 1（建议 ISOLATED_VENV）；否则 0。
"""
import argparse
import importlib.metadata as md
import os
import re
import sys
import textwrap

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 跳过这些文件/目录（非上游业务代码，或会干扰扫描）
SKIP_FILES = {"run.py", "launcher.py", "probe_upstream.py"}
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "build", "dist",
             "data", "generated_apps"}

# 匹配 `from fasthtml.common import (...)` / `from fasthtml import (...)` 等
IMPORT_RE = re.compile(
    r"from\s+fasthtml(?:\.\w+)?\s+import\s+"
    r"(?:"                              # 两种形式：
    r"\(([^)]*)\)"                      #   (a) 括号多行
    r"|"                                #   (b) 单行
    r"([\w\s,]+?)"                      #       单行符号列表
    r")(?:\s+as\s+\w+)?\s*(?:#.*)?$",
    re.MULTILINE,
)


def collect_symbols_from_source(src: str):
    """从一段源码里抽出所有 `from fasthtml... import X` 的符号名。"""
    syms = set()
    for m in IMPORT_RE.finditer(src):
        body = (m.group(1) or m.group(2) or "")
        for part in re.split(r"[,\s]+", body):
            part = part.strip()
            if not part or part in ("*",):
                continue
            # 处理 `name as alias`
            name = part.split(" as ")[0].strip()
            if name and name.isidentifier():
                syms.add(name)
    return syms


def load_upstream_modules():
    """导入全局 fasthtml，返回 (version, 可解析符号集合)。"""
    try:
        import fasthtml                       # noqa: F401
        import fasthtml.common as fc          # noqa: F401
    except Exception as e:                          # pragma: no cover
        print(f"[probe] 无法导入全局 fasthtml：{e}", file=sys.stderr)
        return None, set()

    try:
        version = md.version("python-fasthtml")
    except Exception:
        version = getattr(fasthtml, "__version__", "unknown")

    # 合并 fasthtml 顶层 + fasthtml.common 的属性名
    present = set(dir(fasthtml)) | set(dir(fc))
    return version, present


def scan_dir(root: str):
    """扫描目录，返回 {file: 缺失符号集合}。"""
    version, present = load_upstream_modules()
    if version is None:
        return None

    results = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".py") or fn in SKIP_FILES:
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    src = f.read()
            except OSError:
                continue
            syms = collect_symbols_from_source(src)
            missing = {s for s in syms if s not in present}
            if missing:
                rel = os.path.relpath(path, root)
                results[rel] = missing
    return version, results


def main():
    ap = argparse.ArgumentParser(description="探测上游 fasthtml API 漂移")
    ap.add_argument("path", nargs="?", default=os.path.join(SKILL_ROOT, "examples"),
                    help="示例目录或 examples/ 根")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    targets = []
    if os.path.isdir(args.path) and \
       any(os.path.isdir(os.path.join(args.path, d)) for d in os.listdir(args.path)
            if d.startswith(("01-", "02-", "03-"))):
        # 当作 examples/ 根，逐个子目录
        for name in sorted(os.listdir(args.path)):
            sub = os.path.join(args.path, name)
            if os.path.isdir(sub) and re.match(r"^\d{2}-", name):
                targets.append(sub)
    else:
        targets.append(args.path)

    any_missing = False
    report = {}
    for t in targets:
        res = scan_dir(t)
        if res is None:
            continue
        version, results = res
        report[os.path.basename(t)] = {f: sorted(s) for f, s in results.items()}
        if results:
            any_missing = True

    if args.json:
        import json
        print(json.dumps({"fasthtml": version, "examples": report},
                         ensure_ascii=False, indent=2))
    else:
        print(f"[probe] 全局 python-fasthtml 版本：{version}")
        if not any_missing:
            print("[probe] 未发现上游 import 了已移除的 fasthtml 符号 ✓")
        else:
            print("[probe] ⚠ 发现上游依赖了当前 fasthtml 已移除的符号：")
            for ex, files in report.items():
                if not files:
                    continue
                print(f"  • {ex}:")
                for f, syms in files.items():
                    print(f"      {f} -> {', '.join(syms)}")
            print(textwrap.dedent("""
            建议：在 gen_launchers.py 给该示例配置 isolated_venv（外置隔离环境），
            并在 requirements.txt 锁定兼容的 python-fasthtml 版本（如 <0.14.0），
            避免降级全局基线。详见 examples/README.md §启动器策略「版本互斥的正确处置」。
            """).strip())

    sys.exit(1 if any_missing else 0)


if __name__ == "__main__":
    main()
