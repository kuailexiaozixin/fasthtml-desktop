# 测试驱动开发（Test-Driven Development）

> 适用范围：fasthtml-desktop 技能自身的测试方法论。
> 定位：填补「业务逻辑单元/集成测试」缺口——现有质检（语法门禁、ruff、路由卫生、ui\_audit、pywebview 原生视觉质检、冒烟）覆盖的是打包/运行时/UI 层，**本文件补齐工作流 ⑥ 编码步骤缺失的测试文化**。
> 原则：本文件只写 fasthtml-desktop 自己的测试主题，不复用、不交叉引用任何外部 TDD 技能原文。

---

## 0. 为什么需要 TDD

fasthtml-desktop 的交付物是**本地桌面 EXE**：FastHTML 在本地起一个 HTTP 服务，pywebview 套上原生窗口。它的质量风险有两类：

1. **逻辑错**（算错、解析错、归档错、边界错）—— 现有质检**完全看不见**，只能靠人肉点。
2. **界面坏**（重叠、裸英文、对比度、需真实渲染才能发现的视觉问题）—— 已有 `ui_window_verify.py` / `ui_audit.py` 覆盖。

TDD 解决第 1 类：在写实现前先写会失败的测试，把「逻辑对不对」变成**可重复、可进 CI、零 GUI 依赖**的断言。

---

## 1. 测试类型全景与归属（回答「还需要哪些测试」）

下表列出常见的测试类型，明确**哪些由本技能新增（pytest）、哪些已由现有机制承担、哪些归人类伙伴**。这是把外部 TDD 思想内化后的落地映射，不是另起炉灶。

| 测试类型 | 是否必需 | fasthtml-desktop 落地方式 | 与现有机制的关系 |
|----------|----------|---------------------------|------------------|
| **单元测试 Unit** | ✅ 必需（主体 ~80%） | `pytest` 测纯逻辑：`stock_validator` / `organizer` / `excel_processor.merge` / `config` 解析 / 日期处理。无 I/O、无网络，毫秒级 | **新增**（pytest） |
| **集成测试 Integration** | ✅ 必需 | `starlette.testclient.TestClient` 对路由/API 做 HTTP 级断言，跨「HTTP 边界 / Excel 读写 / 路由调用链」。无需端口、无需浏览器 | **新增**（pytest） |
| **功能测试 Functional** | ✅ 需要，并入集成层 | 「单接口给定输入的行为」= 集成测试的一个子集，不单列；用 TestClient 直接断言某路由的返回 | 并入集成测试 |
| **业务流程测试 Business-process** | ✅ 需要 | 集成层内**串联多路由的旅程测试**（搜索 → 选择 → 下载 → 校验文件）；关键 UI 路径再用 pywebview 原生视觉质检守护 | 集成测试 + 原生窗口 |
| **数据驱动测试 Data-driven** | ✅ 强烈建议（原两 TDD 技能都漏了） | `pytest.mark.parametrize` 对样本数据集参数化：各交易所前缀、各财报格式、空值、超长字段、异常码 | **新增**（pytest） |
| **端到端测试 E2E** | ✅ 需要（双层落地，见 §11） | fasthtml-desktop **不建浏览器点击式 E2E**（桌面窗口 + 沙箱无显示 + 极 flaky）；改用双层真 E2E：① **业务路径 E2E**——对真实 EXE 发 HTTP 走完整业务流（搜索→选择→下载→校验文件产物，跨进程、含 onefile/runtime 全链路）；② **视觉 E2E**——pywebview 原生窗口做 DOM 断言式机器视觉（图标/重叠/对比度/空白页/视觉回归），无显示器时回退 html2canvas 无头截图。两层都打真实产物、都无头友好（视觉层仅需能创建窗口） | **已有**（业务路径 + 原生视觉，见 §11） |
| **冒烟测试 Smoke** | ✅ 必需（打包门禁） | EXE 启动健全性：应用能否启动、关键 HTTP 端点是否 200、窗口句柄是否创建（见 `packaging/05-smoke-test.md` 的 `scripts/smoke_test.py`）。**非 TDD 制品**，属打包/分发层门禁，只回答「能不能跑起来」、不验证业务正确性 | **已有**（smoke_test.py） |
| **UI 自动化测试 UI-automation** | ✅ 必需且已实现 | `ui_window_verify.py`（pywebview 原生窗口：图标真实图形/重叠/溢出/对比度/空白页）+ `ui_audit.py`（HTML 结构）。`pytest` **绝不写脆弱的 DOM/渲染单测**——那是 `ui_window_verify.py` 的职责 | **已有**（原生窗口/HTML） |
| **回归测试 Regression** | ✅ 必需，作为「门禁纪律」 | 不是独立测试类型，而是**每次改动后跑全量 `pytest` + 全量 HTML/视觉审计，非零即阻断**。把「防回归」从隐含好处变成显式门禁 | 纪律 + 既有测试 |
| **用户/验收测试 User-acceptance** | ✅ 必需，但**不属 agent 测试套件** | 人类伙伴在浏览器/EXE 手测；agent 提供 pywebview 截图 + 冒烟报告作为证据，**不把人工验收伪装成自动化** | 人类职责 + agent 证据 |

