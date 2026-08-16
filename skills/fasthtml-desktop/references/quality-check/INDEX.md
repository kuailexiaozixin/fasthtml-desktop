# 质量检查与验证（目录）

> 本目录由原单文件 `08-quality-check.md` 拆分而来，内容**完整保留、未删改**。
> **该原文件 `08-quality-check.md` 已拆分删除（当前不存在）**，拆分为 4 个子文件（01-static-code-checks / 02-ui-audit / 03-route-hygiene / 04-smoke-and-delivery），原文内容**完整保留、未删改**，未保留独立 .bak 备份。
> **`05-ui-verification-details.md` 为拆分后新增**（pywebview 导入/质检/截图细节），不在 08 拆分之列。SKILL.md 质量门禁三阶段已分别链接到 01/02/03/04/05（阶段一→01、阶段二 ui_audit→02 / 质检与自动化→05、阶段三路由→03 / 冒烟→04）。

## 章节导航

| 子文件 | 内容范围 | 关键锚点 |
| --- | --- | --- |
| `01-static-code-checks.md` | 代码检查流程总览；语法门禁、修改后导入测试、pytest 门禁、Ruff、运行验证、UI 反模式（§4.1） | §1 / §1b / §1.5 / §2 / §3 / §4 / §4.1 |
| `02-ui-audit.md` | `ui_audit.py` 13 条禁令的纯 Python 实现；产品 UI 专用检查（§4.2）、AI Slop 测试（§4.3）、通用设计规则自检（§4.4）、a11y CSS（§4.4.1）、路由卫生静态检查（§4.5） | §4.2 / §4.3 / §4.4 / §4.4.1 / §4.5 |
| `03-route-hygiene.md` | 路由卫生实战：`products.py` / `app.py` 示例、生成指向路由的 URL、未出现在 `ar.rt_funcs` 的处理程序、前端→后端链路校验（§4.6） | §4.6 |
| `04-smoke-and-delivery.md` | 冒烟测试门禁（HTTP / 业务路径 / EXE 窗口 / HTML 结构 / UI 视觉质检 / 进程退出 / CI 无头编排）；打包前检查清单；发布前自检（统一 release_gate，P6） | 测试项一~七 / 测试项五 / 5.0 / P2 / P6 |
| `05-ui-verification-details.md` | pywebview 导入与启动、质检脚本用法（`ui_window_verify.py` / `ui_automate.py` / `ui_audit.py` / `ui_headless_verify.py`）、DOM 断言检查能力（重叠检测/对比度/溢出）、像素截图技术要点 | — |
| _(脚本)_ `scripts/ui_window_verify.py` | **pywebview 原生窗口质检**：直接驱动应用所在 WebView2 窗口，`evaluate_js` 读 DOM 计算样式做机器断言；截图可选（有显示器时 `CoreWebView2.CapturePreviewAsync`，无显示器时 `evaluate_js` + html2canvas 渲染 canvas 导出 PNG，库随技能离线分发）。重叠/对比度计算已加「被裁剪元素守卫」（`isClipped()`，排除可滚动容器内滚出可视区导致的假重叠误报）。实测要点与局限见 `SKILL.md` 上文「正确路径」段落及脚本内文档字符串 | 界面门禁 / 原生窗口 |
| _(脚本)_ `scripts/ui_automate.py` | **pywebview 原生 UI 自动化**：在真实渲染的 DOM 上执行声明式步骤（click / type / wait / assert_visible / assert_text / assert_attr / assert_not / assert_count_gt / snapshot / navigate），零额外浏览器、零浏览器授权。支持 JSON 步骤文件或内置 demo 模式（`--demo`）。适用于验证按钮交互、表单输入、状态切换、导航流程等 UI 行为正确性 | UI 交互自动化 / 原生窗口 |

## 跨文件引用说明

- 其它技能文档中形如 `08-quality-check.md §4.5` 的引用（该原文件已拆分删除），已统一改写为对应子文件：
  - §4.4.1 / §4.5 → `02-ui-audit.md`
  - §4.6 → `03-route-hygiene.md`
  - 测试项五 / 5.0 / P2 / P6 / 业务路径验证 → `04-smoke-and-delivery.md`

## 原文件行号 ↔ 子文件对照

| 原行号 | 子文件 |
| --- | --- |
| 1–81 | `01-static-code-checks.md` |
| 82–226 | `02-ui-audit.md` |
| 227–318 | `03-route-hygiene.md` |
| 319–633 | `04-smoke-and-delivery.md` |
