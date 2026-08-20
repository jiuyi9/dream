# 云眸 API 规范

## 公共规范

> 本规范全局适用，各端差异详见对应章节

### URL 规范

#### 占位符

- `<>` 为必选段
- `[]` 为可选段

#### 命名风格

- 路径段使用驼峰风格
- 资源名词取复数形式

### 查询请求

简单查询操作默认使用 GET。当满足以下任一条件时，改走自定义操作（POST）：

- 参数包含数组类型
- 参数包含嵌套结构

### 分页参数

分页查询需携带如下参数：

| 参数 | 类型 | 必须 | 说明 |
|------|------|:----:|------|
| `pageNo` | Integer | 是 | 页码 |
| `pageSize` | Integer | 是 | 每页条数 |

- GET 请求：参数放在 URL Query
- POST 请求：参数放在请求体中

### 请求体

必须使用 JSON 格式

### 返回结果

#### 标准格式

```json
{
  "code": 0,
  "success": true,
  "message": "",
  "data": null
}
```

- `code` 为 `0` 表示成功

**data 取值：**

| 操作类型 | 有数据 | 无数据 |
|--------|------|------|
| 新增/修改/删除 | `null` | `null` |
| 详情查询 | 对象 | `null` |
| 列表查询 | 数组 | `[]` |

- `data` 不允许直接返回基础类型

#### 分页格式

分页接口 `data` 替换为分页对象：

```json
{
  "code": 0,
  "success": true,
  "message": "",
  "data": {
    "pageNo": 1,
    "pageSize": 10,
    "totalPage": 1,
    "total": 1,
    "hasNextPage": false,
    "hasPreviousPage": false,
    "firstPage": true,
    "lastPage": true,
    "rows": []
  }
}
```

**rows 取值：**

| 场景 | 取值 |
|------|------|
| 有数据 | 数组 |
| 无数据 | `[]` |

- `rows` 不允许为 `null`，必须返回数组类型

### 字段类型

| 类型 | 适用场景 | 示例 |
|------|----------|------|
| `String` | 文本 | `"xxx"` |
| `Number` | 数值 | `1`、`3.14` |
| `Boolean` | 布尔 | `true` |
| `DateTime` | 日期时间 | `"2026-05-21 10:30:00"` |
| `Date` | 日期 | `"2026-05-21"` |
| `Object` | JSON 对象 | `{}` |
| `Array<T>` | 数组 | `[{"id":1}]` |

## Web 接口

面向于 Web、H5、App 及小程序等前端应用

### URL 结构

```
/v1/<业务标识>/<组件标识>/<资源复数>[/<资源ID>][/actions/<具体操作>]
├── 路径前缀: /v1/<业务标识>/<组件标识>
└── 资源路径: <资源复数>[/<资源ID>][/actions/<具体操作>]
```

### HTTP 方法

仅支持 `GET`、`POST`、`PUT`、`DELETE` 四种方法

### 接口定义

| 操作 | HTTP 方法 | URL 路径 | 示例 |
|------|-----------|----------|------|
| 分页查询（简单） | GET | `/v1/<业务标识>/<组件标识>/<资源复数>` | `GET /v1/siot/video/channelPatrols` |
| 新增 | POST | `/v1/<业务标识>/<组件标识>/<资源复数>` | `POST /v1/siot/video/channelPatrols` |
| 主键查询 | GET | `/v1/<业务标识>/<组件标识>/<资源复数>/<资源ID>` | `GET /v1/siot/video/channelPatrols/123` |
| 全量更新 | PUT | `/v1/<业务标识>/<组件标识>/<资源复数>/<资源ID>` | `PUT /v1/siot/video/channelPatrols/123` |
| 删除 | DELETE | `/v1/<业务标识>/<组件标识>/<资源复数>/<资源ID>` | `DELETE /v1/siot/video/channelPatrols/123` |
| 非主键查询（简单） | GET | `/v1/<业务标识>/<组件标识>/<资源复数>/actions/getXxx` | `GET /v1/siot/video/channelPatrols/actions/getByName` |
| 列表查询（非分页，简单） | GET | `/v1/<业务标识>/<组件标识>/<资源复数>/actions/listXxx` | `GET /v1/siot/video/channelPatrols/actions/listActive` |
| 自定义操作 | POST | `/v1/<业务标识>/<组件标识>/<资源复数>[/<资源ID>]/actions/<具体操作>` | `POST /v1/siot/video/channelPatrols/actions/batchEnable` · `POST /v1/siot/video/channelPatrols/123/actions/enable` |

