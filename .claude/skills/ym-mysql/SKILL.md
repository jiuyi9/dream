---
name: ym-mysql
description: MySQL 8.0+ 全栈指南：SQL 编写/审查/调优、表结构设计、索引优化、慢查询/死锁诊断、MyBatis 集成、数据建模（OLTP/数仓）。
---

# MySQL 数据库技能

## 决策树

遇到 MySQL 问题按此顺序定位：

```
用户请求
├── 写 SQL / 审查 SQL
│   ├── 不确定语法 → sql-patterns.md（窗口函数、CTE、分页、行列转换）
│   ├── 担心性能   → sql-tuning.md（索引失效、JOIN 优化、子查询改写）
│   └── 规范检查   → sql-conventions.md（命名、格式化、强制约束）
├── 设计表结构
│   └── 任何表设计 → design.md（规范化、关系基数、OLTP/数仓建模、命名）
├── 优化已有查询
│   ├── 先看执行计划 → sql-tuning.md（EXPLAIN 解读）
│   └── 再看索引     → index-strategy.md（复合索引、覆盖索引）
├── 排查故障
│   ├── 慢查询       → sql-tuning.md + index-strategy.md
│   ├── 死锁/锁等待  → sql-tuning.md（锁和并发优化章节）
│   └── 连接数/内存  → 参考 MySQL 官方文档
└── MyBatis 开发
    └── mybatis-mysql.md（Mapper 命名、XML 规范、租户隔离、N+1 陷阱）
```

## 快速参考卡片

### 索引
```sql
-- 复合索引：等值列在前，范围列在后
CREATE INDEX idx_dept_sal ON t(department_id, salary);  -- WHERE dept_id=? AND salary>?

-- 覆盖索引：包含 SELECT 和 WHERE 所有列
CREATE INDEX idx_cover ON t(dept_id, last_name, salary);  -- SELECT last_name,salary WHERE dept_id=?

-- 避免索引失效：列上不用函数、不隐式转换、不用前导通配符
```

### 查询改写
```
IN 子查询        → EXISTS 或 JOIN
NOT IN           → NOT EXISTS 或 LEFT JOIN + IS NULL
相关子查询       → JOIN 派生表 或 窗口函数
大 OFFSET 分页   → 游标分页 (WHERE id > :last_id) 或 延迟关联
SELECT *         → 显式列名
```

### 强制约束
```
主键        → CHAR(32)，UUID
多租户      → 所有表含 tenant_id CHAR(32)，所有 SQL 必须携带
时间戳      → create_time + update_time，由数据库自动维护
表注释      → 所有表必须有 COMMENT
```

### 窗口函数速查 (MySQL 8.0+)
```
ROW_NUMBER()   → 行号，去重保留一条
RANK()         → 跳号排名 (1,2,2,4)
DENSE_RANK()   → 连续排名 (1,2,2,3)
NTILE(N)       → 分 N 个桶
LAG(col, N)    → 前 N 行值
LEAD(col, N)   → 后 N 行值
SUM/AVG OVER   → 累计/移动平均
```

## 文件索引

| 文件 | 内容 | 何时读 |
|------|------|--------|
| `sql-dev/sql-patterns.md` | 分页、递归CTE、行列转换、窗口函数、去重、字符串/日期 | 写 SQL 不确定语法时 |
| `sql-dev/sql-tuning.md` | 索引失效、JOIN优化、子查询改写、排序优化、批量操作、锁 | 查询慢或审查性能时 |
| `sql-dev/sql-conventions.md` | 命名规范、格式化、强制约束、常见错误清单 | 生成 DDL 或审查规范时 |
| `design/design.md` | ERD 概念、关系基数、规范化 1NF-5NF、OLTP/数仓建模、命名标准 | 设计新表结构或数据架构时 |
| `performance/index-strategy.md` | B-Tree、复合索引、覆盖索引、列顺序规则 | 建索引或优化索引时 |
| `frameworks/mybatis-mysql.md` | Mapper 命名、XML 模板、租户隔离、N+1 陷阱 | MyBatis 开发时 |

## 常见多步骤流程

| 任务 | 步骤 |
|------|------|
| 诊断慢查询 | `EXPLAIN` → `sql-tuning.md`(改写) → `index-strategy.md`(索引) |
| 设计新表 | `design.md`(规范化) → `sql-conventions.md`(约束) → `index-strategy.md`(索引) → **询问是否写本地文件** |
| 数仓建模 | `design.md`(星型模式) → `index-strategy.md`(索引) |
| MyBatis 开发 | `mybatis-mysql.md`(模板) → `sql-conventions.md`(SQL 规范) |
| 代码审查 | `sql-conventions.md`(规范) → `sql-tuning.md`(性能) |

## 设计表结构后询问

**新设计表结构完成后，必须询问用户：**

> DDL 已生成，是否写到本地文件？如需写入，请提供文件路径。

