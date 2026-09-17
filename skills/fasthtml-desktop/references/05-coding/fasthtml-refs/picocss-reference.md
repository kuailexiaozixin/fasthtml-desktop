# PicoCSS v2 — FastHTML 默认 CSS 框架参考

> **当前版本**: 2.1.1 | CDN: `https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css`
> **官方文档**: https://picocss.com/docs | **示例**: https://picocss.com/examples | **GitHub**: https://github.com/picocss/pico

---

## 一、概述

PicoCSS 是一个极简的语义化 HTML CSS 框架——"写 HTML，加 Pico CSS，搞定"。它不对 HTML 做任何假设，而是让原生 HTML 元素在没有 class 的情况下直接拥有优雅的样式。

### 核心理念

- **Class-light & 语义化**：优先使用原生 HTML 元素，无需记忆 CSS class 名称
- **响应式一切**：所有元素默认响应式
- **明暗模式**：自动适配系统主题，也支持手动切换
- **超强 HTML Reset**：比 Normalize.css 更进一步，称"steroid reset"
- **极小体积**：完整版仅约 28KB（minified + gzipped）

### v2.x 相比 v1.x 的关键变化

| 变化 | 说明 |
|------|------|
| 颜色体系 | 380 个手工调校的颜色，20 个预编译主题，100+ CDN 组合 |
| 无障碍 | 默认主题符合 WCAG 2.1 AAA 标准 |
| CSS Variables | 新增至 130+ 个 CSS 自定义属性，全部以 `pico-` 前缀 |
| Group 组件 | `role="group"` 水平堆叠表单元素和按钮 |
| Conditional 模式 | 通过 `.pico` 容器选择性应用样式，避免全局污染 |
| SASS | 全部 `.scss` 重构，模块可按需 `@use` |
| 断点更新 | 跟随标准设备宽度，新增超大屏断点 |

---

## 二、快速开始

### 2.1 CDN 引入（推荐）

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light dark">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    <title>Hello world!</title>
  </head>
  <body>
    <main class="container">
      <h1>Hello world!</h1>
    </main>
  </body>
</html>
```

### 2.2 NPM 安装

```shell
npm install @picocss/pico
```

在 SCSS 中导入：

```scss
@use "pico";
```

### 2.3 Composer 安装

```shell
composer require picocss/pico
```

---

## 三、CDN 文件清单与选型指南

所有文件位于 `https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/`

### 3.1 文件命名规则

```
pico[.variant][.color].min.css
        ├── classless       — 无类版本（连 .container 也不需要）
        ├── fluid.classless — 流式无类版本
        ├── conditional     — 条件版本（需 .pico 容器包裹）
        ├── colors          — 仅颜色工具类（57KB）
        └── (空)            — 标准版本
```

### 3.2 常用文件速查

| 文件 | 说明 | 适用场景 |
|------|------|---------|
| `pico.min.css` | **标准版**（默认） | 大多数项目，需 `class="container"` |
| `pico.classless.min.css` | 无类版（居中定宽） | 纯内容页面，无需写任何 class |
| `pico.fluid.classless.min.css` | 无类版（流式宽） | 全屏布局的无类版本 |
| `pico.conditional.min.css` | 条件版 | 需要与别的 CSS 框架共存 |
| `pico.colors.min.css` | 仅颜色工具 | 只需 Pico 色板时 |
| `pico.blue.min.css` | 蓝色主题 | 标准版 + 蓝色调 |
| `pico.red.min.css` | 红色主题 | 标准版 + 红色调 |

### 3.3 20 种颜色主题

| 颜色 | 标准版 | Classless | Conditional | Fluid Classless |
|------|--------|-----------|-------------|-----------------|
| amber | `pico.amber.min.css` | `pico.classless.amber.min.css` | `pico.conditional.amber.min.css` | `pico.fluid.classless.amber.min.css` |
| blue | ✓ | ✓ | ✓ | ✓ |
| cyan | ✓ | ✓ | ✓ | ✓ |
| fuchsia | ✓ | ✓ | ✓ | ✓ |
| green | ✓ | ✓ | ✓ | ✓ |
| grey | ✓ | ✓ | ✓ | ✓ |
| indigo | ✓ | ✓ | ✓ | ✓ |
| jade | ✓ | ✓ | ✓ | ✓ |
| lime | ✓ | ✓ | ✓ | ✓ |
| orange | ✓ | ✓ | ✓ | ✓ |
| pink | ✓ | ✓ | ✓ | ✓ |
| pumpkin | ✓ | ✓ | ✓ | ✓ |
| purple | ✓ | ✓ | ✓ | ✓ |
| red | ✓ | ✓ | ✓ | ✓ |
| sand | ✓ | ✓ | ✓ | ✓ |
| slate | ✓ | ✓ | ✓ | ✓ |
| violet | ✓ | ✓ | ✓ | ✓ |
| yellow | ✓ | ✓ | ✓ | ✓ |
| zinc | ✓ | ✓ | ✓ | ✓ |

所有颜色主题 × 所有变体 = 100+ CDN 组合。

---

## 四、主题与配色

### 4.1 明暗模式

PicoCSS 通过 `<meta name="color-scheme" content="light dark">` 自动适配系统主题。

**强制亮色模式**：将 meta 改为 `content="light"`。
**强制暗色模式**：将 meta 改为 `content="dark"`。

### 4.2 使用颜色主题

直接替换 CDN 链接中的文件名：

```html
<!-- 蓝色主题 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.blue.min.css">

