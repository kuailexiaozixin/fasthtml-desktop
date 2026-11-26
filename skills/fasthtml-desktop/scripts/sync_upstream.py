#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fasthtml-desktop examples 上游同步 + 环境 + 启动器（三合一，--ensure 一键就绪）。

用法：
    python scripts/sync_upstream.py            # 检测并同步有更新的上游，然后建 venv + 补 bat
    python scripts/sync_upstream.py --check     # 仅检测漂移，不写盘
    python scripts/sync_upstream.py --ensure     # 使用技能前：补齐缺失/不完整 + 追新 + venv + bat
    python scripts/sync_upstream.py --force <id>  # 强制重拉指定 example

设计（与 VBA/xlwings 同源范式，适配 fasthtml-desktop）：
  * HEAD 与 pinned SHA 一致时跳过；默认经 compare → trees → raw 做文件级增量。
  * 变更过多或增量不可用时，下载固定 HEAD SHA 的整仓库 tarball 全量兜底。
  * 增量与全量均在临时 stage 校验完整文件集与 blob SHA，替换失败回滚目标目录。
  * 深度清理：按 manifest.exclude（mandatory + media）删无用产物，省体积。
  * keep：远端 keep 文件不覆盖本地；替换时保留本地启动脚本与 .venv。
  * 共享 venv：examples/.venv（D:\\Python 3.13.14）；依赖清单变化则重装。
  * 启动器：为缺 bat 的 example 生成简化 启动-<名>.bat（port/entry 读现有 bat 或默认）。
