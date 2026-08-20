# MySQL SQL 调优

系统性 SQL 性能优化指南。调优目标：最小化 I/O、减少 CPU 消耗、降低锁争用。

## 目录

1. [EXPLAIN 解读](#1-explain-解读)
2. [索引失效场景](#2-索引失效场景)
3. [JOIN 优化](#3-join-优化)
4. [子查询改写](#4-子查询改写)
5. [排序和分组优化](#5-排序和分组优化)
6. [分页优化](#6-分页优化)
7. [批量操作](#7-批量操作)
8. [锁和并发](#8-锁和并发)

---

## 1. EXPLAIN 解读

```sql
EXPLAIN SELECT * FROM employees WHERE department_id = 50 AND salary > 5000;
```

### 关键列

| 列 | 含义 | 好/坏 |
|----|------|-------|
| `type` | 访问类型 | `system` > `const` > `eq_ref` > `ref` > `range` > `index` > `ALL` |
| `key` | 实际使用的索引 | `NULL` 表示未用索引 |
| `rows` | 扫描行数 | 越少越好 |
| `Extra` | 额外信息 | `Using index` 好，`Using filesort`/`Using temporary` 坏 |

### type 详解

```
system      -- 表只有一行
const       -- 主键/唯一索引等值匹配
eq_ref      -- 主键/唯一索引 JOIN（每驱动表行匹配一行）
ref         -- 普通索引等值匹配
range       -- 索引范围扫描
index       -- 全索引扫描
ALL         -- 全表扫描（最坏）
```

---

## 2. 索引失效场景

### 函数应用于列

```sql
-- 坏：索引失效
SELECT * FROM employees WHERE UPPER(last_name) = 'SMITH';
SELECT * FROM orders WHERE YEAR(order_date) = 2026;

-- 好：生成列 + 索引
ALTER TABLE employees 
ADD last_name_upper VARCHAR(100) 
GENERATED ALWAYS AS (UPPER(last_name)) STORED;
CREATE INDEX idx_last_name_upper ON employees(last_name_upper);

SELECT * FROM employees WHERE last_name_upper = 'SMITH';

-- 好：范围查询
SELECT * FROM orders 
WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01';
```

### 隐式类型转换

```sql
-- 坏：字符串列传数字
SELECT * FROM employees WHERE employee_id = '100';  -- employee_id 是 INT

-- 坏：字符集不匹配导致 JOIN 隐式转换
SELECT * FROM employees e
JOIN departments d ON e.dept_code = d.dept_code;  -- 两边字符集不同

-- 好：类型匹配
SELECT * FROM employees WHERE employee_id = 100;
```

### 前导通配符

```sql
-- 坏：前导通配符
SELECT * FROM employees WHERE last_name LIKE '%Smith';

-- 好：全文索引（MySQL 5.6+）
CREATE FULLTEXT INDEX idx_last_name_ft ON employees(last_name);
SELECT * FROM employees WHERE MATCH(last_name) AGAINST('Smith');
```

### OR 条件

```sql
-- 坏：OR 一侧无索引
SELECT * FROM employees WHERE department_id = 50 OR salary > 10000;

-- 好：UNION
SELECT * FROM employees WHERE department_id = 50
UNION
SELECT * FROM employees WHERE salary > 10000;
```

### IN 列表过大

```sql
-- 坏：IN 列表过长
SELECT * FROM employees WHERE department_id IN (1,2,3,4,5,6,7,8,9,10,11,12);

-- 好：临时表 + JOIN
CREATE TEMPORARY TABLE dept_list (dept_id INT);
INSERT INTO dept_list VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12);
SELECT e.* FROM employees e JOIN dept_list d ON e.department_id = d.dept_id;
```

---

## 3. JOIN 优化

### JOIN 顺序

```sql
-- 优化器通常自动选择正确顺序
-- 小表驱动大表原则

-- 强制 JOIN 顺序（仅当优化器选择错误时）
SELECT STRAIGHT_JOIN e.last_name, d.dept_name
FROM employees e  -- 先扫描小表
JOIN departments d ON e.department_id = d.department_id;
```

### JOIN 类型

```sql
-- EXISTS 通常比 IN 快（半连接，找到匹配即停止）
SELECT * FROM departments d
WHERE EXISTS (
    SELECT 1 FROM employees e WHERE e.department_id = d.department_id
);

-- NOT EXISTS 或 LEFT JOIN + IS NULL 替代 NOT IN
SELECT * FROM departments d
WHERE NOT EXISTS (
    SELECT 1 FROM employees e WHERE e.department_id = d.department_id
);

-- 等价于
SELECT d.* FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
WHERE e.employee_id IS NULL;
```

---

## 4. 子查询改写

### 相关子查询

```sql
-- 坏：相关子查询每外层行执行一次
SELECT * FROM employees e
WHERE salary > (
    SELECT AVG(salary) FROM employees 
    WHERE department_id = e.department_id
);

-- 好：JOIN + 派生表
SELECT e.* FROM employees e
JOIN (
    SELECT department_id, AVG(salary) AS avg_sal
    FROM employees
    GROUP BY department_id
) d ON e.department_id = d.department_id
WHERE e.salary > d.avg_sal;

-- 或用窗口函数（MySQL 8.0+）
SELECT * FROM (
    SELECT e.*, AVG(salary) OVER (PARTITION BY department_id) AS avg_sal
    FROM employees e
) derived
WHERE salary > avg_sal;
```

### IN 子查询

```sql
-- 坏：IN 子查询可能物化
SELECT * FROM employees
WHERE department_id IN (
    SELECT department_id FROM departments WHERE location = 'Beijing'
);

-- 好：EXISTS
SELECT * FROM employees e
WHERE EXISTS (
    SELECT 1 FROM departments d 
    WHERE d.department_id = e.department_id AND d.location = 'Beijing'
);

-- 更好：JOIN
SELECT DISTINCT e.* FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE d.location = 'Beijing';
```

### NOT IN 子查询

```sql
-- 坏：NOT IN 对 NULL 值敏感
SELECT * FROM employees
WHERE department_id NOT IN (
    SELECT department_id FROM departments WHERE status = 'inactive'
);

-- 好：NOT EXISTS
SELECT * FROM employees e
WHERE NOT EXISTS (
    SELECT 1 FROM departments d 
    WHERE d.department_id = e.department_id AND d.status = 'inactive'
);

-- 更好：LEFT JOIN + IS NULL
SELECT e.* FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id AND d.status = 'inactive'
WHERE d.department_id IS NULL;
```

---

## 5. 排序和分组优化

### 避免文件排序

```sql
-- 坏：ORDER BY 无索引
SELECT * FROM employees ORDER BY hire_date;

-- 好：添加索引
CREATE INDEX idx_hire_date ON employees(hire_date);

-- 坏：ORDER BY 表达式
SELECT * FROM employees ORDER BY YEAR(hire_date);

-- 好：生成列 + 索引
ALTER TABLE employees 
ADD hire_year INT GENERATED ALWAYS AS (YEAR(hire_date)) STORED;
CREATE INDEX idx_hire_year ON employees(hire_year);

-- 坏：ORDER BY 多列方向不一致
SELECT * FROM employees ORDER BY department_id ASC, salary DESC;

-- 好：MySQL 8.0+ 支持降序索引
CREATE INDEX idx_dept_sal ON employees(department_id, salary DESC);
```

### LIMIT 优化

```sql
-- 坏：大 OFFSET
SELECT * FROM employees ORDER BY employee_id LIMIT 100000, 20;

-- 好：延迟关联
SELECT e.* FROM employees e
JOIN (
    SELECT employee_id FROM employees 
    ORDER BY employee_id LIMIT 100000, 20
) d ON e.employee_id = d.employee_id;

-- 好：游标分页
SELECT * FROM employees 
WHERE employee_id > :last_id 
ORDER BY employee_id LIMIT 20;
```

---

## 6. 分页优化

### 大 OFFSET 问题

```sql
-- OFFSET 100000 扫描 100020 行，丢弃前 100000 行
SELECT * FROM employees ORDER BY hire_date LIMIT 100000, 20;
```

### 延迟关联

```sql
-- 先定位主键（覆盖索引扫描），再关联回表
SELECT e.* FROM employees e
JOIN (
    SELECT employee_id FROM employees 
    ORDER BY hire_date 
    LIMIT 100000, 20
) d ON e.employee_id = d.employee_id;
```

### 游标分页（推荐）

```sql
-- 记录上次最后一条的主键
-- 第 1 页
SELECT * FROM employees ORDER BY employee_id LIMIT 20;
-- 最后一条 employee_id = 100

-- 第 2 页（从上次位置继续）
SELECT * FROM employees 
WHERE employee_id > 100 
ORDER BY employee_id LIMIT 20;

-- 多列排序游标
SELECT * FROM employees 
WHERE (department_id, employee_id) > (50, 100) 
ORDER BY department_id, employee_id LIMIT 20;
```

---

## 7. 批量操作

### 批量插入

```sql
-- 坏：单行插入
INSERT INTO employees (last_name, email) VALUES ('Smith', 'smith@example.com');
INSERT INTO employees (last_name, email) VALUES ('Jones', 'jones@example.com');

-- 好：多行 VALUES
INSERT INTO employees (last_name, email) VALUES 
('Smith', 'smith@example.com'),
('Jones', 'jones@example.com'),
('Brown', 'brown@example.com');
```

### 批量更新

```sql
-- 坏：逐行更新
UPDATE employees SET salary = salary * 1.1 WHERE employee_id = 1;
UPDATE employees SET salary = salary * 1.1 WHERE employee_id = 2;

-- 好：CASE 批量更新
UPDATE employees SET salary = CASE employee_id
    WHEN 1 THEN salary * 1.1
    WHEN 2 THEN salary * 1.15
    WHEN 3 THEN salary * 1.2
    ELSE salary
END
WHERE employee_id IN (1, 2, 3);
```

### 批量删除

```sql
-- 坏：大事务删除
DELETE FROM orders WHERE order_date < '2020-01-01';  -- 可能锁表

-- 好：分批删除
DELETE FROM orders WHERE order_date < '2020-01-01' LIMIT 1000;
-- 循环执行直到影响行数 = 0
```

---

## 8. 锁和并发

### 减少锁等待

```sql
-- 坏：长事务持有锁
START TRANSACTION;
UPDATE employees SET salary = salary * 1.1 WHERE department_id = 1;
-- 长时间业务逻辑...
COMMIT;

-- 好：短事务
START TRANSACTION;
UPDATE employees SET salary = salary * 1.1 WHERE department_id = 1;
COMMIT;
-- 处理业务逻辑...

-- 好：按主键范围分批
UPDATE employees SET salary = salary * 1.1 
WHERE department_id = 1 AND employee_id BETWEEN 1 AND 100;
UPDATE employees SET salary = salary * 1.1 
WHERE department_id = 1 AND employee_id BETWEEN 101 AND 200;
```

### 乐观锁

```sql
-- 悲观锁（SELECT ... FOR UPDATE）
START TRANSACTION;
SELECT * FROM employees WHERE employee_id = 100 FOR UPDATE;
UPDATE employees SET salary = salary * 1.1 WHERE employee_id = 100;
COMMIT;

-- 乐观锁（版本号）
-- 表结构增加 version 列
ALTER TABLE employees ADD version INT DEFAULT 0;

-- 读取
SELECT employee_id, salary, version FROM employees WHERE employee_id = 100;

-- 更新（检查版本号）
UPDATE employees 
SET salary = salary * 1.1, version = version + 1 
WHERE employee_id = 100 AND version = :old_version;

-- 检查影响行数，0 表示被其他事务修改
```

---

## 快速参考

| 问题 | 解决方案 |
|------|----------|
| 全表扫描 | 检查 EXPLAIN type，添加/优化索引 |
| 索引失效 | 避免列上函数、隐式转换、前导通配符 |
| JOIN 慢 | 检查外键索引，小表驱动大表 |
| 子查询慢 | 改写为 JOIN 或窗口函数 |
| 大 OFFSET | 游标分页或延迟关联 |
| 锁等待 | 短事务，分批处理，乐观锁 |
