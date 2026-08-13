# -*- coding: utf-8 -*-
"""dev_check.py — 02-TrafficData 一键质量门禁（测试/调试/检查/验证）

进程内 TestClient 验证，不占端口、不弹窗口：
  1. 导入桌面壳 build_app()：装配 src-layout 包 + 生成合成数据 + 接线离线 plotly
  2. 六个看板页面全部可达            -> 200
  3. 本地 plotly.min.js 可被静态路由取到 -> 200 且体积合理
  4. 首页确实引用本地 js、不再指向 cdn.plot.ly（离线可用的实质判据）
  5. 合成数据表非空（zones / od / speed / journey / gps）

全部通过 exit 0；任一失败 exit 1（供 CI / 打包前门禁串联）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

failures = []


def check(name, ok, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"{tag} {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    import main as shell  # 导入副作用：插入 src/ 到 sys.path、chdir 到项目根

    application = shell.build_app()

    from starlette.testclient import TestClient

    c = TestClient(application)

    for route in ["/", "/od", "/speed", "/journey", "/map", "/sources"]:
        r = c.get(route)
        check(f"GET {route}", r.status_code == 200, f"status={r.status_code}")

    # 本地 plotly.js（离线图表的关键）
    r = c.get("/vendor/plotly.min.js")
    ok = r.status_code == 200 and len(r.content) > 1_000_000
    check(
        "GET /vendor/plotly.min.js",
        ok,
        f"status={r.status_code}, size={len(r.content) / 1048576:.1f}MB",
    )

    home = c.get("/").text
    check("首页引用本地 plotly.js", "/vendor/plotly.min.js" in home)
    check("首页不再依赖 cdn.plot.ly", "cdn.plot.ly" not in home)

    # 合成数据完整性
    from devon_traffic.data import get_bundle

    bundle = get_bundle()
    for key in ["zones", "od", "speed", "journey", "gps"]:
        n = len(bundle[key])
        check(f"合成数据 {key} 非空", n > 0, f"{n} rows")

    print()
    if failures:
        print(f"[GATE] 未通过：{len(failures)} 项失败 -> {failures}")
        sys.exit(1)
    print("[GATE] 全部通过，可交付/可打包")
    sys.exit(0)


if __name__ == "__main__":
    main()
