# MySQL SQL 模式

常用 SQL 查询模式速查。适用于 MySQL 8.0+。

## 目录

1. [分页查询](#1-分页查询)
2. [递归查询](#2-递归查询)
3. [行列转换](#3-行列转换)
4. [窗口函数](#4-窗口函数)
5. [存在性检查](#5-存在性检查)
6. [重复数据处理](#6-重复数据处理)
7. [条件逻辑](#7-条件逻辑)
8. [字符串和日期](#8-字符串和日期)

---

## 1. 分页查询

### LIMIT/OFFSET

```sql
-- 第 N 页，每页 M 条：LIMIT (N-1)*M, M
SELECT * FROM employees ORDER BY employee_id LIMIT 20 OFFSET 0;  -- 第 1 页
SELECT * FROM employees ORDER BY employee_id LIMIT 20 OFFSET 20; -- 第 2 页
```

### 延迟关联（大 OFFSET 优化）

```sql
-- 原始查询（慢）
SELECT * FROM employees ORDER BY hire_date LIMIT 100000, 20;

-- 优化：先定位主键，再关联回表
SELECT e.* FROM employees e
JOIN (
    SELECT employee_id FROM employees 
    ORDER BY hire_date 
    LIMIT 100000, 20
) d ON e.employee_id = d.employee_id;
```

### 游标分页（Keyset Pagination）

```sql
-- 记录上次最后一条的主键
SELECT * FROM employees 
WHERE employee_id > 100 
ORDER BY employee_id 
LIMIT 20;

-- 多列排序游标
SELECT * FROM employees 
WHERE (department_id, employee_id) > (50, 100) 
ORDER BY department_id, employee_id 
LIMIT 20;
```

### 带总计的分页

```sql
-- 窗口函数一次查询（MySQL 8.0+）
SELECT 
    employee_id,
    last_name,
    department_id,
    COUNT(*) OVER () AS total_count
FROM employees
WHERE department_id = 50
ORDER BY employee_id
LIMIT 20 OFFSET 40;
```

---

## 2. 递归查询

### CTE 递归（MySQL 8.0+）

```sql
-- 组织架构：员工 - 经理层级
WITH RECURSIVE org_hierarchy AS (
    -- 锚点成员：顶层（无经理）
    SELECT employee_id, last_name, manager_id, 1 AS level
    FROM employees WHERE manager_id IS NULL
    
    UNION ALL
    
    -- 递归成员：下级员工
    SELECT e.employee_id, e.last_name, e.manager_id, h.level + 1
    FROM employees e
    JOIN org_hierarchy h ON e.manager_id = h.employee_id
)
SELECT * FROM org_hierarchy ORDER BY level, last_name;
```

### 路径追踪

```sql
WITH RECURSIVE org_path AS (
    SELECT employee_id, last_name, manager_id,
           CAST(last_name AS CHAR(200)) AS path, 1 AS level
    FROM employees WHERE manager_id IS NULL
    
    UNION ALL
    
    SELECT e.employee_id, e.last_name, e.manager_id,
           CONCAT(h.path, ' -> ', e.last_name), h.level + 1
    FROM employees e
    JOIN org_path h ON e.manager_id = h.employee_id
)
SELECT * FROM org_path ORDER BY employee_id;
```

### 树形结构展平

```sql
WITH RECURSIVE dept_tree AS (
    SELECT department_id, department_name, parent_id, 0 AS depth,
           CAST(department_id AS CHAR(200)) AS path
    FROM departments WHERE parent_id IS NULL
    
    UNION ALL
    
    SELECT d.department_id, d.department_name, d.parent_id,
           t.depth + 1, CONCAT(t.path, ',', d.department_id)
    FROM departments d
    JOIN dept_tree t ON d.parent_id = t.department_id
)
SELECT department_id,
       CONCAT(REPEAT('  ', depth), department_name) AS indented_name,
       depth, path
FROM dept_tree ORDER BY path;
```

---

## 3. 行列转换

### 行转列（PIVOT）

```sql
-- 源数据：销售记录
-- +------------+------------+-------+
-- | sale_date  | product    | amount|

-- MySQL 无 PIVOT 语法，用 CASE + GROUP BY
SELECT sale_date,
    SUM(CASE WHEN product = 'Apple' THEN amount ELSE 0 END) AS apple_sales,
    SUM(CASE WHEN product = 'Banana' THEN amount ELSE 0 END) AS banana_sales,
    SUM(CASE WHEN product = 'Orange' THEN amount ELSE 0 END) AS orange_sales
FROM sales
GROUP BY sale_date
ORDER BY sale_date;
```

### 列转行（UNPIVOT）

```sql
-- 源数据：宽表
-- +------------+-------+--------+--------+
-- | sale_date  | Apple | Banana | Orange |

-- 用 UNION ALL
SELECT sale_date, 'Apple' AS product, apple_amount AS amount FROM sales
UNION ALL
SELECT sale_date, 'Banana', banana_amount FROM sales
UNION ALL
SELECT sale_date, 'Orange', orange_amount FROM sales;
```

---

## 4. 窗口函数

### ROW_NUMBER()

```sql
-- 每个部门工资排名
SELECT employee_id, last_name, department_id, salary,
    ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank
FROM employees;

-- 取每个部门工资最高的 3 人
SELECT * FROM (
    SELECT employee_id, last_name, department_id, salary,
           ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rn
    FROM employees
) ranked
WHERE rn <= 3;
```

### RANK() / DENSE_RANK()

```sql
-- RANK(): 跳号排名（1, 2, 2, 4）
SELECT employee_id, salary,
    RANK() OVER (ORDER BY salary DESC) AS salary_rank
FROM employees;

-- DENSE_RANK(): 连续排名（1, 2, 2, 3）
SELECT employee_id, salary,
    DENSE_RANK() OVER (ORDER BY salary DESC) AS salary_rank
FROM employees;
```

### NTILE()

```sql
-- 分组到 4 个桶
SELECT employee_id, salary,
    NTILE(4) OVER (ORDER BY salary DESC) AS salary_quartile
FROM employees;
```

### LAG() / LEAD()

```sql
-- LAG(): 访问前一行
SELECT employee_id, salary,
    LAG(salary, 1) OVER (ORDER BY employee_id) AS prev_salary,
    salary - LAG(salary, 1) OVER (ORDER BY employee_id) AS salary_diff
FROM employees;

-- 同比环比
SELECT sale_date, amount,
    LAG(amount, 1) OVER (ORDER BY sale_date) AS prev_day_amount,
    ROUND((amount - LAG(amount, 1) OVER (ORDER BY sale_date)) * 100.0 / 
          LAG(amount, 1) OVER (ORDER BY sale_date), 2) AS day_over_day_pct
FROM daily_sales;
```

### 移动平均/累计

```sql
-- 累计和
SELECT sale_date, amount,
    SUM(amount) OVER (ORDER BY sale_date ROWS UNBOUNDED PRECEDING) AS running_total
FROM daily_sales;

-- 移动平均（最近 7 天）
SELECT sale_date, amount,
    AVG(amount) OVER (ORDER BY sale_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg_7d
FROM daily_sales;
```

---

## 5. 存在性检查

```sql
-- EXISTS: 找到匹配即返回（高效）
SELECT * FROM departments d
WHERE EXISTS (SELECT 1 FROM employees e WHERE e.department_id = d.department_id);

-- NOT EXISTS: 正确处理 NULL
SELECT * FROM departments d
WHERE NOT EXISTS (SELECT 1 FROM employees e WHERE e.department_id = d.department_id);

-- LEFT JOIN + IS NULL（等价于 NOT EXISTS）
SELECT d.* FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
WHERE e.employee_id IS NULL;
```

---

## 6. 重复数据处理

### 查找重复

```sql
SELECT email, COUNT(*) AS cnt
FROM employees
GROUP BY email
HAVING COUNT(*) > 1;

-- 查看完整重复记录
SELECT e.* FROM employees e
JOIN (
    SELECT email FROM employees GROUP BY email HAVING COUNT(*) > 1
) dup ON e.email = dup.email
ORDER BY e.email;
```

### 删除重复（保留一条）

```sql
-- 自连接删除
DELETE e1 FROM employees e1
JOIN employees e2 ON e1.email = e2.email AND e1.employee_id > e2.employee_id;

-- 窗口函数（MySQL 8.0+）
DELETE FROM employees
WHERE employee_id IN (
    SELECT * FROM (
        SELECT employee_id FROM (
            SELECT employee_id,
                   ROW_NUMBER() OVER (PARTITION BY email ORDER BY employee_id) AS rn
            FROM employees
        ) ranked
        WHERE rn > 1
    ) t
);
```

### 去重查询

```sql
-- DISTINCT
SELECT DISTINCT department_id, city FROM departments;

-- 窗口函数去重（保留最新）
SELECT * FROM (
    SELECT e.*,
           ROW_NUMBER() OVER (PARTITION BY email ORDER BY last_modified DESC) AS rn
    FROM employees e
) deduped
WHERE rn = 1;
```

---

## 7. 条件逻辑

### CASE 表达式

```sql
-- 简单 CASE
SELECT employee_id, salary,
    CASE 
        WHEN salary < 5000 THEN 'Low'
        WHEN salary < 10000 THEN 'Medium'
        ELSE 'High'
    END AS salary_level
FROM employees;

-- 聚合中的 CASE
SELECT department_id,
    SUM(CASE WHEN salary < 5000 THEN 1 ELSE 0 END) AS low_count,
    SUM(CASE WHEN salary BETWEEN 5000 AND 10000 THEN 1 ELSE 0 END) AS mid_count,
    SUM(CASE WHEN salary > 10000 THEN 1 ELSE 0 END) AS high_count,
    COUNT(*) AS total
FROM employees
GROUP BY department_id;
```

### IF / IFNULL / NULLIF

```sql
-- IF 函数
SELECT employee_id, IF(salary > 10000, 'High', 'Low') AS salary_level FROM employees;

-- IFNULL（NULL 替换）
SELECT employee_id, IFNULL(commission_pct, 0) AS commission FROM employees;

-- COALESCE（返回第一个非 NULL）
SELECT employee_id,
    COALESCE(phone_mobile, phone_home, 'N/A') AS contact_phone
FROM employees;
```

---

## 8. 字符串和日期

### 字符串处理

```sql
-- 拼接
SELECT CONCAT(last_name, ', ', first_name) AS full_name FROM employees;
SELECT GROUP_CONCAT(last_name ORDER BY last_name SEPARATOR ', ') AS emp_list 
FROM employees GROUP BY department_id;

-- 截取
SELECT SUBSTRING(email, 1, INSTR(email, '@') - 1) AS username FROM employees;

-- 替换
SELECT REPLACE(phone, '-', '') AS phone_digits FROM employees;

-- 大小写
SELECT UPPER(last_name), LOWER(email) FROM employees;

-- 填充
SELECT LPAD(employee_id, 6, '0') AS padded_id FROM employees;
```

### 日期处理

```sql
-- 日期计算
SELECT hire_date,
    DATE_ADD(hire_date, INTERVAL 1 YEAR) AS one_year_later,
    DATE_SUB(hire_date, INTERVAL 1 MONTH) AS one_month_earlier,
    DATEDIFF(NOW(), hire_date) AS days_employed
FROM employees;

-- 日期提取
SELECT hire_date,
    YEAR(hire_date) AS hire_year,
    MONTH(hire_date) AS hire_month,
    DAYOFWEEK(hire_date) AS day_of_week,
    DATE_FORMAT(hire_date, '%Y-%m') AS hire_month_str
FROM employees;

-- 日期范围查询
SELECT * FROM employees
WHERE hire_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
AND hire_date < CURDATE();
```

---

## 快速参考

| 模式 | 语法 |
|------|------|
| 分页 | `LIMIT offset, count` 或 游标 `WHERE id > :last_id` |
| 递归 | `WITH RECURSIVE ... UNION ALL ...` |
| 排名 | `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` |
| 去重 | `ROW_NUMBER() ... WHERE rn = 1` |
| 存在 | `EXISTS (SELECT 1 FROM ...)` |
| 累计 | `SUM() OVER (ORDER BY ... ROWS UNBOUNDED PRECEDING)` |
| 移动平均 | `AVG() OVER (ORDER BY ... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` |