<!-- 绿色主题无类版本 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.green.min.css">
```

### 4.3 pico.colors.min.css — 颜色工具类

单独的颜色系统文件（~57KB），提供一组颜色 CSS 变量和工具类，可与任何版本搭配使用。

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.colors.min.css">
```

---

## 五、布局系统

### 5.1 Container

标准版中，内容必须包裹在 `<main class="container">` 内才能居中对齐：

```html
<main class="container">
  <!-- 居中内容，最大宽度约 1020px -->
</main>
```

FastHTML 提供了 `Container` 组件自动生成此结构：

```python
Container(H1("Title"), P("Content"))
# <main class="container"><h1>Title</h1><p>Content</p></main>
```

**注意**：Classless 版本无需 `.container`，`<main>` 自动充当容器。

### 5.2 Grid 网格

PicoCSS 的网格基于 Flexbox，自动列布局。使用 `<div class="grid">` 包裹子元素即可：

```html
<div class="grid">
  <div>1</div>
  <div>2</div>
  <div>3</div>
  <div>4</div>
</div>
```

- 列数由子元素数量自动决定
- 每列宽度均分
- **不在 classless 版本中可用**
- **小屏幕（<768px）自动折叠为单列**

FastHTML 中：

```python
from fasthtml.pico import Grid

Grid(Div("1"), Div("2"), Div("3"))
# <div class="grid"><div>1</div><div>2</div><div>3</div></div>
```

PicoCSS 保持 grid 系统极简——完整的 Flexbox grid（含排序、偏移、断点工具）体积可能超过 Pico 库本身的总大小。需要复杂布局时，建议使用 CSS Grid 或 Bootstrap Grid System。

### 5.3 Landmarks & Sections 语义结构

PicoCSS 为语义化 HTML5 元素提供内置样式：

| 元素 | 用途 |
|------|------|
| `<header>` | 页面头部 / section 头部 |
| `<main>` | 页面主体（推荐用 `.container` 包裹） |
| `<footer>` | 页面底部 / section 底部 |
| `<section>` | 内容分区 |
| `<article>` | 独立内容块 |
| `<aside>` | 侧边栏 / 附属信息 |
| `<nav>` | 导航 |

这些元素自动获得适当的间距和排版样式，无需额外 class。

---

## 六、内容元素

### 6.1 排版

| 元素 | 效果 |
|------|------|
| `<h1>` ~ `<h6>` | 标题层级，自动缩放 |
| `<p>` | 段落，行高约 1.5 |
| `<blockquote>` | 引用块，左侧有竖线标识 |
| `<figure>` + `<figcaption>` | 图文组合说明 |
| `<pre>` + `<code>` | 代码块，等宽字体 |
| `<mark>` | 高亮标记 |
| `<abbr>` | 缩写，下划线虚线提示 |
| `<kbd>` | 键盘输入标记 |
| `<ul>` / `<ol>` | 列表，适当缩进和间距 |
| `<hr>` | 分割线 |

### 6.2 链接

```html
<a href="#">普通链接</a>
```

- 默认颜色为主色
- 悬停时下划线
- 访问后颜色变化