"""
from __future__ import annotations
import concurrent.futures, fnmatch, gzip, hashlib, json, os, platform, re, shutil, stat, subprocess, sys, tarfile, tempfile, threading, time, urllib.request, ssl, uuid, zlib
from contextlib import contextmanager
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import quote, urlsplit

SKILL_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = SKILL_ROOT / "manifest.json"
TEMP = Path(os.environ.get("TEMP", "."))
TIMEOUT, RETRIES, RETRY_SLEEP = 900, 3, 3
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_MEMBER_BYTES = 128 * 1024 * 1024
MAX_LOCAL_FILE_BYTES = MAX_MEMBER_BYTES
HASH_CHUNK_BYTES = 1024 * 1024
MAX_MEMBERS = 100000
WINDOWS_MAX_PATH = 260
CFG = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
EXCL, KEEP, VENV = CFG["exclude"], CFG["keep"], CFG["venv"]
PIP_MIRRORS = [  # 国内优先，失败降级
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "https://pypi.org/simple/",
]
GH_API_CONCURRENCY = 3
_API_SEMAPHORE = threading.BoundedSemaphore(GH_API_CONCURRENCY)
_HEAD_CACHE: dict[tuple[str, str], str] = {}
_TREE_CACHE: dict[tuple[str, str], dict[str, dict]] = {}
_API_CACHE_LOCK = threading.Lock()


def _clear_api_cache() -> None:
    with _API_CACHE_LOCK:
        _HEAD_CACHE.clear()
        _TREE_CACHE.clear()


def _ensure_io_path(path: Path) -> Path:
    """在 Windows 非扩展路径达到 MAX_PATH 前明确失败，不依赖全局注册表设置。"""
    if os.name != "nt":
        return path
    text = os.fspath(path)
    if text.startswith("\\\\?\\"):
        return path
    absolute = os.path.abspath(text)
    units = len(absolute.encode("utf-16-le", "surrogatepass")) // 2
    if units >= WINDOWS_MAX_PATH:
        raise OSError(f"Windows MAX_PATH 路径过长（{units} >= {WINDOWS_MAX_PATH}）: {path}")
    return path


def find_gh():
    for c in (os.environ.get("GH", ""), r"C:\Users\贺新\AppData\Local\Programs\gh\bin\gh.exe",
              os.path.expanduser("~/.local/bin/gh"), "/usr/local/bin/gh"):
        if c and Path(c).is_file():
            return c
    return shutil.which("gh") or shutil.which("gh.exe")


GH = find_gh()


def run(cmd, timeout=60):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def _http_get(url, timeout=60):
    ctx = ssl.create_default_context()
    request = urllib.request.Request(url, headers={"User-Agent": "fasthtml-desktop-sync"})
    deadline = time.monotonic() + timeout
    for a in range(RETRIES):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            with urllib.request.urlopen(request, timeout=remaining, context=ctx) as response:
                headers = {key.lower(): value for key, value in response.headers.items()}
                declared = headers.get("content-length")
                if declared is not None:
                    try:
                        expected = int(declared)
                    except ValueError:
                        return None
                    if expected < 0 or expected > MAX_DOWNLOAD_BYTES:
                        return None
                chunks, total = [], 0
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return None
                    chunk = response.read(min(1024 * 1024, MAX_DOWNLOAD_BYTES + 1 - total))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        return None
                    chunks.append(chunk)
                if declared is not None and total != expected:
                    return None
                return b"".join(chunks)
        except Exception:
            if a < RETRIES - 1:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                time.sleep(min(RETRY_SLEEP, remaining))
    return None


def _gh_text(result) -> str:
    if result is None:
        return ""
    return (str(getattr(result, "stdout", "") or "") + "\n" +
            str(getattr(result, "stderr", "") or ""))


def _gh_http_status(result) -> int | None:
    match = re.search(r"\bHTTP\s+(\d{3})\b", _gh_text(result), re.IGNORECASE)
    return int(match.group(1)) if match else None


def _gh_rate_limited(result) -> bool:
    status = _gh_http_status(result)
    text = _gh_text(result).lower()
    return status == 429 or (status == 403 and
                             ("rate limit" in text or "abuse" in text or
                              re.search(r"x-ratelimit-remaining\s*:\s*0\b", text)))


def _gh_retryable(result) -> bool:
    if result is None:
        return True
    if result.returncode == 0:
        return True
    status = _gh_http_status(result)
    if status is not None:
        return _gh_rate_limited(result) or status in (408, 500, 502, 503, 504)
    text = _gh_text(result).lower()
    return any(word in text for word in ("timeout", "timed out", "connection", "network", "temporarily"))


def _gh_retry_delay(result) -> float:
    text = _gh_text(result)
    headers = {key.lower(): value.strip() for key, value in
               re.findall(r"(?im)^\s*([\w-]+)\s*:\s*([^\r\n]+)", text)}
    retry_after = headers.get("retry-after")
    if retry_after:
        try:
            return max(0, float(retry_after))
        except ValueError:
            try:
                date = parsedate_to_datetime(retry_after)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                return max(0, date.timestamp() - time.time())
            except (TypeError, ValueError, OverflowError):
                pass
    reset = headers.get("x-ratelimit-reset")
    if reset:
        try:
            return max(0, float(reset) - time.time())
        except ValueError:
            pass
    return RETRY_SLEEP


def _run_gh(args, timeout, deadline=None):
    deadline = time.monotonic() + timeout if deadline is None else deadline
    remaining = deadline - time.monotonic()
    if remaining <= 0 or not _API_SEMAPHORE.acquire(timeout=remaining):
        return None
    try:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        return run(args, timeout=remaining)
    finally:
        _API_SEMAPHORE.release()


def latest_head(repo, ref, timeout=60, retries=None):
    if not GH:
        return None
    key = (repo, ref)
    with _API_CACHE_LOCK:
        cached = _HEAD_CACHE.get(key)
    if cached is not None:
        return cached
    attempts = RETRIES if retries is None else retries
    deadline = time.monotonic() + timeout
    for attempt in range(attempts):
        try:
            result = _run_gh([GH, "api", f"repos/{repo}/commits/{ref}", "--jq", ".sha"], timeout, deadline)
        except (subprocess.SubprocessError, OSError):
            result = None
        if result is not None and result.returncode == 0:
            value = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
            if re.fullmatch(r"[0-9a-fA-F]{40}", value):
                with _API_CACHE_LOCK:
                    _HEAD_CACHE[key] = value
                return value
        if not _gh_retryable(result):
            return None
        if attempt < attempts - 1:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            time.sleep(min(_gh_retry_delay(result), remaining))
    return None


def _gh_api(path: str, timeout: int = 60, retries=None):
    if not GH:
        return None
    attempts = RETRIES if retries is None else retries
    deadline = time.monotonic() + timeout
    for attempt in range(attempts):
        try:
            result = _run_gh([GH, "api", path], timeout, deadline)
        except (subprocess.SubprocessError, OSError):
            result = None
        if result is not None and result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
        if not _gh_retryable(result):
            return None
        if attempt < attempts - 1:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            time.sleep(min(_gh_retry_delay(result), remaining))
    return None


def _safe_rel(rel: str) -> bool:
    if not isinstance(rel, str) or not rel or "\\" in rel or ":" in rel:
        return False
    parts = rel.split("/")
    reserved = {"con", "prn", "aux", "nul", "clock$"}
    reserved.update(f"com{i}" for i in range(1, 10))
    reserved.update(f"lpt{i}" for i in range(1, 10))
    reserved.update({"com¹", "com²", "com³", "lpt¹", "lpt²", "lpt³"})
    for part in parts:
        if part in ("", ".", "..") or part.endswith((".", " ")):
            return False
        if any(ord(char) < 32 or ord(char) == 127 for char in part):
            return False
        if part.split(".", 1)[0].casefold() in reserved:
            return False
    return True


def index_tree(repo: str, sha: str, timeout: int = 60, retries=None) -> dict[str, dict] | None:
    key = (repo, sha)
    with _API_CACHE_LOCK:
        cached = _TREE_CACHE.get(key)
    if cached is not None:
        return cached
    data = _gh_api(f"repos/{repo}/git/trees/{sha}?recursive=1", timeout=timeout, retries=retries)
    if not isinstance(data, dict) or data.get("truncated") or not isinstance(data.get("tree"), list):
        return None
    tree = {}
    for node in data["tree"]:
        if not isinstance(node, dict) or not _safe_rel(node.get("path")):
            return None
        path, kind = node["path"], node.get("type")
        if kind == "blob":
            blob, size = node.get("sha"), node.get("size", 0)
            if (not isinstance(blob, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", blob)
                    or not isinstance(size, int) or size < 0 or path in tree):
                return None
            tree[path] = {"sha": blob, "size": size}
        elif kind not in ("tree", "commit"):
            return None
    with _API_CACHE_LOCK:
        _TREE_CACHE[key] = tree
    return tree


def compare_changes(repo: str, old: str, new: str) -> list[dict] | None:
    data = _gh_api(f"repos/{repo}/compare/{old}...{new}")
    if not isinstance(data, dict) or not isinstance(data.get("files"), list):
        return None
    files = data["files"]
    allowed = {"added", "removed", "modified", "renamed", "copied", "changed", "unchanged"}
    if len(files) >= 300:
        return None
    changes = []
    for item in files:
        if not isinstance(item, dict):
            return None
        path, status = item.get("filename"), item.get("status")
        previous = item.get("previous_filename", "")
        if not _safe_rel(path) or status not in allowed:
            return None
        if status == "renamed" and not _safe_rel(previous):
            return None
        if previous and not _safe_rel(previous):
            return None
        changes.append({"path": path, "status": status, "previous_path": previous})
    return changes


def fetch_raw(repo: str, sha: str, path: str, expected_sha: str) -> bytes | None:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha) or not re.fullmatch(r"[0-9a-fA-F]{40}", expected_sha):
        return None
    encoded = quote(path, safe="/")
    urls = [f"https://raw.githubusercontent.com/{repo}/{sha}/{encoded}",
            f"https://ghfast.top/https://raw.githubusercontent.com/{repo}/{sha}/{encoded}"]
    for url in urls:
        data = _http_get(url, min(TIMEOUT, 180))
        if data is not None and _git_blob_sha(data) == expected_sha:
            return data
    return None


def _safe_stage_path(stage: Path, rel: str) -> Path | None:
    if not _safe_rel(rel):
        return None
    candidate = stage.joinpath(*rel.split("/"))
    _ensure_io_path(candidate)
    try:
        root = stage.resolve()
        resolved = candidate.resolve()
    except (OSError, RuntimeError):
        return None
    if resolved == root or not resolved.is_relative_to(root):
        return None
    return candidate


def _config_path(value, label: str) -> tuple[Path, Path]:
    if not _safe_rel(value):
        raise OSError(f"manifest {label} 必须是规范相对路径: {value!r}")
    candidate = SKILL_ROOT.joinpath(*value.split("/"))
    _ensure_io_path(candidate)
    try:
        root = SKILL_ROOT.resolve()
        resolved = candidate.resolve()
    except (OSError, RuntimeError) as error:
        raise OSError(f"无法解析 manifest {label}: {value!r}: {error}") from error
    if resolved == root or not resolved.is_relative_to(root):
        raise OSError(f"manifest {label} 越界或指向 SKILL_ROOT 本身: {value!r}")
    return candidate, resolved


def _reject_protected_path(resolved: Path, label: str, value) -> None:
    for name in ("scripts", "manifest.json", "SKILL.md", "README.md", "README.txt",
                 ".git", ".gitignore", "examples/README.md"):
        protected = (SKILL_ROOT / name).resolve()
        if _paths_overlap(resolved, protected):
            raise OSError(f"manifest {label} 不得指向或覆盖自研技能路径: {value!r}")


def _validate_source_path(src) -> Path:
    if not isinstance(src, dict):
        raise OSError("manifest source 必须是对象")
    candidate, resolved = _config_path(src.get("local_dir"), "local_dir")
    if candidate.is_symlink():
        raise OSError(f"manifest local_dir 不得为 symlink: {src.get('local_dir')!r}")
    _reject_protected_path(resolved, "local_dir", src.get("local_dir"))
    return candidate


def _validate_web_entry(wf, check_target: bool = False) -> Path:
    if not isinstance(wf, dict):
        raise OSError("manifest web_files 条目必须是对象")
    candidate, resolved = _config_path(wf.get("local_path"), "local_path")
    _reject_protected_path(resolved, "local_path", wf.get("local_path"))
    url = wf.get("url")
    if not isinstance(url, str) or not url or any(char.isspace() or ord(char) < 32 for char in url):
        raise OSError(f"manifest Web URL 无效: {url!r}")
    try:
        parsed = urlsplit(url)
    except ValueError as error:
        raise OSError(f"manifest Web URL 无效: {url!r}: {error}") from error
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise OSError(f"manifest Web URL 仅允许 http/https 且须包含主机: {url!r}")
    if check_target and candidate.is_symlink():
        raise OSError(f"Web 目标不得为 symlink，拒绝修复 referent: {candidate}")
    return candidate


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first.is_relative_to(second) or second.is_relative_to(first)


def _validate_venv(config, source_paths=(), web_paths=()) -> Path:
    venv = config.get("venv") if isinstance(config, dict) else None
    if not isinstance(venv, dict):
        raise OSError("manifest VENV 配置缺失")
    candidate, resolved = _config_path(venv.get("dir"), "VENV.dir")
    if candidate.is_symlink():
        raise OSError(f"manifest VENV.dir 不得为 symlink: {venv.get('dir')!r}")
    python = venv.get("python")
    if not isinstance(python, str) or not python:
        raise OSError("manifest VENV.python 必须是非空路径")
    protected = [SKILL_ROOT / name for name in
                 ("scripts", "manifest.json", "SKILL.md", "README.md", "README.txt")]
    protected.extend(source_paths)
    protected.extend(web_paths)
    for path in protected:
        try:
            other = path.resolve()
        except (OSError, RuntimeError) as error:
            raise OSError(f"无法验证 VENV 保护路径: {path}: {error}") from error
        if _paths_overlap(resolved, other):
            raise OSError(f"VENV.dir 不得指向或覆盖自研/源文件路径: {venv.get('dir')!r} 与 {path}")
    pyexe = candidate / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")
    _ensure_io_path(pyexe)
    if candidate.exists():
        if not candidate.is_dir():
            raise OSError(f"VENV.dir 不是目录: {candidate}")
        recognized = (candidate / "pyvenv.cfg").is_file() or pyexe.is_file()
        if not recognized and any(candidate.iterdir()):
            raise OSError(f"VENV.dir 是非空非 venv 目录，拒绝覆盖: {candidate}")
    return candidate


def _validate_venv_usage(config, sources) -> Path:
    source_paths = [_validate_source_path(src) for src in sources]
    web_files = config.get("web_files", []) if isinstance(config, dict) else []
    if not isinstance(web_files, list):
        raise OSError("manifest web_files 必须是列表")
    web_paths = [_validate_web_entry(wf) for wf in web_files]
    return _validate_venv(config, source_paths, web_paths)


def _validate_config(config) -> None:
    if not isinstance(config, dict) or not isinstance(config.get("sources"), list):
        raise OSError("manifest sources 必须是列表")
    web_files = config.get("web_files", [])
    if not isinstance(web_files, list):
        raise OSError("manifest web_files 必须是列表")
    source_paths = [_validate_source_path(src).resolve() for src in config["sources"]]
    web_paths = [_validate_web_entry(wf).resolve() for wf in web_files]
    for index, first in enumerate(source_paths):
        for second in source_paths[index + 1:]:
            if _paths_overlap(first, second):
                raise OSError(f"manifest 源路径重叠: {first} 与 {second}")
        for web_path in web_paths:
            if _paths_overlap(first, web_path):
                raise OSError(f"manifest Web 目标与源路径重叠: {web_path} 与 {first}")
    _validate_venv_usage(config, config["sources"])


def _tree_content_root(tree: dict[str, dict], nested: str) -> tuple[dict[str, dict], str]:
    if not nested or not tree:
        return tree, ""
    prefix = nested + "/"
    if not all(isinstance(rel, str) and rel.startswith(prefix) and _safe_rel(rel[len(prefix):])
               for rel in tree):
        return tree, ""
    return {rel[len(prefix):]: node for rel, node in tree.items()}, prefix


def _content_rel(rel: str, prefix: str) -> str:
    return rel[len(prefix):] if prefix and rel.startswith(prefix) else rel


def sync_incremental(repo: str, old: str, new: str, src: dict) -> tuple[Path, str] | tuple[None, None]:
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", old) or not re.fullmatch(r"[0-9a-fA-F]{40}", new):
        return None, None
    old_tree = index_tree(repo, old)
    new_tree = index_tree(repo, new)
    if old_tree is None or new_tree is None:
        return None, None
    content, nested = _project_content_dir(SKILL_ROOT / src["local_dir"])
    old_tree, prefix = _tree_content_root(old_tree, nested)
    new_tree, _ = _tree_content_root(new_tree, nested)
    if not _snapshot_matches(content, old_tree):
        return None, None
    changes = compare_changes(repo, old, new)
    if changes is None or len(changes) > 20:
        return None, None
    stage = None
    success = False
    try:
        Path(TEMP).mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix="fhd_inc_", dir=TEMP))
        for rel, node in old_tree.items():
            if _is_excluded(rel) or _is_kept(rel):
                continue
            target = _safe_stage_path(stage, rel)
            source = _safe_stage_path(content, rel)
            if target is None or source is None:
                raise OSError("不安全路径")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for change in changes:
            raw_rel, status = change["path"], change["status"]
            rel = _content_rel(raw_rel, prefix)
            raw_previous = change["previous_path"] if status == "renamed" else raw_rel
            previous = _content_rel(raw_previous, prefix)
            if status in ("removed", "renamed"):
                if not _is_excluded(previous):
                    target = _safe_stage_path(stage, previous)
                    if target is None:
                        raise OSError("不安全路径")
                    if target.is_dir():
                        shutil.rmtree(target)
                    elif target.exists():
                        target.unlink()
        for change in changes:
            raw_rel, status = change["path"], change["status"]
            rel = _content_rel(raw_rel, prefix)
            if status in ("removed", "unchanged", "not_modified") or _is_excluded(rel) or _is_kept(rel):
                continue
            node = new_tree.get(rel)
            target = _safe_stage_path(stage, rel)
            if node is None or target is None:
                raise OSError("变更元数据不完整")
            previous = _content_rel(change["previous_path"], prefix)
            data = None
            if status == "renamed" and old_tree.get(previous, {}).get("sha") == node["sha"]:
                source = _safe_stage_path(content, previous)
                if source is None:
                    raise OSError("不安全路径")
                data = source.read_bytes()
            if data is None:
                data = fetch_raw(repo, new, raw_rel, node["sha"])
            if data is None or _git_blob_sha(data) != node["sha"]:
                raise OSError("文件校验失败")
            if target.is_dir():
                shutil.rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if not _snapshot_matches(stage, new_tree):
            raise OSError("新快照校验失败")
        success = True
        return stage, "incremental"
    except OSError:
        return None, None
    finally:
        if stage is not None and not success:
            shutil.rmtree(stage, ignore_errors=True)


def _extract_tarball(tf: Path, stage: Path) -> Path | None:
    top = None
    count = declared_total = 0
    with tarfile.open(tf, mode="r:*", stream=True) as archive:
        for member in archive:
            count += 1
            if count > MAX_MEMBERS:
                raise OSError("归档成员数过多")
            if member.size < 0:
                raise OSError("非法归档大小")
            if member.size > MAX_MEMBER_BYTES:
                raise OSError("归档单文件过大")
            declared_total += member.size
            if declared_total > MAX_ARCHIVE_BYTES:
                raise OSError("归档总展开体积过大")
            if top is None:
                top = member.name.split("/", 1)[0]
                if not _safe_rel(top) or "/" in top:
                    return None
            if member.name != top and not member.name.startswith(top + "/"):
                raise OSError("归档顶层目录不一致")
            target = _safe_stage_path(stage, member.name)
            if target is None:
                raise OSError("不安全归档路径")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise OSError("归档文件不可读")
                written = 0
                with source, target.open("wb") as output:
                    while True:
                        chunk = source.read(min(HASH_CHUNK_BYTES, member.size - written + 1))
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > member.size or declared_total - member.size + written > MAX_ARCHIVE_BYTES:
                            raise OSError("归档实际展开体积过大")
                        output.write(chunk)
                if written != member.size:
                    raise OSError("归档文件大小不一致")
            elif member.issym():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(member.linkname.encode("utf-8", "surrogateescape"))
            else:
                raise OSError("不支持的归档类型")
    if top is None:
        return None
    root = _safe_stage_path(stage, top)
    return root if root is not None and root.is_dir() else None


def download_tarball(repo: str, sha: str, expected_tree: dict[str, dict] | None = None) -> tuple[Path, str] | tuple[None, None]:
    """按 commit SHA 下载；通道降级：codeload 直连 → ghfast 镜像。"""
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        return None, None
    slug = repo.split("/")[1]
    urls = [f"https://codeload.github.com/{repo}/tar.gz/{sha}",
            f"https://ghfast.top/https://github.com/{repo}/archive/{sha}.tar.gz"]
    try:
        Path(TEMP).mkdir(parents=True, exist_ok=True)
    except OSError:
        return None, None
    for url, ch in zip(urls, ("codeload", "ghfast")):
        data = _http_get(url, TIMEOUT)
        if data is None or len(data) > MAX_ARCHIVE_BYTES:
            continue
        stage = None
        success = False
        try:
            stage = Path(tempfile.mkdtemp(prefix=f"fhd_{slug}_", dir=TEMP))
            tf = stage / f"{slug}.tar.gz"
            tf.write_bytes(data)
            expanded = 0
            with gzip.open(tf, "rb") as compressed:
                while True:
                    chunk = compressed.read(HASH_CHUNK_BYTES)
                    if not chunk:
                        break
                    expanded += len(chunk)
                    if expanded > MAX_ARCHIVE_BYTES:
                        raise OSError("gzip 展开体积过大")
            root = _extract_tarball(tf, stage)
            if root is not None:
                content, nested = _project_content_dir(root, name=slug)
                tree, _ = _tree_content_root(expected_tree, nested) if expected_tree is not None else (None, "")
                if tree is not None and not _snapshot_matches(content, tree):
                    raise OSError("归档与目标 tree 不一致")
                tf.unlink()
                success = True
                return content, ch
        except (EOFError, OSError, tarfile.TarError, zlib.error):
            pass
        finally:
            if stage is not None and not success:
                shutil.rmtree(stage, ignore_errors=True)
    return None, None


def _is_excluded(rel: str, deep: bool = True) -> bool:
    patterns = list(EXCL["mandatory"]) + (EXCL.get("media", []) if deep else [])
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat):
            return True
        if pat.endswith("/"):
            prefix = pat
            if rel.startswith(prefix) or f"/{prefix}" in rel:
                return True
        elif "*" not in pat and "?" not in pat:
            if rel == pat or rel.startswith(pat + "/"):
                return True
    return False


def _is_kept(rel: str) -> bool:
    parts = Path(rel).parts
    return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(parts[-1], pat) or pat in parts
               for pat in KEEP)


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _git_file_blob_sha(path: Path) -> str:
    _ensure_io_path(path)
    size = path.stat().st_size
    if size < 0 or size > MAX_LOCAL_FILE_BYTES:
        raise OSError(f"本地文件过大: {path}")
    digest = hashlib.sha1(b"blob " + str(size).encode("ascii") + b"\0")
    total = 0
    with path.open("rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise OSError(f"本地内容不是普通文件: {path}")
        while True:
            chunk = source.read(HASH_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_LOCAL_FILE_BYTES:
                raise OSError(f"本地文件过大: {path}")
            digest.update(chunk)
    if total != size:
        raise OSError(f"本地文件读取时发生变化: {path}")
    return digest.hexdigest()


def _local_blobs(content: Path) -> dict[str, str]:
    local = {}
    if content.is_symlink():
        raise OSError(f"本地内容目录不得为 symlink: {content}")
    if content.exists():
        for p in content.rglob("*"):
            rel = p.relative_to(content).as_posix()
            if _is_excluded(rel) or _is_kept(rel):
                continue
            if p.is_symlink():
                local[rel] = "<invalid-non-regular>"
            elif p.is_file():
                local[rel] = _git_file_blob_sha(p)
            elif not p.is_dir():
                local[rel] = "<invalid-non-regular>"
    return local


def _blobs_match(local: dict[str, str], tree: dict[str, dict]) -> bool:
    expected = {rel: node["sha"] for rel, node in tree.items()
                if not _is_excluded(rel) and not _is_kept(rel)}
    return local == expected


def _snapshot_matches(content: Path, tree: dict[str, dict]) -> bool:
    try:
        return _blobs_match(_local_blobs(content), tree)
    except OSError:
        return False


def _fingerprint_blobs(local: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for rel, blob in sorted(local.items()):
        digest.update(rel.encode("utf-8", "surrogateescape") + b"\0")
        digest.update(blob.encode("ascii") + b"\0")
    return digest.hexdigest()


def _snapshot_fingerprint(content: Path, blobs: dict[str, str] | None = None) -> str:
    return _fingerprint_blobs(_local_blobs(content) if blobs is None else blobs)


def apply_exclude(stage: Path, deep: bool = True):
    """按 manifest.exclude 删无用产物。返回 (删除项数, 释放字节数)。"""
    removed, freed = 0, 0
    for p in list(stage.rglob("*")):
        rel = p.relative_to(stage).as_posix()
        if not _is_excluded(rel, deep=deep):
            continue
        if p.is_file():
            freed += p.stat().st_size
            p.unlink()
        else:
            shutil.rmtree(p, ignore_errors=True)
        removed += 1
    return removed, freed


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _read_manifest_source(example: Path) -> dict | None:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        raise OSError(f"无法读取 manifest 以恢复 {example}: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise OSError(f"manifest 格式无效，拒绝恢复: {MANIFEST}")
    target = example.resolve()
    for src in data["sources"]:
        if not isinstance(src, dict) or not _safe_rel(src.get("local_dir")):
            continue
        candidate = SKILL_ROOT / src["local_dir"]
        try:
            if candidate.resolve() == target:
                return src
        except OSError:
            continue
    return None


def _manifest_matches(src: dict | None, pin, snapshot) -> bool:
    if src is None:
        return False
    current_pin = str(src.get("pinned_sha") or "").lower()
    return current_pin == str(pin or "").lower() and src.get("snapshot_sha256") == snapshot


def _valid_recovery_name(value, prefix: str) -> bool:
    return (isinstance(value, str) and Path(value).name == value and value.startswith(prefix)
            and re.fullmatch(r"(?:[0-9a-f]{8}|[0-9a-f]{32})", value[len(prefix):]) is not None)


def _recovery_dir(path: Path, marker: Path, required: bool = False) -> bool:
    if path.is_symlink():
        raise OSError(f"恢复路径不得为 symlink，保留现场: {path} ({marker})")
    if path.exists():
        if not path.is_dir():
            raise OSError(f"恢复路径不是目录，保留现场: {path} ({marker})")
        return True
    if required:
        raise OSError(f"恢复目录缺失，保留现场: {path} ({marker})")
    return False


def _recovery_fingerprint(path: Path, marker: Path, label: str) -> str:
    try:
        return _snapshot_fingerprint(path)
    except OSError as error:
        raise OSError(f"无法验证{label}指纹，保留现场: {path} ({marker}): {error}") from error


def _recover_example(example: Path) -> bool:
    marker = example.with_name(f".{example.name}.sync-recovery.json")
    if marker.is_symlink():
        raise OSError(f"恢复标记不得为 symlink，保留现场: {marker}")
    if not marker.exists():
        orphans = list(example.parent.glob(f".{example.name}.sync-new-*"))
        for orphan in orphans:
            if not _valid_recovery_name(orphan.name, f".{example.name}.sync-new-"):
                raise OSError(f"无效孤立构建目录，保留现场: {orphan}")
            _recovery_dir(orphan, marker, required=True)
            _remove_path(orphan)
        return bool(orphans)
    try:
        state = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OSError(f"无法读取同步恢复标记，保留现场: {marker}: {error}") from error
    if not isinstance(state, dict) or state.get("version") != 1 or state.get("target") != example.name:
        raise OSError(f"无效同步恢复标记，保留现场: {marker}")
    if state.get("phase") not in ("replacing", "committed") or not isinstance(state.get("had_old"), bool):
        raise OSError(f"无效同步恢复状态，保留现场: {marker}")
    for key in ("old_pin", "new_pin"):
        value = state.get(key)
        if not isinstance(value, str) or (value and not re.fullmatch(r"[0-9a-fA-F]{7,40}", value)):
            raise OSError(f"无效同步恢复 pin，保留现场: {marker}")
    old_snapshot, new_snapshot = state.get("old_snapshot"), state.get("new_snapshot")
    if old_snapshot is not None and (not isinstance(old_snapshot, str) or
                                      not re.fullmatch(r"[0-9a-fA-F]{64}", old_snapshot)):
        raise OSError(f"无效同步恢复旧指纹，保留现场: {marker}")
    if not isinstance(new_snapshot, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", new_snapshot):
        raise OSError(f"无效同步恢复新指纹，保留现场: {marker}")
    nested = state.get("nested")
    if not isinstance(nested, str) or (nested and (not _safe_rel(nested) or "/" in nested)):
        raise OSError(f"无效同步恢复布局，保留现场: {marker}")
    backup_name, new_name = state.get("backup"), state.get("new")
    for value, prefix in ((backup_name, f".{example.name}.sync-backup-"),
                          (new_name, f".{example.name}.sync-new-")):
        if not _valid_recovery_name(value, prefix):
            raise OSError(f"无效同步恢复路径，保留现场: {marker}")
    backup, new = example.with_name(backup_name), example.with_name(new_name)
    backup_exists = _recovery_dir(backup, marker)
    new_exists = _recovery_dir(new, marker)
    if new_exists and _recovery_fingerprint(new / nested, marker, "构建目录") != new_snapshot:
        raise OSError(f"构建目录指纹不匹配，保留现场: {new} ({marker})")
    if not state["had_old"] and backup_exists:
        raise OSError(f"无旧快照却存在备份，保留现场: {backup} ({marker})")
    live_exists = _recovery_dir(example, marker)
    live_fingerprint = (_recovery_fingerprint(example / nested, marker, "live")
                        if live_exists else None)
    live_kind = ("missing" if not live_exists else
                 "new" if live_fingerprint == new_snapshot else
                 "old" if old_snapshot is not None and live_fingerprint == old_snapshot else
                 "unknown")
    current = _read_manifest_source(example)
    committed = _manifest_matches(current, state["new_pin"], new_snapshot)
    rolled_back = _manifest_matches(current, state["old_pin"], old_snapshot)
    if not committed and not rolled_back:
        raise OSError(f"manifest 状态与恢复标记不匹配，保留现场: {marker}")
    try:
        if committed:
            if live_kind != "new":
                raise OSError(f"已提交 live 目录缺失或指纹不匹配，保留现场: {example} ({marker})")
            _remove_path(backup)
            _remove_path(new)
        elif state["had_old"]:
            if live_kind == "old":
                if backup_exists:
                    raise OSError(f"live 与备份同时为旧快照，保留现场: {example} ({marker})")
                if new_exists:
                    _remove_path(new)
            elif live_kind in ("new", "missing"):
                if not backup_exists or old_snapshot is None:
                    raise OSError(f"无法确认旧备份，保留现场: {backup} ({marker})")
                if _recovery_fingerprint(backup / nested, marker, "旧备份") != old_snapshot:
                    raise OSError(f"旧备份指纹不匹配，保留现场: {backup} ({marker})")
                if live_exists:
                    _remove_path(example)
                backup.rename(example)
                if new_exists:
                    _remove_path(new)
            else:
                raise OSError(f"live 状态不明确，保留现场: {example} ({marker})")
        else:
            if live_kind not in ("new", "missing"):
                raise OSError(f"无旧快照但 live 状态不明确，保留现场: {example} ({marker})")
            if live_exists:
                _remove_path(example)
            if new_exists:
                _remove_path(new)
        marker.unlink()
    except OSError as error:
        if "保留现场" in str(error):
            raise
        raise OSError(f"恢复失败，事务状态保留在 {marker}: {error}") from error
    return True


def replace_example(stage: Path, example: Path, commit=None, old_pin=None, new_pin=None,
                    old_snapshot=None, new_snapshot=None) -> bool:
    """在完整临时目录中构建快照，保留 KEEP 文件；中断或失败可恢复。"""
    example.parent.mkdir(parents=True, exist_ok=True)
    had_old = example.exists()
    old_content, nested = _project_content_dir(example) if had_old else (example, "")
    stage_content, _ = _project_content_dir(stage, name=example.name)
    if had_old and old_snapshot is None:
        old_snapshot = _snapshot_fingerprint(old_content)
    if new_snapshot is None:
        new_snapshot = _snapshot_fingerprint(stage_content)
    token = uuid.uuid4().hex
    backup = example.with_name(f".{example.name}.sync-backup-{token}")
    new = example.with_name(f".{example.name}.sync-new-{token}")
    new.mkdir()
    marker = example.with_name(f".{example.name}.sync-recovery.json")
    state = {"version": 1, "target": example.name, "had_old": had_old,
             "backup": backup.name, "new": new.name, "phase": "replacing",
             "old_pin": old_pin or "", "new_pin": new_pin or "",
             "old_snapshot": old_snapshot, "new_snapshot": new_snapshot,
             "nested": nested}
    swapped = committed_marker = False
    try:
        content = new / nested if nested else new
        n = 0
        for p in stage_content.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(stage_content).as_posix()
            if _is_kept(rel):
                continue
            target = _safe_stage_path(content, rel)
            if target is None:
                raise OSError("不安全快照路径")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            n += 1
        if n == 0:
            raise OSError("空快照")
        if had_old:
            for p in example.rglob("*"):
                rel = p.relative_to(example).as_posix()
                if not _is_kept(rel):
                    continue
                target = new / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if p.is_symlink():
                    target.symlink_to(os.readlink(p))
                elif p.is_dir():
                    target.mkdir(exist_ok=True)
                elif p.is_file():
                    shutil.copy2(p, target)
        _atomic_write_bytes(marker, json.dumps(state, ensure_ascii=False).encode("utf-8"))
        if had_old:
            example.rename(backup)
        new.rename(example)
        swapped = True
        state["phase"] = "committed"
        _atomic_write_bytes(marker, json.dumps(state, ensure_ascii=False).encode("utf-8"))
        committed_marker = True
        if commit is not None:
            commit()
    except OSError:
        if marker.exists():
            if commit is not None:
                try:
                    _recover_example(example)
                except OSError as recovery_error:
                    raise OSError(f"恢复失败，事务状态保留在 {marker}: {recovery_error}") from recovery_error
                current = _read_manifest_source(example)
                return _manifest_matches(current, state["new_pin"], state["new_snapshot"])
            try:
                if had_old and backup.exists():
                    _remove_path(example)
                    backup.rename(example)
                elif not had_old and swapped:
                    _remove_path(example)
                _remove_path(new)
                marker.unlink()
            except OSError as recovery_error:
                raise OSError(f"恢复失败，事务状态保留在 {marker}: {recovery_error}") from recovery_error
        else:
            _remove_path(new)
        return False
    backup_cleaned = True
    try:
        _remove_path(backup)
    except OSError:
        backup_cleaned = False
    if backup_cleaned:
        try:
            marker.unlink()
        except OSError:
            pass
    return True


def is_incomplete(src) -> bool:
    """本地 example 缺失/无源码或偏离已记录快照指纹时视为需重建。"""
    t = _validate_source_path(src)
    if not t.exists() or not any(t.rglob("*")):
        return True
    content = _project_content_dir(t)[0]
    if not (any(content.rglob("*.py")) or (content / "README.md").exists()):
        return True
    expected = src.get("snapshot_sha256")
    return bool(expected and _snapshot_fingerprint(content) != expected)


def _clean_env():
    """去掉 PYTHONHOME/PYTHONPATH（本机常被灵犀 python-env 劫持，会导致 venv 建失败/SRE mismatch）。"""
    return {k: v for k, v in os.environ.items() if k not in ("PYTHONHOME", "PYTHONPATH")}


def _collect_all_deps(sources) -> list[str]:
    """收集所有 example 的依赖（requirements.txt + pyproject.toml），返回去重后的 pip 包名列表。"""
    import tomllib
    seen: dict[str, None] = {}
    for s in sources:
        ex = _validate_source_path(s)
        for d in [_project_content_dir(ex)[0]]:
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
    vdir = _validate_venv_usage(CFG, sources)
    env = _clean_env()
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


def _project_content_dir(ex: Path, name: str | None = None) -> tuple[Path, str]:
    child = ex / (name or ex.name)
    code_markers = ("web_app.py", "api_app.py", "main.py", "app.py", "server.py")
    markers = code_markers + ("README.md",)
    if (child != ex and child.is_dir() and not child.is_symlink()
            and not any((ex / marker).exists() for marker in code_markers)
            and any((child / marker).exists() for marker in markers)):
        return child, child.name
    return ex, ""


def _detect_entry(ex: Path) -> tuple[str, str, str]:
    """检测入口文件、运行模式、嵌套子目录。
    返回 (entry, mode, nested):
      entry: "web_app:app" (uvicorn 模式) 或 "web_app.py" (直接运行模式)
      mode:  "uvicorn" 或 "direct"
      nested: "" (无嵌套) 或子目录名（如 "FastERP"）
    """
    search_dir, nested = _project_content_dir(ex)

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
    # 默认按字母序分配（FastAccounts=5026, FastBI=5027, …）
    defaults = {"FastAccounts":"5026","FastBI":"5027","FastBot":"5028","FastCal":"5005",
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
        lines.append(f'set "PORT={port}"')
        if nested:
            lines.append(f'cd /d "%~dp0{nested}"')
        lines.append(
            f'start "" /min "%PY%" "%~dp0..\\..\\scripts\\open_when_ready.py" '
            f'"http://127.0.0.1:{port}" 90')
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



def _atomic_write_bytes(path: Path, data: bytes) -> None:
    _ensure_io_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def sync_web_files(check: bool = False, persist=None) -> bool | None:
    """同步 manifest.web_files；None 表示至少一个源失败。"""
    web_files = CFG.get("web_files", [])
    if not web_files:
        return False
    changed = False
    failed = False
    for wf in web_files:
        try:
            local_path, _ = _config_path(wf.get("local_path"), "local_path")
        except OSError as error:
            print(f"  [web] {wf.get('id', '?')}: 路径无效 ({error})")
            failed = True
            continue
        local_path = _validate_web_entry(wf, check_target=True)
        pinned = wf.get("pinned_sha", "")
        data = _http_get(wf["url"], timeout=60)
        if data is None:
            print(f"  [web] {wf['id']}: 下载失败")
            failed = True
            continue
        data_lf = data.replace(b"\r\n", b"\n")
        remote_sha = hashlib.sha256(data_lf).hexdigest()[:12]
        try:
            old_data = local_path.read_bytes() if local_path.is_file() else None
        except OSError as error:
            print(f"  [web] {wf['id']}: 本地读取失败 ({error})")
            failed = True
            continue
        local_sha = (hashlib.sha256(old_data.replace(b"\r\n", b"\n")).hexdigest()[:12]
                     if old_data is not None else None)
        local_ok = local_sha == remote_sha
        pin_changed = remote_sha != pinned
        if check:
            if not local_ok:
                status = "本地缺失或损坏"
                if pin_changed:
                    status += f"，上游有更新（{pinned} -> {remote_sha}）"
                failed = True
            else:
                status = "有更新" if pin_changed else "已是最新"
            print(f"[check] web:{wf['id']}: {status}")
            continue
        if not local_ok or pin_changed:
            written = False
            try:
                if not local_ok:
                    _atomic_write_bytes(local_path, data_lf)
                    written = True
                if pin_changed:
                    wf["pinned_sha"] = remote_sha
                    if persist is not None:
                        persist()
            except OSError as error:
                wf["pinned_sha"] = pinned
                if written:
                    try:
                        if old_data is None:
                            local_path.unlink(missing_ok=True)
                        else:
                            _atomic_write_bytes(local_path, old_data)
                    except OSError as recovery_error:
                        raise OSError(f"Web 恢复失败: {local_path}: {recovery_error}") from recovery_error
                print(f"  [web] {wf['id']}: 提交失败，已恢复 ({error})")
                failed = True
                continue
            changed = True
            action = "已修复本地" if not local_ok else "已更新 pin"
            detail = f"，上游 {pinned} -> {remote_sha}" if pin_changed else ""
            print(f"  [web] {wf['id']}: {action}{detail}")
        else:
            print(f"  [web] {wf['id']}: 已是最新")
    return None if failed else changed


def _cleanup_stage(stage: Path, channel: str) -> None:
    target = stage if channel == "incremental" else stage.parent
    shutil.rmtree(target, ignore_errors=True)


def _write_manifest() -> None:
    data = (json.dumps(CFG, ensure_ascii=False, indent=2) + "\n").encode("utf-8-sig")
    _atomic_write_bytes(MANIFEST, data)


def sync_example(src: dict, head: str, force: bool = False, persist=None) -> str:
    if not isinstance(head, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        return "failed"
    try:
        _validate_source_path(src)
        pinned = str(src.get("pinned_sha") or "")
        old_snapshot = src.get("snapshot_sha256")
        missing = is_incomplete(src)
    except OSError as error:
        print(f"  [{src.get('id', '?')}] 本地路径无效 ({error})")
        return "failed"
    legacy_tree = None
    if not force and not missing and not old_snapshot and pinned and head[:12] == pinned[:12]:
        legacy_tree = index_tree(src["repo"], head)
        if legacy_tree is None:
            return "failed"
        content, nested = _project_content_dir(SKILL_ROOT / src["local_dir"])
        check_tree, _ = _tree_content_root(legacy_tree, nested)
        local = _local_blobs(content)
        if _blobs_match(local, check_tree):
            src["snapshot_sha256"] = _fingerprint_blobs(local)
            try:
                if persist is not None:
                    persist()
            except OSError:
                src.pop("snapshot_sha256", None)
                return "failed"
            print(f"  [{src['id']}] 已补精确快照指纹（未下载内容）")
            return "unchanged"
        missing = True
    if not (force or missing or head[:12] != pinned[:12]):
        return "unchanged"
    stage = channel = None
    if not force and not missing and pinned:
        stage, channel = sync_incremental(src["repo"], pinned, head, src)
    if stage is None:
        tree = legacy_tree if legacy_tree is not None else index_tree(src["repo"], head)
        if tree is None:
            return "failed"
        stage, channel = download_tarball(src["repo"], head, expected_tree=tree)
    if stage is None:
        return "failed"
    try:
        removed, freed = apply_exclude(stage, deep=True)
        snapshot = _snapshot_fingerprint(stage)
        src["pinned_sha"] = head
        src["snapshot_sha256"] = snapshot
        example = SKILL_ROOT / src["local_dir"]
        transaction = {"old_pin": pinned, "new_pin": head,
                       "old_snapshot": old_snapshot, "new_snapshot": snapshot}
        replaced = (replace_example(stage, example, commit=persist, **transaction) if persist is not None
                    else replace_example(stage, example, **transaction))
        if not replaced:
            src["pinned_sha"] = pinned
            if old_snapshot is None:
                src.pop("snapshot_sha256", None)
            else:
                src["snapshot_sha256"] = old_snapshot
            return "failed"
    except OSError:
        src["pinned_sha"] = pinned
        if old_snapshot is None:
            src.pop("snapshot_sha256", None)
        else:
            src["snapshot_sha256"] = old_snapshot
        return "failed"
    finally:
        _cleanup_stage(stage, channel)
    print(f"  [{src['id']}] 已更新（{channel}）：清产物 {freed/1e6:.1f}MB/{removed} 项 → {src['local_dir']}")
    return "updated"


USAGE = """用法: python scripts/sync_upstream.py [选项]

  --ensure        使用技能前补齐缺失 / 不完整 + 追新 + 建 venv + 生成启动器
  --check         只检测（不写入）：缺失 / 上游新提交；Web 源下载校验，旧快照核对 tree
  --force <id>... 强制重拉指定 example（可多个 id，如 FastCRM FastVC）
  (无参数)        等同 --ensure 的完整同步
