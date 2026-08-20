# MySQL SQL 规范与强制约束

## 目录

1. [强制约束](#1-强制约束)
2. [命名规范](#2-命名规范)
3. [SQL 格式化](#3-sql-格式化)
4. [编写规则](#4-编写规则)
5. [常见错误速查](#5-常见错误速查)

---

## 1. 强制约束

所有 DDL 必须满足以下约束，无例外。

### 主键

```sql
-- 所有表主键必须使用 CHAR(32)，UUID
CREATE TABLE users (
    id CHAR(32) NOT NULL,
    PRIMARY KEY (id)
);
```

### 多租户

```sql
-- 所有业务表必须包含 tenant_id CHAR(32)
-- 所有增删改查 SQL 必须携带 tenant_id 条件
CREATE TABLE users (
    id CHAR(32) NOT NULL,
    tenant_id CHAR(32) NOT NULL,
    PRIMARY KEY (id)
);
```

### 时间戳

```sql
-- 所有表必须包含 create_time 和 update_time，由数据库自动维护
-- INSERT/UPDATE 语句不得显式写入这两个字段
CREATE TABLE users (
    id CHAR(32) NOT NULL,
    tenant_id CHAR(32) NOT NULL,
    create_time DATETIME NOT NULL DEFAULT NOW(),
    update_time DATETIME NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    PRIMARY KEY (id)
);
```

### 表注释

```sql
-- 所有表必须有 COMMENT
CREATE TABLE users (
    id CHAR(32) NOT NULL,
    -- ...
) COMMENT='用户表';
```

### 禁止显式指定引擎和字符集

```sql
-- 禁止
CREATE TABLE users (
    id CHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';

-- 正确
CREATE TABLE users (
    id CHAR(32) NOT NULL
) COMMENT='用户表';
```

> MySQL server 已配置默认引擎 InnoDB、默认字符集 utf8mb4。DDL 携带这些配置是冗余的。

---

## 2. 命名规范

### 通用规则

| 对象 | 规范 | 示例 |
|------|------|------|
| 表 | 复数名词，snake_case | `employees`, `order_items` |
| 列 | 描述性名词，snake_case | `employee_id`, `hire_date` |
| 主键 | `pk_<table>` | `pk_employees` |
| 唯一约束 | `uk_<table>_<column>` | `uk_employees_email` |
| 普通索引 | `idx_<table>_<column(s)>` | `idx_orders_order_date` |

### 避免保留字

常见误用保留字及替代：

| 保留字 | 替代 |
|--------|------|
| `date` | `order_date`, `hire_date` |
| `comment` | `order_comment`, `remark` |
| `status` | 可用但谨慎，建议 `order_status` |
| `group` | `group_name`, `dept_group` |
| `order` | `sort_order`, `display_order` |
| `key` | `sort_key`, `cache_key` |

完整列表参考 [MySQL 8.0 Keywords](https://dev.mysql.com/doc/refman/8.0/en/keywords.html)。

### 别名

```sql
-- 好：有意义别名
SELECT e.id, e.last_name, d.dept_name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id;

-- 坏：无意义别名
SELECT t1.id, t2.name FROM employees t1 JOIN departments t2 ...;
```

---

## 3. SQL 格式化

### 关键字大写

```sql
-- 推荐
SELECT e.id, e.last_name
FROM employees e
WHERE e.dept_id = 50
ORDER BY e.last_name;

-- 避免
select e.id from employees e where e.dept_id = 50;
```

### 缩进规则

- 每行一个列
- JOIN 条件单独一行
- 子查询/派生表缩进一级
- 复杂 WHERE 条件换行

```sql
SELECT e.id, e.last_name, d.dept_name
FROM employees e
INNER JOIN departments d ON e.dept_id = d.dept_id
LEFT JOIN locations l ON d.location_id = l.location_id
WHERE (e.dept_id = 50 OR e.dept_id = 60)
  AND (e.salary > 5000 OR e.bonus > 1000)
  AND e.hire_date >= '2020-01-01';

-- 派生表
SELECT d.dept_name, d.emp_count
FROM (
    SELECT dept_id, COUNT(*) AS emp_count
    FROM employees
    GROUP BY dept_id
) d
JOIN departments ON d.dept_id = departments.dept_id;
```

---

## 4. 编写规则

### SELECT

- 禁止 `SELECT *`，必须显式指定列名
- 表达式列必须有别名
- 谨慎使用 `DISTINCT`——可能掩盖 JOIN 笛卡尔积问题
- 查询数量用 `SELECT COUNT(*)`

### JOIN

- 必须用显式 `JOIN ... ON`，禁止隐式逗号连接
- 避免 `RIGHT JOIN`，统一用 `LEFT JOIN`
- 多表 JOIN 确保条件完整，避免笛卡尔积

### WHERE

- 列上禁止使用函数（索引失效）
- 禁止隐式类型转换（如 INT 列传入字符串）
- 禁止前导通配符 `LIKE '%xxx'`

### GROUP BY

- SELECT 中非聚合列必须在 GROUP BY 中（ONLY_FULL_GROUP_BY）
- WHERE 过滤行，HAVING 过滤组，不可混用

### ORDER BY

- 明确 ASC/DESC
- 避免表达式排序
- MySQL 8.0+ 支持 `NULLS FIRST/LAST`

### 子查询

- 优先 `EXISTS` 替代 `IN`
- 优先 `NOT EXISTS` 或 `LEFT JOIN + IS NULL` 替代 `NOT IN`（避免 NULL 陷阱）
- 避免相关子查询，改用 JOIN 派生表或窗口函数

### 注释

```sql
-- 单行注释说明业务逻辑
/* 多行注释用于复杂逻辑说明 */
-- 表和列用 COMMENT 属性
ALTER TABLE customer COMMENT '已完成账户创建的注册用户';
ALTER TABLE customer MODIFY email VARCHAR(255) COMMENT '唯一登录邮箱，存储前小写';
```

---

## 5. 常见错误速查

| 错误 | 后果 | 正确做法 |
|------|------|----------|
| `SELECT *` | 多余 I/O，覆盖索引失效 | 显式列名 |
| 列上函数 `WHERE YEAR(col)=2026` | 索引失效，全表扫描 | 范围查询 `col >= '2026-01-01' AND col < '2027-01-01'` |
| 隐式类型转换 `WHERE id=100`（id 是 CHAR） | 索引失效 | `WHERE id='100'` |
| 前导通配符 `LIKE '%xxx'` | 索引失效 | 全文索引或 ES |
| 隐式逗号 JOIN | 可读性差，易遗漏条件 | 显式 `JOIN ... ON` |
| `NOT IN` 子查询含 NULL | 结果为空 | `NOT EXISTS` 或 `LEFT JOIN + IS NULL` |
| 相关子查询 | 每行执行一次，性能差 | JOIN 派生表或窗口函数 |
| 大 OFFSET `LIMIT 100000,20` | 扫描 100020 行 | 游标分页或延迟关联 |
| 无索引外键 | JOIN 慢，父表 DML 锁升级 | 外键列必须建索引 |
| `INSERT/UPDATE` 显式写时间戳 | 覆盖数据库自动值 | 不写 `create_time`/`update_time` |
| 漏 `tenant_id` | 跨租户数据泄露 | 所有 SQL 必须携带 |
