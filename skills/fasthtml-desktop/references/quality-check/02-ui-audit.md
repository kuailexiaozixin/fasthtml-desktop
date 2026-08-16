# ui_audit.py 核心检查函数 — 13 条禁令的纯 Python 实现
def check_absolute_bans(html: str) -> list[dict]:
    """检查 13 条绝对禁令，返回违规列表"""
    import re
    issues = []
    
    bans = [
        ("侧边色条边框", r"border-(left|right)\s*:\s*[^0;]+[^;]*color"),
        ("渐变文字", r"background-clip:\s*text"),
        ("毛玻璃默认装饰", r"backdrop-filter:\s*blur\("),
        ("英雄指标模板", r"\d+[\.\,]?\d*\s*(万|亿|%|K|M|B)"),  # 大数字+指标
        ("纯黑/纯灰", r"#[0]+\b|#[Ff]+[Ff]\b"),
        ("卡片嵌套卡片", r"<div[^>]*class="[^"]*card[^"]*"[^>]*>.*?<div[^>]*class="[^"]*card[^"]*""),
        ("过度圆角 ≥32px", r"border-radius:\s*(3[2-9]|[4-9]\d+)\s*px"),
        ("条纹对角线背景", r"repeating-linear-gradient"),
        ("网格装饰背景", r"linear-gradient.*\btransparent\b.*\btransparent\b.*#.*,"),
        ("自定义滚动条", r"::-webkit-scrollbar"),
        ("弹跳缓动", r"cubic-bezier\([^)]*[23]\.\)"),
        ("手绘 SVG", r"feTurbulence"),
        ("毛玻璃导航", r"backdrop-filter:\s*blur\(.*px\)|background.*rgba\(255,"),
    ]
    
    inline_style = re.findall(r'style="([^"]+)"', html, re.I)
    all_styles = ' '.join(inline_style)
    
    for name, pattern in bans:
        if re.search(pattern, all_styles, re.I):
            issues.append({"ban": name, "pattern": pattern, "severity": "FAIL"})
        else:
            issues.append({"ban": name, "passed": True})
    
    return issues
