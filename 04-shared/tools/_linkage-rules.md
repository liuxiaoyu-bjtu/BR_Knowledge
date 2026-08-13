---
title: 知识库联动更新规则
category: 共享资源
tags: [联动规则, 维护规范, 约束]
status: active
last_updated: 2026-08-05
---

# 知识库联动更新规则

> 本文档定义知识库内容变更时的必检清单和更新流程。任何向知识库新增、修改、移动或删除文件的操作，都必须对照本规则执行联动更新。

---

## 一、变更类型与联动范围

| 变更类型 | 触发条件 | 必须联动检查的文件 |
|---------|---------|------------------|
| **新增文件/目录** | 向任意目录添加新文件（如归档新课程素材） | 全部「统计数字类」+「索引类」+「导航类」 |
| **修改文件** | 修改已有文件的内容或 frontmatter | 「交叉引用类」中所有引用该文件的其他文档 |
| **移动/重命名文件** | 改变文件路径或文件名 | 「交叉引用类」中所有引用旧路径的文档（用 `grep` 全库搜索旧路径） |
| **删除文件** | 移除文件 | 同上 + 清理所有指向该文件的链接 |
| **新增调研/约束** | 向 `_construction-notes.md` 新增记录 | `CHANGELOG.md` |

---

## 二、必检文件清单（按优先级排序）

### 高优先级 — 每次变更必须检查

| # | 文件 | 检查内容 |
|---|------|---------|
| 1 | `CHANGELOG.md` | 新增对应版本的变更条目 |
| 2 | `README.md` | 版本号、更新日期、更新日志表 |
| 3 | `INDEX.md` | `last_updated`、关键词索引条目是否完整 |
| 4 | `05-internal-materials/_README.md` | 文件统计数字、目录结构表 |
| 5 | `KNOWLEDGE-MAP.md` | 文件统计数字、完成度评估 |

### 中优先级 — 涉及课程/教育内容变更时检查

| # | 文件 | 检查内容 |
|---|------|---------|
| 6 | `00-navigation/dashboard.md` | `last_updated`、文档数、完成度 |
| 7 | `00-navigation/quick-reference.md` | `last_updated`、速查链接是否覆盖新内容 |
| 8 | `02-embodied-ai-edu/03-curriculum/_curriculum-overview.md` | 文件统计数字、新课程线引用 |
| 9 | `02-embodied-ai-edu/03-curriculum/_index.md` | 新课程线条目 |
| 10 | `02-embodied-ai-edu/03-curriculum/k1-通识课/README.md` | 逐阶分析引用是否完整 |

### 低优先级 — 特定内容变更时检查

| # | 文件 | 检查内容 |
|---|------|---------|
| 11 | `03-cross-reference/competition-to-curriculum.md` | `last_updated`、赛事-课程映射是否需要扩展 |
| 12 | `03-cross-reference/theory-to-product.md` | `last_updated`、理论-产品映射是否需要扩展 |
| 13 | `03-cross-reference/product-to-standard.md` | 同上 |
| 14 | `03-cross-reference/case-to-solution.md` | 同上 |

---

## 三、变更执行流程

### 步骤 1：变更前 — 记录当前状态

```bash
# 在变更前，用 git status 确认当前状态干净
cd /workspace/booster-knowledge-base && git status
```

### 步骤 2：执行主变更

完成核心操作（新增/修改/移动/删除文件）。

### 步骤 3：联动搜索 — 查找所有引用

```bash
# 如果移动/重命名了文件，搜索所有引用旧路径的文件
grep -rn "旧文件名或路径" --include="*.md" /workspace/booster-knowledge-base/
```

### 步骤 4：逐项更新

按照「二、必检文件清单」逐项更新所有需要联动的文件。

### 步骤 5：变更后 — 验证一致性

```bash
# 确认所有引用指向有效路径
# 确认统计数字与实际文件数一致
# 确认 CHANGELOG 已记录
cd /workspace/booster-knowledge-base && git diff --stat
```

### 步骤 6：提交推送

```bash
git add -A
git commit -m "vX.Y: 变更说明（含联动更新）"
git push origin main
```

---

## 四、特殊规则

### 4.1 文件移动规则

当移动文件到新位置时：
1. 使用 `git mv` 或 `mv` 保持 Git 历史
2. 用 `grep -rn` 全库搜索旧文件名，更新所有引用
3. 如果该文件被 frontmatter 的 `source` 字段引用，同步更新

### 4.2 统计数字规则

以下位置涉及文件数量统计，变更后必须同步更新：
- `05-internal-materials/_README.md` — "共 **N 份 Markdown 文件**"
- `KNOWLEDGE-MAP.md` — "✅ N 份源文件归档"
- `00-navigation/dashboard.md` — "文档数" 和 "~N篇"
- `README.md` — 更新日志中的文件数描述

### 4.3 版本号规则

- 主版本号（v1, v2）：架构级变更（如新增 Core C）
- 次版本号（v1.1, v1.2）：内容级变更（如新增文件/目录、新增调研记录）
- 每次变更必须更新 `README.md` 版本号和 `CHANGELOG.md`

### 4.4 SDK 测试脚本放置规则

SDK 相关的测试/验证脚本（`.py` / `.ipynb`）**必须**放置于 `04-shared/sdk-tests/` 目录，禁止直接放在 `04-shared/` 根目录或其他模块目录：

- 每个测试脚本需在 `04-shared/sdk-tests/_README.md` 文件清单中登记（测试内容、覆盖接口、运行方式）
- 涉及 BoosterOS SDK API 的测试脚本以 `booster-sdk.md` 为技术依据，接口变动时同步更新
- 环境验证类脚本（如机器人连通性检查、SDK 安装检测）同样归入本目录

### 4.5 建构笔记联动规则

`_construction-notes.md` 中的约束/调研/审计记录：
- 每条记录标注日期和状态
- 当调研结论被后续实践修正时，在原记录末尾追加更新而非删除
- 新增调研时同步更新 `CHANGELOG.md`

---

## 五、快捷检查命令

```bash
# 检查所有 frontmatter 中 last_updated 早于 30 天的文件
find /workspace/booster-knowledge-base -name "*.md" -exec grep -l "last_updated.*2026-07" {} \;

# 检查是否有断链（指向不存在路径的链接）
# 人工检查：grep -rn "](.*\.md)" 后逐条验证

# 统计 course-outlines 目录实际文件数
ls -1 /workspace/booster-knowledge-base/05-internal-materials/course-outlines/*.md /workspace/booster-knowledge-base/05-internal-materials/course-outlines/*/*.md 2>/dev/null | wc -l
```
