# MySQL 索引策略

索引是 MySQL 高效定位行的主要机制。选择正确的索引类型、结构和列顺序对查询性能至关重要。

## 目录

1. [B-Tree 索引](#1-b-tree-索引)
2. [复合索引](#2-复合索引)
3. [覆盖索引](#3-覆盖索引)
4. [索引失效场景](#4-索引失效场景)
5. [最佳实践](#5-最佳实践)
6. [常见错误](#6-常见错误)

---

## 1. B-Tree 索引

B-Tree（平衡树）是默认和最多功能的索引类型，支持等值、范围、排序访问。

### 何时使用

- 高基数列（主键、唯一标识符、时间戳）
- `WHERE` 子句含等值或范围谓词的列
- 外键列（防止父表 DML 期间全表锁）
- `ORDER BY` 或 `GROUP BY` 受益于预排序的列

### 何时不使用

- 非常低基数列（Y/N 标志、性别）
- 几乎总是全表扫描访问的列
- 重 DML 列，索引开销超过查询收益

```sql
-- 简单 B-Tree 索引
CREATE INDEX idx_salary ON employees (salary);

-- 唯一 B-Tree 索引（强制唯一性并启用 UNIQUE SCAN）
CREATE UNIQUE INDEX idx_email ON employees (email);
```

---

## 2. 复合索引

复合索引覆盖两列或更多。**列顺序关键**，必须匹配查询访问模式。

### 列顺序规则

**规则 1: 前导列必须出现在查询谓词中**

索引才用于访问（范围或等值扫描）。跳过前导列的查询只能用索引跳过扫描，仅当前导列基数很低时高效。

**规则 2: 等值谓词列应先，范围谓词在后**

```sql
-- 索引 (DEPT_ID, SALARY)
CREATE INDEX idx_dept_sal ON employees (department_id, salary);

-- 使用索引（前导列在谓词中）
SELECT * FROM employees WHERE department_id = 50 AND salary > 5000;
-- 访问：INDEX RANGE SCAN on department_id=50, 过滤 salary>5000

-- 使用索引（仅前导列）
SELECT * FROM employees WHERE department_id = 50;
-- 访问：INDEX RANGE SCAN

-- 不高效使用索引（缺少前导列）
SELECT * FROM employees WHERE salary > 5000;
-- 访问：INDEX FULL SCAN 或 TABLE ACCESS FULL（取决于基数）
```

### 范围谓词的列顺序

```sql
-- 索引 (DEPT_ID, HIRE_DATE) — 好：WHERE dept=X AND hire_date BETWEEN...
CREATE INDEX idx_dept_date ON employees (department_id, hire_date);

-- 索引 (HIRE_DATE, DEPT_ID) — 仅当 hire_date 是等值时高效
CREATE INDEX idx_date_dept ON employees (hire_date, department_id);
```

### 何时复合索引胜过两个独立索引

- 查询过滤两列 → 单索引范围扫描 vs 两单独扫描 + 合并
- 索引覆盖所有需要列 → **仅索引扫描**（无表访问）
- `ORDER BY` 或 `GROUP BY` 可用索引顺序

---

## 3. 覆盖索引

覆盖索引包含查询需要的所有列（SELECT + WHERE），无需回表访问。

```sql
-- 无覆盖索引：索引扫描 + 表行获取（每行两 I/O）
-- 查询：SELECT last_name, salary FROM employees WHERE department_id = 60
-- 索引：idx_dept(department_id)
-- 执行：INDEX RANGE SCAN + TABLE ACCESS BY ROWID

-- 有覆盖索引：仅索引扫描（每行一 I/O）
-- 覆盖索引包含所有选择 + 过滤列：
CREATE INDEX idx_dept_cover ON employees (department_id, last_name, salary);

-- 验证
EXPLAIN SELECT department_id, last_name, salary FROM employees WHERE department_id = 50;
-- Extra: Using index（无表访问）
```

---

## 4. 索引失效场景

| 场景 | 示例 | 修复 |
|------|------|------|
| 列上函数 | `WHERE UPPER(last_name) = 'SMITH'` | 生成列 + 索引 |
| 隐式转换 | `WHERE id = '100'`（id 是 INT） | 类型匹配 |
| 前导通配符 | `WHERE name LIKE '%Smith'` | 全文索引 |
| OR 条件 | `WHERE dept_id = 50 OR salary > 10000` | UNION |
| IN 列表过大 | `WHERE dept_id IN (1,2,3...12)` | 临时表 + JOIN |

详见 `sql-dev/sql-tuning.md`。

---

## 5. 最佳实践

- **始终在外键列创建索引** — 避免锁争用和不必要全扫描
- **高频 OLTP 查询用覆盖索引** — 消除表行获取步骤
- **复合索引匹配查询模式** — 等值列在前，范围列在后
- **定期监控未用索引** — 删除冗余索引减少 DML 开销
- **降序索引（MySQL 8.0+）** — `ORDER BY col DESC` 场景

```sql
-- 降序索引（MySQL 8.0+）
CREATE INDEX idx_dept_sal_desc ON employees (department_id, salary DESC);
```

---

## 6. 常见错误

| 错误 | 影响 | 修复 |
|------|------|------|
| B-Tree 索引建在 Y/N 标志列 | 很少使用，DML 开销无收益 | 考虑其他方案或无索引 |
| 复合索引列顺序错误 | 常见查询不使用索引 | 等值列先，然后范围 |
| 不索引外键列 | 父 DML 锁升级；慢 JOIN | 必须索引外键列 |
| 过度索引 | DML 性能下降，存储浪费 | 监控未用索引并删除 |
| 索引不包含 SELECT 列 | 回表 I/O | 考虑覆盖索引 |

---

## 快速参考

```sql
-- 复合索引：等值列在前，范围列在后
CREATE INDEX idx_dept_sal ON t(department_id, salary);  -- WHERE dept_id=? AND salary>?

-- 覆盖索引：包含 SELECT 和 WHERE 所有列
CREATE INDEX idx_cover ON t(dept_id, last_name, salary);  -- SELECT last_name,salary WHERE dept_id=?

-- 降序索引（MySQL 8.0+）
CREATE INDEX idx_sal_desc ON t(department_id, salary DESC);  -- ORDER BY salary DESC

-- 关联列必须索引
CREATE INDEX idx_dept_id ON employees(department_id);
```