> **结论**：单元、集成（含功能/业务流程）、数据驱动、回归由本文件新增（pytest）；E2E（业务路径 + 原生视觉）、UI 自动化、冒烟已由现有机制承担（引用而非重复）；用户验收归人类。各层职责清晰、无重叠（见 §7）。

> **概念澄清：冒烟测试 ≠ 端到端测试（E2E）**
> 二者在「覆盖深度 / 反馈速度 / 依赖」上完全不同，不可混为一谈：
> - **冒烟测试（Smoke）**：最浅的**启动健全性**检查——应用能否启动、关键 HTTP 端点是否返回 200、窗口句柄是否创建成功。只回答「能不能跑起来」，**不验证业务正确性**，秒级、零界面依赖。
> - **端到端测试（E2E）**：最深的**用户旅程**验证——走完整业务流程（如「搜索 → 选择 → 下载 → 校验文件」），断言最终业务结果。本技能不靠 UI 点击驱动，而是用**业务路径 E2E + 视觉 E2E** 两层落地，回答「用户能不能真正用起来」。
> - **fasthtml-desktop 的 E2E 落地**：E2E 由两层真验证承担——**业务路径 E2E**（对真实 EXE 发 HTTP 走完整业务流、断言落盘产物）覆盖「流程走得通」，**视觉 E2E**（pywebview 原生窗口 DOM 断言 + 可选 html2canvas 无头截图）覆盖「界面真的、没坏」。冒烟只管启动健全性，不替代 E2E；浏览器点击式 E2E 因桌面窗口特性与 flaky 风险**有意不建**（详见 §11）。

---

## 2. Red-Green-Refactor（适配 Python / pytest）

```
RED     写失败测试（src/<pkg>/tests/test_xxx.py）→ 亲眼看到它失败（原因=功能缺失，非拼写错）
  ↓
GREEN   写最小实现使其通过，不过度设计（YAGNI）
  ↓
REFACTOR  保持绿，清理重复、改善命名、提取 helper
  ↓
  回到 RED，下一个行为
```

- **RED 必须验证失败**：`uv run pytest tests/test_xxx.py::test_yyy -q`，确认失败且失败原因正确（功能缺失，不是 import 错）。
- **GREEN 最小实现**：只写让测试通过的最少代码，不要顺手加功能/重构。
- **REFACTOR 保持绿**：每次小改后重跑测试，确认仍全绿。

### 示例（单元，先 RED）

```python
# tests/test_stock_validator.py  （RED 阶段）
from src.announcement_downloader.stock_validator import validate

def test_szse_prefix_matches():
    vr = validate("000001", "SZSE")
    assert vr.is_valid is True
    assert vr.detected_market == "SZSE"

def test_wrong_market_detected():
    # 600519 是上交所，却选了深交所
    vr = validate("600519", "SZSE")
    assert vr.is_valid is False
    assert vr.detected_market == "SSE"
```

> 先跑：看到 `test_wrong_market_detected` 失败（因为实现还没写 / 规则还没覆盖），再写 `validate` 的最小实现使其通过。

---

## 3. fasthtml 测试金字塔（映射到现有分层）

