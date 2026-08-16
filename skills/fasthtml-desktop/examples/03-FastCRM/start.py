# -*- coding: utf-8 -*-
"""start.py — FastCRM 一键启动脚本（开发/测试/调试/验证统一入口）

用法：
  python start.py            # 首次自动建 .venv + 装依赖，然后桌面启动
  python start.py --server   # 仅 HTTP 服务（无窗口，适合服务器/调试）
  python start.py --check    # 运行 dev_check.py 一键质量门禁（测试/检查/验证）
  python start.py --reseed   # 删除本地数据库，下次启动重新播种合成数据
  python start.py --port N   # 指定端口

开发流程（技能约定）：改代码 -> python start.py --check 全绿 -> 手动跑
python start.py 目检 -> 确认可交付后再打包 EXE。
"""
import os, sys, subprocess, venv
from pathlib import Path

HERE = Path(__file__).parent
VENV = HERE / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_env():
    if not PY.exists():
        print("[SETUP] 创建虚拟环境 .venv ...")
        venv.create(VENV, with_pip=True)
        print("[SETUP] 安装依赖（requirements.txt + pywebview）...")
        subprocess.check_call([str(PY), "-m", "pip", "install", "-q",
                               "-r", str(HERE / "requirements.txt"), "pywebview"])
    else:
        # 幂等补装（requirements 变化时仍能对齐）
        subprocess.check_call([str(PY), "-m", "pip", "install", "-q",
                               "-r", str(HERE / "requirements.txt"), "pywebview"])


def main():
    args = sys.argv[1:]
    ensure_env()

    if "--reseed" in args:
        db_file = HERE / "fastcrm.sqlite"
        if db_file.exists():
            db_file.unlink()
            print(f"[OK] 已删除 {db_file.name}，下次启动将重新播种")
        else:
            print("[INFO] 数据库不存在，无需重置")
        args.remove("--reseed")
        if not args:
            return

    env = dict(os.environ)
    if "--port" in args:
        i = args.index("--port")
        env["PORT"] = args[i + 1]

    if "--check" in args:
        print("[GATE] 运行一键质量门禁 dev_check.py ...")
        r = subprocess.run([str(PY), str(HERE / "dev_check.py")], cwd=HERE, env=env)
        sys.exit(r.returncode)

    if "--server" in args:
        env["SERVER_ONLY"] = "1"

    r = subprocess.run([str(PY), str(HERE / "main.py")], cwd=HERE, env=env)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
