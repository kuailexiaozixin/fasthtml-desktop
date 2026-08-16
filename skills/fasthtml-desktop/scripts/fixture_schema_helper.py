#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fixture_schema_helper.py — 测试夹具 schema 对齐助手（fasthtml-desktop）

问题背景：pytest fixture 凭印象写 insert 字典，引用了 db 模型不存在的列
（如 Expense.subject_code / Organization.code），导致整批测试静默失败（fixture rot）。

本模块提供**可复用断言**：把 fixture 里的 insert 字典键集合，与 db 模型真实列
做差集，任何不存在的列立即报错。属于测试收集/运行时契约，从根上防止 E 类问题。

用法（在项目的 conftest.py 或 test_*.py 中）：
    from fixture_schema_helper import assert_fixture_matches_schema
    # db 是 fasthite/fastlite 的数据库对象，表通过 db.t 访问
    assert_fixture_matches_schema(db.t.expense, [{"subject_id":1,"amount":10}])

也可在 pytest 收集阶段批量校验多个 fixture（见 check_fixture_module）。
"""

import importlib
import inspect
from pathlib import Path
from types import ModuleType


def _table_columns(table) -> set[str]:
    """返回 fasthite/fastlite 表的真实列名集合。

    兼容三种取列方式：
      - table.__columns__ / table.columns（fastlite Table 对象）
      - 直接是 dataclass/pydantic 的 __dataclass_fields__ / model_fields
      - 退回 inspect 不到时的空集合（调用方需自行保证）
    """
    cols: set[str] = set()
    for attr in ("__columns__", "columns"):
        v = getattr(table, attr, None)
        if v:
            cols |= {c if isinstance(c, str) else getattr(c, "name", str(c)) for c in v}
    # dataclass
    dc = getattr(table, "__dataclass_fields__", None)
    if dc:
        cols |= set(dc.keys())
    # pydantic v2
    mf = getattr(table, "model_fields", None)
    if mf:
        cols |= set(mf.keys())
    # 真实列对象可能带 .name
    cols = {c if isinstance(c, str) else getattr(c, "name", str(c)) for c in cols}
    return {c for c in cols if c and not c.startswith("_")}


def assert_fixture_matches_schema(table, rows: list[dict], table_name: str = "") -> None:
    """断言 fixture 的 insert 字典键，全部存在于 table 真实列中。

    任一未知列 → 抛出 AssertionError，列出漂移的列与可用列，便于立即修正。
    """
    if not rows:
        return
    real = _table_columns(table)
    if not real:
        # 无法推断列时不强行失败（避免误伤），但给出告警
        import warnings
        warnings.warn(f"无法从 {table_name or table!r} 推断列，跳过 fixture 对齐校验")
        return
    unknown: set[str] = set()
    for r in rows:
        unknown |= (set(r.keys()) - real)
    if unknown:
        raise AssertionError(
            f"[fixture schema drift] 表 '{table_name or getattr(table,'__name__','?')}' "
            f"的 fixture 引用了不存在的列: {sorted(unknown)}\n"
            f"  真实列: {sorted(real)}"
        )


def check_fixture_module(db_module: ModuleType,
                          fixture_module: ModuleType,
                          mapping: dict[str, str]) -> list[str]:
    """批量校验：fixture_module 中每个返回 list[dict] 的函数，对应 db_module 的某张表。

    mapping: { fixture函数名: "db.t.表名" 的点路径 }
    返回漂移信息列表（空=全部对齐）。
    """
    import importlib

    errors: list[str] = []
    for fn_name, table_path in mapping.items():
        fn = getattr(fixture_module, fn_name, None)
        if not callable(fn):
            errors.append(f"fixture 函数缺失: {fn_name}")
            continue
        try:
            rows = fn()
        except Exception as e:  # noqa: BLE001
            errors.append(f"调用 {fn_name} 失败: {e}")
            continue
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            continue  # 非 insert 字典，跳过
        # 解析 db.t.xxx
        obj = db_module
        for part in table_path.split("."):
            obj = getattr(obj, part, None)
            if obj is None:
                errors.append(f"表路径不存在: {table_path}")
                break
        if obj is None:
            continue
        try:
            assert_fixture_matches_schema(obj, rows, table_path)
        except AssertionError as e:
            errors.append(str(e))
    return errors


if __name__ == "__main__":
    # 自测：用一份"错误 fixture"验证能抓到漂移
    import types

    class FakeTable:
        __columns__ = ["id", "subject_id", "person_id", "amount"]

    bad_rows = [{"subject_id": 1, "amount": 10, "subject_code": "X"}]  # subject_code 不存在
    try:
        assert_fixture_matches_schema(FakeTable(), bad_rows, "expense")
        print("SELF-TEST FAIL: 未抓到漂移")
        raise SystemExit(1)
    except AssertionError as e:
        print("SELF-TEST OK: 抓到 fixture schema 漂移 ->")
        print("  " + str(e).splitlines()[0])
    # 正确 fixture 应通过
    ok_rows = [{"subject_id": 1, "amount": 10}]
    assert_fixture_matches_schema(FakeTable(), ok_rows, "expense")
    print("SELF-TEST OK: 合法 fixture 通过校验")
