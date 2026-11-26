from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
import io
import tarfile
import tempfile
import threading
import time
import unittest
import zlib
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "sync_upstream.py"
SPEC = importlib.util.spec_from_file_location("fasthtml_sync_upstream", SCRIPT)
sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync)


class DependencyCollectionTests(unittest.TestCase):
    def test_same_name_package_does_not_hide_root_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ex = root / "examples" / "Demo"
            (ex / "Demo").mkdir(parents=True)
            (ex / "Demo" / "__init__.py").write_text("", encoding="utf-8")
            (ex / "requirements.txt").write_text("requests==2.32.0\n", encoding="utf-8")
            old_root = sync.SKILL_ROOT
            sync.SKILL_ROOT = root
            try:
                deps = sync._collect_all_deps([{"id": "Demo", "local_dir": "examples/Demo"}])
            finally:
                sync.SKILL_ROOT = old_root

            self.assertIn("requests", deps)


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def write_transaction_marker(example, backup, new, phase, old_snapshot, new_snapshot,
                             old_pin="a" * 40, new_pin="b" * 40, nested="", had_old=True):
    marker = example.with_name(f".{example.name}.sync-recovery.json")
    marker.write_text(sync.json.dumps({
        "version": 1, "target": example.name, "had_old": had_old,
        "backup": backup.name, "new": new.name, "phase": phase,
        "old_pin": old_pin, "new_pin": new_pin,
        "old_snapshot": old_snapshot, "new_snapshot": new_snapshot,
        "nested": nested,
    }), encoding="utf-8")
    return marker


def write_manifest_source(root, example, pin, snapshot):
    manifest = root / "manifest.json"
    manifest.write_text(sync.json.dumps({"sources": [{
        "id": example.name, "repo": "owner/repo", "ref": "main",
        "local_dir": example.relative_to(root).as_posix(),
        "pinned_sha": pin, "snapshot_sha256": snapshot,
    }]}), encoding="utf-8")
    return manifest


def manifest_config(sources):
    return {"sources": sources, "web_files": [],
            "venv": {"dir": "examples/.venv", "python": "python"}}


class HttpBoundaryTests(unittest.TestCase):
    def test_content_length_over_limit_is_rejected_before_read(self):
        response = mock.MagicMock()
        response.headers = {"Content-Length": str(sync.MAX_DOWNLOAD_BYTES + 1)}
        response.__enter__.return_value = response
        response.read.return_value = b"unexpected"
        with (mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync.urllib.request, "urlopen", return_value=response)):
            self.assertIsNone(sync._http_get("https://example.test/large"))
        response.read.assert_not_called()

    def test_chunked_response_over_limit_is_rejected(self):
        response = mock.MagicMock()
        response.headers = {}
        response.__enter__.return_value = response
        response.read.side_effect = [b"123456", b"78901", b""]
        with (mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync, "MAX_DOWNLOAD_BYTES", 10),
              mock.patch.object(sync.urllib.request, "urlopen", return_value=response)):
            self.assertIsNone(sync._http_get("https://example.test/stream"))

    def test_content_length_mismatch_is_rejected(self):
        response = mock.MagicMock()
        response.headers = {"Content-Length": "5"}
        response.__enter__.return_value = response
        response.read.side_effect = [b"abc", b""]
        with (mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync.urllib.request, "urlopen", return_value=response)):
            self.assertIsNone(sync._http_get("https://example.test/short"))

    def test_stream_total_timeout_is_enforced_between_chunks(self):
        response = mock.MagicMock()
        response.headers = {}
        response.__enter__.return_value = response
        response.read.side_effect = [b"x", b""]
        with (mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync.time, "monotonic", side_effect=[0, 0, 0, 2]),
              mock.patch.object(sync.urllib.request, "urlopen", return_value=response)):
            self.assertIsNone(sync._http_get("https://example.test/slow", timeout=1))
        response.read.assert_called_once()


class RemoteMetadataTests(unittest.TestCase):
    def setUp(self):
        if hasattr(sync, "_clear_api_cache"):
            sync._clear_api_cache()

    def test_head_success_is_cached_by_repo_and_ref(self):
        result = mock.Mock(returncode=0, stdout="a" * 40 + "\n", stderr="")
        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync, "run", return_value=result) as run):
            self.assertEqual(sync.latest_head("owner/cache", "main"), "a" * 40)
            self.assertEqual(sync.latest_head("owner/cache", "main"), "a" * 40)
        run.assert_called_once()

    def test_tree_success_is_cached_by_repo_and_sha(self):
        data = {"truncated": False, "tree": [
            {"path": "app.py", "type": "blob", "sha": "a" * 40, "size": 3},
        ]}
        with mock.patch.object(sync, "_gh_api", return_value=data) as api:
            first = sync.index_tree("owner/tree-cache", "b" * 40)
            second = sync.index_tree("owner/tree-cache", "b" * 40)
        self.assertEqual(first, second)
        api.assert_called_once()

    def test_non_retryable_http_error_is_not_retried(self):
        result = mock.Mock(returncode=1, stdout="", stderr="gh: Not Found (HTTP 404)\n")
        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 3),
              mock.patch.object(sync, "run", return_value=result) as run,
              mock.patch.object(sync.time, "sleep") as sleep):
            self.assertIsNone(sync.latest_head("owner/missing", "main"))
        run.assert_called_once()
        sleep.assert_not_called()

    def test_rate_limit_uses_retry_after_header(self):
        limited = mock.Mock(returncode=1, stdout="",
                            stderr="gh: rate limit (HTTP 429)\nretry-after: 7\n")
        success = mock.Mock(returncode=0, stdout='{"ok": true}\n', stderr="")
        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 2),
              mock.patch.object(sync, "run", side_effect=[limited, success]) as run,
              mock.patch.object(sync.time, "sleep") as sleep):
            self.assertEqual(sync._gh_api("repos/owner/rate/contents"), {"ok": True})
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(7)

    def test_forbidden_rate_limit_uses_reset_header(self):
        limited = mock.Mock(returncode=1, stdout="",
                            stderr="gh: API rate limit exceeded (HTTP 403)\nx-ratelimit-reset: 1020\n")
        success = mock.Mock(returncode=0, stdout="a" * 40 + "\n", stderr="")
        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 2),
              mock.patch.object(sync, "run", side_effect=[limited, success]),
              mock.patch.object(sync.time, "time", return_value=1000),
              mock.patch.object(sync.time, "sleep") as sleep):
            self.assertEqual(sync.latest_head("owner/limited", "main"), "a" * 40)
        sleep.assert_called_once_with(20)

    def test_api_subprocesses_obey_concurrency_semaphore(self):
        active = 0
        maximum = 0
        guard = threading.Lock()

        def fake_run(*args, **kwargs):
            nonlocal active, maximum
            with guard:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.03)
            with guard:
                active -= 1
            return mock.Mock(returncode=0, stdout="a" * 40 + "\n", stderr="")

        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync, "_API_SEMAPHORE", threading.BoundedSemaphore(2), create=True),
              mock.patch.object(sync, "run", side_effect=fake_run),
              concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool):
            results = list(pool.map(lambda i: sync.latest_head("owner/concurrent", f"ref{i}"), range(3)))
        self.assertEqual(results, ["a" * 40] * 3)
        self.assertLessEqual(maximum, 2)

    def test_api_semaphore_wait_obeys_total_timeout(self):
        semaphore = mock.MagicMock()
        semaphore.acquire.return_value = False
        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync, "_API_SEMAPHORE", semaphore),
              mock.patch.object(sync, "run") as run):
            self.assertIsNone(sync.latest_head("owner/waiting", "main", timeout=1))
        semaphore.acquire.assert_called_once()
        run.assert_not_called()

    def test_head_timeout_and_invalid_sha_fail_safely(self):
        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync, "run", side_effect=sync.subprocess.TimeoutExpired("gh", 1))):
            self.assertIsNone(sync.latest_head("owner/repo", "main"))
        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync, "run", return_value=mock.Mock(returncode=0, stdout="not-a-sha\n"))):
            self.assertIsNone(sync.latest_head("owner/repo", "main"))

    def test_api_subprocess_oserror_returns_none(self):
        with (mock.patch.object(sync, "GH", "gh"),
              mock.patch.object(sync, "RETRIES", 1),
              mock.patch.object(sync, "run", side_effect=OSError("gh missing"))):
            self.assertIsNone(sync._gh_api("repos/owner/repo/git/trees/main"))

    def test_tree_records_preserve_blob_sha_and_reject_truncation(self):
        data = {"truncated": False, "tree": [
            {"path": "app.py", "type": "blob", "sha": "a" * 40, "size": 3},
            {"path": "pkg", "type": "tree", "sha": "b" * 40},
        ]}
        with mock.patch.object(sync, "_gh_api", return_value=data):
            self.assertEqual(sync.index_tree("owner/repo", "a" * 40),
                             {"app.py": {"sha": "a" * 40, "size": 3}})
        with mock.patch.object(sync, "_gh_api", return_value={"truncated": True}):
            self.assertIsNone(sync.index_tree("owner/repo", "c" * 40))


    def test_tree_rejects_malformed_or_unsafe_entries(self):
        invalid = [
            {"truncated": False, "tree": "not-a-list"},
            {"truncated": False, "tree": [{}]},
            {"truncated": False, "tree": [{"path": "../escape", "type": "blob", "sha": "a" * 40}]},
            {"truncated": False, "tree": [{"path": "app.py", "type": "blob", "sha": "short"}]},
        ]
        for data in invalid:
            with self.subTest(data=data), mock.patch.object(sync, "_gh_api", return_value=data):
                self.assertIsNone(sync.index_tree("owner/repo", "a" * 40))

    def test_compare_rejects_incomplete_file_list(self):
        data = {"files": [{"filename": "new.py", "status": "added"},
                          {"filename": "old.py", "previous_filename": "before.py", "status": "renamed"}]}
        with mock.patch.object(sync, "_gh_api", return_value=data):
            self.assertEqual(sync.compare_changes("owner/repo", "a" * 40, "b" * 40), [
                {"path": "new.py", "status": "added", "previous_path": ""},
                {"path": "old.py", "status": "renamed", "previous_path": "before.py"},
            ])
        with mock.patch.object(sync, "_gh_api", return_value={"files": [{}] * 300}):
            self.assertIsNone(sync.compare_changes("owner/repo", "a" * 40, "b" * 40))

    def test_compare_rejects_unknown_status_and_incomplete_rename(self):
        for item in ({"filename": "app.py", "status": "invented"},
                     {"filename": "new.py", "status": "renamed"}):
            with self.subTest(item=item), mock.patch.object(sync, "_gh_api", return_value={"files": [item]}):
                self.assertIsNone(sync.compare_changes("owner/repo", "a" * 40, "b" * 40))