### 6.3 按钮

#### 标准按钮

```html
<button>提交</button>
<input type="submit" value="提交">
<a href="#" role="button">链接按钮</a>
```

#### 按钮变体

```html
<!-- 次要按钮 -->
<button class="secondary">次要</button>

<!-- 对比按钮（常用于危险操作） -->
<button class="contrast">删除</button>

<!-- 轮廓按钮 -->
<button class="outline">轮廓</button>

<!-- 可组合 -->
<button class="outline secondary">次要轮廓</button>
<button class="outline contrast">危险轮廓</button>
```

### 6.4 表格

```html
<figure>
  <table>
    <thead>
      <tr><th>名称</th><th>数值</th></tr>
    </thead>
    <tbody>
      <tr><td>A</td><td>1</td></tr>
      <tr><td>B</td><td>2</td></tr>
    </tbody>
    <tfoot>
      <tr><th>合计</th><td>3</td></tr>
    </tfoot>
  </table>
</figure>
```

- 可选 `<caption>` 作为标题
- 可选 `<figure>` 包裹（可配套 `<figcaption>`）

---

## 七、表单

PicoCSS 为表单元素提供开箱即用的美观样式：

### 7.1 基本表单结构

```html
<form>
  <label for="name">姓名
    <input type="text" id="name" name="name" placeholder="请输入姓名" required>
  </label>

  <label for="email">邮箱
    <input type="email" id="email" name="email" placeholder="your@email.com" autocomplete="email">
  </label>

  <label for="bio">简介
    <textarea id="bio" name="bio" placeholder="介绍一下你自己..." rows="5"></textarea>
  </label>

  <label for="country">国家
    <select id="country" name="country" required>
      <option value="" selected disabled>请选择...</option>
      <option value="CN">中国</option>
      <option value="US">美国</option>
      <option value="JP">日本</option>
    </select>
  </label>

  <button type="submit">提交</button>
</form>
```

**关键设计**：PicoCSS 推荐将 `<label>` 包裹在 `<input>` 外部（而非通过 `for`/`id` 关联），这样标签始终在上方。

### 7.2 输入类型

| 类型 | HTML |
|------|------|
| 文本 | `<input type="text">` |
| 邮箱 | `<input type="email">` |
| 密码 | `<input type="password">` |
| 数字 | `<input type="number">` |
| 电话 | `<input type="tel">` |
| 日期 | `<input type="date">` |
| URL | `<input type="url">` |
| 搜索 | `<input type="search">` |
| 文件 | `<input type="file">` |
| 颜色 | `<input type="color">` |

输入框的可选样式：

```html
<!-- 无效状态（自动样式，配合 :invalid） -->
<input type="email" value="invalid-email">

<!-- 禁用状态 -->
<input type="text" disabled>

<!-- aria-invalid -->
<input type="text" aria-invalid="true">
<input type="text" aria-invalid="false">
```

### 7.3 选择框

```html
<select name="city" required>
  <option value="" selected disabled>请选择城市...</option>
  <option value="beijing">北京</option>
  <option value="shanghai">上海</option>
</select>

<!-- 多选 -->
<select name="tags" multiple size="3">
  <option>HTML</option>
  <option>CSS</option>
  <option>JavaScript</option>
</select>
```

### 7.4 复选框与单选框

```html
<!-- 复选框 -->
<label>
  <input type="checkbox" name="agree" checked>
  同意条款
</label>

<!-- 单选框组 -->
<fieldset>
  <legend>性别</legend>
  <label>
    <input type="radio" name="gender" value="male" checked>
    男
  </label>
  <label>
    <input type="radio" name="gender" value="female">
    女
  </label>
</fieldset>
```

### 7.5 开关 (Switch)

使用 `role="switch"` 将复选框渲染为开关样式：

```html
<label>
  <input type="checkbox" role="switch" checked>
  开启通知
</label>
```

### 7.6 范围滑块

```html
<label for="volume">
  音量
  <input type="range" id="volume" min="0" max="100" value="50">
</label>
```

### 7.7 辅助文本

```html
<label for="email">
  邮箱
  <input type="email" name="email" aria-describedby="email-help">
  <small id="email-help">我们不会共享您的邮箱地址</small>
</label>
```

### 7.8 Group 组件（水平堆叠）

