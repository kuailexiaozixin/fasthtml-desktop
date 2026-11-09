#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fasthtml-desktop examples 上游同步 + 环境 + 启动器（三合一，--ensure 一键就绪）。

用法：
    python scripts/sync_upstream.py            # 检测并同步有更新的上游，然后建 venv + 补 bat
    python scripts/sync_upstream.py --check     # 仅检测漂移，不写盘
    python scripts/sync_upstream.py --ensure     # 使用技能前：补齐缺失/不完整 + 追新 + venv + bat
    python scripts/sync_upstream.py --force <id>  # 强制重拉指定 example

设计（与 VBA/xlwings 同源范式，适配 fasthtml-desktop）：
  * 上游 = predictivelabsai 组织各 example 仓库的 tarball 快照（examples/<名>/，无 .git）。
  * 深度清理：解压后按 manifest.exclude（mandatory + media）删无用产物，省体积。
  * keep：全量替换 example 目录时保留本地自研的 启动-*.bat。
  * 共享 venv：examples/.venv（D:\\Python 3.13.14）；依赖清单变化则重装。
  * 启动器：为缺 bat 的 example 生成简化 启动-<名>.bat（port/entry 读现有 bat 或默认）。
"""
from __future__ import annotations
import fnmatch, hashlib, json, os, platform, re, shutil, subprocess, sys, tarfile, time, urllib.request, ssl
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = SKILL_ROOT / "manifest.json"
TEMP = Path(os.environ.get("TEMP", "."))
TIMEOUT, RETRIES, RETRY_SLEEP = 900, 3, 3
CFG = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
EXCL, KEEP, VENV = CFG["exclude"], CFG["keep"], CFG["venv"]
PIP_MIRRORS = [  # 国内优先，失败降级
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "https://pypi.org/simple/",
]


def find_gh():
    for c in (os.environ.get("GH", ""), r"C:\Users\贺新\AppData\Local\Programs\gh\bin\gh.exe",
              os.path.expanduser("~/.local/bin/gh"), "/usr/local/bin/gh"):
        if c and Path(c).is_file():
            return c
    return shutil.which("gh") or shutil.which("gh.exe")


GH = find_gh()


def run(cmd, timeout=60):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _http_get(url, timeout=60):
    ctx = ssl.create_default_context()
    for a in range(RETRIES):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fasthtml-desktop-sync"}), timeout=timeout, context=ctx).read()
        except Exception:
            if a < RETRIES - 1:
                time.sleep(RETRY_SLEEP)
    return None


def latest_head(repo, ref):
    for a in range(RETRIES):
        if GH:
            r = run([GH, "api", f"repos/{repo}/commits/{ref}", "--jq", ".sha"], timeout=60)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip().splitlines()[0]
        time.sleep(RETRY_SLEEP)
    return None


def download_tarball(repo, ref):
    """通道降级：codeload 直连 → ghfast 镜像。返回 (stage 顶层目录, channel) 或 (None, None)。"""
    slug = repo.split("/")[1]
    urls = [f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{ref}",
            f"https://ghfast.top/https://github.com/{repo}/archive/refs/heads/{ref}.tar.gz"]
    for url, ch in zip(urls, ("codeload", "ghfast")):
        for a in range(RETRIES):
            data = _http_get(url, TIMEOUT)
            if not data:
                if a < RETRIES - 1:
                    time.sleep(RETRY_SLEEP)
                break
            stage = Path(TEMP) / f"fhd_{slug}_{int(time.time())}"
            stage.mkdir(parents=True, exist_ok=True)
            tf = stage / f"{slug}.tar.gz"
            tf.write_bytes(data)
            try:
                top = None
                with tarfile.open(tf) as t:
                    top = t.getnames()[0].split("/")[0]
                    t.extractall(stage)
                if top and (stage / top).is_dir():
                    return stage / top, ch
            except Exception:
                pass  # 截断/损坏 → 下一通道
            shutil.rmtree(stage, ignore_errors=True)
    return None, None


def apply_exclude(stage: Path, deep: bool = True):
    """按 manifest.exclude 删无用产物。返回 (删除项数, 释放字节数)。"""
    patterns = list(EXCL["mandatory"]) + (EXCL.get("media", []) if deep else [])
    removed, freed = 0, 0
    for p in list(stage.rglob("*")):
        rel = p.relative_to(stage).as_posix()
        hit = (any(fnmatch.fnmatch(rel, pat) for pat in patterns)
               or any(rel.startswith(pat.rstrip("/")) for pat in patterns if "*" not in pat and "?" not in pat))
        if not hit:
            continue
        if p.is_file():
            freed += p.stat().st_size
            p.unlink()
        else:
            shutil.rmtree(p, ignore_errors=True)
        removed += 1
    return removed, freed


def replace_example(stage: Path, example: Path) -> bool:
    """备份 example→.old → 清空 → 拷入 stage → 恢复本地 启动-*.bat → 删 .old。"""
    old = example.with_name(example.name + ".old")
    if old.exists():
        shutil.rmtree(old, ignore_errors=True)
    example.rename(old)
    example.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in stage.rglob("*"):
        if p.is_file():
            tgt = example / p.relative_to(stage)
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, tgt)
            n += 1
    for b in old.rglob("启动-*.bat"):  # 保留本地自研启动脚本
        r = b.relative_to(old)
        (example / r).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(b, example / r)
    if n == 0:
        shutil.rmtree(example, ignore_errors=True)
        old.rename(example)
        return False
    shutil.rmtree(old, ignore_errors=True)
    return True


def is_incomplete(src) -> bool:
    """本地 example 缺失/无源码视为需重建。用「有任意 .py 或 README」判完整，
    不依赖特定入口文件名（各 example 入口命名不一：web_app/api_app/app/main…），避免误判。"""
    t = SKILL_ROOT / src["local_dir"]
    if not t.exists() or not any(t.rglob("*")):
        return True
    return not (any(t.rglob("*.py")) or (t / "README.md").exists())


def _clean_env():
    """去掉 PYTHONHOME/PYTHONPATH（本机常被灵犀 python-env 劫持，会导致 venv 建失败/SRE mismatch）。"""
    return {k: v for k, v in os.environ.items() if k not in ("PYTHONHOME", "PYTHONPATH")}


def _collect_all_deps(sources) -> list[str]:
    """收集所有 example 的依赖（requirements.txt + pyproject.toml），返回去重后的 pip 包名列表。"""
    import tomllib
    seen: dict[str, None] = {}
    for s in sources:
        ex = SKILL_ROOT / s["local_dir"]
        # 处理嵌套目录（FastERP/FastERP/, FastCRM/FastCRM/ 等）
        sub = ex / s["id"]
        search_dirs = [sub] if sub.is_dir() else [ex]
        for d in search_dirs:
            req = d / "requirements.txt"
            if req.is_file():
                for line in req.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if not line or line.startswith(("#", "-", "--")):
                        continue
                    m = re.match(r"^([a-zA-Z0-9][a-zA-Z0-9._\-]*(?:\[[\w,\-]+\])?)", line)
                    if m:
                        seen.setdefault(m.group(1).lower(), None)
            pyp = d / "pyproject.toml"
            if pyp.is_file():
                try:
                    with open(pyp, "rb") as f:
                        data = tomllib.load(f)
                    for dep in data.get("project", {}).get("dependencies", []):
                        m = re.match(r"^\s*([a-zA-Z0-9][a-zA-Z0-9._\-]*(?:\[[\w,\-]+\])?)", dep)
                        if m:
                            seen.setdefault(m.group(1).lower(), None)
                except Exception:
                    pass
    # 加上通用依赖
    for extra in ("uvicorn", "python-fasthtml"):
        seen.setdefault(extra, None)
    return list(seen.keys())

def ensure_venv(sources):
    """建/复用共享 examples/.venv；依赖清单变化则用国内镜像重装。"""
    env = _clean_env()
    vdir = SKILL_ROOT / VENV["dir"]
    py = VENV["python"]
    pyexe = vdir / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")
    if not vdir.exists() or not pyexe.exists():
        shutil.rmtree(vdir, ignore_errors=True)
        r = subprocess.run([py, "-m", "venv", str(vdir)], capture_output=True, text=True, env=env)
        print(f"  [venv] 新建 {vdir.name}" + ("" if r.returncode == 0 else "（失败）: " + r.stderr.strip()[:120]))
        if r.returncode:
            return
    # 收集所有依赖
    all_pkgs = _collect_all_deps(sources)
    blob = "|".join(sorted(all_pkgs))
    digest = hashlib.sha256(blob.encode()).hexdigest()
    marker = vdir / ".deps.sha256"
    changed = (not marker.is_file()) or marker.read_text().strip() != digest
    if changed:
        vpython = str(pyexe)
        print(f"  [venv] 依赖变化 → 安装 {len(all_pkgs)} 个包…")
        installed = False
        for mirror in PIP_MIRRORS:
            cmd = [vpython, "-m", "pip", "install", "-q", "-i", mirror]
            if "aliyun" in mirror:
                cmd += ["--trusted-host", "mirrors.aliyun.com"]
            cmd += all_pkgs
            r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=900)
            if r.returncode == 0:
                print(f"  [venv] 安装成功（{mirror}）")
                installed = True
                break
            print(f"  [venv] {mirror} 失败: {r.stderr.strip()[:120]}")
        if not installed:
            print("  [venv] 全部镜像失败，请手动: pip install " + " ".join(all_pkgs[:5]) + " …")
        else:
            marker.write_text(digest)
    else:
        print(f"  [venv] 依赖未变（{len(all_pkgs)} 个），跳过重装")


def _detect_entry(ex: Path) -> tuple[str, str, str]:
    """检测入口文件、运行模式、嵌套子目录。
    返回 (entry, mode, nested):
      entry: "web_app:app" (uvicorn 模式) 或 "web_app.py" (直接运行模式)
      mode:  "uvicorn" 或 "direct"
      nested: "" (无嵌套) 或子目录名（如 "FastERP"）
    """
    # 检测嵌套子目录（examples/FastERP/FastERP/）
    nested = ""
    for child in ex.iterdir():
        if child.is_dir() and child.name == ex.name:
            nested = child.name
            break
    search_dir = ex / nested if nested else ex

    # 优先查入口候选
    candidates = ["web_app.py", "api_app.py", "main.py", "app.py", "server.py"]
    found = None
    for cand in candidates:
        if (search_dir / cand).is_file():
            found = cand
            break
    if not found:
        # 回退：找任意 .py（排除 test/seed/migration）
        for py in sorted(search_dir.glob("*.py")):
            if not any(x in py.name for x in ("test", "seed", "conftest", "migration")):
                found = py.name
                break
    if not found:
        return "web_app:app", "uvicorn", nested

    # 判断运行模式：文件含 uvicorn.run() 或 serve() 则用 direct
    content = (search_dir / found).read_text(errors="ignore")[:5000]
    if "uvicorn.run(" in content or "serve(app" in content or "if __name__" in content and "serve" in content:
        return found, "direct", nested
    return f"{found[:-3]}:app", "uvicorn", nested

def _port_for(s: dict, ex: Path) -> str:
    """从已有 bat 读端口，否则用默认值。"""
    existing = list(ex.glob("启动-*.bat"))
    if existing:
        m = re.search(r"--port\s+(\d{4,5})", existing[0].read_text(encoding="gbk", errors="ignore"))
        if m:
            return m.group(1)
    # 默认按字母序分配（FastAccounts=5026, FastBI=5000, …）
    defaults = {"FastAccounts":"5026","FastBI":"5000","FastBot":"5028","FastCal":"5005",
                "FastCLM":"5029","FastCRM":"5006","FastDataGov":"5062","FastDPS":"5030",
                "FastDocs":"5016","FastDrive":"5012","FastERP":"5011","FastFPA":"5031",
                "FastHRM":"5032","FastLegal":"5007","FastMail":"5009","FastMeet":"5015",
                "FastOffice":"5020","FastSheets":"5014","FastShop":"5025","FastSlides":"5013",
                "FastSurvey":"5035","FastVC":"5036","FastWiki":"5022"}
    return defaults.get(s["id"], "5000")

def gen_bats(sources):
    """为缺 bat 且非 db_required 的 example 生成带 preflight 的 启动-<名>.bat。"""
    made = 0
    for s in sources:
        ex = SKILL_ROOT / s["local_dir"]
        if not ex.exists() or s.get("db_required") or list(ex.glob("启动-*.bat")):
            continue
        entry, mode, nested = _detect_entry(ex)
        port = _port_for(s, ex)
        ex_id = s["id"]
        # 构建 bat 内容
        lines = [
            '@echo off',
            'setlocal',
            'cd /d "%~dp0"',
            'chcp 65001 >nul',
            'set "VENV=%~dp0..\\.venv"',
            'set "PY=%VENV%\\Scripts\\python.exe"',
            'if not exist "%PY%" (',
            '    echo [错误] 共享 venv 缺失',
            '    echo 请先运行: python scripts\\sync_upstream.py --ensure',
            '    pause & exit /b 1',
            ')',
            'REM 依赖自检：缺失则自动安装（Aliyun 镜像）',
            f'"%PY%" "%~dp0..\\check_deps.py" {ex_id}',
            'if errorlevel 1 (',
            '    echo [错误] 依赖安装失败',
            '    pause & exit /b 1',
            ')',
            f'echo ========================================',
            f'echo  {ex_id}  http://127.0.0.1:{port}',
            'echo  关闭此窗口即停止服务',
            f'echo ========================================',
        ]
        if nested:
            lines.append(f'cd /d "%~dp0{nested}"')
        lines.append(f'start "" "http://127.0.0.1:{port}"')
        if mode == "direct":
            lines.append(f'"%PY%" {entry}')
        else:
            lines.append(f'"%PY%" -m uvicorn {entry} --host 127.0.0.1 --port {port}')
        lines.append('if errorlevel 1 pause')
        (ex / f"启动-{ex_id}.bat").write_text("\r\n".join(lines) + "\r\n", encoding="gbk")
        made += 1
    print(f"  [bat] 生成 {made} 个 启动脚本（已有/需配库者保留）")

def migrate_bats(sources):
    """为已有 bat 添加 preflight check_deps.py 调用（一次性迁移，幂等）。"""
    migrated = 0
    for s in sources:
        if s.get("db_required"):
            continue
        ex = SKILL_ROOT / s["local_dir"]
        bats = list(ex.glob("启动-*.bat"))
        if not bats:
            continue
        for bat in bats:
            content = bat.read_text(encoding="gbk", errors="ignore")
            if "check_deps.py" in content:
                continue  # 已有 preflight，跳过
            # 在 "echo =" 行之前插入 preflight 块
            ex_id = s["id"]
            preflight = (
                f'REM 依赖自检：缺失则自动安装（Aliyun 镜像）\r\n'
                f'"%PY%" "%~dp0..\\check_deps.py" {ex_id}\r\n'
                f'if errorlevel 1 (\r\n'
                f'    echo [错误] 依赖安装失败\r\n'
                f'    pause & exit /b 1\r\n'
                f')\r\n'
            )
            # 找插入位置：在 "start " 或 uvicorn/python 行之前
            lines = content.split("\r\n")
            insert_at = len(lines)
            for i, line in enumerate(lines):
                if line.startswith("start ") or "uvicorn" in line or '"%PY%"' in line:
                    insert_at = i
                    break
            lines.insert(insert_at, preflight.rstrip("\r\n"))
            bat.write_text("\r\n".join(lines), encoding="gbk")
            migrated += 1
    if migrated:
        print(f"  [bat] 迁移 {migrated} 个已有 bat（添加 preflight）")


def main() -> int:
    args = sys.argv[1:]
    check = "--check" in args
    ensure = "--ensure" in args
    force = [a for a in args[args.index("--force") + 1:] if not a.startswith("--")] if "--force" in args else []
    sources = CFG["sources"]
    stats = {"updated": [], "unchanged": [], "failed": []}
    for src in sources:
        vid = src["id"]
        if force and vid not in force:
            continue
        head = latest_head(src["repo"], src["ref"])
        pinned = (src.get("pinned_sha") or "")[:12]
        stale = head is not None and head[:12] != pinned
        missing = is_incomplete(src)
        if check:
            print(f"[check] {vid}: " + ("需重建(缺失)" if missing else "有更新" if stale else "已是最新"))
            stats["unchanged"].append(vid)
            continue
        do = missing or stale or vid in force or (ensure and (missing or stale))
        if not do:
            stats["unchanged"].append(vid)
            continue
        stage, ch = download_tarball(src["repo"], src["ref"])
        if stage is None:
            stats["failed"].append(vid)
            print(f"  [{vid}] 下载失败（通道均不可达）")
            continue
        removed, freed = apply_exclude(stage, deep=True)
        if not replace_example(stage, SKILL_ROOT / src["local_dir"]):
            stats["failed"].append(vid)
            print(f"  [{vid}] 替换失败")
            continue
        if head:
            src["pinned_sha"] = head
        stats["updated"].append(vid)
        print(f"  [{vid}] 已更新（{ch}）：清产物 {freed/1e6:.1f}MB/{removed} 项 → {src['local_dir']}")
    if not check:
        MANIFEST.write_text(json.dumps(CFG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig")
        ensure_venv(sources)
        gen_bats(sources)
        migrate_bats(sources)
        print("\n完成：" + "; ".join(f"{k}: {'、'.join(v) if v else '无'}" for k, v in stats.items()))
    return 1 if stats["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