class TarballTests(unittest.TestCase):
    def test_tarball_url_is_pinned_to_commit_sha(self):
        payload = b"print('ok')\n"
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            info = tarfile.TarInfo("Demo-sha/app.py")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (mock.patch.object(sync, "TEMP", root),
                  mock.patch.object(sync, "_http_get", return_value=buffer.getvalue()) as get):
                stage, channel = sync.download_tarball("owner/repo", "b" * 40)
            self.assertIsNotNone(stage)
            self.assertEqual(channel, "codeload")
            self.assertEqual((stage / "app.py").read_bytes(), payload)
            self.assertEqual(get.call_args_list[0].args[0],
                             f"https://codeload.github.com/owner/repo/tar.gz/{'b' * 40}")

    def test_tarball_wrapper_is_stripped_before_tree_validation(self):
        payload = b"print('ok')\n"
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            info = tarfile.TarInfo("Demo-sha/Demo/app.py")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        expected = {"Demo/app.py": {"sha": blob_sha(payload), "size": len(payload)}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (mock.patch.object(sync, "TEMP", root),
                  mock.patch.object(sync, "_http_get", return_value=buffer.getvalue())):
                stage, channel = sync.download_tarball("owner/Demo", "b" * 40, expected_tree=expected)
            self.assertIsNotNone(stage)
            self.assertEqual(channel, "codeload")
            self.assertEqual((stage / "app.py").read_bytes(), payload)
            self.assertFalse((stage / "Demo" / "app.py").exists())

    def test_truncated_gzip_trailer_is_rejected(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            for name in ("Demo-sha/a.txt", "Demo-sha/b.txt"):
                info = tarfile.TarInfo(name)
                info.size = 1
                archive.addfile(info, io.BytesIO(b"x"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (mock.patch.object(sync, "TEMP", root),
                  mock.patch.object(sync, "_http_get", return_value=buffer.getvalue()[:-8]) as get):
                self.assertEqual(sync.download_tarball("owner/repo", "b" * 40), (None, None))
            self.assertEqual(get.call_count, 2)
            self.assertEqual(list(root.iterdir()), [])

    def test_symlink_is_materialized_as_link_target_text(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            info = tarfile.TarInfo("Demo-sha/target.txt")
            info.size = 6
            archive.addfile(info, io.BytesIO(b"target"))
            link = tarfile.TarInfo("Demo-sha/link.txt")
            link.type = tarfile.SYMTYPE
            link.linkname = "target.txt"
            archive.addfile(link)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (mock.patch.object(sync, "TEMP", root),
                  mock.patch.object(sync, "_http_get", return_value=buffer.getvalue())):
                stage, channel = sync.download_tarball("owner/repo", "b" * 40)
            self.assertIsNotNone(stage)
            self.assertEqual(channel, "codeload")
            self.assertFalse((stage / "link.txt").is_symlink())
            self.assertEqual((stage / "link.txt").read_bytes(), b"target.txt")

    def test_tarball_rejects_negative_member_size_before_extraction(self):
        info = tarfile.TarInfo("Demo-sha/bad.bin")
        info.size = -1
        archive = mock.MagicMock()
        archive.__enter__.return_value.__iter__.return_value = iter([info])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            with mock.patch.object(sync.tarfile, "open", return_value=archive):
                with self.assertRaisesRegex(OSError, "非法归档大小"):
                    sync._extract_tarball(root / "unused.tar.gz", stage)

    def test_tarball_rejects_oversized_member_before_extraction(self):
        info = tarfile.TarInfo("Demo-sha/huge.bin")
        info.size = 128 * 1024 * 1024 + 1
        archive = mock.MagicMock()
        archive.__enter__.return_value.__iter__.return_value = iter([info])
        archive.__enter__.return_value.extractfile.return_value = None
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            with mock.patch.object(sync.tarfile, "open", return_value=archive):
                with self.assertRaisesRegex(OSError, "单文件过大"):
                    sync._extract_tarball(root / "unused.tar.gz", stage)

    def test_tarball_rejects_excessive_total_expanded_size(self):
        members = []
        for i in range(5):
            info = tarfile.TarInfo(f"Demo-sha/part{i}.bin")
            info.type = tarfile.DIRTYPE
            info.size = 120 * 1024 * 1024
            members.append(info)
        archive = mock.MagicMock()
        archive.__enter__.return_value.__iter__.return_value = iter(members)
        archive.__enter__.return_value.extractfile.return_value = None
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            with mock.patch.object(sync.tarfile, "open", return_value=archive):
                with self.assertRaisesRegex(OSError, "总展开体积过大"):
                    sync._extract_tarball(root / "unused.tar.gz", stage)

    def test_tarball_iterates_members_and_stops_at_count_limit(self):
        members = []
        for name in ("Demo-sha/one", "Demo-sha/two", "Demo-sha/three"):
            info = tarfile.TarInfo(name)
            info.type = tarfile.DIRTYPE
            members.append(info)
        archive = mock.MagicMock()
        archive.__enter__.return_value.__iter__.return_value = iter(members)
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / "stage"
            stage.mkdir()
            with (mock.patch.object(sync.tarfile, "open", return_value=archive),
                  mock.patch.object(sync, "MAX_MEMBERS", 2)):
                with self.assertRaisesRegex(OSError, "成员数过多"):
                    sync._extract_tarball(Path(tmp) / "unused.tar.gz", stage)
            archive.__enter__.return_value.getmembers.assert_not_called()
            archive.__enter__.return_value.extractfile.assert_not_called()

    def test_zlib_error_cleans_every_download_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (mock.patch.object(sync, "TEMP", root),
                  mock.patch.object(sync, "_http_get", return_value=b"broken"),
                  mock.patch.object(sync.gzip, "open", side_effect=zlib.error("bad gzip"))):
                self.assertEqual(sync.download_tarball("owner/repo", "b" * 40), (None, None))
            self.assertEqual(list(root.iterdir()), [])

    def test_tarball_mkdtemp_failure_is_reported_per_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            with (mock.patch.object(sync, "TEMP", Path(tmp)),
                  mock.patch.object(sync, "_http_get", return_value=b"archive"),
                  mock.patch.object(sync.tempfile, "mkdtemp", side_effect=OSError("no temp space"))):
                self.assertEqual(sync.download_tarball("owner/repo", "b" * 40), (None, None))

    def test_tarball_missing_expected_file_is_rejected(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            info = tarfile.TarInfo("Demo-sha/app.py")
            info.size = 4
            archive.addfile(info, io.BytesIO(b"app\n"))
        expected = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4},
                    "missing.py": {"sha": blob_sha(b"missing\n"), "size": 8}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (mock.patch.object(sync, "TEMP", root),
                  mock.patch.object(sync, "_http_get", return_value=buffer.getvalue())):
                self.assertEqual(sync.download_tarball("owner/repo", "b" * 40, expected_tree=expected),
                                 (None, None))
            self.assertEqual(list(root.iterdir()), [])


class RawDownloadTests(unittest.TestCase):
    def test_download_uses_pinned_commit_and_matching_blob(self):
        data = b"print('ok')\n"
        with mock.patch.object(sync, "_http_get", return_value=data) as get:
            self.assertEqual(sync.fetch_raw("owner/repo", "b" * 40, "src/app.py", blob_sha(data)), data)
        self.assertIn("/" + "b" * 40 + "/", get.call_args_list[0].args[0])

    def test_download_rejects_same_size_blob_tamper(self):
        with mock.patch.object(sync, "_http_get", return_value=b"bad\n") as get:
            self.assertIsNone(sync.fetch_raw("owner/repo", "b" * 40, "app.py", blob_sha(b"good\n")))
        self.assertEqual(get.call_count, 2)


class SnapshotBaselineTests(unittest.TestCase):
    def test_same_count_tamper_and_unignored_extra_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp)
            (content / "app.py").write_bytes(b"new\n")
            (content / "docs").mkdir()
            (content / "docs" / "guide.pdf").write_bytes(b"excluded")
            tree = {"app.py": {"sha": blob_sha(b"old\n"), "size": 4}}

            self.assertFalse(sync._snapshot_matches(content, tree))
            (content / "app.py").write_bytes(b"old\n")
            (content / "runtime.db").write_bytes(b"runtime")
            self.assertFalse(sync._snapshot_matches(content, tree))

    def test_exact_core_files_match_while_excluded_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp)
            (content / "app.py").write_bytes(b"app\n")
            (content / "docs").mkdir()
            (content / "docs" / "guide.pdf").write_bytes(b"excluded")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4}}

            self.assertTrue(sync._snapshot_matches(content, tree))

    def test_remote_keep_files_are_ignored_on_both_sides(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp)
            (content / "app.py").write_bytes(b"app\n")
            (content / "启动-Demo.bat").write_bytes(b"local")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4},
                    "启动-Demo.bat": {"sha": blob_sha(b"remote"), "size": 6}}

            self.assertTrue(sync._snapshot_matches(content, tree))


    def test_non_kept_symlink_is_a_mismatch_and_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp) / "content"
            content.mkdir()
            link = content / "link.py"
            link.write_bytes(b"app\n")
            tree = {"link.py": {"sha": blob_sha(b"app\n"), "size": 4}}
            real_is_symlink = Path.is_symlink

            def fake_is_symlink(path):
                return path == link or real_is_symlink(path)

            with (mock.patch.object(Path, "is_symlink", autospec=True, side_effect=fake_is_symlink),
                  mock.patch.object(Path, "read_bytes", side_effect=AssertionError("symlink followed"))):
                self.assertFalse(sync._snapshot_matches(content, tree))

    def test_local_blob_hashing_is_chunked_not_read_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp)
            (content / "app.py").write_bytes(b"app\n")
            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("whole-file read")):
                self.assertEqual(sync._local_blobs(content), {"app.py": blob_sha(b"app\n")})

    def test_local_blob_hashing_rejects_files_over_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp)
            (content / "large.bin").write_bytes(b"1234")
            with mock.patch.object(sync, "MAX_LOCAL_FILE_BYTES", 3):
                with self.assertRaisesRegex(OSError, "文件过大"):
                    sync._local_blobs(content)