通过 `role="group"` 将多个表单元素或按钮水平排列：

```html
<fieldset role="group">
  <input name="email" type="email" placeholder="输入邮箱">
  <button type="submit">订阅</button>
</fieldset>
```

FastHTML 中：

```python
from fasthtml.pico import Group

Group(Input(name="email", type="email", placeholder="输入邮箱"),
      Button("订阅"))
# <fieldset role="group"><input...><button...></fieldset>
```

### 7.9 Search 组件

```html
<form role="search">
  <input name="q" type="search" placeholder="搜索...">
  <button type="submit">搜索</button>
</form>
```

FastHTML 中：

```python
from fasthtml.pico import Search

Search(Input(name="q", type="search", placeholder="搜索..."),
       Button("搜索"))
# <form role="search"><input...><button...></form>
```

---

## 八、UI 组件

### 8.1 Accordion 手风琴

```html
<details>
  <summary>点击展开</summary>
  <p>这里是折叠内容...</p>
</details>

<details open>
  <summary>默认展开</summary>
  <p>使用 open 属性控制初始状态</p>
</details>
```

### 8.2 Card 卡片

```html
<article>
  <header>卡片标题</header>
  <p>卡片正文内容...</p>
  <footer>卡片底部</footer>
</article>
```

FastHTML 中：

```python
from fasthtml.pico import Card

Card(P("内容"), header=H2("标题"), footer=P("底部"))
# <article><header><h2>标题</h2></header><p>内容</p><footer><p>底部</p></footer></article>
```

`Card` 本质上是 `<article>`，无需额外 class。

### 8.3 Dropdown 下拉菜单

```html
<details class="dropdown">
  <summary>下拉菜单</summary>
  <ul>
    <li><a href="#">选项一</a></li>
    <li><a href="#">选项二</a></li>
    <li><a href="#">选项三</a></li>
  </ul>
</details>
```

### 8.4 Modal 模态框

```html
<!-- 触发按钮 -->
<button class="contrast" data-target="modal-example" onClick="toggleModal(event)">打开模态框</button>

<!-- 模态框 -->
<dialog id="modal-example">
  <article>
    <header>
      <button aria-label="Close" rel="prev" onClick="toggleModal(event)"></button>
      <h3>确认操作</h3>
    </header>
    <p>确定要执行此操作吗？</p>
    <footer>
      <button role="button" class="secondary" onClick="toggleModal(event)">取消</button>
      <button role="button" onClick="toggleModal(event)">确认</button>
    </footer>
  </article>
</dialog>

<script>
// PicoCSS 推荐的模态框切换函数
function toggleModal(event) {
  const target = document.getElementById(event.currentTarget.dataset?.target || 'modal-example');
  const isOpen = target.getAttribute('open') !== null;
  if (isOpen) target.removeAttribute('open');
  else target.setAttribute('open', 'true');
}
</script>
```

FastHTML 中：

```python
from fasthtml.pico import DialogX

DialogX(
    Card("确认内容", header=H3("确认操作"),
         footer=(Button("取消"), Button("确认"))),
    id="modal-example"
)
```

### 8.5 Nav 导航

```html
<nav>
  <ul>
    <li><a href="#">首页</a></li>
    <li><a href="#">关于</a></li>
  </ul>
  <ul>
    <li><a href="#">登录</a></li>
  </ul>
</nav>
```

`<nav>` 内的 `<ul>` 自动水平排列 —— 左侧 `<ul>` 左对齐，右侧 `<ul>` 右对齐。

### 8.6 Progress 进度条

```html
<progress value="60" max="100"></progress>
```

### 8.7 Loading / Spinner

```html
<!-- 内联加载指示器 -->
<span aria-busy="true">加载中...</span>

<!-- 按钮加载态 -->
<button aria-busy="true">提交中...</button>
```

设置 `aria-busy="true"` 的元素会自动显示旋转动画。

### 8.8 Tooltip 工具提示

```html
<button data-tooltip="这是一段提示文本">悬停查看</button>
<a href="#" data-tooltip="了解更多">关于</a>
<abbr data-tooltip="Cascading Style Sheets">CSS</abbr>
```

使用 `data-tooltip` 属性，支持任意元素。

---

## 九、Classless 模式

PicoCSS 的无类版本是最小化的入口——你只需写纯 HTML，无需任何 class 即可获得美观样式。

