# -*- coding: utf-8 -*-
"""dev_check.py — FastCRM 一键质量门禁（测试/调试/检查/验证）

进程内 TestClient 验证，不占端口、不弹窗口，秒级完成：
  1. 未登录访问 /            -> 落地页或跳转（不能 500）
  2. GET /login              -> 200
  3. POST /login 错误口令     -> 拒绝（非跳转）
  4. POST /login 正确口令     -> 303 跳转 /
  5. 登录态遍历关键业务路由    -> 全部 200
  6. GET /swagger.json       -> 200 且为合法 JSON
  7. 静态资源可达             -> 200

全部通过 exit 0；任一失败 exit 1（供 CI / 打包前门禁串联）。
"""
import os, sys, json
from pathlib import Path

HERE = Path(__file__).parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

EMAIL = "admin@fastcrm.example"
PASSWORD = "FastCRM2026$"
ROUTES = ['/leads', '/deals', '/tasks', '/contacts', '/organizations', '/ai', '/guide']

failures = []



def _bootstrap_db():
    """与上游 Dockerfile 的 CMD 一致：import web_app 前先确保数据库已播种。
    （如 FastInsights 的 web.api 在 import 期就要求仓库表已存在）"""
    import db
    if not db.db_exists():
        print("[INFO] 首次启动：正在生成合成种子数据...")
        import seed
        seed.build()

def check(name, ok, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"{tag} {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    from starlette.testclient import TestClient
    _bootstrap_db()
    import web_app  # import 即自动建库 + 播种

    c = TestClient(web_app.app)

    r = c.get("/", follow_redirects=False)
    check("未登录访问 /", r.status_code in (200, 303, 302, 307), f"status={r.status_code}")

    r = c.get("/login")
    check("GET /login", r.status_code == 200, f"status={r.status_code}")

    r = c.post("/login", data={"email": EMAIL, "password": "wrong"}, follow_redirects=False)
    check("POST /login 错误口令被拒", r.status_code == 200 and "Invalid" in r.text,
          f"status={r.status_code}")

    r = c.post("/login", data={"email": EMAIL, "password": PASSWORD}, follow_redirects=False)
    check("POST /login 正确口令跳转", r.status_code in (302, 303), f"status={r.status_code}")

    r = c.get("/")
    check("登录态 GET /", r.status_code == 200, f"status={r.status_code}")

    for route in ROUTES:
        r = c.get(route)
        check(f"登录态 GET {route}", r.status_code == 200, f"status={r.status_code}")

    r = c.get("/swagger.json")
    ok = r.status_code == 200
    if ok:
        try:
            json.loads(r.text)
        except Exception:
            ok = False
    check("GET /swagger.json 合法 JSON", ok, f"status={r.status_code}")

    static_dir = HERE / "static"
    if static_dir.is_dir():
        files = [f for f in static_dir.iterdir() if f.is_file()]
        if files:
            r = c.get(f"/static/{files[0].name}")
            check(f"静态资源 /static/{files[0].name}", r.status_code == 200,
                  f"status={r.status_code}")

    print()
    if failures:
        print(f"[GATE] 未通过：{len(failures)} 项失败 -> {failures}")
        sys.exit(1)
    print("[GATE] 全部通过，可交付/可打包")
    sys.exit(0)


if __name__ == "__main__":
    main()
