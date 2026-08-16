# -*- coding: utf-8 -*-
"""dev_check.py — Bricksmith 一键质量门禁（测试/调试/检查/验证）

进程内 TestClient 验证，不占端口、不弹窗口，秒级完成：
  1. 导入 app（首次会自动建库 + 迁移 SQLite schema / vec0 向量表 / 播种 prompt 版本）
  2. 未登录访问落地页 / 与产品页           -> 200
  3. 访问 3 栏聊天产品页 /app              -> 200
  4. 静态资源可达                          -> 200

注意：/app/_debug/ping 需要大模型 API Key（XAI_API_KEY / OPENAI_API_KEY），
不在门禁范围内；聊天问答依赖该 Key，但页面与路由骨架不依赖。

全部通过 exit 0；任一失败 exit 1（供 CI / 打包前门禁串联）。
"""
import os, sys
from pathlib import Path

HERE = Path(__file__).parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

failures = []


def check(name, ok, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"{tag} {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    # 导入即触发 db/__init__ 迁移守卫：若 data/bricksmith.db 不存在则自动建库
    import app  # noqa: F401  (import 副作用：注册路由 + 必要时迁移)

    from starlette.testclient import TestClient
    c = TestClient(app.app)

    public_routes = [
        "/", "/platform", "/agents", "/how-it-works",
        "/pricing", "/contact", "/app",
    ]
    for route in public_routes:
        r = c.get(route)
        check(f"GET {route}", r.status_code == 200, f"status={r.status_code}")

    # 静态资源可达性
    static_dir = HERE / "static"
    if static_dir.is_dir():
        files = [f for f in static_dir.iterdir() if f.is_file()]
        if files:
            r = c.get(f"/static/{files[0].name}")
            check(f"静态资源 /static/{files[0].name}", r.status_code == 200,
                  f"status={r.status_code}")
        else:
            check("静态资源目录非空", False, "static/ 下无文件")
    else:
        check("静态资源目录存在", False, "static/ 不存在")

    print()
    if failures:
        print(f"[GATE] 未通过：{len(failures)} 项失败 -> {failures}")
        sys.exit(1)
    print("[GATE] 全部通过，可交付/可打包")
    sys.exit(0)


if __name__ == "__main__":
    main()
