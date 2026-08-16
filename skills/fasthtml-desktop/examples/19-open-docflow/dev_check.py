# -*- coding: utf-8 -*-
"""dev_check.py — open-docflow 一键质量门禁（测试/调试/检查/验证）

进程内 TestClient 验证，不占端口、不弹窗口、不碰真实数据库（全程跑在临时目录）：
  1. 未登录访问业务路由      -> 303 跳转 /login
  2. GET /login              -> 200 且带账号弹窗与一键演示按钮
  3. POST /auth/local/login 错误口令 -> 401
  4. POST /auth/local/register 新账号 -> 200（离线免邮件验证）
  5. 新注册账号可直接登录     -> 200
  6. 演示账号可登录           -> 200
  7. 登录态遍历关键业务路由   -> 全部 200
  8. 文档详情 + 状态流转      -> 200 且流转成功
  9. GET /logout             -> 303，登出后再访问业务路由 -> 303

全部通过 exit 0；任一失败 exit 1（供 CI / 打包前门禁串联）。
"""
import os, sys, json, shutil, tempfile
from pathlib import Path

HERE = Path(__file__).parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

# 全部落到临时目录，避免污染 data/open-docflow.sqlite 与 uploads/
SCRATCH = Path(tempfile.mkdtemp(prefix="docflow-devcheck-"))
os.environ["DOCFLOW_DB"] = str(SCRATCH / "open-docflow.sqlite")
os.environ["FASTSME_AUTH_DB"] = str(SCRATCH / "fastsme-accounts.sqlite")
os.environ["DOCFLOW_UPLOAD_DIR"] = str(SCRATCH / "uploads")
os.environ["DOCFLOW_SECRET"] = "dev-check-secret-key"

EMAIL = os.environ.get("DOCFLOW_ADMIN_EMAIL", "admin@docflow.example")
PASSWORD = os.environ.get("DOCFLOW_ADMIN_PASSWORD", "DocFlow2026$")
NEW_EMAIL = "tester@docflow.example"
NEW_PASSWORD = "TesterPass2026$"
ROUTES = ["/", "/documents", "/upload", "/stats"]

failures = []


def check(name, ok, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"{tag} {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    from starlette.testclient import TestClient

    import app as web  # import 即建表 + 播种文档类型 + 播种演示账号

    # 少量样本数据，够验证列表/详情/流转即可
    from data.generate_sample import generate_documents
    generate_documents(12)

    from src.models import Document, get_session
    session = get_session()
    try:
        doc = session.query(Document).filter(Document.status == "gautas").first()
        doc_id = doc.id if doc else session.query(Document).first().id
        doc_status = doc.status if doc else "gautas"
        total_docs = session.query(Document).count()
    finally:
        session.close()
    check("样本数据已播种", total_docs >= 12, f"documents={total_docs}")

    c = TestClient(web.app, follow_redirects=False)

    r = c.get("/")
    check("未登录 GET / 跳转登录页", r.status_code == 303 and r.headers.get("location") == "/login",
          f"status={r.status_code} location={r.headers.get('location')}")

    r = c.get("/documents")
    check("未登录 GET /documents 跳转登录页", r.status_code == 303,
          f"status={r.status_code}")

    r = c.get("/login")
    ok = r.status_code == 200 and "auth-overlay" in r.text and "Use demo account" in r.text
    check("GET /login 含账号弹窗与演示按钮", ok, f"status={r.status_code}")

    r = c.post("/auth/local/login", data={"email": EMAIL, "password": "wrong-password"})
    check("错误口令登录被拒 401", r.status_code == 401, f"status={r.status_code}")

    r = c.post("/auth/local/register",
               data={"name": "Tester", "email": NEW_EMAIL, "password": NEW_PASSWORD})
    check("注册新账号成功", r.status_code == 200, f"status={r.status_code} body={r.text[:120]}")

    r = c.post("/auth/local/login", data={"email": NEW_EMAIL, "password": NEW_PASSWORD})
    ok = r.status_code == 200
    if ok:
        try:
            ok = json.loads(r.text).get("redirect") == "/"
        except Exception:
            ok = False
    check("新注册账号可直接登录", ok, f"status={r.status_code}")

    r = c.get("/logout")
    check("GET /logout 跳转登录页", r.status_code == 303, f"status={r.status_code}")

    r = c.get("/")
    check("登出后 GET / 再次跳转登录页", r.status_code == 303, f"status={r.status_code}")

    r = c.post("/auth/local/login", data={"email": EMAIL, "password": PASSWORD})
    check("演示账号登录成功", r.status_code == 200, f"status={r.status_code} body={r.text[:120]}")

    for route in ROUTES:
        r = c.get(route)
        check(f"登录态 GET {route}", r.status_code == 200, f"status={r.status_code}")

    r = c.get(f"/documents/{doc_id}")
    check(f"登录态 GET /documents/{doc_id}", r.status_code == 200, f"status={r.status_code}")

    r = c.get("/documents?status=gautas&q=")
    check("文档筛选查询", r.status_code == 200, f"status={r.status_code}")

    target = "perziurimas" if doc_status == "gautas" else "patvirtintas"
    r = c.post(f"/documents/{doc_id}/transition",
               data={"to_status": target, "actor": "Dev Check", "comment": "gate"})
    check("状态流转成功", r.status_code == 200 and "flash-success" in r.text,
          f"status={r.status_code} body={r.text[:120]}")

    r = c.post(f"/documents/{doc_id}/transition",
               data={"to_status": target, "actor": "", "comment": ""})
    check("空执行人被拒", r.status_code == 200 and "flash-error" in r.text,
          f"status={r.status_code}")

    print()
    if failures:
        print(f"[RESULT] {len(failures)} 项失败: {', '.join(failures)}")
        return 1
    print("[RESULT] 全部通过")
    return 0


if __name__ == "__main__":
    code = 1
    try:
        code = main()
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    sys.exit(code)