class WebSyncTests(unittest.TestCase):
    def test_web_atomic_replace_failure_keeps_old_file_and_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "ctx.txt"
            target.write_bytes(b"old\n")
            old_sha = hashlib.sha256(b"old\n").hexdigest()[:12]
            wf = {"id": "ctx", "url": "https://example.test/ctx", "local_path": "ctx.txt",
                  "pinned_sha": old_sha}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", {"web_files": [wf]}),
                  mock.patch.object(sync, "_http_get", return_value=b"new\r\n"),
                  mock.patch.object(sync.os, "replace", side_effect=OSError("replace failed"))):
                self.assertIsNone(sync.sync_web_files())
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual(wf["pinned_sha"], old_sha)
            self.assertEqual(list(root.glob("ctx.txt.*.tmp")), [])

    def test_web_manifest_failure_restores_old_file_and_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "ctx.txt"
            target.write_bytes(b"old\n")
            old_sha = hashlib.sha256(b"old\n").hexdigest()[:12]
            wf = {"id": "ctx", "url": "https://example.test/ctx", "local_path": "ctx.txt",
                  "pinned_sha": old_sha}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", {"web_files": [wf]}),
                  mock.patch.object(sync, "_http_get", return_value=b"new\r\n"),
                  mock.patch.object(sync, "_write_manifest", side_effect=OSError("disk full"))):
                self.assertIsNone(sync.sync_web_files(persist=sync._write_manifest))
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual(wf["pinned_sha"], old_sha)

    def test_web_sync_reports_manifest_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wf = {"id": "ctx", "url": "https://example.test/ctx", "local_path": "ctx.txt",
                  "pinned_sha": "0" * 12}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", {"web_files": [wf]}),
                  mock.patch.object(sync, "_http_get", return_value=b"line\r\n") as get):
                self.assertTrue(sync.sync_web_files())
            get.assert_called_once_with(wf["url"], timeout=60)
            self.assertEqual((root / "ctx.txt").read_bytes(), b"line\n")
            self.assertEqual(wf["pinned_sha"], hashlib.sha256(b"line\n").hexdigest()[:12])

    def test_web_check_reports_local_damage_when_remote_pin_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ctx.txt").write_bytes(b"tampered\n")
            pin = hashlib.sha256(b"good\n").hexdigest()[:12]
            wf = {"id": "ctx", "url": "https://example.test/ctx", "local_path": "ctx.txt",
                  "pinned_sha": pin}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", {"web_files": [wf]}),
                  mock.patch.object(sync, "_http_get", return_value=b"good\n")):
                self.assertIsNone(sync.sync_web_files(check=True))
            self.assertEqual((root / "ctx.txt").read_bytes(), b"tampered\n")
            self.assertEqual(wf["pinned_sha"], pin)

    def test_web_repairs_missing_local_file_without_rewriting_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pin = hashlib.sha256(b"good\n").hexdigest()[:12]
            wf = {"id": "ctx", "url": "https://example.test/ctx", "local_path": "ctx.txt",
                  "pinned_sha": pin}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", {"web_files": [wf]}),
                  mock.patch.object(sync, "_http_get", return_value=b"good\n"),
                  mock.patch.object(sync, "_write_manifest") as write):
                self.assertTrue(sync.sync_web_files(persist=sync._write_manifest))
            self.assertEqual((root / "ctx.txt").read_bytes(), b"good\n")
            self.assertEqual(wf["pinned_sha"], pin)
            write.assert_not_called()


class MainFlowTests(unittest.TestCase):
    def test_write_mode_recovers_interrupted_snapshot_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            backup = root / "examples" / ".Demo.sync-backup-deadbeef"
            new = root / "examples" / ".Demo.sync-new-deadbeef"
            backup.mkdir(parents=True)
            (backup / "app.py").write_bytes(b"old\n")
            new.mkdir()
            (new / "app.py").write_bytes(b"new\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            new_snapshot = sync._snapshot_fingerprint(new)
            marker = write_transaction_marker(example, backup, new, "replacing",
                                              old_snapshot, new_snapshot)
            sources = [{"id": "Demo", "repo": "owner/repo", "ref": "main",
                        "local_dir": "examples/Demo", "pinned_sha": "a" * 40,
                        "snapshot_sha256": old_snapshot}]
            manifest = write_manifest_source(root, example, "a" * 40, old_snapshot)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(sync, "CFG", manifest_config(sources)),
                  mock.patch.object(sync.sys, "argv", ["sync_upstream.py"]),
                  mock.patch.object(sync, "latest_head", return_value="a" * 40) as latest,
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "sync_example", return_value="unchanged"),
                  mock.patch.object(sync, "sync_web_files", return_value=False),
                  mock.patch.object(sync, "ensure_venv"),
                  mock.patch.object(sync, "gen_bats"),
                  mock.patch.object(sync, "migrate_bats")):
                self.assertEqual(sync.main(), 0)
            self.assertEqual((example / "app.py").read_bytes(), b"old\n")
            self.assertFalse(marker.exists())
            latest.assert_called_once()

    def test_recovery_failure_stops_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", root / "manifest.json"),
                  mock.patch.object(sync, "CFG", manifest_config([
                      {"id": "Demo", "repo": "owner/repo", "ref": "main", "local_dir": "examples/Demo"}])),
                  mock.patch.object(sync.sys, "argv", ["sync_upstream.py"]),
                  mock.patch.object(sync, "_recover_example", side_effect=OSError("recovery failed")),
                  mock.patch.object(sync, "latest_head") as latest):
                self.assertEqual(sync.main(), 1)
            latest.assert_not_called()

    def test_write_mode_stops_before_network_when_lock_is_busy(self):
        lock = mock.MagicMock()
        lock.__enter__.side_effect = OSError("busy")
        with (tempfile.TemporaryDirectory() as tmp,
              mock.patch.object(sync, "MANIFEST", Path(tmp) / "manifest.json"),
              mock.patch.object(sync, "CFG", manifest_config([
                      {"id": "One", "repo": "owner/one", "ref": "main", "local_dir": "examples/One"}])),
              mock.patch.object(sync.sys, "argv", ["sync_upstream.py"]),
              mock.patch.object(sync, "_exclusive_sync_lock", return_value=lock),
              mock.patch.object(sync, "latest_head") as latest):
            self.assertEqual(sync.main(), 1)
        latest.assert_not_called()

    def test_check_mode_stops_before_network_when_lock_is_busy(self):
        lock = mock.MagicMock()
        lock.__enter__.side_effect = OSError("busy")
        with (tempfile.TemporaryDirectory() as tmp,
              mock.patch.object(sync, "MANIFEST", Path(tmp) / "manifest.json"),
              mock.patch.object(sync, "CFG", manifest_config([
                      {"id": "One", "repo": "owner/one", "ref": "main", "local_dir": "examples/One"}])),
              mock.patch.object(sync.sys, "argv", ["sync_upstream.py", "--check"]),
              mock.patch.object(sync, "_exclusive_sync_lock", return_value=lock),
              mock.patch.object(sync, "_execute_check") as check,
              mock.patch.object(sync, "latest_head") as latest):
            self.assertEqual(sync.main(), 1)
        lock.__enter__.assert_called_once_with()
        check.assert_not_called()
        latest.assert_not_called()

    def test_check_rejects_pending_transaction_before_any_source_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = [{"id": name, "repo": f"owner/{name.lower()}", "ref": "main",
                        "local_dir": f"examples/{name}", "pinned_sha": "a" * 40}
                       for name in ("One", "Two")]
            for src in sources:
                (root / src["local_dir"]).mkdir(parents=True)
            marker = root / "examples" / ".Two.sync-recovery.json"
            marker.write_text("interrupted", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(sync.json.dumps({"sources": sources}), encoding="utf-8")
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(sync, "CFG", manifest_config(sources)),
                  mock.patch.object(sync.sys, "argv", ["sync_upstream.py", "--check"]),
                  mock.patch.object(sync, "latest_head") as latest,
                  mock.patch.object(sync.sys, "stdout", new_callable=io.StringIO)):
                self.assertEqual(sync.main(), 1)
            latest.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"), "interrupted")

    def test_check_detects_transaction_marker_created_during_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            sources = [{"id": "Demo", "repo": "owner/repo", "ref": "main",
                        "local_dir": "examples/Demo", "pinned_sha": "a" * 40}]
            manifest = root / "manifest.json"
            manifest.write_text(sync.json.dumps({"sources": sources}), encoding="utf-8")
            marker = example.with_name(".Demo.sync-recovery.json")

            def create_marker(sources, force, stats):
                marker.write_text("interrupted", encoding="utf-8")
                return 0

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(sync, "CFG", manifest_config(sources)),
                  mock.patch.object(sync.sys, "argv", ["sync_upstream.py", "--check"]),
                  mock.patch.object(sync, "_execute_check", side_effect=create_marker),
                  mock.patch.object(sync, "_recover_example") as recover,
                  mock.patch.object(sync, "_write_manifest") as write,
                  mock.patch.object(sync.sys, "stdout", new_callable=io.StringIO)):
                self.assertEqual(sync.main(), 1)
            recover.assert_not_called()
            write.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"), "interrupted")

    def test_check_detects_manifest_change_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = [{"id": "Demo", "repo": "owner/repo", "ref": "main",
                        "local_dir": "examples/Demo", "pinned_sha": "a" * 40}]
            manifest = root / "manifest.json"
            original = sync.json.dumps({"sources": sources}).encode("utf-8")
            manifest.write_bytes(original)
            changed = sync.json.dumps({"sources": sources, "changed": True}).encode("utf-8")

            def change_manifest(sources, force, stats):
                manifest.write_bytes(changed)
                return 0

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(sync, "CFG", manifest_config(sources)),
                  mock.patch.object(sync.sys, "argv", ["sync_upstream.py", "--check"]),
                  mock.patch.object(sync, "_execute_check", side_effect=change_manifest),
                  mock.patch.object(sync, "_write_manifest") as write,
                  mock.patch.object(sync.sys, "stdout", new_callable=io.StringIO)):
                self.assertEqual(sync.main(), 1)
            write.assert_not_called()
            self.assertEqual(manifest.read_bytes(), changed)

    def test_check_acquires_and_releases_lock_without_recovery_or_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = [{"id": "Demo", "repo": "owner/repo", "ref": "main",
                        "local_dir": "examples/Demo", "pinned_sha": "a" * 40}]
            manifest = root / "manifest.json"
            original = sync.json.dumps({"sources": sources}).encode("utf-8")
            manifest.write_bytes(original)
            lock = mock.MagicMock()
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(sync, "CFG", manifest_config(sources)),
                  mock.patch.object(sync.sys, "argv", ["sync_upstream.py", "--check"]),
                  mock.patch.object(sync, "_exclusive_sync_lock", return_value=lock),
                  mock.patch.object(sync, "_execute_check", return_value=0),
                  mock.patch.object(sync, "_recover_example") as recover,
                  mock.patch.object(sync, "_write_manifest") as write,
                  mock.patch.object(sync.sys, "stdout", new_callable=io.StringIO)):
                self.assertEqual(sync.main(), 0)
            lock.__enter__.assert_called_once_with()
            lock.__exit__.assert_called_once_with(None, None, None)
            recover.assert_not_called()
            write.assert_not_called()
            self.assertEqual(manifest.read_bytes(), original)

    def test_main_persists_after_each_successful_source(self):
        sources = [
            {"id": "One", "repo": "owner/one", "ref": "main", "local_dir": "examples/One", "pinned_sha": "a" * 40},
            {"id": "Two", "repo": "owner/two", "ref": "main", "local_dir": "examples/Two", "pinned_sha": "c" * 40},
        ]
        def fake_sync(src_cfg, detected_head=None, force=False, persist=None):
            if src_cfg["id"] == "One" and persist is not None:
                persist()
                return "updated"
            return "unchanged"

        with (tempfile.TemporaryDirectory() as tmp,
              mock.patch.object(sync, "MANIFEST", Path(tmp) / "manifest.json"),
              mock.patch.object(sync, "CFG", manifest_config(sources)),
              mock.patch.object(sync.sys, "argv", ["sync_upstream.py"]),
              mock.patch.object(sync, "latest_head", side_effect=["b" * 40, "c" * 40]),
              mock.patch.object(sync, "sync_example", side_effect=fake_sync) as sync_one,
              mock.patch.object(sync, "_write_manifest") as write,
              mock.patch.object(sync, "sync_web_files", return_value=False) as web,
              mock.patch.object(sync, "ensure_venv"),
              mock.patch.object(sync, "gen_bats"),
              mock.patch.object(sync, "migrate_bats")):
            self.assertEqual(sync.main(), 0)
        self.assertEqual(sync_one.call_count, 2)
        write.assert_called_once_with()
        web.assert_called_once_with(check=False, persist=write)