```

| 分类 | 禁令 | 检测要点 | 修复指引 |
|------|------|---------|---------|
| 边框 | 侧边色条边框 | `border-left`/`border-right` > 1px 的彩色装饰边框 | 改用全边框、背景色块、序号图标，或去掉 |
| 文字 | 渐变文字 | `background-clip: text` + 渐变背景 | 使用纯色，强调通过字重/字号实现 |
| 背景 | 毛玻璃默认装饰 | `backdrop-filter: blur()` 作为默认装饰 | 必须有明确的功能理由才用 |
| 布局 | 英雄指标模板 | 大数字+小标签+统计+渐变的大标题区 | 避免 SaaS 仪表盘模板化布局 |
| 布局 | 相同卡片网格 | 图标+标题+正文完全相同的卡片无限重复 | 差异化内容结构 |
| 排版 | 每个区块的角标 | 每个 section 上方小号大写字母+宽间距的 "ABOUT" "PROCESS" 等标签 | 仅在有意义的命名系统中使用 |
| 排版 | 数字序号标记 | 每个 section 上方 `01 · About / 02 · Process` 式序号 | 仅在实际有顺序关系的流程中使用 |
| 布局 | 文本溢出容器 | 长标题+大 clamp 比例在小屏溢出 | 每个断点测试标题，调整 clamp 最大值或重写文案 |
| 边框 | 鬼影卡片 | `border: 1px solid X` + `box-shadow: 0 Npx Mpx` 且 M ≥ 16px | 边框和阴影二选一，阴影 blur ≤ 8px |
| 圆角 | 过度圆角 | `border-radius` ≥ 32px 用于卡片/区块/输入框 | 卡片 12–16px；胶囊只用在标签/按钮 |
| 插图 | 手绘 SVG 插图 | `feTurbulence`/"sketch"/"doodle" 类 SVG 插图 | 无法渲染真实资源就不配图 |
| 背景 | 条纹对角线 | `repeating-linear-gradient()` 装饰条纹 | 去掉 |
| 背景 | 网格装饰背景 | CSS `linear-gradient` 模拟的双轴网格线 | 仅在画布/地图/测量工具场景使用 |

#### 4.2 产品 UI 专用检查（产品/工具类界面额外检查）

当界面类型为产品 UI（仪表盘、管理后台、设置面板、数据表格等），增加以下检查：

| # | 检查项 | 规则 | 验证方式 |
|---|--------|------|---------|
| 1 | 动效目的 | 装饰性动效应避免；动效必须传达状态变化 | 检查所有 transition/animation 是否有状态含义 |
| 2 | 组件一致性 | 相同功能的组件在不同页面形态一致 | 对比保存/取消等按钮的样式一致性 |
| 3 | 显示字体 | 标签/按钮/数据不应使用展示字体 | 检查 font-family 在 UI 元素上的使用 |
| 4 | 标准交互 | 不重新发明标准交互（自定义滚动条/非标准表单控件） | 检查原生交互元素是否被替换 |
| 5 | 非活跃状态 | 非活跃状态使用轻色而非高饱和度色彩 | 检查 disabled/inactive 状态的颜色 |
| 6 | 模态框使用 | 优先内联/渐进式替代方案，模态框应是最后选择 | 检查是否有更轻量的替代方案 |
| 7 | 字体族 | 产品 UI 通常一个字体族即可 | 检查是否无必要地使用了 display/body 配对 |
| 8 | 字号比例 | 保持 1.125–1.2 的紧凑比例 | 检查 h1→h2→h3 的比例 |
| 9 | 颜色策略 | 产品 UI 默认 Restrained 策略 | 检查是否过度使用饱和色 |
| 10 | 状态语义 | hover/focus/active/disabled/loading/error 等完整实现 | 检查所有交互状态是否已实现 |
| 11 | 骨架屏 | 加载状态使用骨架屏而非居中 spinner | 检查 loading 状态的实现方式 |
| 12 | 空状态 | 空状态应具有教学意义，而非"暂无数据" | 检查空列表/空结果的提示方式 |
| 13 | 动效时长 | 产品 UI 过渡 150–250ms | 检查 transition duration |

#### 4.3 AI Slop 测试

对生成的 UI 进行两级鉴别：

**一阶检查**：能否仅凭类别就能猜出主题和配色？
- 例如：看到"AI 工具"就自动 SaaS 蓝色 → 属于训练数据反射
- 通过改写场景描述和颜色策略打破预期

**二阶检查**：能否通过"避免类别默认"+"选择另一条已知路径"猜出美学家族？
- 例如：不是 SaaS 奶油色 → 编辑式排版风 → 仍然是反射
- 需要确保两个答案都不明显

#### 4.4 通用设计规则自检清单

**颜色**
- [ ] 正文对比度 ≥ 4.5:1（大号/粗体文字 ≥ 3:1）
- [ ] 占位符文字对比度 ≥ 4.5:1（不可用默认灰色）
- [ ] 彩色背景上文字使用背景色同色系的深色，而非灰色
- [ ] 使用 OKLCH 色彩空间（新项目）
- [ ] 避免暖色中性色默认值（奶油/沙色/纸张底色是 AI 默认）
- [ ] 中性色调添加 0.005–0.015 色度向品牌色靠拢
- [ ] 选择主题前有明确的物理场景描述（谁、在哪、什么光环境、什么情绪）

**排版**
- [ ] 正文行宽 65–75ch
- [ ] 不使用相似但不同的字体配对（两个几何无衬线、两个人文无衬线）
- [ ] 展示标题 clamp() 最大值 ≤ 6rem（~96px）
- [ ] 展示标题字间距 ≥ -0.04em
- [ ] h1–h3 使用 `text-wrap: balance`，长文本使用 `text-wrap: pretty`

**布局**
- [ ] 间距有节奏变化（非统一间距）
- [ ] 仅在明确需要时才使用卡片布局（无嵌套卡片）
- [ ] 一维用 Flexbox，二维用 Grid（不默认 Grid）
- [ ] 无断点响应式网格：`repeat(auto-fit, minmax(280px, 1fr))`
- [ ] 语义化 z-index 层叠体系（dropdown → sticky → modal-backdrop → modal → toast → tooltip）

**动效**
- [ ] 不动画化 CSS 布局属性（width/height/top/left 等）
- [ ] 使用指数型缓出曲线（ease-out-quart/quint/expo）
- [ ] 所有动画有 `@media (prefers-reduced-motion: reduce)` 降级方案
- [ ] 列表项有适当的交错延迟，不同 section 用不同的入场方式
- [ ] 入场动画不遮挡内容可见性（有默认可见状态）

**交互**
- [ ] 下拉菜单不因 `overflow: hidden`/`auto` 容器被裁剪
- [ ] `<img>` 元素无 hover 动画（包括 Tailwind 的 group-hover 模式）

#### 4.4.1 键盘可访问性与数字对齐（CSS/ARIA 规范，P3）

`ui_audit.py` 的结构化 a11y lint（4.1 附注）覆盖 `alt`/可访问名/标题层级，但**看不见 CSS 级的可访问性**——以下三项须在 `components.py` 的 `APP_CSS` 中显式落实，否则纯键盘用户与读屏用户会受损：

1. **键盘焦点可见性（必做）**：`a / button / input / select / textarea / .btn / .nav-item` 全部设 `:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }`。仅 `:focus` 不够（鼠标点击也会触发，干扰视觉）；仅 `outline:none` 等于剥夺键盘可达性。
2. **数字等宽对齐（必做）**：所有展示数值的元素（统计卡数字、金额、百分比）加 `font-variant-numeric: tabular-nums;`，避免表格/卡片中数字因字符宽度不一而抖动错位。
3. **容器 ARIA 角色（推荐）**：侧边导航容器加 `role="navigation"` + `aria-label`；模态框根节点加 `role="dialog"` + `aria-modal="true"` + `aria-label={title}`，关闭按钮加 `aria-label="关闭"`；当前激活导航项加 `aria-current="page"`。

> 以上三项建议通过 `tests/test_a11y.py` 静态回归（断言 `role=navigation`、`aria-modal`、`tabular-nums`、`:focus-visible` 均存在）。技能默认 `components.py` 为**按项目生成**（无统一模板），故此处给规范，由 AI 在生成骨架时套用。

#### 4.5 路由卫生检查（APIRouter 默认路由陷阱，静态门禁）

fasthtml 的 `@rt` / `@ar` 在**未显式给出路径字符串**时，会用「函数名」自动生成路由（下划线转连字符），并把类型注解参数当作查询参数。手写 RESTful href（如 `/expenses/new`）会与自动生成的 `/expenses_new` 对不上 → **全站 404，且运行时除非逐个点否则发现不了**。

**硬规则（适用多文件拆分路由、或页面中有手写 href/redirect 时）**：每个路由**必须显式声明路径**，需要路径参数用 `{name}`；不要依赖函数名自动映射，也不要把类型注解当成路径参数来源。

```python
from fasthtml.common import APIRouter
ar = APIRouter()

