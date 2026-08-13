"""将 references/02-architecture.md 拆分为 references/architecture/ 目录"""
import re, pathlib, shutil
import sys

# 强制 UTF-8 输出：Windows 默认 GBK 控制台打印中文/emoji 会抛 UnicodeEncodeError。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

SKILL_DIR = pathlib.Path(__file__).parent.parent
ARCH_FILE = SKILL_DIR / "references" / "02-architecture.md"
ARCH_DIR = SKILL_DIR / "references" / "architecture"

if not ARCH_FILE.exists():
    print(f"not found: {ARCH_FILE}")
    exit(1)

content = ARCH_FILE.read_text(encoding="utf-8")

# 18 个章节的标题和文件名映射
CHAPTERS = [
    ("01-system-context", "系统上下文与边界"),
    ("02-business-flow", "核心业务流"),
    ("03-module-decomposition", "模块分解"),
    ("04-data-architecture", "数据架构"),
    ("05-interface-design", "接口设计"),
    ("06-unified-framework", "统一架构框架"),
    ("07-scenario-driven", "场景驱动的架构类型选择"),
    ("08-adr", "架构决策记录"),
    ("09-common-mistakes", "常见架构错误"),
    ("10-checklist", "设计检查清单"),
    ("11-pattern-selection", "架构模式选型"),
    ("12-state-machine", "状态机设计"),
    ("13-storage-selection", "存储选择表"),
    ("14-tech-debt", "技术债记录"),
    ("15-error-handling", "统一错误处理"),
    ("16-non-functional", "非功能设计"),
    ("17-mvp-boundary", "MVP 边界表"),
    ("18-diagram-guide", "图生成指南"),
]

# 解析章节：查找 ## 标题，提取各个 ## 级别的章节
sections = re.split(r'\n(?=## )', content)

# 移除第一个空白段（文件头）
if sections and not sections[0].startswith("##"):
    header = sections.pop(0)

# 创建目录
if ARCH_DIR.exists():
    shutil.rmtree(ARCH_DIR)
ARCH_DIR.mkdir(parents=True)

# 匹配章节标题到预设映射
written = []
for section in sections:
    first_line = section.split('\n')[0]
    title = first_line.replace('## ', '').strip()
    
    # 找到对应的文件名
    matched = None
    for fname, cname in CHAPTERS:
        if cname in title or title in cname:
            matched = fname
            break
    
    if matched:
        filepath = ARCH_DIR / f"{matched}.md"
        # 在内容前加章节标题
        filepath.write_text(
            f"# {title}\n\n"
            f"> 本文档由 `02-architecture.md` 自动拆分生成。\n"
            f"> 源文件：[../02-architecture.md](../02-architecture.md)\n\n"
            f"{section.strip()}\n",
            encoding="utf-8"
        )
        written.append(f"{matched}.md  —  {title}")
        print(f"  [OK] {matched}.md ({len(section)} 字符)")

# 写入口索引文件
index_content = [
    "# 架构设计参考（拆分版）",
    "",
    "> 本文档由 `02-architecture.md` 按章节拆分，便于单文件查阅。",
    "> 完整原始文档：[../02-architecture.md](../02-architecture.md)",
    "",
    "| # | 文件 | 章节 |",
    "|---|------|------|",
]
for i, (fname, cname) in enumerate(CHAPTERS, 1):
    exists = "✅" if (ARCH_DIR / f"{fname}.md").exists() else "❌"
    index_content.append(f"| {i:02d} | `{fname}.md` | {cname} |  |")

index_content.extend([
    "",
    "---",
    "",
    "### 使用指引",
    "",
    "- **简单项目**：重点阅读 01（系统上下文）、10（检查清单）、17（MVP 边界）",
    "- **中等复杂度**：增加 03（模块分解）、05（接口设计）、07（场景驱动）",
    "- **复杂企业应用**：全部章节均需阅读",
    "",
    "详细内容请打开对应章节文件。",
])

(ARCH_DIR / "INDEX.md").write_text("\n".join(index_content), encoding="utf-8")
print(f"\n  [OK] INDEX.md — 入口索引")

# 更新 02-architecture.md 为入口文件
new_header = f"""# 架构设计参考（入口）

> **注意**：本文档已拆分为 `references/architecture/` 目录下的独立文件。
> 请访问 [architecture/INDEX.md](architecture/INDEX.md) 查看完整索引。
> 
> 本文保留完整原始内容，供全局搜索和全文检索使用。
> 单章节查阅请使用拆分版。

---

{header}
"""

ARCH_FILE.write_text(new_header + "\n\n".join(sections), encoding="utf-8")
print(f"\n  [OK] 02-architecture.md 已更新为入口文件")

print(f"\n=== 完成: {len(written)}/{len(CHAPTERS)} 章节拆分 ===")
