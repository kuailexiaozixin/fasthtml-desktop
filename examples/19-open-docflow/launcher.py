# -*- coding: utf-8 -*-
"""launcher.py — 一键启动决策层（`启动.bat` 的唯一后端，配置驱动）

本文件是一个**无状态引擎**：所有项目相关配置都从同目录下的 `launcher.json` 读取，
本文件本身在 20 个示例间逐字节相同（由 `scripts/gen_launchers.py` 统一分发）。
含义：改逻辑只改这一份；改某个示例的行为只改它的 `launcher.json`。

设计铁律（见 SKILL.md §标准交付物 / references/launch-standard-deliverable.md）：
  * **bat 只派发、Python 做决策**：`启动.bat` 仅 `cd` + 确认 PATH 有 python +
    调用 `python launcher.py %*`（≤8 行）。依赖预检 / 安装 / 降级防护 / WebView2
    探测 / 日志取证全部在本引擎，用 `sys.executable` 天然消除解释器二义性。
  * **依赖预检必须解析 requirements.txt 逐条检查**，禁止写死模块名子集（会假阳性放行）。
  * **禁止降级用户已装包**：安装前用 `pip install --dry-run --report` 预演，
    检出任何 downgrade（含传递依赖）即告警中止。
  * **禁止全量重定向**：控制台实时输出 + 同步 tee 到 `启动诊断.log`，两者兼得。
  * **零硬编码路径**：所有路径相对 `__file__`；跨解释器重入用 subprocess 列表传参，
    兼容含空格的路径（如 `...\\WPS 灵犀\\...`），可在任意用户机器上运行。

三种环境策略（互斥，由 launcher.json 字段控制）：
  * use_venv=false（默认，examples）：复用系统全局 site-packages，不建 .venv，目录干净。
  * use_venv=true（真实项目）：在项目目录内建最小 .venv 并 re-exec 进去，隔离优先。
  * isolated_venv / bundled_venv（非空）：在**项目目录之外**（默认
    `%LOCALAPPDATA%/fasthtml-desktop/venvs/`，可用环境变量 `FD_VENV_HOME` 改）建
    `--system-site-packages` 环境并 re-exec 进去。
      - isolated_venv（conflict）：版本互斥示例（如 fasthtml<0.14.0 vs 全局 0.14.9），
        装进去的包遮蔽全局同名包，全局原版一个字节不动；示例目录不留 .venv。
      - bundled_venv（bundled）：无版本互斥、仅依赖体积大/可选（如 LLM SDK），
        继承全局、只补装重型包，全局依旧不被污染。这是*显式声明的重型依赖收纳处*，
        不是借版本互斥之名行规避之实（与铁律「禁止用隔离规避非冲突」不冲突）。

用法：
    python launcher.py            # 桌面窗口模式
    python launcher.py server     # 无头模式（SERVER_ONLY=1，CI / 服务器）
    python launcher.py --check    # 只做依赖体检，不启动
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG_PATH = HERE / "启动诊断.log"
CFG_PATH = HERE / "launcher.json"
TAG = "[launcher]"

# launcher.json 字段默认值（examples 行为）。真实项目经 bootstrap 生成时会覆盖。
_DEFAULTS = {
    "app_name": "FastHTML Desktop App",
    "entry": None,            # None = 自动探测 src/main.py -> main.py
    "use_venv": False,        # 真实项目用 true（建 .venv）
    "isolated_venv": "",      # 非空 = 版本互斥示例：目录外隔离环境并 re-exec
    "bundled_venv": "",       # 非空 = 重型可选依赖示例：目录外收纳（不污染全局）
    "auto_install": True,     # false = 只预检不安装（依赖版本与其它示例互斥时）
    "install_note": "",       # auto_install=false 时展示给用户的说明
    "startup_note": "",       # 启动前的额外提示（如需要 API Key）
    "side_processes": [],     # 伴随子进程：[{cmd:[...], cwd:".", wait_port:int, wait_timeout:30}]
    "pip_index": "https://pypi.tuna.tsinghua.edu.cn/simple",
}


def _load_cfg() -> dict:
    cfg = dict(_DEFAULTS)
    if CFG_PATH.exists():
        try:
            data = json.loads(CFG_PATH.read_text(encoding="utf-8", errors="replace"))
            if isinstance(data, dict):
                cfg.update({k: v for k, v in data.items() if k in _DEFAULTS})
        except Exception as e:
            sys.stderr.write(f"{TAG} 读取 launcher.json 失败，使用默认配置：{e}\n")
    return cfg


CFG = _load_cfg()

# 由配置注入的模块级常量（下方逻辑与旧 run.py 完全相同，只是来源从「手填常量」改为「launcher.json」）
APP_NAME = CFG["app_name"]
ENTRY = CFG["entry"]
USE_VENV = CFG["use_venv"]
ISOLATED_VENV = CFG["isolated_venv"]
BUNDLED_VENV = CFG["bundled_venv"]
AUTO_INSTALL = CFG["auto_install"]
INSTALL_NOTE = CFG["install_note"]
STARTUP_NOTE = CFG["startup_note"]
SIDE_PROCESSES = CFG["side_processes"]
PIP_INDEX = CFG["pip_index"]

# 分发名 -> import 名（仅在 importlib.metadata 查不到时兜底）
_DIST2MOD = {
    "python-fasthtml": "fasthtml",
    "pywebview": "webview",
    "python-dotenv": "dotenv",
    "pillow": "PIL",
    "pyyaml": "yaml",
    "beautifulsoup4": "bs4",
    "python-multipart": "multipart",
    "ast-grep-py": "ast_grep_py",
    "astra-assistants": "astra_assistants",
    "sqlite-minutils": "sqlite_minutils",
    "standard-imghdr": "imghdr",
    "hermes-agent": "run_agent",
}


# ------------------------------------------------------------------ 控制台 / 日志
class Tee:
    """控制台实时输出 + 同步落盘。绝不用 `> log 2>&1` 吞掉全部输出。"""

    def __init__(self, path: Path):
        self.path = path
        # 切解释器重入时用追加模式，否则子进程会把父进程刚写的建环境记录截断掉
        mode = "a" if os.environ.get("FD_REEXEC") else "w"
        try:
            self.fh = open(path, mode, encoding="utf-8", errors="replace")
        except Exception:
            self.fh = None

    def write(self, text: str = "") -> None:
        try:
            print(text, flush=True)
        except UnicodeEncodeError:                     # 老式 GBK 控制台兜底
            sys.stdout.buffer.write(text.encode("utf-8", "replace") + b"\n")
            sys.stdout.flush()
        if self.fh:
            self.fh.write(text + "\n")
            self.fh.flush()

    def close(self) -> None:
        if self.fh:
            self.fh.close()
            self.fh = None


# ------------------------------------------------------------------ requirements 解析
class Req:
    __slots__ = ("name", "spec", "raw")

    def __init__(self, name: str, spec: str, raw: str):
        self.name = name          # 规范化分发名（小写、- 统一）
        self.spec = spec          # 传给 pip 的完整片段（含版本约束，不含 marker）
        self.raw = raw            # 原始行


def _marker_ok(marker: str) -> bool:
    """求值 PEP 508 environment marker 的常用子集，无法判定时按 True 处理。"""
    env = {
        "sys_platform": sys.platform,
        "platform_system": {"win32": "Windows", "darwin": "Darwin"}.get(sys.platform, "Linux"),
        "python_version": "%d.%d" % sys.version_info[:2],
        "python_full_version": "%d.%d.%d" % sys.version_info[:3],
        "os_name": os.name,
    }
    expr = marker.strip()
    if not expr:
        return True
    for key, val in env.items():
        expr = re.sub(r"\b%s\b" % key, repr(val), expr)
    if re.search(r"[^\w\s'\"().,=<>!+-]", expr):
        return True                                     # 出现未知 token，保守放行
    try:
        return bool(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 (受限表达式)
    except Exception:
        return True


def parse_requirements(path: Path, _seen: set[Path] | None = None) -> list[Req]:
    """逐条解析 requirements.txt（支持注释 / marker / extras / -r 递归 / 全局选项行）。"""
    _seen = _seen or set()
    if not path.exists() or path in _seen:
        return []
    _seen.add(path)
    out: list[Req] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith(("-r ", "--requirement ")):
            out += parse_requirements((path.parent / line.split(None, 1)[1].strip()).resolve(), _seen)
            continue
        if line.startswith("-"):                        # --only-binary / --index-url 等全局选项
            continue
        spec, _, marker = line.partition(";")
        if marker and not _marker_ok(marker):
            continue
        spec = spec.strip()
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", spec)
        if not m:
            continue
        out.append(Req(m.group(1).lower().replace("_", "-"), spec, raw.strip()))
    return out


def reqs_from_pyproject(path: Path) -> list[Req]:
    """无 requirements.txt 时从 pyproject.toml [project].dependencies 兜底提取。"""
    if not path.exists():
        return []
    try:
        import tomllib
    except ModuleNotFoundError:                         # Python < 3.11
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[Req] = []
    for dep in data.get("project", {}).get("dependencies", []) or []:
        spec, _, marker = str(dep).partition(";")
        if marker and not _marker_ok(marker):
            continue
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", spec.strip())
        if m:
            out.append(Req(m.group(1).lower().replace("_", "-"), spec.strip(), str(dep)))
    return out


# ------------------------------------------------------------------ 已装版本探测
def installed_version(dist_name: str) -> str | None:
    """优先按分发名查 metadata（最准），查不到再按 import 名兜底探测。"""
    import importlib.metadata as md
    import importlib.util

    for candidate in (dist_name, dist_name.replace("-", "_"), dist_name.replace("_", "-")):
        try:
            return md.version(candidate)
        except Exception:
            continue
    mod = _DIST2MOD.get(dist_name, dist_name.replace("-", "_"))
    try:
        if importlib.util.find_spec(mod) is not None:
            return "unknown"
    except Exception:
        pass
    return None


def _vt(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4]) or (0,)


# ------------------------------------------------------------------ pip 执行
def pip_run(args: list[str], tee: Tee, capture: bool = False) -> tuple[int, str]:
    cmd = [sys.executable, "-m", "pip", *args]
    if PIP_INDEX and not any(a.startswith(("-i", "--index-url")) for a in args):
        cmd += ["-i", PIP_INDEX]
    tee.write("  $ " + " ".join(cmd[1:]))
    if capture:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace", bufsize=1)
    for line in p.stdout:                               # 实时逐行，绝不静默数分钟
        tee.write("    " + line.rstrip())
    p.wait()
    return p.returncode, ""


def plan_downgrades(specs: list[str], tee: Tee) -> list[tuple[str, str, str]]:
    """用 pip --dry-run --report 预演本次安装，检出所有会被降级的包（含传递依赖）。"""
    rc, out = pip_run(["install", "--dry-run", "--quiet", "--report", "-", *specs], tee, capture=True)
    if rc != 0:
        tee.write("  [提示] 安装预演未成功（离线或解析失败），跳过降级预检。")
        return []
    try:
        report = json.loads(out[out.index("{"):out.rindex("}") + 1])
    except Exception:
        return []
    downs: list[tuple[str, str, str]] = []
    for item in report.get("install", []):
        meta = item.get("metadata", {})
        name, new = str(meta.get("name", "")).lower(), str(meta.get("version", ""))
        cur = installed_version(name)
        if cur and cur != "unknown" and new and _vt(new) < _vt(cur):
            downs.append((name, cur, new))
    return downs


# ------------------------------------------------------------------ WebView2
def check_webview2() -> bool:
    if sys.platform != "win32":
        return True
    key = r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    try:
        import winreg
        for hive, sub in ((winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node" + key[len("SOFTWARE"):]),
                          (winreg.HKEY_LOCAL_MACHINE, key),
                          (winreg.HKEY_CURRENT_USER, key)):
            try:
                with winreg.OpenKey(hive, sub):
                    return True
            except OSError:
                continue
    except Exception:
        pass
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base and Path(base, "Microsoft", "EdgeWebView", "Application").exists():
            return True
    return False


# ------------------------------------------------------------------ 切解释器重入
def reexec(py: Path, tee: Tee) -> None:
    """切换到 `py` 解释器重新执行本文件，并以子进程退出码退出。

    ⚠️ **Windows 上禁止用 `os.execv`**：CRT 的 execv 用空格拼接 argv 且**不加引号**，
    只要脚本路径含空格（如 `...\\WPS 灵犀\\...`）子进程就会把路径截成两段，实测报
    `can't open file 'C:\\Users\\x\\AppData\\Roaming\\WPS'`。改用 subprocess 传列表，
    由 list2cmdline 正确加引号；代价只是多留一个父进程壳，换来路径健壮性。
    """
    cmd = [str(py), str(Path(__file__).resolve()), *sys.argv[1:]]
    tee.write("  $ " + subprocess.list2cmdline(cmd))
    tee.close()
    env = dict(os.environ, FD_REEXEC="1")               # 让子进程以追加模式续写同一份日志
    sys.exit(subprocess.call(cmd, env=env))


# ------------------------------------------------------------------ venv（仅真实项目）
def ensure_venv(tee: Tee) -> None:
    """use_venv=true 时：确保 .venv 存在并重入（examples 不走这里）。"""
    venv_py = HERE / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if Path(sys.prefix).resolve() == (HERE / ".venv").resolve():
        return
    if not venv_py.exists():
        tee.write(f"{TAG} 创建最小虚拟环境 .venv ...")
        subprocess.run([sys.executable, "-m", "venv", str(HERE / ".venv")], check=True)
    tee.write(f"{TAG} 切换到 .venv 解释器重新执行 ...")
    reexec(venv_py, tee)


# --------------------------------------------- 外置隔离 venv（仅版本互斥示例）
def venv_home() -> Path:
    """隔离环境的统一落点：**永远在项目目录之外**，保证技能/示例目录零膨胀。

    Windows 下统一落在用户指定的 D:\临时环境（可用 FD_VENV_HOME 覆盖），
    与 hermes-desktop 技能一致；非 Windows 回退到用户主目录 .cache，避免硬编码盘符。
    """
    if os.environ.get("FD_VENV_HOME"):
        return Path(os.environ["FD_VENV_HOME"])
    if os.name == "nt":
        candidate = Path(r"D:\临时环境")
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except Exception:
            pass
        root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(root) / "fasthtml-desktop" / "venvs"
    return Path(os.path.expanduser("~")) / ".cache" / "fasthtml-desktop" / "venvs"


def isolated_dir() -> Path:
    return venv_home() / ISOLATED_VENV


def in_isolated() -> bool:
    try:
        return bool(ISOLATED_VENV) and Path(sys.prefix).resolve() == isolated_dir().resolve()
    except Exception:
        return False


def external_venv_name() -> str:
    """当前生效的"目录外运行环境"名字：版本互斥=isolated_venv，重型可选依赖=bundled_venv。"""
    return ISOLATED_VENV or BUNDLED_VENV


def external_venv_dir() -> Path:
    return venv_home() / external_venv_name()


def in_external_venv() -> bool:
    name = external_venv_name()
    if not name:
        return False
    try:
        return Path(sys.prefix).resolve() == external_venv_dir().resolve()
    except Exception:
        return False


def external_venv_mode() -> str:
    if ISOLATED_VENV:
        return "conflict"   # 版本互斥：装进去的包遮蔽全局同名包
    if BUNDLED_VENV:
        return "bundled"    # 重型可选依赖：继承全局、仅补装重型包
    return ""


def _uv() -> list[str] | None:
    """探测 uv：优先 PATH 上的独立二进制，其次 `python -m uv`。都没有则返回 None。"""
    exe = shutil.which("uv")
    if exe:
        return [exe]
    try:
        p = subprocess.run([sys.executable, "-m", "uv", "--version"],
                           capture_output=True, timeout=20)
        if p.returncode == 0:
            return [sys.executable, "-m", "uv"]
    except Exception:
        pass
    return None


def _stream(cmd: list[str], tee: Tee) -> int:
    tee.write("  $ " + " ".join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace", bufsize=1)
    for line in p.stdout:
        tee.write("    " + line.rstrip())
    return p.wait()


def ensure_external_venv(tee: Tee, install: bool = True, name: str | None = None,
                         mode: str | None = None) -> bool:
    """建"目录外 + 继承全局"的运行环境并 re-exec 进去；成功不返回（已 sys.exit）。

    `name`/`mode` 缺省时取 isolated_venv（版本互斥）或 bundled_venv（重型可选依赖）。
    两种档位共用同一套机制（都落在 %LOCALAPPDATA%/fasthtml-desktop/venvs/<名字>，
    都是 --system-site-packages），区别仅在于*意图*：
      * conflict（isolated_venv）：上游版本与全局互斥（如 fasthtml<0.14.0 vs 0.14.9），
        装进去的包会**遮蔽**全局同名包，全局原版一个字节不动。
      * bundled（bundled_venv）：无版本互斥，仅依赖体积大/可选（如 LLM SDK），不想灌全局；
        继承全局、只补装重型包，全局依旧不被污染。
    这与铁律"禁止用隔离规避非冲突"不冲突——bundled_venv 是*显式声明的重型依赖收纳处*，
    不是借版本互斥之名行规避之实。
    """
    name = name or external_venv_name()
    if not name:
        return False
    mode = mode or external_venv_mode()
    target = venv_home() / name
    py = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    uv = _uv()
    if mode == "bundled":
        tee.write(f"{TAG} 重型可选依赖示例：使用目录外运行环境收纳依赖（不污染全局）")
    else:
        tee.write(f"{TAG} 版本互斥示例：使用隔离环境（在项目目录之外，示例目录不留 .venv）")
    tee.write(f"    位置：{target}")
    tee.write(f"    装包器：{'uv（全局 cache 硬链接，秒级）' if uv else 'pip（未装 uv，建议 pip install uv 提速）'}")

    if not py.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        made = False
        if uv:
            made = _stream([*uv, "venv", str(target), "--python", sys.executable,
                            "--system-site-packages"], tee) == 0 and py.exists()
        if not made:
            made = _stream([sys.executable, "-m", "venv", "--system-site-packages",
                            str(target)], tee) == 0 and py.exists()
        if not made:
            tee.write(f"{TAG} 运行环境创建失败，回退为「只预检不安装」。")
            return False

    # requirements 指纹戳：内容变了才重装，日常启动零开销
    req = HERE / "requirements.txt"
    stamp = target / ".fd_reqs_stamp"
    want = hashlib.md5(req.read_bytes()).hexdigest() if req.exists() else ""
    have = stamp.read_text(encoding="utf-8").strip() if stamp.exists() else ""
    if install and req.exists() and want != have:
        tee.write(f"{TAG} 向运行环境补装依赖（继承全局，只补缺的/与 pin 冲突的）...")
        ok = False
        if uv:
            cmd = [*uv, "pip", "install", "--python", str(py), "-r", str(req)]
            if PIP_INDEX:
                cmd += ["--index-url", PIP_INDEX]
            ok = _stream(cmd, tee) == 0
            if not ok:
                # uv 的 requirements 语法比 pip 严（例：`--only-binary a,b` 逗号列表 uv 拒收），
                # 上游 requirements 不该为装包器让路 —— 装包器失败就回退 pip，别卡住用户。
                tee.write(f"{TAG} uv 装包失败，回退 pip 重试（uv 对 requirements 语法更严格）...")
        if not ok:
            cmd = [str(py), "-m", "pip", "install", "-r", str(req)]
            if PIP_INDEX:
                cmd += ["-i", PIP_INDEX]
            ok = _stream(cmd, tee) == 0
        if ok:
            stamp.write_text(want, encoding="utf-8")
        else:
            tee.write(f"{TAG} 运行环境装包失败（检查网络或镜像源）；本次仍尝试进入该环境启动。")

    tee.write(f"{TAG} 切换到运行环境解释器重新执行 ...")
    reexec(py, tee)
    return True                                         # 不可达（reexec 内 sys.exit）


def ensure_isolated_venv(tee: Tee, install: bool = True) -> bool:
    """兼容包装：版本互斥档位（isolated_venv）。新代码请直接用 ensure_external_venv。"""
    return ensure_external_venv(tee, install, ISOLATED_VENV, "conflict")


# ------------------------------------------------------------------ 启动
def resolve_entry() -> Path | None:
    if ENTRY:
        p = HERE / ENTRY
        return p if p.exists() else None
    for cand in ("src/main.py", "main.py"):
        if (HERE / cand).exists():
            return HERE / cand
    return None


def launch(entry: Path, tee: Tee, headless: bool) -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"                   # 修子进程中文日志乱码
    env["PYTHONUTF8"] = "1"
    env.setdefault("PYTHONUNBUFFERED", "1")
    if headless:
        env["SERVER_ONLY"] = "1"
        env["RD_NO_GUI"] = "1"

    tee.write(f"{TAG} 启动 {APP_NAME} —— {entry.name}（日志同步写入 {LOG_PATH.name}）")
    tee.write("-" * 60)
    p = subprocess.Popen([sys.executable, str(entry)], cwd=str(HERE), env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace", bufsize=1)
    opened = closed = False
    try:
        for line in p.stdout:                           # 实时 tee，不做全量重定向
            line = line.rstrip()
            tee.write(line)
            if "WEBVIEW_WINDOW_OPENED" in line:
                opened = True
            if "WEBVIEW_WINDOW_CLOSED" in line:
                closed = True
    except KeyboardInterrupt:
        p.terminate()
    rc = p.wait()
    tee.write("-" * 60)

    if closed or (headless and rc == 0):
        tee.write(f"{TAG} {APP_NAME} 已正常退出。")
    elif opened:
        tee.write(f"{TAG} 窗口曾打开但事件循环异常退出（退出码 {rc}）。")
    elif rc != 0:
        tee.write(f"{TAG} 启动失败（退出码 {rc}）。请查看上方错误。")
        if sys.platform == "win32" and not check_webview2():
            tee.write(f"{TAG} 可能原因：未安装 Microsoft WebView2 Runtime。")
    else:
        tee.write(f"{TAG} 应用未打开窗口即退出。")
    return rc


# ------------------------------------------------------------------ 伴随子进程监管
_SIDE_PROCS: list = []


def _port_open(host: str, port: int, timeout: float = 30.0) -> bool:
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def _cleanup_side_procs() -> None:
    for p in _SIDE_PROCS:
        try:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except Exception:
                    p.kill()
        except Exception:
            pass


def start_side_processes(tee: Tee) -> None:
    """启动 side_processes 声明的伴随子进程（如外部服务 `langgraph dev`）并等待端口就绪；
    进程退出时由 atexit + 信号自动回收，无需示例自己手搓 subprocess。

    语义：把"多进程 / 外部服务"示例（如 #01 FastHTML UI + langgraph dev）的监管收归统一壳，
    桌面入口（desktop.py）只需打开窗口，不必再 `subprocess.Popen` 拉服务、再自己清理。
    每个 spec：{"cmd":[...], "cwd":"."（默认 HERE）, "wait_port":int, "wait_timeout":30}。
    """
    if not SIDE_PROCESSES:
        return
    import atexit
    import signal

    def _on_exit(*_a):
        _cleanup_side_procs()

    atexit.register(_on_exit)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _on_exit)
        except Exception:
            pass

    # 把当前解释器目录（可能是隔离/收纳 venv 的 Scripts/bin）前置到 PATH，
    # 让 `langgraph` 等命令解析到运行环境内那份，而非全局。
    env = dict(os.environ)
    bin_dir = str(Path(sys.executable).parent)
    env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")

    for spec in SIDE_PROCESSES:
        cmd = spec.get("cmd")
        if not cmd:
            continue
        cwd = spec.get("cwd") or str(HERE)
        tee.write(f"{TAG} 启动伴随子进程：{' '.join(cmd)} (cwd={cwd})")
        try:
            p = subprocess.Popen(cmd, cwd=cwd, env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            tee.write(f"{TAG} 伴随子进程启动失败：{e}")
            continue
        _SIDE_PROCS.append(p)
        port = spec.get("wait_port")
        if port:
            host = spec.get("wait_host", "127.0.0.1")
            timeout = float(spec.get("wait_timeout", 30))
            tee.write(f"{TAG} 等待伴随子进程端口 {host}:{port} 就绪（最多 {timeout}s）...")
            if _port_open(host, int(port), timeout):
                tee.write(f"{TAG} 伴随子进程端口 {host}:{port} 就绪。")
            else:
                tee.write(f"{TAG} 警告：等待 {host}:{port} 超时，继续启动（可能页面打不开）。")


# ------------------------------------------------------------------ 主流程
def main() -> int:
    args = [a.lower() for a in sys.argv[1:]]
    headless = "server" in args or os.environ.get("SERVER_ONLY") == "1"
    check_only = "--check" in args

    tee = Tee(LOG_PATH)
    tee.write(f"=== {APP_NAME} 启动器 ===")
    tee.write(f"{TAG} Python {sys.version.split()[0]}  ->  {sys.executable}")
    if sys.version_info < (3, 10):
        tee.write(f"{TAG} 错误：需要 Python 3.10+。")
        return 1

    if USE_VENV:
        ensure_venv(tee)

    # 0) 目录外运行环境（版本互斥 isolated_venv / 重型可选依赖 bundled_venv）：
    #    成功即重入，下面代码在新解释器里跑。
    #    --check 只在环境**已存在**时重入（体检要如实反映真正的运行环境），且不触发装包，
    #    避免"只想体检却被动建环境/下载几百 MB"。
    ext_name = external_venv_name()
    in_ext = in_external_venv()
    if ext_name and not in_ext:
        if not check_only:
            ensure_external_venv(tee)
        elif external_venv_dir().exists():
            ensure_external_venv(tee, install=False)
        else:
            tee.write(f"{TAG} --check：运行环境尚未创建（{external_venv_dir()}），"
                      "以下预检针对当前解释器，首次启动时会自动建环境。")
        in_ext = in_external_venv()
    if in_ext:
        tee.write(f"{TAG} 运行于目录外运行环境（全局环境未被改动）：{sys.prefix}")

    # 1) 依赖预检：逐条解析 requirements.txt（无则回退 pyproject.toml）
    reqs = parse_requirements(HERE / "requirements.txt")
    source = "requirements.txt"
    if not reqs:
        reqs = reqs_from_pyproject(HERE / "pyproject.toml")
        source = "pyproject.toml"
    if not reqs:
        tee.write(f"{TAG} 警告：未找到 requirements.txt / pyproject.toml，跳过依赖预检。")
    else:
        missing = [r for r in reqs if installed_version(r.name) is None]
        tee.write(f"{TAG} 依赖预检（{source}，共 {len(reqs)} 项）：缺失 {len(missing)} 项"
                  + ("" if not missing else " -> " + ", ".join(r.name for r in missing)))

        if missing and check_only:
            tee.write(f"{TAG} --check 模式：仅体检，不执行安装。缺失项如下")
            for r in missing:
                tee.write(f"    - {r.raw}")
        elif missing and (AUTO_INSTALL or in_ext):
            specs = [r.spec for r in missing]
            # 隔离环境内的降级是"预期行为"（互斥版本本就要遮蔽全局），不做降级拦截
            downs = []
            if not in_ext:
                tee.write(f"{TAG} 安装前预演，检查是否会降级已装包 ...")
                downs = plan_downgrades(specs, tee)
            if downs:
                tee.write(f"{TAG} 已中止安装：本次安装会降级以下已装包（禁止污染全局环境）")
                for name, cur, new in downs:
                    tee.write(f"    - {name}: 已装 {cur}  ->  将被降到 {new}")
                tee.write(f"{TAG} 处理建议：放宽本项目的版本 pin，或在独立虚拟环境中运行本项目。")
                tee.close()
                return 2
            tee.write(f"{TAG} 安装缺失依赖（只装缺的，不动已装包）...")
            rc, _ = pip_run(["install", *specs], tee)
            if rc != 0:
                tee.write(f"{TAG} 依赖安装失败（检查网络或镜像源）。")
                tee.close()
                return rc
            still = [r.name for r in missing if installed_version(r.name) is None]
            if still:
                tee.write(f"{TAG} 警告：安装后仍缺 " + ", ".join(still))
        elif missing:
            tee.write(f"{TAG} 本示例不自动安装依赖到当前环境（auto_install=false）。")
            if INSTALL_NOTE:
                tee.write(INSTALL_NOTE)
            if ext_name:
                tee.write("    运行环境未能建立（见上方日志）。手动重建：")
                tee.write(f'        python -m venv --system-site-packages "{external_venv_dir()}"')
                tee.write(f'        "{external_venv_dir() / "Scripts" / "python.exe"}" -m pip install -r requirements.txt')
                tee.write("    删除该目录即可完全卸载本示例的依赖，全局环境不受影响。")
            else:
                tee.write("    手动安装命令：")
                tee.write(f"    {Path(sys.executable).name} -m pip install -r requirements.txt")
            tee.close()
            return 3

    if check_only:
        tee.write(f"{TAG} --check 模式：依赖体检完成，不启动应用。")
        tee.close()
        return 0

    # 2.5) 伴随子进程（外部服务，如 langgraph dev）：由统一壳监管，桌面入口只管开窗
    start_side_processes(tee)

    # 2) WebView2（Windows 桌面窗口硬依赖）
    if not headless and not check_webview2():
        tee.write(f"{TAG} 警告：未检测到 Microsoft WebView2 Runtime，桌面窗口可能打不开。")
        tee.write("    下载：https://developer.microsoft.com/zh-cn/microsoft-edge/webview2/")

    if STARTUP_NOTE:
        tee.write(STARTUP_NOTE)

    # 3) 启动
    entry = resolve_entry()
    if entry is None:
        tee.write(f"{TAG} 错误：未找到入口（src/main.py 或 main.py）。")
        tee.close()
        return 1
    rc = launch(entry, tee, headless)
    tee.close()
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
