# MyBatis + MySQL 集成

## 目录

1. [Mapper 命名规范](#1-mapper-命名规范)
2. [SQL 规范](#2-sql-规范)
3. [基础 CRUD 模板](#3-基础-crud-模板)
4. [动态 SQL](#4-动态-sql)
5. [租户隔离](#5-租户隔离)
6. [批量操作](#6-批量操作)
7. [结果映射](#7-结果映射)
8. [N+1 查询陷阱](#8-n1-查询陷阱)
9. [MySQL 特定功能](#9-mysql-特定功能)
10. [常见错误](#10-常见错误)

---

## 1. Mapper 命名规范

| 操作类型 | 命名格式 | 示例 |
|---------|---------|------|
| 分页查询 | `pageByXxx` | `pageByName` |
| 获取单个对象 | `getXxx` / `getByXxx` | `getById` |
| 获取列表 | `listXxx` / `listByXxx` | `listByStatus` |
| 获取数量 | `countXxx` / `countByXxx` | `countByStatus` |
| 插入操作 | `insert` / `insertSelective` | `insertSelective` |
| 删除操作 | `deleteXxx` / `deleteByXxx` | `deleteById` |
| 更新操作 | `update` / `updateByXxx` / `updateSelective` / `updateSelectiveByXxx` | `updateSelectiveById` |
| 批量操作 | `batchXxx` | `batchInsert` |

> 插入/更新操作优先使用 `Selective` 方法（仅处理非空字段）。

---

## 2. SQL 规范

- SQL 语句职责单一、语义明确，禁止编写复杂、多条件、多场景复用的「大而全」SQL
- SQL 关键字必须使用大写（`SELECT`、`FROM`、`WHERE`）
- 禁止使用 `SELECT *`，必须显式指定字段
- 查询数量用 `SELECT COUNT(*)`
- `INSERT` / `UPDATE` 语句不得显式写入 `create_time`、`update_time`，由数据库自动维护
- 所有按 `tenantId` 隔离的业务表，增/删/改/查必须携带 `tenant_id` 条件

---

## 3. 基础 CRUD 模板

### 模型类

```java
package com.example.model;

import java.math.BigDecimal;
import java.time.LocalDate;

public class Employee {
    private String     employeeId;      // UuidUtil.create()
    private String     lastName;
    private String     email;
    private BigDecimal salary;
    private LocalDate  hireDate;
    private String     departmentId;
    private String     tenantId;        // 租户 ID
    // getters / setters
}
```

### Mapper 接口

```java
package com.example.mapper;

import com.example.model.Employee;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface EmployeeMapper {
    Employee getById(@Param("id") String id, @Param("tenantId") String tenantId);
    List<Employee> listByDept(@Param("deptId") String deptId, @Param("tenantId") String tenantId);
    int countByDept(@Param("deptId") String deptId, @Param("tenantId") String tenantId);
    int insertSelective(Employee employee);
    int updateSelectiveById(Employee employee);
    int deleteById(@Param("id") String id, @Param("tenantId") String tenantId);
}
```

### Mapper XML

```xml
<mapper namespace="com.example.mapper.EmployeeMapper">

    <resultMap id="employeeMap" type="Employee">
        <id     column="employee_id"   property="employeeId"/>
        <result column="last_name"     property="lastName"/>
        <result column="email"         property="email"/>
        <result column="salary"        property="salary"/>
        <result column="hire_date"     property="hireDate"/>
        <result column="department_id" property="departmentId"/>
        <result column="tenant_id"     property="tenantId"/>
    </resultMap>

    <!-- 获取单个对象 -->
    <select id="getById" resultMap="employeeMap">
        SELECT employee_id, last_name, email, salary, hire_date, department_id, tenant_id
        FROM   employees
        WHERE  employee_id = #{id}
        AND    tenant_id   = #{tenantId}
    </select>

    <!-- 获取列表 -->
    <select id="listByDept" resultMap="employeeMap">
        SELECT employee_id, last_name, salary, department_id
        FROM   employees
        WHERE  department_id = #{deptId}
        AND    tenant_id     = #{tenantId}
        ORDER BY last_name
    </select>

    <!-- 获取数量 -->
    <select id="countByDept" resultType="int">
        SELECT COUNT(*)
        FROM   employees
        WHERE  department_id = #{deptId}
        AND    tenant_id     = #{tenantId}
    </select>

    <!-- 插入（仅非空字段） -->
    <insert id="insertSelective">
        INSERT INTO employees
        <trim prefix="(" suffix=")" suffixOverrides=",">
            <if test="employeeId != null">employee_id,</if>
            <if test="lastName != null">last_name,</if>
            <if test="email != null">email,</if>
            <if test="salary != null">salary,</if>
            <if test="hireDate != null">hire_date,</if>
            <if test="departmentId != null">department_id,</if>
            <if test="tenantId != null">tenant_id,</if>
        </trim>
        <trim prefix="VALUES (" suffix=")" suffixOverrides=",">
            <if test="employeeId != null">#{employeeId},</if>
            <if test="lastName != null">#{lastName},</if>
            <if test="email != null">#{email},</if>
            <if test="salary != null">#{salary},</if>
            <if test="hireDate != null">#{hireDate},</if>
            <if test="departmentId != null">#{departmentId},</if>
            <if test="tenantId != null">#{tenantId},</if>
        </trim>
    </insert>

    <!-- 更新（仅非空字段） -->
    <update id="updateSelectiveById">
        UPDATE employees
        <set>
            <if test="lastName != null">last_name = #{lastName},</if>
            <if test="email != null">email = #{email},</if>
            <if test="salary != null">salary = #{salary},</if>
            <if test="hireDate != null">hire_date = #{hireDate},</if>
            <if test="departmentId != null">department_id = #{departmentId},</if>
        </set>
        WHERE employee_id = #{employeeId}
        AND   tenant_id   = #{tenantId}
    </update>

    <!-- 删除 -->
    <delete id="deleteById">
        DELETE FROM employees WHERE employee_id = #{id} AND tenant_id = #{tenantId}
    </delete>

</mapper>
```

---

## 4. 动态 SQL

### 多条件 WHERE

```java
// Mapper 接口
List<Employee> search(@Param("lastName") String lastName,
        @Param("deptId") String deptId,
        @Param("minSal") BigDecimal minSal);
```

```xml
<select id="search" resultMap="employeeMap">
    SELECT employee_id, last_name, salary, department_id
    FROM   employees
    <where>
        <if test="lastName != null and lastName != ''">
            AND last_name LIKE CONCAT('%', #{lastName}, '%')
        </if>
        <if test="deptId != null">
            AND department_id = #{deptId}
        </if>
        <if test="minSal != null">
            AND salary >= #{minSal}
        </if>
    </where>
    ORDER BY last_name
</select>
```

### IN 子句

```java
List<Employee> listByIds(@Param("ids") List<String> ids);
```

```xml
<select id="listByIds" resultMap="employeeMap">
    SELECT employee_id, last_name
    FROM   employees
    WHERE  employee_id IN
    <foreach collection="ids" item="id" open="(" separator="," close=")">
        #{id}
    </foreach>
</select>
```

### LIKE 模糊查询

```java
Employee getByName(@Param("name") String name);
```

```xml
<select id="getByName" resultMap="employeeMap">
    SELECT employee_id, last_name, email
    FROM   employees
    WHERE  last_name LIKE CONCAT('%', #{name}, '%')
</select>
```

---

## 5. 租户隔离

```java
// Mapper 接口
Employee getTenantById(@Param("id") String id, @Param("tenantId") String tenantId);
List<Employee> listByDeptAndTenant(@Param("deptId") String deptId,
        @Param("tenantId") String tenantId);
```

```xml
<!-- 单表租户隔离 -->
<select id="getTenantById" resultMap="employeeMap">
    SELECT employee_id, last_name, email, salary, hire_date, department_id, tenant_id
    FROM   employees
    WHERE  employee_id = #{id}
    AND    tenant_id   = #{tenantId}
</select>

<!-- 列表租户隔离 -->
<select id="listByDeptAndTenant" resultMap="employeeMap">
    SELECT employee_id, last_name, salary, department_id
    FROM   employees
    WHERE  department_id = #{deptId}
    AND    tenant_id     = #{tenantId}
    ORDER BY last_name
</select>
```

---

## 6. 批量操作

### 批量插入

```java
int batchInsert(@Param("list") List<Employee> employees);
```

```xml
<!-- 批量插入（多行 VALUES） -->
<insert id="batchInsert">
    INSERT INTO employees (last_name, email, salary, hire_date, department_id, tenant_id)
    VALUES
    <foreach collection="list" item="e" separator=",">
        (#{e.lastName}, #{e.email}, #{e.salary}, #{e.hireDate}, #{e.departmentId}, #{e.tenantId})
    </foreach>
</insert>
```

### 批量更新

```java
int batchUpdate(@Param("list") List<Employee> employees);
```

```xml
<!-- 批量更新（多语句，需 allowMultiQueries=true） -->
<update id="batchUpdate">
    <foreach collection="list" item="e" separator=";">
        UPDATE employees
        SET last_name = #{e.lastName},
            email = #{e.email}
        WHERE employee_id = #{e.employeeId}
    </foreach>
</update>
```

---

## 7. 结果映射

### 关联和集合

```java
Department getDeptWithEmployees(@Param("deptId") String deptId);
```

```xml
<resultMap id="deptWithEmployees" type="Department">
    <id     column="department_id"   property="departmentId"/>
    <result column="department_name" property="departmentName"/>
    <collection property="employees" ofType="Employee">
        <id     column="employee_id"   property="employeeId"/>
        <result column="last_name"     property="lastName"/>
        <result column="salary"        property="salary"/>
    </collection>
</resultMap>

<select id="getDeptWithEmployees" resultMap="deptWithEmployees">
    SELECT d.department_id, d.department_name,
           e.employee_id, e.last_name, e.salary
    FROM   departments d
    JOIN   employees e ON d.department_id = e.department_id
    WHERE  d.department_id = #{deptId}
</select>
```

---

## 8. N+1 查询陷阱

N+1 是 MyBatis 最常见性能陷阱：先查主表（1 次），再循环查子表（N 次）。

```java
// 错误：N+1 查询
List<Department> depts = deptMapper.listAll();           // 1 次查询
for (Department dept : depts) {
    List<Employee> emps = empMapper.listByDept(dept.getId()); // N 次查询
}
```

```xml
<!-- 错误：collection 用子查询导致 N+1 -->
<resultMap id="deptWithEmployees" type="Department">
    <id column="department_id" property="departmentId"/>
    <collection property="employees" column="department_id"
                select="com.example.mapper.EmployeeMapper.listByDept"/>
    <!-- 每个部门触发一次子查询！ -->
</resultMap>

<!-- 正确：用 JOIN 一次查出所有数据 -->
<resultMap id="deptWithEmployees" type="Department">
    <id     column="department_id"   property="departmentId"/>
    <result column="department_name" property="departmentName"/>
    <collection property="employees" ofType="Employee">
        <id     column="employee_id"   property="employeeId"/>
        <result column="last_name"     property="lastName"/>
        <result column="salary"        property="salary"/>
    </collection>
</resultMap>

<select id="getDeptWithEmployees" resultMap="deptWithEmployees">
    SELECT d.department_id, d.department_name,
           e.employee_id, e.last_name, e.salary
    FROM   departments d
    JOIN   employees e ON d.department_id = e.department_id
    WHERE  d.department_id = #{deptId}
</select>
```

---

## 9. MySQL 特定功能

### ON DUPLICATE KEY UPDATE

```xml
<!-- 存在则更新，不存在则插入 -->
<insert id="upsert">
    INSERT INTO employees (employee_id, last_name, email, salary)
    VALUES (#{employeeId}, #{lastName}, #{email}, #{salary})
    ON DUPLICATE KEY UPDATE
    last_name = VALUES(last_name),
    email = VALUES(email),
    salary = VALUES(salary)
</insert>
```

### REPLACE INTO

```xml
<!-- 唯一键冲突时删除旧行插入新行 -->
<insert id="replaceInto">
    REPLACE INTO employees (employee_id, last_name, email)
    VALUES (#{employeeId}, #{lastName}, #{email})
</insert>
```

---

## 10. 常见错误

| 最佳实践 | 常见错误 | 修复 |
|---------|---------|------|
| 始终用 `#{param}` | `${param}` 导致 SQL 注入 | 永远用 `#{param}` |
| 显式 `<resultMap>` | 忘记 `map-underscore-to-camel-case` | 配置启用或显式映射 |
| 显式指定字段 | `SELECT *` 性能浪费 | 列出所需字段 |
| 租户表带 `tenant_id` | 查询漏 `tenant_id` 导致越权 | 所有操作必须携带条件 |
| 方法命名规范 | 命名随意如 `find`, `query` | 遵循 `getByXxx`, `listByXxx` |
| Selective 方法 | 全字段更新覆盖 NULL | 用 `insertSelective`, `updateSelectiveById` |
| 批量操作用多行 VALUES | 循环单条插入 | 用 `<foreach>` 多行 VALUES |
| 关联查询用 JOIN | N+1 查询（先查主表再循环查子表） | 用 JOIN 或嵌套结果映射 |