### 9.1 引入方式

```html
<!-- 居中定宽版本 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css">

<!-- 流式（全宽）版本 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.fluid.classless.min.css">
```

### 9.2 核心差异

| 特性 | 标准版 | Classless 版 |
|------|--------|-------------|
| 需写 class | `container`、`grid` 等 | 无需任何 class |
| 容器 | `<main class="container">` | `<main>` 自动成为容器 |
| Grid | 可用 `class="grid"` | **不提供** |
| Group | 可用 `role="group"` | **不提供** |
| 适用场景 | 定制化项目 | 纯内容页面、文档 |

### 9.3 与颜色主题组合

```html
<!-- 蓝色主题 + classless -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.blue.min.css">

<!-- 流式 + 橙色 + classless -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.fluid.classless.orange.min.css">
```

---

## 十、Conditional 模式（条件样式）

v2 新增。条件模式通过 `.pico` 类选择性地应用 Pico 样式，避免全局污染。

### 10.1 引入

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.conditional.min.css">
```

### 10.2 使用

```html
<!-- 只有 .pico 容器内的元素受 Pico 影响 -->
<div class="pico">
  <button>有 Pico 样式</button>
</div>
<button>无 Pico 样式（继承其他框架）</button>
```

### 10.3 适用场景

- 渐进增强：在已有项目中局部使用 Pico
- 多框架共存：Pico + Bootstrap / Tailwind 混合使用
- 微前端：不同子应用使用不同样式体系

### 10.4 与主题和 classless 组合

```html
<!-- 条件 + 蓝色主题 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.conditional.blue.min.css">

<!-- 条件 + classless + 红色 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.conditional.red.min.css">
```

---

## 十一、CSS Variables 自定义

PicoCSS 提供 130+ CSS 自定义属性（全部以 `pico-` 前缀），覆盖颜色、间距、排版、组件等所有方面。

### 11.1 基础自定义示例

```css
:root {
  /* 主色调 */
  --pico-primary: #0070f0;
  --pico-primary-hover: #0058c4;
  --pico-primary-background: #0070f0;

  /* 字体 */
  --pico-font-family: "Source Han Sans", system-ui, sans-serif;
  --pico-font-size: 18px;
  --pico-line-height: 1.6;

  /* 圆角 */
  --pico-border-radius: 8px;

  /* 间距 */
  --pico-spacing: 1.2rem;
  --pico-block-spacing-vertical: 2rem;
}

/* 暗色模式适配 */
[data-theme="dark"] {
  --pico-primary: #4d9eff;
  --pico-primary-hover: #7ab3ff;
}
```

### 11.2 关键变量分类

| 分类 | 变量前缀 | 示例 |
|------|---------|------|
| 颜色 | `--pico-{color}` | `--pico-primary`, `--pico-background` |
| 排版 | `--pico-font-*` | `--pico-font-family`, `--pico-font-size` |
| 表单 | `--pico-form-*` | `--pico-form-element-spacing-vertical` |
| 组件 | `--pico-{component}-*` | `--pico-card-background-color` |
| 断点 | `--pico-breakpoint-*` | `--pico-breakpoint-sm` |
| 间距 | `--pico-spacing` | `--pico-spacing`, `--pico-block-spacing-vertical` |
| 动画 | `--pico-transition-*` | `--pico-transition`, `--pico-hover-translate` |

### 11.3 断点变量

```css
--pico-breakpoint-sm: 576px;    /* 手机横屏 */
--pico-breakpoint-md: 768px;    /* 平板 */
--pico-breakpoint-lg: 1024px;   /* 桌面 */
--pico-breakpoint-xl: 1280px;   /* 大桌面 */
--pico-breakpoint-xxl: 1536px;  /* 超大屏 */
```

### 11.4 SASS 自定义

通过 NPM 安装后，在 SCSS 中使用 `@use` 导入并自定义：

```scss
// 1. 先自定义变量
$pico-primary: #e74c3c;
$pico-font-size: 16px;

// 2. 再导入 Pico
@use "pico" with (
  $primary: $pico-primary,
  $enable-semantic-container: true,
  $enable-viewport: true,
);
```

---

## 十二、FastHTML 集成指南

### 12.1 默认集成

FastHTML 的 `fast_app()` 默认启用 PicoCSS：

```python
from fasthtml.common import *

