---
title: 通用文档模板
category: templates
tags: [模板, 文档规范, YAML frontmatter]
status: completed
last_updated: 2026-07-16
---

# 通用文档模板

## YAML Frontmatter 标准

所有知识库文档必须包含以下 YAML frontmatter：

```yaml
---
title: [文档标题，中文]
category: [所属分类]
tags: [标签1, 标签2, 标签3]
status: [draft | completed | archived]
last_updated: YYYY-MM-DD
---
```

### 字段说明

| 字段 | 说明 | 必填 | 示例 |
|------|------|------|------|
| `title` | 文档标题，使用中文 | 是 | `具身智能教育定义` |
| `category` | 所属分类 | 是 | `embodied-ai-edu` |
| `tags` | 标签列表，3-5个为宜 | 是 | `[具身智能, 教育定义]` |
| `status` | 文档状态 | 是 | `draft` / `completed` / `archived` |
| `last_updated` | 最后更新日期 | 是 | `2026-07-16` |

### 状态说明

| 状态 | 含义 | 适用场景 |
|------|------|---------|
| `draft` | 草稿 | 框架阶段、内容待填充 |
| `completed` | 已完成 | 内容完整、可对外使用 |
| `archived` | 已归档 | 不再更新、保留参考 |

### Category 分类规范

| 分类 | 说明 |
|------|------|
| `competitive-analysis` | 竞品分析 |
| `embodied-ai-edu` | 具身智能教育体系 |
| `cross-reference` | 交叉引用 |
| `templates` | 模板文件 |
| `tools` | 工具文档 |

## Markdown 内容规范

### 标题层级

```markdown
# 一级标题（文档标题，仅一个）
## 二级标题（主要章节）
### 三级标题（子章节）
#### 四级标题（尽量不用）
```

### 表格规范

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容 | 内容 | 内容 |
```

### 代码块规范

```markdown
```python
# Python 代码
print("Hello")
```
```

### 链接规范

```markdown
- 内部链接：[文档名](./relative-path.md)
- 外部链接：[链接文字](URL)
```

### 列表规范

```markdown
- 无序列表项
1. 有序列表项
  - 嵌套列表（2空格缩进）
```

### 强调规范

```markdown
**粗体** 用于强调关键词
*斜体* 用于术语或引用
```

## 完整文档模板

```markdown
---
title: [文档标题]
category: [分类]
tags: [标签]
status: draft
last_updated: YYYY-MM-DD
---

# [文档标题]

## 概述

[用1-3句话描述本文档的目的和范围]

## [第一节标题]

[内容]

### [子节标题]

[内容]

## [第二节标题]

[内容]

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| | | |

## 相关文档

- [相关文档1](./path.md)
- [相关文档2](./path.md)
```