class ManifestTests(unittest.TestCase):
    def test_manifest_is_written_with_bom_and_atomic_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text("old", encoding="utf-8")
            with (mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(sync, "CFG", {"sources": [], "label": "中文"}),
                  mock.patch.object(sync.os, "replace", wraps=sync.os.replace) as replace):
                sync._write_manifest()
            self.assertEqual(replace.call_count, 1)
            self.assertTrue(manifest.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(sync.json.loads(manifest.read_text(encoding="utf-8-sig")),
                             {"sources": [], "label": "中文"})
            self.assertEqual(list(root.iterdir()), [manifest])


class ManifestValidationTests(unittest.TestCase):
    def config(self, local_dir="examples/Demo", web_path="references/ctx.txt",
               venv_dir="examples/.venv", url="https://example.test/ctx"):
        return {
            "venv": {"dir": venv_dir, "python": "python"},
            "sources": [{"id": "Demo", "repo": "owner/repo", "ref": "main",
                         "local_dir": local_dir, "pinned_sha": "a" * 40}],
            "web_files": [{"id": "ctx", "url": url, "local_path": web_path,
                           "pinned_sha": "0" * 12}],
        }

    def test_valid_relative_paths_and_http_urls_are_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "examples" / ".venv").mkdir(parents=True)
            (root / "examples" / ".venv" / "pyvenv.cfg").write_text("home = python", encoding="utf-8")
            with mock.patch.object(sync, "SKILL_ROOT", root):
                self.assertIsNone(sync._validate_config(self.config()))
                self.assertIsNone(sync._validate_config(self.config(url="http://example.test/ctx")))

    def test_source_local_dir_must_be_canonical_relative_path(self):
        invalid = ["../outside", "/absolute", "C:/outside", "a\\b", "examples/../Demo",
                   "examples//Demo", "examples/Demo/", "", "."]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sync, "SKILL_ROOT", Path(tmp)):
            for value in invalid:
                with self.subTest(value=value), self.assertRaisesRegex(OSError, "local_dir"):
                    sync._validate_config(self.config(local_dir=value))

    def test_web_local_path_must_be_canonical_relative_path(self):
        invalid = ["../outside", "/absolute", "C:/outside", "a\\b", "references/../ctx.txt",
                   "references//ctx.txt", "references/ctx.txt/", ""]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sync, "SKILL_ROOT", Path(tmp)):
            for value in invalid:
                with self.subTest(value=value), self.assertRaisesRegex(OSError, "local_path"):
                    sync._validate_config(self.config(web_path=value))

    def test_venv_dir_must_be_canonical_relative_path(self):
        invalid = ["../venv", "/venv", "C:/venv", "a\\b", "examples/../.venv",
                   "examples//.venv", "examples/.venv/", ""]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sync, "SKILL_ROOT", Path(tmp)):
            for value in invalid:
                with self.subTest(value=value), self.assertRaisesRegex(OSError, "VENV.dir"):
                    sync._validate_config(self.config(venv_dir=value))

    def test_resolved_paths_must_remain_inside_skill_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            root.mkdir()
            outside = Path(tmp) / "outside"
            cases = [("examples/Demo", "local_dir"),
                     ("references/ctx.txt", "local_path"),
                     ("examples/.venv", "VENV.dir")]
            for value, label in cases:
                candidate = root / value
                cfg = (self.config(local_dir=value) if label == "local_dir" else
                       self.config(web_path=value) if label == "local_path" else
                       self.config(venv_dir=value))
                real_resolve = Path.resolve

                def fake_resolve(path, *args, **kwargs):
                    if path == candidate:
                        return outside
                    return real_resolve(path, *args, **kwargs)

                with self.subTest(label=label), mock.patch.object(sync, "SKILL_ROOT", root), \
                        mock.patch.object(Path, "resolve", autospec=True, side_effect=fake_resolve):
                    with self.assertRaisesRegex(OSError, "SKILL_ROOT|越界"):
                        sync._validate_config(cfg)

    def test_web_url_requires_http_or_https_scheme_and_host(self):
        invalid = ["ftp://example.test/ctx", "file:///tmp/ctx", "javascript:alert(1)",
                   "https:///missing-host", "//example.test/ctx"]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sync, "SKILL_ROOT", Path(tmp)):
            for value in invalid:
                with self.subTest(value=value), self.assertRaisesRegex(OSError, "URL"):
                    sync._validate_config(self.config(url=value))

    def test_source_cannot_target_self_authored_skill_files(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sync, "SKILL_ROOT", Path(tmp)):
            with self.assertRaisesRegex(OSError, "local_dir"):
                sync._validate_config(self.config(local_dir="scripts"))

    def test_web_target_cannot_overwrite_self_authored_skill_files(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sync, "SKILL_ROOT", Path(tmp)):
            with self.assertRaisesRegex(OSError, "local_path"):
                sync._validate_config(self.config(web_path="scripts/sync_upstream.py"))

    def test_source_paths_cannot_overlap_each_other(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sync, "SKILL_ROOT", Path(tmp)):
            cfg = self.config()
            cfg["sources"].append({"id": "Nested", "repo": "owner/nested", "ref": "main",
                                   "local_dir": "examples/Demo/Nested"})
            with self.assertRaisesRegex(OSError, "重叠"):
                sync._validate_config(cfg)

    def test_venv_cannot_point_to_existing_file_or_skill_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            venv_file = root / "examples" / ".venv"
            venv_file.parent.mkdir(parents=True)
            venv_file.write_bytes(b"not a directory")
            with mock.patch.object(sync, "SKILL_ROOT", root):
                with self.assertRaisesRegex(OSError, "VENV"):
                    sync._validate_config(self.config())
            venv_file.unlink()
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "sync_upstream.py").write_bytes(b"self-authored")
            with mock.patch.object(sync, "SKILL_ROOT", root):
                with self.assertRaisesRegex(OSError, "VENV"):
                    sync._validate_config(self.config(venv_dir="scripts"))

    def test_venv_cannot_overlap_source_or_web_target(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sync, "SKILL_ROOT", Path(tmp)):
            with self.assertRaisesRegex(OSError, "VENV"):
                sync._validate_config(self.config(venv_dir="examples/Demo/.venv"))
            with self.assertRaisesRegex(OSError, "VENV"):
                sync._validate_config(self.config(venv_dir="references"))

    def test_nonempty_non_venv_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vdir = root / "examples" / ".venv"
            vdir.mkdir(parents=True)
            (vdir / "important.txt").write_bytes(b"keep")
            with mock.patch.object(sync, "SKILL_ROOT", root):
                with self.assertRaisesRegex(OSError, "VENV"):
                    sync._validate_config(self.config())

    def test_invalid_manifest_stops_main_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = self.config(local_dir="../outside")
            manifest = root / "manifest.json"
            manifest.write_text(sync.json.dumps(cfg), encoding="utf-8")
            for args in (["sync_upstream.py"], ["sync_upstream.py", "--check"]):
                with self.subTest(args=args), mock.patch.object(sync, "SKILL_ROOT", root), \
                        mock.patch.object(sync, "MANIFEST", manifest), \
                        mock.patch.object(sync, "CFG", cfg), \
                        mock.patch.object(sync.sys, "argv", args), \
                        mock.patch.object(sync, "latest_head") as latest, \
                        mock.patch.object(sync, "_http_get") as get, \
                        mock.patch.object(sync.sys, "stdout", new_callable=io.StringIO):
                    self.assertEqual(sync.main(), 1)
                latest.assert_not_called()
                get.assert_not_called()

    def test_web_sync_rejects_unsafe_path_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            root.mkdir()
            cfg = self.config(web_path="../outside.txt")
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", cfg),
                  mock.patch.object(sync, "_http_get") as get,
                  mock.patch.object(sync.sys, "stdout", new_callable=io.StringIO)):
                self.assertIsNone(sync.sync_web_files())
            get.assert_not_called()
            self.assertFalse((Path(tmp) / "outside.txt").exists())

    def test_web_sync_rejects_symlink_target_without_touching_referent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            external = root / "external.txt"
            external.write_bytes(b"external sentinel")
            target = root / "references" / "ctx.txt"
            real_is_symlink = Path.is_symlink

            def fake_is_symlink(path):
                return path == target or real_is_symlink(path)

            cfg = self.config()
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", cfg),
                  mock.patch.object(Path, "is_symlink", autospec=True, side_effect=fake_is_symlink),
                  mock.patch.object(sync, "_http_get") as get):
                with self.assertRaisesRegex(OSError, "symlink"):
                    sync.sync_web_files()
            get.assert_not_called()
            self.assertEqual(external.read_bytes(), b"external sentinel")

    def test_web_sync_rejects_non_http_url_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = self.config(url="file:///tmp/ctx")
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", cfg),
                  mock.patch.object(sync, "_http_get") as get):
                with self.assertRaisesRegex(OSError, "URL"):
                    sync.sync_web_files()
            get.assert_not_called()

    def test_ensure_venv_rejects_skill_directory_before_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "sync_upstream.py").write_bytes(b"self-authored")
            cfg = self.config(venv_dir="scripts")
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", cfg),
                  mock.patch.object(sync, "VENV", cfg["venv"]),
                  mock.patch.object(sync.subprocess, "run") as run):
                with self.assertRaisesRegex(OSError, "VENV"):
                    sync.ensure_venv([])
            run.assert_not_called()
            self.assertEqual((scripts / "sync_upstream.py").read_bytes(), b"self-authored")

    def test_sync_example_rejects_unsafe_source_path_before_metadata_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "../outside",
                   "pinned_sha": "a" * 40}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "index_tree") as index):
                self.assertEqual(sync.sync_example(src, "b" * 40), "failed")
            index.assert_not_called()


