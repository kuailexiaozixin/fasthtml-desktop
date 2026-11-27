from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"
BLUEPRINT = TEMPLATES / "project-blueprints" / "web-desktop-exe"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_project.ps1"


class TemplateCoverageTests(unittest.TestCase):
    def test_bootstrap_consumes_every_active_template(self):
        source = BOOTSTRAP.read_text(encoding="utf-8-sig")
        names = (
            "pyproject.patch.toml.tmpl",
            "requirements.txt.tmpl",
            ".env.example.tmpl",
            ".gitignore.tmpl",
            "src\\main.py.tmpl",
            "src\\app.py.tmpl",
            "src\\dev_main.py.tmpl",
            "README.md.tmpl",
            "启动.bat.tmpl",
            "pyinstaller_hooks\\hook-genai_prices.py",
            "..\\templates\\shared\\launcher.py",
        )
        for name in names:
            with self.subTest(name=name):
                self.assertIn(name, source)

    def test_shared_main_and_blueprint_template_are_exactly_in_sync(self):
        shared = (TEMPLATES / "shared" / "main.py").read_text(encoding="utf-8")
        template = (BLUEPRINT / "src" / "main.py.tmpl").read_text(encoding="utf-8")
        self.assertEqual(shared.replace("__APP_TITLE__", "{{APP_NAME}}"), template)

    def test_blueprint_has_no_unused_or_duplicate_sample_files(self):
        self.assertFalse((BLUEPRINT / "src" / "app.py").exists())
        self.assertFalse((TEMPLATES / "inline-css").exists())

    def test_active_templates_are_utf8_without_bom(self):
        for path in TEMPLATES.rglob("*"):
            if path.is_file():
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertFalse(path.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_generated_app_has_explicit_routes_and_health_endpoint(self):
        source = (BLUEPRINT / "src" / "app.py.tmpl").read_text(encoding="utf-8")
        self.assertIn('@rt("/")', source)
        self.assertIn('@rt("/healthz")', source)
        self.assertNotIn("\n@rt\ndef", source)

    def test_blueprint_project_metadata_matches_runtime_contract(self):
        pyproject = (BLUEPRINT / "pyproject.patch.toml.tmpl").read_text(encoding="utf-8")
        requirements = (BLUEPRINT / "requirements.txt.tmpl").read_text(encoding="utf-8")
        self.assertIn('requires-python = ">=3.11"', pyproject)
        self.assertNotIn("[project.scripts]", pyproject)
        self.assertIn("requests>=2.31", pyproject)
        self.assertIn("requests>=2.31", requirements)

    def test_launcher_bat_requires_python_311_and_is_gbk_crlf(self):
        data = (BLUEPRINT / "启动.bat.tmpl").read_bytes()
        text = data.decode("gbk")
        self.assertIn("3,11", text)
        self.assertEqual(data.count(b"\r\n"), data.count(b"\n"))
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()