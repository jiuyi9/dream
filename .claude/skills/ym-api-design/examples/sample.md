# 交互示例

## Web 接口

### 用户输入

> 我需要一个通道巡检的功能，列表要分页，能按通道名搜，然后能创建巡检任务，还能按 id 查详情。另外设备那边还要一个配置功能。

### 步骤一：确认基础信息

用户未指定类型，主动询问：

**AI**

接口类型是 Web 还是开放接口？

**用户**

Web 接口。

确定后分别查阅云眸接口规范与接口设计文档模板的对应章节。

项目中已有 `docs/apis/web/v1.1.0_接口设计文档.md` → 版本号推断为 `v1.1.0`。

当前位于子模块 `siot-video` → 业务标识 `siot`，组件标识 `video`，按规范中的路径前缀定义拼接为 `/v1/siot/video`。

汇总确认：

**AI**

确认以下基础信息：
- 接口类型：web
- 版本号：v1.1.0
- URL 路径前缀：/v1/siot/video

**用户**

确认。

### 步骤二：提取并对齐接口

**接口提取**

从上下文/已有的设计中提取接口信息。

**接口对齐**

以接口设计文档模板结构为框架、以云眸接口规范为约束，逐项填充：

| 分组 | 接口 | 动作 | 方法 | URL | Token Required |
|------|------|------|------|-----|:--------------:|
| 通道巡检 | 分页查询巡检列表 | 分页查询 | GET | `/v1/siot/video/channelPatrols` | true |
| 通道巡检 | 创建巡检任务 | 新增 | POST | `/v1/siot/video/channelPatrols` | true |
| 通道巡检 | 获取巡检详情 | 主键查询 | GET | `/v1/siot/video/channelPatrols/{id}` | true |
| 设备管理 | 配置设备 | 自定义操作 | POST | `/v1/siot/video/devices/{id}/actions/configure` | true |

信息不足时引导用户澄清：

**AI**

1. 分页列表 — `channelName` 是否必填？`rows` 返回哪些字段？
2. 创建任务 — 请求体字段、类型、必填？
3. 获取详情 — `data` 含哪些字段？
4. 配置设备 — 请求体传什么？

**用户**

- `channelName` 模糊匹配，可以不传
- 创建的时候传通道 ID 和巡检类型就行
- 列表和详情都返回 id、通道名称、状态、创建时间
- 配置设备传设备名称和配置参数

### 步骤三：生成并保存设计文档

按对应接口设计文档模板输出文档，写入 `docs/apis/web/v1.1.0_接口设计文档.md`：

````markdown
# v1.1.0 Web 接口设计文档

## 通道巡检

### 分页查询巡检列表

> 分页查询通道巡检记录，支持按通道名称筛选。

**请求方式**：GET

**请求地址**：`/v1/siot/video/channelPatrols`

**Token Required**：true

**请求参数：**

| 名称 | 类型 | 必须 | 默认值 | 长度 | 示例 | 说明 |
|------|------|:----:|--------|------|------|------|
| pageNo | Integer | 否 | 1 | — | 1 | 页码 |
| pageSize | Integer | 否 | 10 | — | 10 | 每页条数 |
| channelName | String | 否 | — | 64 | cam-01 | 通道名称，模糊匹配 |