```
E2E / 视觉  (~5%)   → 业务路径 E2E（真实 EXE + HTTP 业务流）+ 视觉 E2E（ui_window_verify.py，pywebview 原生窗口，驱动真实窗口）
     ▲
集成 (~15%)        → 新增：ASGI TestClient 跑路由/业务流（HTTP 级，无需端口/浏览器）
     ▲
单元 (~80%)        → 新增：纯逻辑（validator / organizer / excel 变换 / config 解析）
```

**测试尺寸（资源模型）**
- **Small（单元）**：单进程、无 I/O、无网络。纯函数。`pytest`，毫秒级。占绝大多数。
- **Medium（集成）**：跨边界（HTTP API、Excel 读写、路由链）。用 TestClient / 临时目录。
- **Large（E2E）**：两层落地——① 业务路径 E2E（真实 EXE + HTTP 业务流，断言落盘产物）；② 视觉 E2E（pywebview 原生窗口，DOM 断言 + 可选 html2canvas 无头截图）。**不建浏览器点击式 E2E**（flaky + 桌面窗口特性）；冒烟只管启动健全性，详见 §11。

### 决策树
```
纯逻辑、无副作用？                → 单元测试（small）
跨边界（API / 数据库 / 文件）？    → 集成测试（medium，TestClient）
关键用户流必须端到端？            → E2E（业务路径 + 原生视觉，限关键路径，见 §11）
一批同类数据要覆盖多种情况？      → 数据驱动（parametrize）
```

---

## 4. 关键技术：Starlette TestClient（无需起端口 / 浏览器）

fasthtml 基于 Starlette（ASGI）。用 `starlette.testclient.TestClient` 直接对应用对象发 HTTP 请求，**不需要监听端口、不需要真实浏览器**，可重复、可进 CI。

