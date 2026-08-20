# MySQL 数据设计与建模

## 目录

1. [建模层次](#1-建模层次)
2. [ERD 核心概念](#2-erd-核心概念)
3. [关系基数](#3-关系基数)
4. [规范化](#4-规范化)
5. [OLTP 建模](#5-oltp-建模)
6. [数仓维度建模](#6-数仓维度建模)
7. [MySQL 物理模型](#7-mysql-物理模型)
8. [命名规范](#8-命名规范)
9. [常见错误](#9-常见错误)

---

## 1. 建模层次

| 层次 | 用途 | 内容 |
|------|------|------|
| **概念** | 与业务干系人沟通 | 实体（客户、订单、产品）、关系（客户下订单） |
| **逻辑** | 平台无关的技术设计 | 表、列、数据类型（通用）、主键、规范化（3NF） |
| **物理** | MySQL 专用 DDL | MySQL 数据类型、InnoDB 引擎、索引、字符集 |

---

## 2. ERD 核心概念

### 实体

- **强实体**: 独立存在（`CUSTOMER`、`PRODUCT`）
- **弱实体**: 依赖强实体存在（`ORDER_ITEM` 依赖 `ORDER`）

### 属性

| 类型 | 描述 | MySQL 映射 |
|------|------|-----------|
| 简单 | 单值、原子 | 标准列 |
| 复合 | 可拆分（如全名） | 多列（`first_name` + `last_name`） |
| 派生 | 计算值 | 生成列或视图 |
| 多值 | 多个值 | 子表（避免数组/CSV） |

---

## 3. 关系基数

### 一对一 (1:1)

实践中罕见，通常表明可合并表或安全拆分。

```sql
CREATE TABLE employee (
    employee_id   INT          NOT NULL AUTO_INCREMENT,
    full_name     VARCHAR(100) NOT NULL,
    CONSTRAINT pk_employee PRIMARY KEY (employee_id)
);

CREATE TABLE employee_security (
    employee_id   INT          NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    last_login    DATETIME,
    CONSTRAINT pk_emp_security PRIMARY KEY (employee_id)
);
```

### 一对多 (1:N)

最常见。"多"端持外键。

```sql
CREATE TABLE department (
    department_id   INT          NOT NULL AUTO_INCREMENT,
    department_name VARCHAR(100) NOT NULL,
    CONSTRAINT pk_department PRIMARY KEY (department_id)
);

CREATE TABLE employee (
    employee_id     INT          NOT NULL AUTO_INCREMENT,
    full_name       VARCHAR(100) NOT NULL,
    department_id   INT          NOT NULL,
    hire_date       DATE         NOT NULL,
    CONSTRAINT pk_employee PRIMARY KEY (employee_id)
);

-- 外键索引（MySQL 不自动创建）
CREATE INDEX idx_emp_dept ON employee(department_id);
```

### 多对多 (M:N)

通过**关联表**解析。

```sql
CREATE TABLE student (
    student_id  INT          NOT NULL AUTO_INCREMENT,
    full_name   VARCHAR(100) NOT NULL,
    CONSTRAINT pk_student PRIMARY KEY (student_id)
);

CREATE TABLE course (
    course_id   INT          NOT NULL AUTO_INCREMENT,
    course_name VARCHAR(200) NOT NULL,
    CONSTRAINT pk_course PRIMARY KEY (course_id)
);

-- 关联表含自身属性
CREATE TABLE enrollment (
    student_id    INT      NOT NULL,
    course_id     INT      NOT NULL,
    enrolled_date DATE     NOT NULL,
    grade         VARCHAR(2),
    CONSTRAINT pk_enrollment PRIMARY KEY (student_id, course_id)
);
```

### 自引用（递归）关系

常见于层次数据（组织架构、分类）。

```sql
CREATE TABLE category (
    category_id        INT          NOT NULL AUTO_INCREMENT,
    category_name      VARCHAR(100) NOT NULL,
    parent_category_id INT          COMMENT 'NULL 表示根节点',
    CONSTRAINT pk_category PRIMARY KEY (category_id)
);
```

MySQL 8.0+ 递归 CTE 遍历：

```sql
WITH RECURSIVE category_tree AS (
    SELECT category_id, category_name, 0 AS depth,
           CAST(category_name AS CHAR(1000)) AS full_path
    FROM category WHERE parent_category_id IS NULL
    
    UNION ALL
    
    SELECT c.category_id, c.category_name, ct.depth + 1,
           CONCAT(ct.full_path, ' > ', c.category_name)
    FROM category c
    JOIN category_tree ct ON c.parent_category_id = ct.category_id
)
SELECT * FROM category_tree ORDER BY full_path;
```

---

## 4. 规范化

### 第一范式 (1NF)

- 所有列值原子（不可分割）
- 无重复组或数组
- 每行唯一可识别（有主键）

```sql
-- 坏：CSV 存多值
CREATE TABLE project (
    project_id   INT,
    team_members VARCHAR(4000)  -- "101,102,103" — 不可查询
);

-- 好：子表
CREATE TABLE project_member (
    project_id   INT NOT NULL,
    employee_id  INT NOT NULL,
    CONSTRAINT pk_project_member PRIMARY KEY (project_id, employee_id)
);
```

### 第二范式 (2NF)

- 在 1NF 基础上
- 非键属性完全依赖**整个**主键（无部分依赖）

```sql
-- 坏：复合 PK (order_id + product_id)，但 product_name 仅依赖 product_id
CREATE TABLE order_item (
    order_id    INT, product_id  INT, quantity  INT,
    product_name VARCHAR(200),  -- 部分依赖！
    CONSTRAINT pk_order_item PRIMARY KEY (order_id, product_id)
);

-- 好：拆分
CREATE TABLE product (
    product_id    INT          NOT NULL AUTO_INCREMENT,
    product_name  VARCHAR(200) NOT NULL,
    CONSTRAINT pk_product PRIMARY KEY (product_id)
);

CREATE TABLE order_item (
    order_id    INT NOT NULL, product_id  INT NOT NULL,
    quantity    INT NOT NULL,
    CONSTRAINT pk_order_item PRIMARY KEY (order_id, product_id)
);
```

### 第三范式 (3NF)

- 在 2NF 基础上
- 无传递依赖（非键属性不依赖其他非键属性）

```sql
-- 坏：传递依赖
EMPLOYEE(employee_id, name, department_id, department_name, department_location)

-- 好：拆分
CREATE TABLE department (...);
CREATE TABLE employee (..., department_id INT, ...);
```

### BCNF、4NF、5NF

- **BCNF**: 每个决定因素是候选键（3NF 更严格）
- **4NF**: 无多值依赖（独立多值事实分表）
- **5NF**: 无非候选键隐含的连接依赖（理论性，实践中罕见）

---

## 5. OLTP 建模

OLTP 系统特征：高量写入、短事务、高并发、行级锁关键、严格 3NF。

```sql
-- 电商 OLTP 模式
CREATE TABLE customers (
    customer_id   INT          NOT NULL AUTO_INCREMENT,
    email         VARCHAR(255) NOT NULL,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id),
    CONSTRAINT uq_customers_email UNIQUE (email)
) COMMENT='客户主数据';

CREATE TABLE orders (
    order_id      INT          NOT NULL AUTO_INCREMENT,
    customer_id   INT          NOT NULL,
    order_date    DATETIME     DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status        VARCHAR(20)  DEFAULT 'PENDING' NOT NULL,
    total_amount  DECIMAL(14,2),
    CONSTRAINT pk_orders PRIMARY KEY (order_id)
) COMMENT='订单头';

-- 外键索引
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
```

---

## 6. 数仓维度建模

数据仓库优先读性能，用**维度建模**（星型模式）。

### 星型模式结构

```
                 dim_date
                    |
dim_customer -- fact_sales -- dim_product
                    |
              dim_store
```

### 维度表

- 代理主键（非业务键）
- 描述属性（宽表，反规范化）
- 缓慢变化维度（SCD Type 2）

```sql
CREATE TABLE dim_date (
    date_key        INT          NOT NULL COMMENT 'YYYYMMDD 代理键',
    full_date       DATE         NOT NULL,
    day_of_week     VARCHAR(10)  NOT NULL,
    month_number    TINYINT      NOT NULL,
    year_number     SMALLINT     NOT NULL,
    is_weekend      CHAR(1)      DEFAULT 'N' NOT NULL,
    is_holiday      CHAR(1)      DEFAULT 'N' NOT NULL,
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
) COMMENT='日期维度';

CREATE TABLE dim_customer (
    customer_key    INT          NOT NULL AUTO_INCREMENT,
    customer_bk     VARCHAR(50)  NOT NULL COMMENT '业务键',
    full_name       VARCHAR(200) NOT NULL,
    city            VARCHAR(100),
    state_province  VARCHAR(100),
    country_code    CHAR(2),
    effective_from  DATETIME     NOT NULL,
    effective_to    DATETIME,
    is_current      CHAR(1)      DEFAULT 'Y' NOT NULL,
    CONSTRAINT pk_dim_customer PRIMARY KEY (customer_key)
) COMMENT='客户维度 (SCD Type 2)';
```

### 事实表

- 外键关联维度表
- 数值度量（数量、金额）
- 退化维度（订单号）
- 分区（按时间）

```sql
CREATE TABLE fact_sales (
    sales_id          BIGINT        NOT NULL AUTO_INCREMENT,
    date_key          INT           NOT NULL,
    customer_key      INT           NOT NULL,
    product_key       INT           NOT NULL,
    store_key         INT           NOT NULL,
    order_number      VARCHAR(50)   COMMENT '退化维度',
    quantity_sold     INT           NOT NULL,
    unit_price        DECIMAL(12,2) NOT NULL,
    gross_revenue     DECIMAL(14,2) NOT NULL,
    sale_timestamp    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fact_sales PRIMARY KEY (sales_id)
) COMMENT='销售事实表'
PARTITION BY RANGE (date_key) (
    PARTITION p_2023 VALUES LESS THAN (20240101),
    PARTITION p_2024 VALUES LESS THAN (20250101),
    PARTITION p_2025 VALUES LESS THAN (20260101),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 事实表索引
CREATE INDEX idx_fs_date ON fact_sales(date_key);
CREATE INDEX idx_fs_customer ON fact_sales(customer_key);
CREATE INDEX idx_fs_product ON fact_sales(product_key);
CREATE INDEX idx_fs_store ON fact_sales(store_key);
```

---

## 7. MySQL 物理模型

### 数据类型选择

```sql
CREATE TABLE physical_model_example (
    -- 数值
    id              INT           NOT NULL AUTO_INCREMENT,
    amount          DECIMAL(18,4) NOT NULL COMMENT '金融精度',
    percentage      DECIMAL(5,2)  NOT NULL COMMENT '999.99',

    -- 字符
    short_code      CHAR(3)       NOT NULL COMMENT '固定长度：ISO 代码',
    description     VARCHAR(4000) NOT NULL,
    large_text      TEXT          COMMENT '>4000 字符',
    json_data       JSON          COMMENT 'MySQL 5.7+',

    -- 日期/时间
    event_date      DATE          NOT NULL,
    created_at      DATETIME(6)   NOT NULL COMMENT '微秒精度',
    updated_at      DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    -- 二进制
    file_content    LONGBLOB,
    thumbnail       BLOB,

    CONSTRAINT pk_pme PRIMARY KEY (id)
);
```

### 生成列（派生属性）

```sql
CREATE TABLE product (
    product_id      INT          NOT NULL AUTO_INCREMENT,
    unit_price      DECIMAL(12,2) NOT NULL,
    tax_rate        DECIMAL(5,4)  NOT NULL,
    price_with_tax  DECIMAL(12,2) GENERATED ALWAYS AS (unit_price * (1 + tax_rate)) STORED,
    CONSTRAINT pk_product PRIMARY KEY (product_id)
);
```

---

## 8. 命名规范

| 对象 | 规范 | 示例 |
|------|------|------|
| 表 | 复数名词，snake_case | `customers`, `order_items` |
| 列 | 描述性名词，snake_case | `customer_id`, `order_date` |
| 主键 | `pk_<table>` | `pk_customers` |
| 唯一约束 | `uk_<table>_<column>` | `uk_customers_email` |
| 索引 | `idx_<table>_<column(s)>` | `idx_orders_order_date` |

### 避免保留字

常见误用：`date`, `order`, `group`, `comment`, `key`, `status`。

```sql
-- 不好
CREATE TABLE orders (order_id INT, `date` DATE, `comment` VARCHAR(500));

-- 好
CREATE TABLE orders (order_id INT, order_date DATE, order_comment VARCHAR(500));
```

---

## 9. 常见错误

| 错误 | 问题 | 修复 |
|------|------|------|
| 单列存多值（CSV） | 不可查询，不可维护 | 子表 |
| AUTO_INCREMENT 作全局唯一 | 分布式环境失效 | UUID |
| OLTP 过度规范化 | JOIN 过多性能差 | 适度反规范化 |
| 唯一约束 NULL 语义 | 多行可存 NULL | 生成列 + 唯一索引 |
| VARCHAR 存固定代码 | 存储浪费 | CHAR(2)/CHAR(3) |
| 漏外键索引 | JOIN 慢，父表 DML 锁升级 | 外键列必须建索引 |
| 维度表用业务键 | 业务键变化导致历史断裂 | 代理键 + SCD Type 2 |