class SourceSyncTests(unittest.TestCase):
    def test_head_detection_failure_is_reported_without_crashing(self):
        src = {"id": "Demo", "repo": "owner/repo", "ref": "main", "local_dir": "examples/Demo",
               "pinned_sha": "a" * 40}
        stats = {"updated": [], "unchanged": [], "failed": []}
        with (mock.patch.object(sync, "CFG", {"web_files": []}),
              mock.patch.object(sync, "latest_head", return_value=None),
              mock.patch.object(sync, "sync_example") as sync_one,
              mock.patch.object(sync, "ensure_venv"),
              mock.patch.object(sync, "gen_bats"),
              mock.patch.object(sync, "migrate_bats")):
            self.assertEqual(sync._execute_sync([src], False, [], stats), 1)
        sync_one.assert_not_called()
        self.assertEqual(stats["failed"], ["Demo"])

    def test_incremental_success_updates_pin_and_cleans_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_bytes(b"app\n")
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "sync_incremental", return_value=(stage, "incremental")) as incremental,
                  mock.patch.object(sync, "download_tarball") as full,
                  mock.patch.object(sync, "apply_exclude", return_value=(2, 100)),
                  mock.patch.object(sync, "replace_example", return_value=True) as replace):
                self.assertEqual(sync.sync_example(src, "b" * 40), "updated")
            incremental.assert_called_once_with("owner/repo", "a" * 40, "b" * 40, src)
            full.assert_not_called()
            self.assertEqual(src["pinned_sha"], "b" * 40)
            self.assertFalse(stage.exists())
            self.assertEqual(replace.call_args.kwargs, {
                "old_pin": "a" * 40, "new_pin": "b" * 40,
                "old_snapshot": None,
                "new_snapshot": sync._fingerprint_blobs({"app.py": blob_sha(b"app\n")}),
            })

    def test_incomplete_snapshot_uses_verified_full_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            container = root / "container"
            stage = container / "Demo-sha"
            stage.mkdir(parents=True)
            (stage / "app.py").write_bytes(b"app\n")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4}}
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "is_incomplete", return_value=True),
                  mock.patch.object(sync, "sync_incremental") as incremental,
                  mock.patch.object(sync, "index_tree", return_value=tree),
                  mock.patch.object(sync, "download_tarball", return_value=(stage, "codeload")) as full,
                  mock.patch.object(sync, "apply_exclude", return_value=(0, 0)),
                  mock.patch.object(sync, "replace_example", return_value=True)):
                self.assertEqual(sync.sync_example(src, "b" * 40), "updated")
            incremental.assert_not_called()
            full.assert_called_once_with("owner/repo", "b" * 40, expected_tree=tree)
            self.assertEqual(src["pinned_sha"], "b" * 40)
            self.assertFalse(container.exists())

    def test_full_fallback_fingerprints_and_installs_the_same_content_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            content = example / "Demo"
            content.mkdir(parents=True)
            (content / "app.py").write_bytes(b"old\n")
            payload = b"new\n"
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
                info = tarfile.TarInfo("Demo-sha/Demo/app.py")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            tree = {"Demo/app.py": {"sha": blob_sha(payload), "size": len(payload)}}
            src = {"id": "Demo", "repo": "owner/Demo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "is_incomplete", return_value=True),
                  mock.patch.object(sync, "index_tree", return_value=tree),
                  mock.patch.object(sync, "_http_get", return_value=buffer.getvalue())):
                self.assertEqual(sync.sync_example(src, "b" * 40), "updated")
            self.assertEqual((content / "app.py").read_bytes(), payload)
            self.assertFalse((content / "Demo" / "app.py").exists())
            self.assertEqual(src["snapshot_sha256"], sync._snapshot_fingerprint(content))

    def test_marker_records_both_manifest_states_before_first_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"old\n")
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_bytes(b"new\n")
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40, "snapshot_sha256": "c" * 64}
            marker = example.with_name(".Demo.sync-recovery.json")
            expected_new_snapshot = sync._snapshot_fingerprint(stage)
            captured = {}
            real_rename = Path.rename

            def crash_first_rename(path, target):
                if path == example and not captured:
                    captured.update(sync.json.loads(marker.read_text(encoding="utf-8")))
                    raise OSError("simulated crash")
                return real_rename(path, target)

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "sync_incremental", return_value=(stage, "incremental")),
                  mock.patch.object(sync, "apply_exclude", return_value=(0, 0)),
                  mock.patch.object(Path, "rename", autospec=True, side_effect=crash_first_rename)):
                self.assertEqual(sync.sync_example(src, "b" * 40), "failed")
            self.assertEqual(captured["old_pin"], "a" * 40)
            self.assertEqual(captured["new_pin"], "b" * 40)
            self.assertEqual(captured["old_snapshot"], "c" * 64)
            self.assertEqual(captured["new_snapshot"], expected_new_snapshot)
            self.assertEqual(captured["nested"], "")

    def test_manifest_commit_failure_restores_old_snapshot_and_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"old\n")
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_bytes(b"new\n")
            old_snapshot = sync._snapshot_fingerprint(example)
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40, "snapshot_sha256": old_snapshot}
            manifest = write_manifest_source(root, example, "a" * 40, old_snapshot)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "sync_incremental", return_value=(stage, "incremental")),
                  mock.patch.object(sync, "apply_exclude", return_value=(0, 0)),
                  mock.patch.object(sync, "_write_manifest", side_effect=OSError("disk full"))):
                self.assertEqual(sync.sync_example(src, "b" * 40, persist=sync._write_manifest), "failed")
            self.assertEqual((example / "app.py").read_bytes(), b"old\n")
            self.assertEqual(src["pinned_sha"], "a" * 40)
            self.assertEqual(src["snapshot_sha256"], old_snapshot)
            self.assertFalse(example.with_name(example.name + ".old").exists())
            self.assertFalse(stage.exists())

    def test_replace_failure_keeps_old_pin_and_cleans_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "sync_incremental", return_value=(stage, "incremental")),
                  mock.patch.object(sync, "apply_exclude", return_value=(0, 0)),
                  mock.patch.object(sync, "replace_example", return_value=False)):
                self.assertEqual(sync.sync_example(src, "b" * 40), "failed")
            self.assertEqual(src["pinned_sha"], "a" * 40)
            self.assertFalse(stage.exists())

    def test_legacy_snapshot_matches_tree_and_only_migrates_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"app\n")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4}}
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "index_tree", return_value=tree) as index,
                  mock.patch.object(sync, "sync_incremental") as incremental,
                  mock.patch.object(sync, "download_tarball") as full,
                  mock.patch.object(sync, "_write_manifest") as write):
                self.assertEqual(sync.sync_example(src, "a" * 40, persist=sync._write_manifest), "unchanged")
            index.assert_called_once_with("owner/repo", "a" * 40)
            incremental.assert_not_called()
            full.assert_not_called()
            write.assert_called_once_with()
            self.assertEqual(src["snapshot_sha256"], sync._snapshot_fingerprint(example))

    def test_legacy_migration_hashes_the_same_single_read_used_for_tree_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            target = example / "app.py"
            target.write_bytes(b"app\n")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4}}
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40}
            real_blobs = sync._local_blobs
            reads = 0

            def tamper_after_first_read(content):
                nonlocal reads
                reads += 1
                blobs = real_blobs(content)
                target.write_bytes(b"tampered\n")
                return blobs

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "index_tree", return_value=tree),
                  mock.patch.object(sync, "_local_blobs", side_effect=tamper_after_first_read),
                  mock.patch.object(sync, "_write_manifest") as write):
                self.assertEqual(sync.sync_example(src, "a" * 40, persist=sync._write_manifest), "unchanged")
            expected = hashlib.sha256(b"app.py\0" + blob_sha(b"app\n").encode("ascii") + b"\0").hexdigest()
            self.assertEqual(src["snapshot_sha256"], expected)
            self.assertEqual(reads, 1)
            write.assert_called_once_with()

    def test_legacy_fingerprint_persist_failure_restores_manifest_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"app\n")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4}}
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "index_tree", return_value=tree),
                  mock.patch.object(sync, "_write_manifest", side_effect=OSError("disk full"))):
                self.assertEqual(sync.sync_example(src, "a" * 40, persist=sync._write_manifest), "failed")
            self.assertNotIn("snapshot_sha256", src)
            self.assertEqual((example / "app.py").read_bytes(), b"app\n")

    def test_legacy_snapshot_tree_mismatch_uses_verified_full_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"tampered\n")
            container = root / "container"
            stage = container / "Demo-sha"
            stage.mkdir(parents=True)
            (stage / "app.py").write_bytes(b"app\n")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4}}
            src = {"id": "Demo", "repo": "owner/repo", "local_dir": "examples/Demo",
                   "pinned_sha": "a" * 40}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "is_incomplete", return_value=False),
                  mock.patch.object(sync, "index_tree", return_value=tree) as index,
                  mock.patch.object(sync, "sync_incremental") as incremental,
                  mock.patch.object(sync, "download_tarball", return_value=(stage, "codeload")) as full,
                  mock.patch.object(sync, "apply_exclude", return_value=(0, 0))):
                self.assertEqual(sync.sync_example(src, "a" * 40), "updated")
            index.assert_called_once_with("owner/repo", "a" * 40)
            incremental.assert_not_called()
            full.assert_called_once_with("owner/repo", "a" * 40, expected_tree=tree)
            self.assertEqual((example / "app.py").read_bytes(), b"app\n")


