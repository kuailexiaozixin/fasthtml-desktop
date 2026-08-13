# -*- coding: utf-8 -*-
"""claudette 兼容性启动包装（07-genui-weather 桌面壳的一部分，不触及上游 genUI 业务代码）。

问题背景
--------
claudette 0.3.14 的 ``Client.structured`` 在传入 **2 个及以上工具** 时，
内部执行 ``ns = mk_ns(*tools)`` —— 但 ``mk_ns(fs)`` 只接受 **1 个** 位置参数，
于是抛 ``TypeError: mk_ns() takes 1 positional argument but N were given``。
genUI 的 ``your_color`` demo 恰好传了 2 个工具（generate_response /
generate_finish_response），因此触发该 bug；而 weather / hal9000 只传 1 个工具，
不触发，所以此前一直“正常”。

修复方式
--------
把 ``mk_ns`` 包成可变参数版本（兼容 单值 / 列表 / dict 三种既有调用形态），
再交给原实现。修复在 uvicorn 子进程启动时一次性注入，**不修改全局 site-packages**，
也不修改任何上游 genUI 代码。

随后等价于 ``python -m uvicorn main:app --app-dir <demo>``，保留原壳的
``reload=False``（避免 fork 残留）、端口 / 静态资源相对路径等语义。
"""
import sys
import claudette.core as _cc

try:
    import toolslm.funccall as _tfc
except Exception:
    _tfc = None

_orig_mk_ns = _cc.mk_ns


def _mk_ns_variadic(*fs):
    # structured() 调用 mk_ns(*tools)：fs 为工具元组
    if len(fs) == 1:
        return _orig_mk_ns(fs[0])
    return _orig_mk_ns(list(fs))


# 同时修正 claudette 与 toolslm 两个命名空间里指向同一函数的绑定
_cc.mk_ns = _mk_ns_variadic
if _tfc is not None:
    _tfc.mk_ns = _mk_ns_variadic

# 等价于 `python -m uvicorn main:app ...`（保留 reload=False 等默认语义）
from uvicorn.main import main
sys.argv = ["uvicorn", "main:app", *sys.argv[1:]]
main()