"""


@contextmanager
def _exclusive_sync_lock():
    lock_path = MANIFEST.with_name(MANIFEST.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        if lock.tell() == 0:
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _check_checkpoint(sources, reject_pending: bool = False):
    try:
        manifest_bytes = MANIFEST.read_bytes()
    except OSError as error:
        raise OSError(f"无法复核 manifest: {error}") from error
    markers = {}
    for src in sources:
        example = _validate_source_path(src)
        marker = example.with_name(f".{example.name}.sync-recovery.json")
        present = marker.exists() or marker.is_symlink()
        markers[marker] = present
        if reject_pending and present:
            raise OSError(f"有未完成事务，拒绝只读检查: {marker}")
    return manifest_bytes, markers


def _inspect_source(src):
    vid = src["id"]
    try:
        example = _validate_source_path(src)
        marker = example.with_name(f".{example.name}.sync-recovery.json")
        if marker.exists():
            return vid, "failed", "有未完成事务（需写模式恢复）"
        head = latest_head(src["repo"], src["ref"], timeout=30, retries=2)
        if head is None:
            return vid, "failed", "检测失败"
        pinned = (src.get("pinned_sha") or "")[:12]
        stale = head[:12] != pinned
        missing = is_incomplete(src)
        if not missing and not src.get("snapshot_sha256") and pinned and not stale:
            tree = index_tree(src["repo"], head, timeout=30, retries=2)
            if tree is None:
                return vid, "failed", "精确校验失败"
            content, nested = _project_content_dir(example)
            check_tree, _ = _tree_content_root(tree, nested)
            missing = not _snapshot_matches(content, check_tree)
        if missing:
            return vid, "failed", "需重建（缺失或不完整）"
        return vid, "unchanged", "有更新" if stale else "已是最新"
    except OSError as error:
        return vid, "failed", f"检测失败（{error}）"


def _execute_check(sources, force, stats) -> int:
    selected = [src for src in sources if not force or src["id"] in force]
    if selected:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(selected))) as pool:
            results = list(pool.map(_inspect_source, selected))
        for vid, status, message in results:
            print(f"[check] {vid}: {message}")
            stats[status].append(vid)
    try:
        web_changed = sync_web_files(check=True, persist=None)
    except OSError as error:
        print(f"  [web] 同步失败: {error}")
        stats["failed"].append("web")
        return 1
    if web_changed is None:
        stats["failed"].append("web")
    return 1 if stats["failed"] else 0


def _execute_sync(sources, check, force, stats) -> int:
    if check:
        return _execute_check(sources, force, stats)
    for src in sources:
        vid = src["id"]
        if force and vid not in force:
            continue
        head = latest_head(src["repo"], src["ref"])
        if head is None:
            print(f"  [{vid}] HEAD 检测失败")
            stats["failed"].append(vid)
            continue
        try:
            status = sync_example(src, head, force=vid in force, persist=_write_manifest)
        except OSError as error:
            print(f"  [{vid}] 同步失败 ({error})")
            status = "failed"
        stats[status].append(vid)
        if status == "failed":
            print(f"  [{vid}] 同步失败（未推进 pin）")
    try:
        web_changed = sync_web_files(check=False, persist=_write_manifest)
    except OSError as error:
        print(f"  [web] 同步失败: {error}")
        stats["failed"].append("web")
        return 1
    if web_changed is None:
        stats["failed"].append("web")
    ensure_venv(sources)
    gen_bats(sources)
    migrate_bats(sources)
    print("\n完成：" + "; ".join(f"{k}: {'、'.join(v) if v else '无'}" for k, v in stats.items()))
    return 1 if stats["failed"] else 0


def main() -> int:
    args = sys.argv[1:]
    if any(a in ("-h", "--help", "/?") for a in args):
        print(USAGE)
        return 0
    check = "--check" in args
    force = [a for a in args[args.index("--force") + 1:] if not a.startswith("--")] if "--force" in args else []
    sources = CFG.get("sources", []) if isinstance(CFG, dict) else []
    stats = {"updated": [], "unchanged": [], "failed": []}
    lock = _exclusive_sync_lock()
    try:
        lock.__enter__()
    except OSError as error:
        print(f"另一个同步进程正在运行: {error}")
        return 1
    try:
        try:
            _validate_config(CFG)
        except OSError as error:
            print(f"manifest 配置无效，已停止: {error}")
            return 1
        if check:
            try:
                before = _check_checkpoint(sources, reject_pending=True)
                result = _execute_sync(sources, True, force, stats)
                after = _check_checkpoint(sources)
            except OSError as error:
                print(f"只读检查状态复核失败: {error}")
                return 1
            if before != after:
                print("只读检查期间 manifest 或事务标记发生变化，结果作废")
                return 1
            return result
        try:
            for src in sources:
                _recover_example(_validate_source_path(src))
        except OSError as error:
            print(f"同步恢复失败，已停止: {error}")
            return 1
        return _execute_sync(sources, False, force, stats)
    finally:
        lock.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(main())