class CheckFlowTests(unittest.TestCase):
    def test_check_probes_sources_concurrently_with_bounded_timeout(self):
        sources = [{"id": name, "repo": f"owner/{name.lower()}", "ref": "main",
                    "local_dir": f"examples/{name}", "pinned_sha": "a" * 40,
                    "snapshot_sha256": "fingerprint"} for name in ("One", "Two")]
        barrier = threading.Barrier(2)

        def concurrent_head(repo, ref, timeout, retries):
            self.assertEqual((timeout, retries), (30, 2))
            barrier.wait(timeout=2)
            return "a" * 40

        stats = {"updated": [], "unchanged": [], "failed": []}
        with (mock.patch.object(sync, "CFG", {"web_files": []}),
              mock.patch.object(sync, "is_incomplete", return_value=False),
              mock.patch.object(sync, "latest_head", side_effect=concurrent_head)):
            self.assertEqual(sync._execute_sync(sources, True, [], stats), 0)
        self.assertEqual(stats["unchanged"], ["One", "Two"])

    def test_check_reports_pending_transaction_without_network_or_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            marker = example.with_name(".Demo.sync-recovery.json")
            marker.write_text("interrupted", encoding="utf-8")
            src = {"id": "Demo", "repo": "owner/repo", "ref": "main",
                   "local_dir": "examples/Demo", "pinned_sha": "a" * 40}
            stats = {"updated": [], "unchanged": [], "failed": []}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", {"web_files": []}),
                  mock.patch.object(sync, "latest_head") as latest):
                self.assertEqual(sync._execute_sync([src], True, [], stats), 1)
            latest.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"), "interrupted")
            self.assertEqual(stats["failed"], ["Demo"])

    def test_check_verifies_legacy_snapshot_and_reports_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"app\n")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4},
                    "missing.py": {"sha": blob_sha(b"missing\n"), "size": 8}}
            src = {"id": "Demo", "repo": "owner/repo", "ref": "main",
                   "local_dir": "examples/Demo", "pinned_sha": "a" * 40}
            stats = {"updated": [], "unchanged": [], "failed": []}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "CFG", {"web_files": []}),
                  mock.patch.object(sync, "latest_head", return_value="a" * 40),
                  mock.patch.object(sync, "index_tree", return_value=tree) as index):
                self.assertEqual(sync._execute_sync([src], True, [], stats), 1)
            index.assert_called_once_with("owner/repo", "a" * 40, timeout=30, retries=2)
            self.assertEqual(stats["failed"], ["Demo"])
            self.assertEqual(stats["unchanged"], [])


class PathLengthTests(unittest.TestCase):
    def test_windows_stage_path_over_max_path_fails_before_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            rel = "a" * 300 + "/app.py"
            with (mock.patch.object(sync.os, "name", "nt"),
                  mock.patch.object(Path, "resolve", autospec=True) as resolve):
                with self.assertRaisesRegex(OSError, "MAX_PATH"):
                    sync._safe_stage_path(stage, rel)
            resolve.assert_not_called()

    def test_windows_atomic_write_rejects_long_path_before_temp_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ("x" * 300)
            with (mock.patch.object(sync.os, "name", "nt"),
                  mock.patch.object(sync.tempfile, "mkstemp", side_effect=AssertionError("I/O reached")) as mkstemp):
                with self.assertRaisesRegex(OSError, "MAX_PATH"):
                    sync._atomic_write_bytes(target, b"data")
            mkstemp.assert_not_called()

    def test_extended_windows_path_is_not_rejected_by_preflight(self):
        target = Path("\\\\?\\C:\\" + "x" * 300)
        with mock.patch.object(sync.os, "name", "nt"):
            self.assertEqual(sync._ensure_io_path(target), target)

    def test_posix_paths_are_not_subject_to_windows_max_path(self):
        target = Path("/" + "x" * 300)
        with mock.patch.object(sync.os, "name", "posix"):
            self.assertEqual(sync._ensure_io_path(target), target)


class SafetyTests(unittest.TestCase):
    def test_stage_paths_reject_traversal_and_windows_drives(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            for rel in ("../escape", "/absolute", "a/../../escape", "C:/escape", "a\\escape", ""):
                with self.subTest(rel=rel):
                    self.assertIsNone(sync._safe_stage_path(stage, rel))
            self.assertEqual(sync._safe_stage_path(stage, "pkg/app.py"), stage / "pkg" / "app.py")

    def test_safe_rel_rejects_each_unsafe_posix_segment(self):
        invalid = [
            "safe/C:escape", "safe/http:value", "C:escape", "C:/escape",
            "/absolute", "//server/share", "a//b", "a/", ".", "..",
            "a/./b", "a/../b", "a\\escape", "name.", "name ",
            "dir/name.", "CON", "nul.txt", "LPT9.log", "com1.dat",
        ]
        for rel in invalid:
            with self.subTest(rel=rel):
                self.assertFalse(sync._safe_rel(rel))

    def test_stage_path_rejects_resolved_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            escaped = root / "outside" / "escape.py"
            candidate = stage / "linked" / "escape.py"
            real_resolve = Path.resolve

            def fake_resolve(path, *args, **kwargs):
                if path == candidate:
                    return escaped
                return real_resolve(path, *args, **kwargs)

            with mock.patch.object(Path, "resolve", autospec=True, side_effect=fake_resolve):
                self.assertIsNone(sync._safe_stage_path(stage, "linked/escape.py"))

    def test_tar_traversal_is_rejected_without_writing_outside_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "bad.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                directory = tarfile.TarInfo("Demo-sha")
                directory.type = tarfile.DIRTYPE
                archive.addfile(directory)
                info = tarfile.TarInfo("Demo-sha/../escape.txt")
                info.size = 1
                archive.addfile(info, io.BytesIO(b"x"))
            stage = root / "stage"
            stage.mkdir()
            with self.assertRaises(OSError):
                sync._extract_tarball(archive_path, stage)
            self.assertFalse((root / "escape.txt").exists())


class IncrementalTests(unittest.TestCase):
    def test_added_and_removed_files_are_applied_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "remove.py").write_bytes(b"remove\n")
            (example / "stable.txt").write_bytes(b"stable\n")
            old_tree = {"remove.py": {"sha": blob_sha(b"remove\n"), "size": 7},
                        "stable.txt": {"sha": blob_sha(b"stable\n"), "size": 7}}
            new_tree = {"added.py": {"sha": blob_sha(b"added\n"), "size": 6},
                        "stable.txt": {"sha": blob_sha(b"stable\n"), "size": 7}}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "index_tree", side_effect=[old_tree, new_tree]),
                  mock.patch.object(sync, "compare_changes", return_value=[
                      {"path": "remove.py", "status": "removed", "previous_path": ""},
                      {"path": "added.py", "status": "added", "previous_path": ""}]),
                  mock.patch.object(sync, "fetch_raw", return_value=b"added\n")):
                stage, channel = sync.sync_incremental("owner/repo", "a" * 40, "b" * 40,
                                                       {"local_dir": "examples/Demo"})
            self.assertIsNotNone(stage)
            self.assertEqual(channel, "incremental")
            self.assertFalse((stage / "remove.py").exists())
            self.assertEqual((stage / "added.py").read_bytes(), b"added\n")
            self.assertTrue(sync._snapshot_matches(stage, new_tree))

    def test_incremental_mkdtemp_failure_is_reported_per_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"app\n")
            tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4}}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "index_tree", return_value=tree),
                  mock.patch.object(sync, "compare_changes", return_value=[]),
                  mock.patch.object(sync.tempfile, "mkdtemp", side_effect=OSError("no temp space"))):
                self.assertEqual(sync.sync_incremental("owner/repo", "a" * 40, "b" * 40,
                                                       {"local_dir": "examples/Demo"}), (None, None))

    def test_more_than_twenty_changes_falls_back_without_creating_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"old\n")
            old_tree = {"app.py": {"sha": blob_sha(b"old\n"), "size": 4}}
            new_tree = dict(old_tree)
            changes = [{"path": f"new{i}.py", "status": "added", "previous_path": ""}
                       for i in range(21)]
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "index_tree", side_effect=[old_tree, new_tree]),
                  mock.patch.object(sync, "compare_changes", return_value=changes),
                  mock.patch.object(sync, "fetch_raw") as fetch):
                self.assertEqual(sync.sync_incremental("owner/repo", "a" * 40, "b" * 40,
                                                       {"local_dir": "examples/Demo"}), (None, None))
            fetch.assert_not_called()
            self.assertFalse((root / "tmp").exists())

    def test_tampered_old_snapshot_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            target = example / "app.py"
            target.write_bytes(b"tampered\n")
            old_tree = {"app.py": {"sha": blob_sha(b"old\n"), "size": 4}}
            new_tree = {"app.py": {"sha": blob_sha(b"new\n"), "size": 4}}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "index_tree", side_effect=[old_tree, new_tree]),
                  mock.patch.object(sync, "compare_changes", return_value=[
                      {"path": "app.py", "status": "modified", "previous_path": ""}]),
                  mock.patch.object(sync, "fetch_raw") as fetch):
                self.assertEqual(sync.sync_incremental("owner/repo", "a" * 40, "b" * 40,
                                                       {"local_dir": "examples/Demo"}), (None, None))
            fetch.assert_not_called()
            self.assertEqual(target.read_bytes(), b"tampered\n")

    def test_modified_file_is_staged_without_touching_live_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"old\n")
            (example / "stable.txt").write_bytes(b"stable\n")
            old_tree = {"app.py": {"sha": blob_sha(b"old\n"), "size": 4},
                        "stable.txt": {"sha": blob_sha(b"stable\n"), "size": 7}}
            new_tree = {"app.py": {"sha": blob_sha(b"new\n"), "size": 4},
                        "stable.txt": {"sha": blob_sha(b"stable\n"), "size": 7}}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "index_tree", side_effect=[old_tree, new_tree]),
                  mock.patch.object(sync, "compare_changes", return_value=[
                      {"path": "app.py", "status": "modified", "previous_path": ""}]),
                  mock.patch.object(sync, "fetch_raw", return_value=b"new\n") as fetch):
                stage, channel = sync.sync_incremental("owner/repo", "a" * 40, "b" * 40,
                                                       {"local_dir": "examples/Demo"})
            self.assertIsNotNone(stage)
            self.assertEqual(channel, "incremental")
            self.assertEqual((stage / "app.py").read_bytes(), b"new\n")
            self.assertEqual((stage / "stable.txt").read_bytes(), b"stable\n")
            self.assertTrue(sync._snapshot_matches(stage, new_tree))
            self.assertEqual((example / "app.py").read_bytes(), b"old\n")
            fetch.assert_called_once_with("owner/repo", "b" * 40, "app.py", blob_sha(b"new\n"))

    def test_incremental_tree_paths_use_existing_nested_content_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            content = example / "Demo"
            content.mkdir(parents=True)
            (content / "app.py").write_bytes(b"old\n")
            old_tree = {"Demo/app.py": {"sha": blob_sha(b"old\n"), "size": 4}}
            new_tree = {"Demo/app.py": {"sha": blob_sha(b"new\n"), "size": 4}}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "index_tree", side_effect=[old_tree, new_tree]),
                  mock.patch.object(sync, "compare_changes", return_value=[
                      {"path": "Demo/app.py", "status": "modified", "previous_path": ""}]),
                  mock.patch.object(sync, "fetch_raw", return_value=b"new\n") as fetch):
                stage, channel = sync.sync_incremental("owner/repo", "a" * 40, "b" * 40,
                                                       {"local_dir": "examples/Demo"})
            self.assertIsNotNone(stage)
            self.assertEqual(channel, "incremental")
            self.assertEqual((stage / "app.py").read_bytes(), b"new\n")
            self.assertFalse((stage / "Demo" / "app.py").exists())
            fetch.assert_called_once_with("owner/repo", "b" * 40, "Demo/app.py", blob_sha(b"new\n"))

    def test_same_blob_rename_is_copied_without_raw_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "old.py").write_bytes(b"same\n")
            old_tree = {"old.py": {"sha": blob_sha(b"same\n"), "size": 5}}
            new_tree = {"new.py": {"sha": blob_sha(b"same\n"), "size": 5}}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "index_tree", side_effect=[old_tree, new_tree]),
                  mock.patch.object(sync, "compare_changes", return_value=[
                      {"path": "new.py", "status": "renamed", "previous_path": "old.py"}]),
                  mock.patch.object(sync, "fetch_raw") as fetch):
                stage, channel = sync.sync_incremental("owner/repo", "a" * 40, "b" * 40,
                                                       {"local_dir": "examples/Demo"})
            self.assertIsNotNone(stage)
            self.assertEqual(channel, "incremental")
            self.assertFalse((stage / "old.py").exists())
            self.assertEqual((stage / "new.py").read_bytes(), b"same\n")
            self.assertTrue(sync._snapshot_matches(stage, new_tree))
            self.assertEqual((example / "old.py").read_bytes(), b"same\n")
            fetch.assert_not_called()

    def test_incomplete_compare_cannot_leave_deleted_file_in_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "remove.py").write_bytes(b"remove\n")
            old_tree = {"remove.py": {"sha": blob_sha(b"remove\n"), "size": 7}}
            new_tree = {"app.py": {"sha": blob_sha(b"app\n"), "size": 4}}
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "TEMP", root / "tmp"),
                  mock.patch.object(sync, "index_tree", side_effect=[old_tree, new_tree]),
                  mock.patch.object(sync, "compare_changes", return_value=[]),
                  mock.patch.object(sync, "fetch_raw") as fetch):
                self.assertEqual(sync.sync_incremental("owner/repo", "a" * 40, "b" * 40,
                                                       {"local_dir": "examples/Demo"}), (None, None))
            fetch.assert_not_called()
            self.assertEqual((example / "remove.py").read_bytes(), b"remove\n")
            self.assertEqual(list((root / "tmp").iterdir()), [])