@ar("/products/{pid}")        # ✅ 显式路径 + 路径参数 → /products/123
def product_detail(pid: int): ...
```

**多文件拆分 + 正确挂载 / URL 生成**：

```python

---

## 能力边界与实现现状（重要）

> **文档-实现差异说明**：本文件上方展示的 13 条禁令为「设计理念版」（侧边色条边框、渐变文字、毛玻璃、英雄指标模板等偏视觉风格）。实际 `scripts/ui_audit.py` 落地的是「可自动判定版」（纯色模态框、左对齐、纯黑白文字、无间距、默认字体、无视觉反馈、层级扁平、验证反馈、默认 outline 等）。两者一脉相承，但**以 `ui_audit.py` 源码为准**。

### 外部 CSS 抓取（消除 CSS 外部化误报）

`ui_audit.py` 会解析页面全部 `<link rel="stylesheet">`，用 `requests` 抓取外部 CSS 内容并**合并进审计文本**，再对 CSS 相关禁令（纯黑白文字 / 无间距 / 默认字体 / 无视觉反馈 / 默认 outline）做判定。因此：

- **CSS 外部化项目**（样式放 `app.css`、主题双变量等）不再因样式不在内联 `style` 而机械误报；
- 反而能**发现旧版漏检的真实问题**（如外部 CSS 中 `button:hover { color:#fff }` 的纯白悬停文字会被正确检出）；
- 抓取失败（404/超时/跨域）只跳过该文件，不阻断审计。
- 审计报告会新增一条「外部 CSS 已纳入审计（N 个文件）」的 UX 级信息项，便于核验覆盖范围。

### 豁免已知误报：`--ignore-ban`

当某条禁令确属已知误报、需显式豁免时，可传 `--ignore-ban`（支持禁令**序号**、**完整名**、任意**子串**，逗号分隔多个）：

```bash
python scripts/ui_audit.py --ignore-ban "纯黑,11" http://127.0.0.1:5001/
```

被豁免的禁令会在报告中标记「（已忽略）」，不计入阻断。
