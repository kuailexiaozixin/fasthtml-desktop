# -*- coding: utf-8 -*-
"""dev_check.py — FastMail 一键质量门禁（测试/调试/检查/验证）

进程内 TestClient 验证，不占端口、不弹窗口：
  A. 登录弹窗（FastSME account store）
     1. GET /                          -> 200 且含「Use demo account」与演示邮箱
     2. POST /auth/local/login 错误口令 -> 401
     3. POST /auth/local/login 正确口令 -> 200 且 redirect=/
     4. POST /auth/local/register 新账号 -> 200，且新账号可立即登录（离线免邮件验证）
     5. 未登录访问 /folder/Inbox        -> 303 跳 /login
     6. 登录态遍历业务路由              -> 全部 200
  B. 原生登录页
     7. POST /login 错误口令            -> 回登录页且报错
     8. POST /login 正确口令            -> 303 跳 /

全部通过 exit 0；任一失败 exit 1（供 CI / 打包前门禁串联）。
"""
import os, sys, uuid
from pathlib import Path

HERE = Path(__file__).parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

# 门禁用独立库文件，避免污染用户的 data/fastmail.sqlite 与账号库
os.environ.setdefault("FASTMAIL_DB", str(HERE / "data" / "devcheck.sqlite"))
os.environ.setdefault("FASTSME_AUTH_DB", str(HERE / "data" / "devcheck-accounts.sqlite"))

ROUTES = ["/folder/Inbox", "/folder/Sent", "/folder/Archive", "/contacts",
          "/labels", "/calendar", "/compose", "/ai", "/guide"]
PUBLIC_ROUTES = ["/login", "/developers", "/swagger.json"]

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

    # --- A. 登录弹窗 -------------------------------------------------------
    r = c.get("/")
    check("GET / 落地页", r.status_code == 200, f"status={r.status_code}")
    check("落地页含演示账号按钮", "Use demo account" in r.text and email in r.text)

    r = c.post("/auth/local/login", data={"email": email, "password": "wrong-password"})
    check("POST /auth/local/login 错误口令被拒", r.status_code == 401, f"status={r.status_code}")

    r = c.post("/auth/local/login", data={"email": email, "password": password})
    check("POST /auth/local/login 正确口令通过",
          r.status_code == 200 and r.json().get("redirect") == "/",
          f"status={r.status_code} body={r.text[:120]}")

    # 注册：离线无 SMTP 时应本地直接置为已验证，且能立刻登录
    new_email = f"gate-{uuid.uuid4().hex[:8]}@fastmail.example"
    new_password = "GateCheck2026$"
    reg = TestClient(app)
    r = reg.post("/auth/local/register",
                 data={"email": new_email, "password": new_password, "name": "Gate"})
    check("POST /auth/local/register 注册成功", r.status_code == 200,
          f"status={r.status_code} body={r.text[:120]}")
    r = reg.post("/auth/local/login", data={"email": new_email, "password": new_password})
    check("新注册账号可直接登录", r.status_code == 200 and r.json().get("redirect") == "/",
          f"status={r.status_code} body={r.text[:120]}")
    r = reg.get("/folder/Inbox", follow_redirects=False)
    check("新注册账号进入 /folder/Inbox", r.status_code == 200, f"status={r.status_code}")

    # 未登录拦截
    anon = TestClient(app)
    r = anon.get("/folder/Inbox", follow_redirects=False)
    check("未登录访问 /folder/Inbox 被拦截",
          r.status_code in (302, 303) and "/login" in r.headers.get("location", ""),
          f"status={r.status_code}")

    for route in PUBLIC_ROUTES:
        r = anon.get(route, follow_redirects=False)
        check(f"公开路由 GET {route}", r.status_code == 200, f"status={r.status_code}")

    # 登录态遍历业务路由（follow_redirects=False 防 303->登录页->200 的假绿）
    for route in ROUTES:
        r = c.get(route, follow_redirects=False)
        check(f"弹窗登录态 GET {route}", r.status_code == 200, f"status={r.status_code}")

    # 邮件详情（取收件箱第一封，验证演示数据已播种）
    import db
    msgs = db.messages_in("Inbox")
    check("演示邮件已播种", bool(msgs), f"count={len(msgs)}")
    if msgs:
        mid = msgs[0]["id"]
        r = c.get(f"/message/{mid}", follow_redirects=False)
        check(f"弹窗登录态 GET /message/{mid}", r.status_code == 200, f"status={r.status_code}")

    # --- B. 原生登录页 -----------------------------------------------------
    nat = TestClient(app)
    r = nat.post("/login", data={"email": email, "password": "nope"}, follow_redirects=False)
    check("POST /login 错误口令被拒",
          r.status_code == 200 and "Invalid email or password" in r.text,
          f"status={r.status_code}")

    r = nat.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    check("POST /login 正确口令跳转",
          r.status_code in (302, 303) and r.headers.get("location") == "/",
          f"status={r.status_code} loc={r.headers.get('location')}")

    r = nat.get("/folder/Inbox", follow_redirects=False)
    check("原生登录态进入收件箱", r.status_code == 200, f"status={r.status_code}")

    print()
    if failures:
        print(f"[GATE] 未通过：{len(failures)} 项失败 -> {failures}")
        sys.exit(1)
    print("[GATE] 全部通过，可交付/可打包")
    sys.exit(0)


if __name__ == "__main__":
    main()