class ExcludePolicyTests(unittest.TestCase):
    def test_mandatory_and_deep_media_rules_share_one_predicate(self):
        self.assertTrue(sync._is_excluded("node_modules/pkg/index.js", deep=False))
        self.assertTrue(sync._is_excluded("docs/guide.pdf", deep=True))
        self.assertFalse(sync._is_excluded("docs/guide.pdf", deep=False))
        self.assertFalse(sync._is_excluded("docs/guide.md", deep=True))

    def test_nested_build_and_cache_directories_are_excluded(self):
        self.assertTrue(sync._is_excluded("pkg/__pycache__/module.pyc", deep=False))
        self.assertTrue(sync._is_excluded("web/node_modules/pkg/index.js", deep=False))
        self.assertTrue(sync._is_excluded("web/dist/app.js", deep=False))
        self.assertFalse(sync._is_excluded("web/distilled/app.js", deep=False))


class ReplacementTests(unittest.TestCase):
    def test_nested_project_layout_and_outer_launcher_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_text("new\n", encoding="utf-8")
            example = root / "Demo"
            content = example / "Demo"
            content.mkdir(parents=True)
            (content / "app.py").write_text("old\n", encoding="utf-8")
            launcher = example / "启动-Demo.bat"
            launcher.write_bytes(b"local-launcher")

            self.assertTrue(sync.replace_example(stage, example))
            self.assertEqual((content / "app.py").read_text(encoding="utf-8"), "new\n")
            self.assertFalse((example / "app.py").exists())
            self.assertEqual(launcher.read_bytes(), b"local-launcher")
            self.assertEqual(list(root.glob(".Demo.sync-*")), [])

    def test_nested_layout_is_not_duplicated_when_stage_has_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            (stage / "Demo").mkdir(parents=True)
            (stage / "Demo" / "app.py").write_bytes(b"new\n")
            example = root / "Demo"
            content = example / "Demo"
            content.mkdir(parents=True)
            (content / "app.py").write_bytes(b"old\n")

            self.assertTrue(sync.replace_example(stage, example))
            self.assertEqual((content / "app.py").read_bytes(), b"new\n")
            self.assertFalse((content / "Demo" / "app.py").exists())

    def test_keep_is_symmetric_and_preserves_nested_local_venv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_bytes(b"new\n")
            (stage / "启动-Demo.bat").write_bytes(b"remote-launcher")
            (stage / ".venv").mkdir()
            (stage / ".venv" / "remote.py").write_bytes(b"remote")
            example = root / "Demo"
            content = example / "Demo"
            content.mkdir(parents=True)
            (content / "app.py").write_bytes(b"old\n")
            (example / "启动-Demo.bat").write_bytes(b"local-launcher")
            (content / ".venv").mkdir()
            (content / ".venv" / "local.py").write_bytes(b"local")

            self.assertTrue(sync.replace_example(stage, example))
            self.assertEqual((example / "启动-Demo.bat").read_bytes(), b"local-launcher")
            self.assertEqual((content / ".venv" / "local.py").read_bytes(), b"local")
            self.assertFalse((content / ".venv" / "remote.py").exists())
            self.assertFalse((example / ".venv").exists())

    def test_commit_failure_rolls_back_and_removes_transaction_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_bytes(b"new\n")
            example = root / "Demo"
            example.mkdir()
            (example / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(example)
            new_snapshot = sync._snapshot_fingerprint(stage)
            manifest = write_manifest_source(root, example, "a" * 40, old_snapshot)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                self.assertFalse(sync.replace_example(
                    stage, example, commit=mock.Mock(side_effect=OSError("manifest failed")),
                    old_pin="a" * 40, new_pin="b" * 40,
                    old_snapshot=old_snapshot, new_snapshot=new_snapshot))
            self.assertEqual((example / "app.py").read_bytes(), b"old\n")
            self.assertEqual(list(root.glob(".Demo.sync-*")), [])

    def test_commit_that_persists_then_raises_keeps_new_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_bytes(b"new\n")
            example = root / "Demo"
            example.mkdir()
            (example / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(example)
            new_snapshot = sync._snapshot_fingerprint(stage)
            manifest = write_manifest_source(root, example, "a" * 40, old_snapshot)

            def persist_then_fail():
                write_manifest_source(root, example, "b" * 40, new_snapshot)
                raise OSError("post-replace failure")

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                self.assertTrue(sync.replace_example(
                    stage, example, commit=persist_then_fail,
                    old_pin="a" * 40, new_pin="b" * 40,
                    old_snapshot=old_snapshot, new_snapshot=new_snapshot))
            self.assertEqual((example / "app.py").read_bytes(), b"new\n")
            self.assertEqual(sync.json.loads(manifest.read_text(encoding="utf-8"))["sources"][0]["pinned_sha"],
                             "b" * 40)
            self.assertEqual(list(root.glob(".Demo.sync-*")), [])

    def test_post_commit_cleanup_failure_does_not_report_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_bytes(b"new\n")
            example = root / "Demo"
            example.mkdir()
            (example / "app.py").write_bytes(b"old\n")
            commit = mock.Mock()
            with mock.patch.object(sync, "_remove_path", side_effect=OSError("backup busy")):
                self.assertTrue(sync.replace_example(stage, example, commit=commit))
            commit.assert_called_once_with()
            self.assertEqual((example / "app.py").read_bytes(), b"new\n")
            marker = example.with_name(".Demo.sync-recovery.json")
            self.assertTrue(marker.exists())
            state = sync.json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(state["phase"], "committed")
            manifest = write_manifest_source(root, example, state["new_pin"], state["new_snapshot"])
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                self.assertTrue(sync._recover_example(example))
            self.assertFalse(marker.exists())
            self.assertEqual(list(root.glob(".Demo.sync-backup-*")), [])

    def test_committed_marker_with_old_manifest_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            example.mkdir()
            (example / "app.py").write_bytes(b"new\n")
            backup.mkdir()
            (backup / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            new_snapshot = sync._snapshot_fingerprint(example)
            marker = write_transaction_marker(example, backup, new, "committed",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "a" * 40, old_snapshot)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                self.assertTrue(sync._recover_example(example))
            self.assertEqual((example / "app.py").read_bytes(), b"old\n")
            self.assertFalse(marker.exists())
            self.assertFalse(backup.exists())

    def test_replacing_marker_with_new_manifest_keeps_verified_live_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            example.mkdir()
            (example / "app.py").write_bytes(b"new\n")
            backup.mkdir()
            (backup / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            new_snapshot = sync._snapshot_fingerprint(example)
            marker = write_transaction_marker(example, backup, new, "replacing",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "b" * 40, new_snapshot)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                self.assertTrue(sync._recover_example(example))
            self.assertEqual((example / "app.py").read_bytes(), b"new\n")
            self.assertFalse(marker.exists())
            self.assertFalse(backup.exists())

    def test_committed_recovery_rejects_empty_live_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            example.mkdir()
            backup.mkdir()
            (backup / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            expected_new = root / "expected-new"
            expected_new.mkdir()
            (expected_new / "app.py").write_bytes(b"new\n")
            new_snapshot = sync._snapshot_fingerprint(expected_new)
            marker = write_transaction_marker(example, backup, new, "committed",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "b" * 40, new_snapshot)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                with self.assertRaisesRegex(OSError, "保留"):
                    sync._recover_example(example)
            self.assertTrue(marker.exists())
            self.assertTrue(backup.exists())

    def test_committed_recovery_rejects_tampered_live_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            example.mkdir()
            (example / "app.py").write_bytes(b"tampered\n")
            backup.mkdir()
            (backup / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            new_snapshot = sync._snapshot_fingerprint(root / "missing-new")
            marker = write_transaction_marker(example, backup, new, "committed",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "b" * 40, new_snapshot)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                with self.assertRaisesRegex(OSError, "保留"):
                    sync._recover_example(example)
            self.assertTrue(marker.exists())
            self.assertEqual((backup / "app.py").read_bytes(), b"old\n")

    def test_committed_recovery_rejects_symlink_live_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            example.mkdir()
            backup.mkdir()
            (backup / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            new_snapshot = sync._snapshot_fingerprint(example)
            marker = write_transaction_marker(example, backup, new, "committed",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "b" * 40, new_snapshot)
            real_is_symlink = Path.is_symlink

            def fake_is_symlink(path):
                return path == example or real_is_symlink(path)

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(Path, "is_symlink", autospec=True, side_effect=fake_is_symlink)):
                with self.assertRaisesRegex(OSError, "保留"):
                    sync._recover_example(example)
            self.assertTrue(marker.exists())
            self.assertTrue(backup.exists())

    def test_recovery_rejects_non_token_backup_and_new_names(self):
        for kind in ("backup", "new"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                example = root / "Demo"
                example.mkdir()
                (example / "app.py").write_bytes(b"new\n")
                backup = root / ".Demo.sync-backup-deadbeef"
                new = root / ".Demo.sync-new-deadbeef"
                backup.mkdir()
                (backup / "app.py").write_bytes(b"old\n")
                if kind == "backup":
                    backup = root / ".Demo.sync-backup-deadbeef-extra"
                    backup.mkdir()
                    (backup / "app.py").write_bytes(b"old\n")
                else:
                    new = root / ".Demo.sync-new-deadbeef-extra"
                    new.mkdir()
                    (new / "app.py").write_bytes(b"new\n")
                old_snapshot = sync._snapshot_fingerprint(root / ".Demo.sync-backup-deadbeef")
                new_snapshot = sync._snapshot_fingerprint(example)
                marker = write_transaction_marker(example, backup, new, "committed",
                                                  old_snapshot, new_snapshot)
                manifest = write_manifest_source(root, example, "b" * 40, new_snapshot)
                with (mock.patch.object(sync, "SKILL_ROOT", root),
                      mock.patch.object(sync, "MANIFEST", manifest)):
                    with self.assertRaisesRegex(OSError, "无效同步恢复路径"):
                        sync._recover_example(example)
                self.assertTrue(marker.exists())

    def test_recovery_rejects_file_backup_and_file_new_types(self):
        for kind in ("backup", "new"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                example = root / "Demo"
                example.mkdir()
                (example / "app.py").write_bytes(b"new\n")
                backup = root / ".Demo.sync-backup-deadbeef"
                new = root / ".Demo.sync-new-deadbeef"
                backup.mkdir()
                (backup / "app.py").write_bytes(b"old\n")
                if kind == "backup":
                    (backup / "app.py").unlink()
                    backup.rmdir()
                    backup.write_bytes(b"not a directory")
                else:
                    new.write_bytes(b"not a directory")
                old_snapshot = sync._fingerprint_blobs({"app.py": blob_sha(b"old\n")})
                new_snapshot = sync._snapshot_fingerprint(example)
                marker = write_transaction_marker(example, backup, new, "committed",
                                                  old_snapshot, new_snapshot)
                manifest = write_manifest_source(root, example, "b" * 40, new_snapshot)
                with (mock.patch.object(sync, "SKILL_ROOT", root),
                      mock.patch.object(sync, "MANIFEST", manifest)):
                    with self.assertRaisesRegex(OSError, "保留"):
                        sync._recover_example(example)
                self.assertTrue(marker.exists())
                self.assertTrue(backup.exists())

    def test_rollback_rejects_tampered_backup_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            example.mkdir()
            (example / "app.py").write_bytes(b"new\n")
            backup.mkdir()
            (backup / "app.py").write_bytes(b"tampered\n")
            old_snapshot = sync._fingerprint_blobs({"app.py": blob_sha(b"old\n")})
            new_snapshot = sync._snapshot_fingerprint(example)
            marker = write_transaction_marker(example, backup, new, "committed",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "a" * 40, old_snapshot)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                with self.assertRaisesRegex(OSError, "保留"):
                    sync._recover_example(example)
            self.assertTrue(marker.exists())
            self.assertEqual((backup / "app.py").read_bytes(), b"tampered\n")

    def test_recovery_rejects_manifest_that_matches_neither_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            example.mkdir()
            (example / "app.py").write_bytes(b"new\n")
            backup.mkdir()
            (backup / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            new_snapshot = sync._snapshot_fingerprint(example)
            marker = write_transaction_marker(example, backup, new, "committed",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "c" * 40, "d" * 64)
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                with self.assertRaisesRegex(OSError, "保留"):
                    sync._recover_example(example)
            self.assertTrue(marker.exists())
            self.assertTrue(backup.exists())

    def test_recovery_restores_backup_after_interrupted_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            backup.mkdir()
            (backup / "app.py").write_bytes(b"old\n")
            new.mkdir()
            (new / "app.py").write_bytes(b"new\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            new_snapshot = sync._snapshot_fingerprint(new)
            marker = write_transaction_marker(example, backup, new, "replacing",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "a" * 40, old_snapshot)

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                self.assertTrue(sync._recover_example(example))
            self.assertEqual((example / "app.py").read_bytes(), b"old\n")
            self.assertFalse(backup.exists())
            self.assertFalse(new.exists())
            self.assertFalse(marker.exists())

    def test_rollback_failure_keeps_backup_and_recovery_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            stage.mkdir()
            (stage / "app.py").write_bytes(b"new\n")
            example = root / "Demo"
            example.mkdir()
            (example / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(example)
            new_snapshot = sync._snapshot_fingerprint(stage)
            manifest = write_manifest_source(root, example, "a" * 40, old_snapshot)
            real_rename = sync.Path.rename

            def fail_backup_restore(path, target):
                if path.name.startswith(".Demo.sync-backup-"):
                    raise OSError("restore blocked")
                return real_rename(path, target)

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest),
                  mock.patch.object(sync.Path, "rename", autospec=True, side_effect=fail_backup_restore),
                  mock.patch.object(sync, "_remove_path", wraps=sync._remove_path)):
                with self.assertRaisesRegex(OSError, "恢复失败"):
                    sync.replace_example(
                        stage, example, commit=mock.Mock(side_effect=OSError("manifest failed")),
                        old_pin="a" * 40, new_pin="b" * 40,
                        old_snapshot=old_snapshot, new_snapshot=new_snapshot)
            marker = example.with_name(".Demo.sync-recovery.json")
            self.assertTrue(marker.exists())
            self.assertEqual(sync.json.loads(marker.read_text(encoding="utf-8"))["phase"], "committed")
            self.assertEqual(len(list(root.glob(".Demo.sync-backup-*"))), 1)
            state = sync.json.loads(marker.read_text(encoding="utf-8"))
            manifest = write_manifest_source(root, example, state["old_pin"], state["old_snapshot"])
            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                self.assertTrue(sync._recover_example(example))
            self.assertEqual((example / "app.py").read_bytes(), b"old\n")
            self.assertFalse(marker.exists())

    def test_recovery_removes_orphan_build_directory_without_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            example.mkdir()
            (example / "app.py").write_bytes(b"old\n")
            orphan = root / ".Demo.sync-new-deadbeef"
            orphan.mkdir()
            (orphan / "app.py").write_bytes(b"partial\n")
            self.assertTrue(sync._recover_example(example))
            self.assertFalse(orphan.exists())
            self.assertEqual((example / "app.py").read_bytes(), b"old\n")

    def test_recovery_keeps_committed_directory_and_cleans_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "Demo"
            backup = root / ".Demo.sync-backup-deadbeef"
            new = root / ".Demo.sync-new-deadbeef"
            example.mkdir()
            (example / "app.py").write_bytes(b"new\n")
            backup.mkdir()
            (backup / "app.py").write_bytes(b"old\n")
            old_snapshot = sync._snapshot_fingerprint(backup)
            new_snapshot = sync._snapshot_fingerprint(example)
            marker = write_transaction_marker(example, backup, new, "committed",
                                              old_snapshot, new_snapshot)
            manifest = write_manifest_source(root, example, "b" * 40, new_snapshot)

            with (mock.patch.object(sync, "SKILL_ROOT", root),
                  mock.patch.object(sync, "MANIFEST", manifest)):
                self.assertTrue(sync._recover_example(example))
            self.assertEqual((example / "app.py").read_bytes(), b"new\n")
            self.assertFalse(backup.exists())
            self.assertFalse(marker.exists())


class CompletenessTests(unittest.TestCase):
    def test_snapshot_fingerprint_detects_same_count_tamper_and_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "Demo"
            example.mkdir(parents=True)
            (example / "app.py").write_bytes(b"old\n")
            (example / "stable.txt").write_bytes(b"stable\n")
            src = {"local_dir": "examples/Demo"}
            with mock.patch.object(sync, "SKILL_ROOT", root):
                src["snapshot_sha256"] = sync._snapshot_fingerprint(example)
                self.assertFalse(sync.is_incomplete(src))
                (example / "app.py").write_bytes(b"new\n")
                self.assertTrue(sync.is_incomplete(src))
                (example / "app.py").write_bytes(b"old\n")
                (example / "stable.txt").unlink()
                self.assertTrue(sync.is_incomplete(src))


class EntryDetectionTests(unittest.TestCase):
    def test_same_name_package_is_not_treated_as_project_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            ex = Path(tmp) / "Demo"
            package = ex / "Demo"
            package.mkdir(parents=True)
            (ex / "app.py").write_text("from fasthtml.core import *\nserve(app)\n", encoding="utf-8")
            (package / "__init__.py").write_text("", encoding="utf-8")

            self.assertEqual(sync._detect_entry(ex), ("app.py", "direct", ""))


if __name__ == "__main__":
    unittest.main()
