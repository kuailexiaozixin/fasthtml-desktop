# -*- coding: utf-8 -*-
"""dev_check.py — FastLegal 一键质量门禁（测试/调试/检查/验证）

进程内 TestClient 验证，不占端口、不弹窗口，秒级完成：
  1. GET /login                 -> 200 且含演示账号按钮
  2. POST /login 错误口令        -> 拒绝
  3. POST /login 正确口令        -> HX-Redirect 到 /assistant
  4. 注册新账号                  -> HX-Redirect 且落库
  5. 未登录访问受保护路由        -> 303 跳 /login
  6. 登录态遍历关键业务路由      -> 全部 200

全部通过 exit 0；任一失败 exit 1（供 CI / 打包前门禁串联）。
"""
import os, sys, uuid
from pathlib import Path

HERE = Path(__file__).parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

# 门禁用独立库文件，避免污染用户的 data/fastlegal.sqlite
os.environ.setdefault("FASTLEGAL_DB", str(HERE / "data" / "devcheck.sqlite"))

ROUTES = ["/assistant", "/projects", "/tabular-reviews", "/workflows", "/account"]

failures = []


def check(name, ok, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"{tag} {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    from starlette.testclient import TestClient
    import desktop

    app, email, password = desktop.build_app()
    c = TestClient(app)

    r = c.get("/login")
    check("GET /login", r.status_code == 200, f"status={r.status_code}")
    check("登录页含演示账号按钮", "Use demo account" in r.text and email in r.text)

    r = c.post("/login", data={"email": email, "password": "wrong-password"})
    check("POST /login 错误口令被拒",
          r.status_code == 200 and "Invalid" in r.text and "HX-Redirect" not in r.headers,
          f"status={r.status_code}")

    r = c.post("/login", data={"email": email, "password": password})
    check("POST /login 正确口令跳转",
          r.headers.get("HX-Redirect") == "/assistant",
          f"hx-redirect={r.headers.get('HX-Redirect')}")

    # 注册新账号（上游无邮件验证门禁，注册后应直接登录）
    new_email = f"gate-{uuid.uuid4().hex[:8]}@fastlegal.example"
    r2 = c.post("/signup", data={"email": new_email, "password": "GateCheck2026$",
                                 "display_name": "Gate", "organisation": "QA"})
    check("POST /signup 新账号注册成功",
          r2.headers.get("HX-Redirect") == "/assistant",
          f"hx-redirect={r2.headers.get('HX-Redirect')}")

    r2b = c.post("/signup", data={"email": new_email, "password": "GateCheck2026$"})
    check("POST /signup 重复邮箱被拒", "already registered" in r2b.text.lower())

    # 用干净 client 验证未登录拦截
    anon = TestClient(app)
    r3 = anon.get("/projects", follow_redirects=False)
    check("未登录访问 /projects 被拦截",
          r3.status_code in (302, 303) and "/login" in r3.headers.get("location", ""),
          f"status={r3.status_code}")

    # 回到演示账号登录态遍历业务路由
    c.post("/login", data={"email": email, "password": password})
    for route in ROUTES:
        # follow_redirects=False：否则未登录时 303->/login->200 会造成假绿
        r4 = c.get(route, follow_redirects=False)
        check(f"登录态 GET {route}", r4.status_code == 200, f"status={r4.status_code}")

    print()
    if failures:
        print(f"[GATE] 未通过：{len(failures)} 项失败 -> {failures}")
        sys.exit(1)
    print("[GATE] 全部通过，可交付/可打包")
    sys.exit(0)


if __name__ == "__main__":
    main()