```python
# tests/test_api_integration.py
import pytest
from starlette.testclient import TestClient

pytest.importorskip("fasthtml")  # 无 fasthtml 运行环境时跳过，不报错

from src.announcement_downloader.app import app

def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

> 这把 `quality-check/04-smoke-and-delivery.md` 里「启动服务后 `requests.get(http://127.0.0.1:PORT)`」的运行时检查，升级为**可重复、可进 CI、零 GUI 依赖**的集成测试。
> 注意：导入 `app` 会触发模块级副作用（`ensure_dir`、调度器启动、`ApiClient()` 构造）。这些在示例自身 venv 内正常；跨环境用 `pytest.importorskip("fasthtml")` 兜底。

---

## 5. 数据驱动测试（@parametrize）

这两个示例的本质是「对一批记录做同样处理」。**数据驱动**是高性价比实践，两个外部 TDD 技能都未提及，这里显式补上。

```python
import pytest
from src.announcement_downloader.stock_validator import MARKET_CODE_RULES, validate

# 每个市场取一个代表前缀 + 一个非法前缀，一次性覆盖全部规则
CASES = [
    ("000001", "SZSE", True),   # 深交所主板
    ("300750", "SZSE", True),   # 创业板
    ("600519", "SSE", True),    # 上交所主板
    ("688981", "SSE", True),    # 科创板
    ("920123", "BSE", True),    # 北交所
    ("600519", "SZSE", False),  # 选错市场 → 检测出来
    ("abcdef", "SZSE", False),  # 非数字
    ("", "SZSE", True),         # 空代码 = 全文搜索
]

@pytest.mark.parametrize("code,market,expect_valid", CASES)
def test_validate_parametrized(code, market, expect_valid):
    vr = validate(code, market)
    assert vr.is_valid is expect_valid
```

真实业务数据（公告样本、财报样本）应落在 `tests/fixtures/` 下，参数化引用，避免测试逻辑里塞死数据。

---

## 6. Mock 层级与反模式

**Mock 优先级（最推荐 → 最不推荐）**
```
1. 真实实现   → 置信度最高，能抓真 bug
2. Fake       → 依赖的内存版（如内存版 DB）
3. Stub       → 返回 canned data，无行为
4. Mock(交互) → 仅验证调用，慎用
```
- HTTP 外部依赖（如 `api.query` 真会打网）用 `respx` 拦截，**禁止 mock DOM / 渲染层**（那是 `ui_window_verify.py` 的职责）。
- 仅在慢 / 非确定 / 副作用不可控时用 mock。

**反模式（来自「测真实行为」纪律，Python 化）**
| 反模式 | 后果 | 修法 |
|--------|------|------|
| 测 mock 行为而非真实行为 | 测试通过但生产坏 | 测真实组件，或解除 mock |
| 给生产类加 test-only 方法 | 污染生产、误调用危险 | 移到 test 工具函数 |
| 不懂依赖就 mock | 破坏了测试依赖的副作用 | 先用真实实现跑一遍，再在正确层级最小化 mock |
| 不完整 mock 结构 | 测试通过但集成失败 | mock 要镜像真实响应完整字段 |
| 把集成测试当事后补 | 实现完才想起测 | TDD：测试先于实现 |
| 过度 mock | 测试绿但生产崩 | 优先真实实现 > fake > stub > mock |

---

## 7. 与各门禁的关系（互补不冲突）

```
业务逻辑正确性  → pytest（单元 + 集成 + 数据驱动）        【本文件新增】
HTML 结构完整    → scripts/ui_headless_verify.py          【已有，quality-check/04-smoke-and-delivery】
视觉 / 运行时    → scripts/ui_window_verify.py（pywebview 原生）【已有，quality-check/04-smoke-and-delivery】
打包后可分发性   → scripts/smoke_test.py（EXE 冒烟）       【已有，packaging/05】
```

职责清晰、无重叠：**pytest 管「逻辑对不对」，原生窗口/HTML 管「界面坏不坏」，冒烟管「EXE 跑不跑得起来」**。`pytest` 绝不写脆弱的 DOM/渲染单测（那属于 `ui_window_verify.py` 层）。

---

## 8. Prove-It 模式（Bug 修复）

收到 bug → **先写复现测试（必失败）→ 实现修复 → 测试通过 → 跑全量防回归**。**绝不无测试修 bug。**

```
bug 报告
  ↓
写复现测试（应当 FAIL）
  ↓
测试 FAIL（确认 bug 存在）
  ↓
实现修复
  ↓
测试 PASS（证明修好）
  ↓
跑全量 pytest + 原生窗口/HTML 审计（无回归）
```

复杂 bug：派 subagent 写复现测试（不含修复知识，测试更健壮），主 agent 验证失败后实现修复。

---

## 9. 回归门禁纪律（每次改动必跑）

回归不是一种测试类型，而是**纪律**：任何代码改动（新增功能、修 bug、重构）后，必须：

1. `uv run pytest` —— 单元 + 集成 + 数据驱动全绿；
2. `python scripts/ui_audit.py http://127.0.0.1:PORT` —— HTML 结构验证（headless，禁止跳过）；
3. 有窗口时 `python scripts/ui_window_verify.py ...` —— pywebview 原生窗口视觉质检；
4. 打包前再跑一遍 pytest（非零退出禁止发布）。

任一步非零退出 = 阻断发布。

### 9.1 Flaky 重复跑纪律（来自 playwright flaky-tests）

为让「全绿」结论可信，关键集成测试可加重复跑兜底（来自 playwright 的 `--repeat-each` / 重试思想）：

- 安装 `pytest-rerunfailures`（或 `pytest-repeat`）：在示例 `pyproject.toml` 的 dev 依赖组追加；
- 关键测试加 `@pytest.mark.flaky(reruns=3)`（网络 / 文件类易抖动的集成测试）；
- CI 层对整轮加 `--reruns` 或作业重试；
- 重复跑**只能兜底偶发环境抖动**，不能掩盖真实失败；若某测试频繁 flaky，必须修根因（竞态 / 未隔离状态 / 时间依赖）。

> 与 §7 分层一致：重复跑只用于 pytest 逻辑层；UI / 视觉层由 `ui_window_verify.py` 在窗口就绪后做断言兜底 flaky，不靠重复跑掩盖渲染时序问题。

### 9.2 改后干净复测回路（防「改了但没生效」假象）

> 典型踩坑：改了某路由模块的 CSS 常量，但 curl 首页反复命中**编辑前启动、仍占着端口的旧 uvicorn**，导致反复误判「修改无效」。

任何「改服务端文件后复测 UI」的流程，必须先确保**服务端真的加载了新代码**：

1. `netstat -ano | findstr :<端口>` 找出占用 dev 端口的 PID，`taskkill /F /PID <pid>` 杀掉旧进程；
2. `find src -name __pycache__ -exec rm -rf {} +` 清掉字节码缓存（否则 uvicorn 可能加载旧 `.pyc`）；
3. 用**全新端口**启动 uvicorn，避开残留绑定（旧进程未真正退出时会占着原端口，导致新进程绑定失败、curl 仍命中旧进程）；
4. **复测前先验证服务端内容**：`curl` 首页并 `grep` 确认下发的 CSS / 路由**已含新规则**，再跑原生窗口质检。第 4 步能根除「改了但没生效」的假象——大多数「改了没用」其实是命中了旧进程。

---

## 10. 示例种子测试与依赖（模板示范）

- `01-announcement-downloader/tests/`：补 `test_stock_validator.py`（各市场前缀 + 选错市场检测 + 空/非数字）、`test_organizer.py`（路径构建、公告 ID 提取、dry_run 清理）、`test_integration_api.py`（TestClient 测 `/api/v1/health`）。
- **`dev_check.py` 一键门禁（09~15 已落地，推荐直接抄）**：用 Starlette `TestClient` 在**进程内**跑「未登录拦截 → 错误口令拒绝 → 正确口令跳转 → 注册 → 业务路由遍历 → 演示数据播种计数」，全绿才允许交付/打包。三条硬要求：① **`follow_redirects=False`**——否则 303 被自动跟随成 200，未登录拦截会假绿；② 用**独立库文件**（如 `data/devcheck.sqlite`）跑，不污染用户数据；③ 复用桌面壳的 `build_app()` 而非另起一套装配，保证「测的就是跑的」。
- `pyproject.toml`：加 dev 依赖组 `pytest` / `respx` / `starlette`（用 `uv sync` 安装；`uv run pytest` 运行）。
- pytest 配置：`pythonpath = ["."]`（示例用 `src/` 命名空间包）、`testpaths = ["tests"]`。
- 示例 README 的「演示产出物」补一行：`tests/` 单元测试 + `dev_check.py` 门禁，遵循 `references/09-test-driven-development.md`。

---

## 11. 端到端测试（E2E）的 fasthtml-desktop 落地方式

E2E 要回答的是「用户能不能真正用起来」：从真实入口出发，走完业务流程，并断言最终业务结果与界面落地。桌面 EXE（pywebview 托管窗口）+ 沙箱无显示的环境，决定了**不采用脆弱的浏览器点击式 E2E（Selenium/Playwright 像素点击）**，而是用一套**无头友好、可门禁、可重复**的两层栈来落地真 E2E（对应 §3 金字塔 Large 层）：

### 11.1 业务路径 E2E（协议级 / 黑盒 HTTP）— 覆盖「流程走得通、产物对不对」

对**真实构建出的 EXE** 起一个子进程，用普通 HTTP 客户端把用户的完整旅程走一遍，**断言最终业务产物**，而不是只断言首页 200。这是最贴近 E2E 定义的层：真实服务 + 真实业务代码 + 真实文件输出，只是绕过 UI 点击。

落地：复用 `quality-check/04-smoke-and-delivery.md` 测试项二（关键业务路径验证），典型模式：

```python
import requests, subprocess, os

proc = subprocess.Popen([str(exe_path)])          # 启动真实 EXE
PORT = _wait_for_port(proc)                        # 动态发现端口（见 packaging/05-smoke-test）

# 1) 搜索
r1 = requests.post(f"http://127.0.0.1:{PORT}/search",
                   data={"market": "SZSE", "keyword": "000001",
                         "start_date": "2026-01-01", "end_date": "2026-07-17", "page": 1},
                   timeout=10)
assert r1.status_code == 200
assert "error" not in r1.text.lower() or "未找到" not in r1.text

# 2) 选择 + 3) 下载
r2 = requests.post(f"http://127.0.0.1:{PORT}/download", data={"id": picked_id}, timeout=30)
assert r2.status_code == 200
out = _download_path(r2)
assert os.path.exists(out) and os.path.getsize(out) > 0   # 4) 校验文件真的落盘

proc.terminate(); proc.wait(timeout=5)                    # 清理，释放端口
```

- **CI 友好**：纯 HTTP、零 GUI、零浏览器依赖，可在 Linux CI 无头跑。
- **与集成测试的区别**：集成测试用 `TestClient` 直连 `app` 对象（进程内、无网络栈）；业务路径 E2E 打的是**真实 EXE 暴露的真实端口**（跨进程、含打包/onefile/runtime 全链路），专门抓「打包后才有」的问题（端口冲突、`sys.frozen` 路径错、`--hidden-import` 漏扫、文件句柄占用）。
- **与业务流程集成测试配合**：多路由串联的「逻辑链」可先在集成层用 `TestClient` 以 TDD 写好（见 §1 业务流程行），E2E 再对**真实产物**做黑盒确认，两层互补。

### 11.2 视觉 E2E（pywebview 原生机器视觉）— 覆盖「界面真的、没坏」

业务路径 E2E 只验逻辑与产物，**看不见界面**。界面层的真实 E2E 用 **pywebview 原生窗口（`evaluate_js` 读真实渲染 DOM 几何 + 计算样式）**做机器视觉断言——这是用户实际看到的窗口，不靠人工截图、不依赖额外浏览器：

```bash
# 对真实窗口做机器视觉断言（窗口会话环境即可，无需浏览器授权）
python scripts/ui_window_verify.py \
  --url http://127.0.0.1:<PORT>/ \
  --out ui-screenshot.png
```

脚本自动断言（见 `quality-check/04-smoke-and-delivery.md` 测试项五）：图标真实图形、元素重叠、横向溢出、WCAG 对比度、空白页、视觉回归基线比对。退出码：`0` 通过（或仅 UX 提示）、`1` BAN 级阻断、`2` 环境错误（无法创建窗口）CI 跳过不阻断。

- **这层就是 UI 旅程的 E2E**：它驱动的是真实窗口（pywebview 原生）、真实 DOM 几何、真实渲染，等价于「打开应用、看界面」——只是用机器断言替代人眼与鼠标。
- **为何不做像素点击**：桌面 EXE 的窗口由 pywebview 托管、SPA 靠 htmx/surreal 局部刷新，像素点击式 E2E 慢且极 flaky；pywebview 原生 `evaluate_js` 直接读渲染后 DOM 几何 + 计算样式，更稳定、更轻（无需第二个浏览器、无需下载 Chromium、无需浏览器授权）。

### 11.3 与冒烟、集成的关系（明确边界）

| 层 | 覆盖范围 | 回答的问题 | 驱动对象 | 工具 | 无头 CI |
|----|----------|------------|----------|------|---------|
| 冒烟 Smoke | 启动健全性 | 能不能跑起来 | 真实 EXE 启动 | `smoke_test.py` | ✅ |
| 业务流程集成 | 进程内多路由链 | 逻辑链对不对 | `app` 对象（TestClient） | `pytest` | ✅ |
| **业务路径 E2E** | 跨进程真实业务流 | 流程走得通、产物对不对 | 真实 EXE + HTTP | HTTP 客户端 | ✅ |
| **视觉 E2E** | 真实窗口渲染状态 | 界面真的、没坏 | 真实 pywebview 窗口 | `ui_window_verify.py`（原生窗口） | ⚠️ 需能创建窗口 |

**结论**：fasthtml-desktop 的 E2E = **业务路径 E2E（协议级）+ 视觉 E2E（pywebview 原生）** 双层，二者都打**真实 EXE / 真实窗口**，且都无头友好（视觉层仅需能创建窗口，无显示器时回退 html2canvas 无头截图）。冒烟只管启动，不替代 E2E；浏览器点击式 E2E 因 flaky 与桌面窗口特性**有意不建**。

> **E2E 与 TDD 的关系**：E2E/视觉/冒烟属**质量门禁**，不由 red-green-refactor 循环驱动（见 §1 标注「非 TDD 制品」）；但其业务路径层本质是 HTTP 断言，**可**按需 test-first 编写。TDD 的主战场仍是单元/集成/数据驱动（§2–§5）。

