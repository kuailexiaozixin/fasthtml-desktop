# Debug —— 失败处理闭环（不是门禁）

回答「失败为什么发生、怎么修好」。任何 Check/Test 失败后进入本节，按「复现 → 定位 → 修复 → 回归 → 沉淀」闭环处理。

| 文件 | 职责 |
|------|------|
| `01-debug-discipline.md` | 调试总纲 + Prove-It 模式（先写复现测试）、Flaky 重复跑纪律、改后干净复测回路；排障沉淀指向 `../../../docs/troubleshooting.md` |

> **与 Check/Test 的区别**：Check 是静态关卡、Test 是动态验证，都是门禁；Debug 不是门禁，是门禁失败后的处理流程。绝不无测试修 bug、绝不「改了没验证」。

回到 [`../INDEX.md`](../INDEX.md) 总入口。