**返回示例：**

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
    "rows": [
      {
        "id": 1,
        "channelName": "cam-01",
        "status": "running",
        "createdAt": "2026-05-21 10:30:00"
      }
    ]
  }
}
```

**rows 字段说明：**

| 名称 | 类型 | 示例 | 说明 |
|------|------|------|------|
| id | Number | 1 | 主键 |
| channelName | String | cam-01 | 通道名称 |
| status | String | running | 巡检状态 |
| createdAt | DateTime | 2026-05-21 10:30:00 | 创建时间 |

### 创建巡检任务

> 创建新的通道巡检任务。

**请求方式**：POST

**请求地址**：`/v1/siot/video/channelPatrols`

**Token Required**：true

**请求体：**

```json
{
  "channelId": "ch-001",
  "patrolType": "daily"
}
```

| 名称 | 类型 | 必须 | 默认值 | 长度 | 示例 | 说明 |
|------|------|:----:|--------|------|------|------|
| channelId | String | 是 | — | 64 | ch-001 | 通道 ID |
| patrolType | String | 是 | — | 32 | daily | 巡检类型 |

**返回示例：**

```json
{
  "code": 0,
  "success": true,
  "message": "",
  "data": null
}
```

### 获取巡检详情

> 按 ID 查询巡检任务详情。

**请求方式**：GET

**请求地址**：`/v1/siot/video/channelPatrols/{id}`

**Token Required**：true

**返回示例：**

```json
{
  "code": 0,
  "success": true,
  "message": "",
  "data": {
    "id": 1,
    "channelName": "cam-01",
    "status": "running",
    "createdAt": "2026-05-21 10:30:00",
    "items": [
      {
        "itemId": "A001",
        "itemName": "摄像头状态",
        "result": "normal"
      }
    ]
  }
}
```

**data 字段说明：**

| 名称 | 类型 | 示例 | 说明 |
|------|------|------|------|
| id | Number | 1 | 主键 |
| channelName | String | cam-01 | 通道名称 |
| status | String | running | 巡检状态 |
| createdAt | DateTime | 2026-05-21 10:30:00 | 创建时间 |
| items | Array | — | 巡检项列表 |
| items[].itemId | String | A001 | 巡检项 ID |
| items[].itemName | String | 摄像头状态 | 巡检项名称 |
| items[].result | String | normal | 巡检结果 |

## 设备管理

### 配置设备

> 对指定设备下发配置。

**请求方式**：POST

**请求地址**：`/v1/siot/video/devices/{id}/actions/configure`

**Token Required**：true

**请求体：**

```json
{
  "deviceName": "cam-01",
  "config": {
    "resolution": "1080p",
    "fps": 30
  }
}
```

| 名称 | 类型 | 必须 | 默认值 | 长度 | 示例 | 说明 |
|------|------|:----:|--------|------|------|------|
| deviceName | String | 是 | — | 64 | cam-01 | 设备名称 |
| config | Object | 是 | — | — | — | 配置参数 |
| config.resolution | String | 是 | — | 16 | 1080p | 分辨率 |
| config.fps | Number | 是 | — | — | 30 | 帧率 |

**返回示例：**

```json
{
  "code": 0,
  "success": true,
  "message": "",
  "data": null
}
```
````

---

## 开放接口

### 用户输入

> 第三方需要查询我们的通道巡检记录，还要能触发巡检任务。

### 步骤一：确认基础信息

用户指定 `open`，确认。确定后分别查阅云眸接口规范与接口设计文档模板的对应章节。

项目中已有 `docs/apis/open/v1.1.0_接口设计文档.md` → 版本号推断为 `v1.1.0`。

当前位于子模块 `siot-video` → 业务标识 `siot`，组件标识 `video`，按规范中的路径前缀定义拼接为 `/siot/video/api`。

汇总确认：

**AI**

确认以下基础信息：
- 接口类型：open
- 版本号：v1.1.0
- URL 路径前缀：/siot/video/api

**用户**

确认。

### 步骤二：提取并对齐接口

**接口提取**

从上下文/已有的设计中提取接口信息。

**接口对齐**

以接口设计文档模板结构为框架、以云眸接口规范为约束，逐项填充：

| 分组 | 接口 | 动作 | 方法 | URL | Token Required |
|------|------|------|------|-----|:--------------:|
| 通道巡检 | 分页查询巡检列表 | 分页查询 | GET | `/siot/video/api/channelPatrols` | true |
| 通道巡检 | 触发巡检任务 | 自定义操作 | POST | `/siot/video/api/channelPatrols/actions/createPatrol` | true |

信息不足时引导用户澄清：

**AI**

1. 分页列表 — 查询参数有哪些？`rows` 返回哪些字段？
2. 触发任务 — 请求体传什么？

**用户**

- 列表支持按通道名称模糊搜索，返回 id、通道名称、状态、创建时间
- 触发任务传通道 ID 和巡检类型

### 步骤三：生成并保存设计文档

按对应接口设计文档模板输出文档，写入 `docs/apis/open/v1.1.0_接口设计文档.md`：

````markdown
# v1.1.0 开放接口设计文档

## 通道巡检

### 分页查询巡检列表

**接口描述**

分页查询通道巡检记录，支持按通道名称筛选。

**请求方式** GET

**请求地址** `https://api2.hik-cloud.com/siot/video/api/channelPatrols`

**参数说明**

| 属性名称 | 属性描述 | 类型 | 长度 | 是否必填 |
| --- | --- | --- | --- | --- |
| pageNo | 页码 | Integer | — | 否 |
| pageSize | 每页条数 | Integer | — | 否 |
| channelName | 通道名称，模糊匹配 | String | 64 | 否 |

**返回结果**

```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        "pageNo": 1,
        "pageSize": 10,
        "totalPage": 1,
        "total": 1,
        "hasNextPage": false,
        "hasPreviousPage": false,
        "firstPage": true,
        "lastPage": true,
        "rows": [
            {
                "id": 1,
                "channelName": "cam-01",
                "status": "running",
                "createdAt": "2026-05-21 10:30:00"
            }
        ]
    }
}
```

**参数说明**

| 属性名称 | 属性描述 | 类型 | 长度 | 是否必填 |
| --- | --- | --- | --- | --- |
| code | 返回码 | String | 10 | 是 |
| message | 返回消息 | String | 64 | 是 |
| data | 节点对象 | Object | | 是 |

data字段说明

| 属性名称 | 属性描述 | 类型 | 长度 | 是否必填 |
| --- | --- | --- | --- | --- |

rows字段说明

| 属性名称 | 属性描述 | 类型 | 长度 | 是否必填 |
| --- | --- | --- | --- | --- |
| id | 主键 | Number | — | 是 |
| channelName | 通道名称 | String | 64 | 是 |
| status | 巡检状态 | String | 32 | 是 |
| createdAt | 创建时间 | DateTime | — | 是 |

### 触发巡检任务

**接口描述**

触发新的通道巡检任务。

**请求方式** POST

**请求地址** `https://api2.hik-cloud.com/siot/video/api/channelPatrols/actions/createPatrol`

**请求包体**

```json
{
    "channelId": "ch-001",
    "patrolType": "daily"
}
```

**参数说明**

| 属性名称 | 属性描述 | 类型 | 长度 | 是否必填 |
| --- | --- | --- | --- | --- |
| channelId | 通道 ID | String | 64 | 是 |
| patrolType | 巡检类型 | String | 32 | 是 |

**返回结果**

```json
{
    "code": 200,
    "message": "操作成功",
    "data": null
}
```

**参数说明**

| 属性名称 | 属性描述 | 类型 | 长度 | 是否必填 |
| --- | --- | --- | --- | --- |
| code | 返回码 | String | 10 | 是 |
| message | 返回消息 | String | 64 | 是 |
| data | 节点对象 | Object | | 是 |
````