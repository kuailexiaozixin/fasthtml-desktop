# -*- coding: utf-8 -*-
"""verify_providers.py — 端到端校验厂商下拉扩展（DeepSeek / OpenRouter / Agnes 2）

用 starlette TestClient 直接驱动真实 ASGI 应用，不占端口、不开窗口：
  1) GET  /            → 无 Key 时应弹出 Key 弹窗，且下拉里有 11 个厂商（含新增 3 个）
  2) POST /provider    → 切到每个新厂商，检查表单字段与预填模型串
运行:  python scripts/verify_providers.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("CA_GENERATED_APPS_DIR", "generated_apps")
# 确保处于「缺 Key」状态，首页才会渲染 Key 弹窗
for var in ("OPENAI_API_KEY", "ASTRA_DB_APPLICATION_TOKEN"):
    os.environ.pop(var, None)

from starlette.testclient import TestClient  # noqa: E402

from code_assistant.main import app  # noqa: E402
from code_assistant.providers_ext import DEFAULT_MODELS, NEW_PROVIDERS  # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print(f"  [{'OK ' if ok else 'FAIL'}] {label}{('  ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def main():
    client = TestClient(app)

    print("1) GET / —— Key 弹窗与厂商下拉")
    html = client.get("/").text
    check("弹窗已渲染", 'id="key_modal"' in html)
    for provider in NEW_PROVIDERS:
        check(f"下拉包含 {provider}", f">{provider}</option>" in html)
    check("原有厂商未丢失", all(f">{p}</option>" in html for p in
                          ["openai", "groq", "anthropic", "gemini", "perplexity",
                           "cohere", "bedrock", "other"]))

    print("2) POST /provider —— 切换厂商后的表单")
    for provider, env_map in NEW_PROVIDERS.items():
        html = client.post("/provider", data={"provider": provider}).text
        for env_var in env_map.values():
            check(f"{provider} 表单含 {env_var}", f'id="{env_var}"' in html)
        check(f"{provider} 预填模型 {DEFAULT_MODELS[provider]}",
              DEFAULT_MODELS[provider] in html)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} 项 -> {FAILURES}")
        return 1
    print("ALL PASS —— DeepSeek / OpenRouter / Agnes 2 已接入模型配置")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