### Token Required

| 值 | 含义 |
|----|------|
| `true` | 需要登录认证（默认） |
| `false` | 不需登录认证 |

## 微服务接口

面向内部微服务

### URL 结构

```
/endpoint/<资源复数>[/<资源ID>][/actions/<具体操作>]
```

### HTTP 方法

仅支持 `GET`、`POST`、`PUT`、`DELETE` 四种方法

### 接口定义

| 操作 | HTTP 方法 | URL 路径 | 示例 |
|------|-----------|----------|------|
| 分页查询（简单） | GET | `/endpoint/<资源复数>` | `GET /endpoint/channelPatrols` |
| 新增 | POST | `/endpoint/<资源复数>` | `POST /endpoint/channelPatrols` |
| 主键查询 | GET | `/endpoint/<资源复数>/<资源ID>` | `GET /endpoint/channelPatrols/123` |
| 全量更新 | PUT | `/endpoint/<资源复数>/<资源ID>` | `PUT /endpoint/channelPatrols/123` |
| 删除 | DELETE | `/endpoint/<资源复数>/<资源ID>` | `DELETE /endpoint/channelPatrols/123` |
| 非主键查询（简单） | GET | `/endpoint/<资源复数>/actions/getXxx` | `GET /endpoint/channelPatrols/actions/getByName` |
| 列表查询（非分页，简单） | GET | `/endpoint/<资源复数>/actions/listXxx` | `GET /endpoint/channelPatrols/actions/listActive` |
| 自定义操作 | POST | `/endpoint/<资源复数>[/<资源ID>]/actions/<具体操作>` | `POST /endpoint/channelPatrols/actions/batchEnable` · `POST /endpoint/channelPatrols/123/actions/enable` |

### Token Required

不需要校验用户 Token

## 开放接口

面向第三方开发者

### URL 结构

```
/<业务标识>/<组件标识>/api/<资源复数>[/<资源ID>][/actions/<具体操作>]
├── 路径前缀: /<业务标识>/<组件标识>/api
└── 资源路径: <资源复数>[/<资源ID>][/actions/<具体操作>]
```

### HTTP 方法

仅支持 `GET`、`POST` 两种方法

### 接口定义

| 操作 | HTTP 方法 | URL 路径 | 示例 |
|------|-----------|----------|------|
| 分页查询（简单） | GET | `/<业务标识>/<组件标识>/api/<资源复数>` | `GET /siot/video/api/channelPatrols` |
| 主键查询 | GET | `/<业务标识>/<组件标识>/api/<资源复数>/<资源ID>` | `GET /siot/video/api/channelPatrols/123` |
| 非主键查询（简单） | GET | `/<业务标识>/<组件标识>/api/<资源复数>/actions/getXxx` | `GET /siot/video/api/channelPatrols/actions/getByName` |
| 列表查询（简单） | GET | `/<业务标识>/<组件标识>/api/<资源复数>/actions/listXxx` | `GET /siot/video/api/channelPatrols/actions/listActive` |
| 自定义操作 | POST | `/<业务标识>/<组件标识>/api/<资源复数>[/<资源ID>]/actions/<具体操作>` | `POST /siot/video/api/channelPatrols/actions/batchEnable` · `POST /siot/video/api/channelPatrols/123/actions/enable` |

### Token Required

`true` — 需要携带授权凭证


### 返回结果

标准格式如下：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": null
}
```

相较于公共规范：

- `code` 为 `200` 表示成功
- 无 `success` 字段
- `data` 及分页规则同公共规范
