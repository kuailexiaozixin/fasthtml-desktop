#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_gate.py — 统一发布门禁编排器（fasthtml-desktop）

把分散的质量门禁串成一条流水线：**全绿才放行**。
任一 required 步骤非零退出 → 整体非零退出（CI 可直接用）。

门禁顺序即契约（来自 quality-check 发布前自检）：
  1. pytest                逻辑门禁（单元/集成全绿）
  2. check_routes         服务端路由显式化（APIRouter 默认路由陷阱）
  3. check_routes_linkage  前端→后端链路校验（404 死链契约断裂）
  4. ui_window_verify     pywebview 原生窗口 UI 质检（DOM 断言 + 可选 html2canvas 截图；
                         需运行服务，--url 提供；否则跳过）
  5. verify_imports       导入完整性（.sh，缺失则仅告警）
  6. check_refs           文件引用完整性（.sh，缺失则仅告警）

路径语义（关键，避免 cwd 依赖导致的误判）：
  --root  : 项目根目录（所有相对路径的基准；默认=当前工作目录）
  --src   : 路由/仓库源码目录（传给 check_routes / check_routes_linkage 做静态扫描）。
            默认 "src"。可为相对 --root 的路径或绝对路径。
  --tests : pytest 测试目录（默认 "tests"，回退到 --src）。
            可为相对 --root 的路径或绝对路径。

用法：
  python release_gate.py --root /path/to/project
  python release_gate.py --root /path/to/project --url http://127.0.0.1:5001/
  python release_gate.py --root /path/to/project --skip-ui --skip-sh

退出码：
  0 = 全部 required 门禁通过
  1 = 有 required 门禁失败
  2 = 用法/环境错误
"""

import argparse
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def here() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def resolve(script_name: str) -> str | None:
    """优先用与本脚本同目录的技能脚本，否则在 PATH 中查找。"""
    sibling = os.path.join(here(), script_name)
    if os.path.isfile(sibling):
        return sibling
    alt = os.path.join(here(), "scripts", script_name)
    if os.path.isfile(alt):
        return alt
    from shutil import which

    return which(script_name)


def resolve_path(p: str, root: str) -> str:
    """相对路径以 --root 为基准解析；绝对路径原样返回。"""
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(root, p))


class Gate:
    def __init__(self, name: str, cmd: list[str], required: bool = True,
                 hint: str = ""):
        self.name = name
        self.cmd = cmd
        self.required = required
        self.hint = hint
        self.ok = None
        self.detail = ""

    def run(self) -> bool:
        try:
            p = subprocess.run(self.cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
        except FileNotFoundError as e:
            self.ok = None
            self.detail = f"未找到可执行：{e}"
            return False
        self.ok = (p.returncode == 0)
        tail = (p.stdout or p.stderr or "").strip().splitlines()[-6:]
        self.detail = "\n".join(tail)
        return self.ok


def main() -> int:
    ap = argparse.ArgumentParser(description="fasthtml-desktop 统一发布门禁")
    ap.add_argument("--root", default=os.getcwd(),
                    help="项目根目录（所有相对路径基准，默认=当前目录）")
    ap.add_argument("--src", default="src",
                    help="路由/源码扫描目录（传给 check_routes / linkage），默认 src")
    ap.add_argument("--tests", default=None,
                    help="pytest 测试目录（默认 tests，回退到 --src）")
    ap.add_argument("--url", default=None,
                    help="运行中的服务基址，提供则启用 UI 视觉质检")
    ap.add_argument("--skip-ui", action="store_true", help="跳过 UI 视觉质检")
    ap.add_argument("--skip-sh", action="store_true",
                    help="跳过 verify_imports / check_refs（.sh 门禁）")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"[FAIL] --root 不存在或不是目录: {root}", file=sys.stderr)
        return 2

    src_path = resolve_path(args.src, root)
    test_dir = resolve_path(args.tests, root) if args.tests else None
    if test_dir and not os.path.isdir(test_dir):
        test_dir = None
    if test_dir is None:
        candidate = resolve_path("tests", root)
        test_dir = candidate if os.path.isdir(candidate) else src_path

    py = sys.executable
    gates: list[Gate] = []

    # 1. pytest（required）— 指向测试目录
    gates.append(Gate("pytest 逻辑门禁",
                      [py, "-m", "pytest", "-q", test_dir],
                      required=True,
                      hint="新业务模块必须 test-first；bug 修复必须 Prove-It"))

    # 2. 服务端路由显式化（required）
    cr = resolve("check_routes.py")
    if cr:
        gates.append(Gate("check_routes 服务端路由显式化",
                          [py, cr, src_path], required=True,
                          hint="禁止 @ar(...) 漏写显式路径（函数名派生 404 陷阱）"))
    else:
        print("[WARN] 未找到 check_routes.py，跳过", file=sys.stderr)

    # 3. 前端→后端链路校验（required）
    crl = resolve("check_routes_linkage.py")
    if crl:
        gates.append(Gate("check_routes_linkage 前端→后端链路",
                          [py, crl, src_path], required=True,
                          hint="前端引用的端点必须有后端路由接住，否则 404 死链"))
    else:
        print("[WARN] 未找到 check_routes_linkage.py，跳过", file=sys.stderr)

    # 4. UI 视觉质检（可选，仅当提供 --url）
    #    pywebview 原生窗口方案（DOM 断言 + 可选 html2canvas 截图），
    #    无需额外浏览器、零浏览器授权。
    if not args.skip_ui and args.url:
        uv = resolve("ui_window_verify.py")
        if uv:
            gates.append(Gate("ui_window_verify 原生窗口质检",
                              [py, uv, "--url", args.url], required=False,
                              hint="pywebview 原生窗口直接驱动，无需额外浏览器、零浏览器授权；交付环境建议启用"))
        else:
            print("[WARN] 未找到 ui_window_verify.py，跳过 UI 视觉质检",
                  file=sys.stderr)
    elif not args.skip_ui and not args.url:
        print("[INFO] 未提供 --url，跳过 UI 视觉质检（如需请加 --url http://127.0.0.1:5001/）",
              file=sys.stderr)

    # 5/6. .sh 门禁（可选）
    if not args.skip_sh:
        for sh in ("verify_imports.sh", "check_refs.sh"):
            s = resolve(sh)
            if s:
                gates.append(Gate(sh, ["bash", s], required=False,
                                  hint="导入/引用完整性"))
            else:
                print(f"[WARN] 未找到 {sh}，跳过", file=sys.stderr)

    print("=" * 64)
    print("  fasthtml-desktop 统一发布门禁（release_gate）")
    print(f"  root = {root}")
    print(f"  src  = {src_path}")
    print(f"  test = {test_dir}")
    print("=" * 64)
    failed_required = 0
    for g in gates:
        mark = "▶ 运行" if g.required else "▶ 运行(可选)"
        print(f"  {mark} {g.name} ...")
        ok = g.run()
        if ok:
            print(f"      ✅ 通过")
        elif ok is False:
            tag = "❌ 失败(阻断)" if g.required else "⚠️ 失败(告警)"
            print(f"      {tag}")
            if g.detail:
                for ln in g.detail.splitlines():
                    print(f"        {ln}")
            if g.required:
                failed_required += 1
        else:
            print(f"      ⚠️ 跳过：{g.detail}")
    print("=" * 64)
    if failed_required:
        print(f"  ❌ {failed_required} 个 required 门禁未通过，禁止发布")
        return 1
    print("  ✅ 全部 required 门禁通过，可以发布")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