# 默认包含 PicoCSS
app, rt = fast_app()
```

### 12.2 禁用 PicoCSS

```python
# 不使用 PicoCSS（使用自定义或 MonsterUI）
app, rt = fast_app(pico=False)
```

### 12.3 替换为自定义颜色主题

```python
from fasthtml.common import *

# 使用蓝色主题替换默认 PicoCSS
app, rt = fast_app(
    pico=False,  # 先禁用默认
    hdrs=(
        Link(rel='stylesheet',
             href='https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.blue.min.css'),
    ),
)
```

### 12.4 使用 Classless 版本

```python
app, rt = fast_app(
    pico=False,
    hdrs=(
        Link(rel='stylesheet',
             href='https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css'),
    ),
)
```

### 12.5 内联自定义主题

```python
from fasthtml.common import *

app, rt = fast_app(
    hdrs=(
        Style("""
            :root {
                --pico-primary: #e74c3c;
                --pico-primary-hover: #c0392b;
                --pico-primary-background: #e74c3c;
                --pico-border-radius: 4px;
                --pico-font-family: "Source Han Sans", system-ui, sans-serif;
            }
        """),
    ),
)
```

### 12.6 FastHTML 内置 PicoCSS 组件

```python
from fasthtml.pico import Card, Group, Search, Grid, DialogX, Container

# Container — <main class="container">
Container(H1("标题"), P("正文"))

# Card — <article>
Card(P("内容"), header=H2("标题"), footer=P("底部"))

# Group — <fieldset role="group">
Group(Input(placeholder="输入"), Button("提交"))

# Search — <form role="search">
Search(Input(type="search"), Button("搜索"))

# Grid — <div class="grid">
Grid(Div("一"), Div("二"), Div("三"))

# Dialog — <dialog>
DialogX(
    Card(P("确认？"), footer=(Button("取消"), Button("确认"))),
    id="my-modal"
)
```

### 12.7 常见模式示例

**登录表单**：

```python
@rt
def login():
    return Titled("登录",
        Container(
            Card(
                Form(
                    Group(
                        Input(name="email", type="email", placeholder="邮箱"),
                        Input(name="pwd", type="password", placeholder="密码"),
                    ),
                    Button("登录", type="submit"),
                ),
                header=H2("用户登录"),
            )
        )
    )
```

**数据表格**：

```python
@rt
def users():
    return Container(
        Grid(H1("用户列表"), A("新增", href="/add", role="button")),
        Table(
            Thead(Tr(Th("ID"), Th("姓名"), Th("操作"))),
            Tbody(
                Tr(Td("1"), Td("张三"), Td(A("编辑", href="/edit/1"))),
                Tr(Td("2"), Td("李四"), Td(A("编辑", href="/edit/2"))),
            ),
        ),
    )
```

**导航栏**：

```python
@rt
def index():
    return Container(
        Nav(
            Ul(Li(Strong("我的应用"))),
            Ul(Li(A("首页")), Li(A("关于"))),
        ),
        H1("欢迎"),
    )
```

---

## 十三、Browser Support

| 浏览器 | 支持 |
|--------|------|
| Chrome | 最新 2 个主要版本 |
| Firefox | 最新 2 个主要版本 |
| Edge | 最新 2 个主要版本 |
| Safari | 最新 2 个主要版本 |
| IE | 不支持（含 IE 11） |

---

## 十四、Limitations（局限性）

- PicoCSS 仅提供原生 HTML 元素的样式——**没有任何辅助/工具类**（如 `.mt-2`, `.d-flex` 等）
- 适合中小型项目或快速原型；大型项目建议结合 SCSS 自定义或切换 MonsterUI / Tailwind
- Grid 系统极简（仅自动列布局），复杂网格布局需配合 CSS Grid 或其他框架
- 不支持 IE

---

## 十五、资源链接

- 官方文档: https://picocss.com/docs
- 示例: https://picocss.com/examples
- GitHub: https://github.com/picocss/pico
- CDN: https://cdn.jsdelivr.net/npm/@picocss/pico@2/
- npm: https://www.npmjs.com/package/@picocss/pico
- FastHTML PicoCSS API: https://www.fastht.ml/docs/api/pico.html
- v2 新特性: https://picocss.com/docs/v2
