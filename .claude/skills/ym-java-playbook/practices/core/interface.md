# 接口层规范

本文档仅约束代码实现，具体接口契约（URL 路径、请求、响应等）详见 shared/ym-api-spec.md。

## 职责与边界

接口层是外部请求的入口——管控安全、解析入参、封装出参、隔离业务逻辑。

**做**

- 安全管控（认证、权限、会话、数据归属）
- 参数解析（@RequestBody / @PathVariable / @RequestParam）
- 入参校验（参数格式、合法性、完整性）
- 响应封装
- 审计日志
- 接口防重提交

**不做**

- 业务判断（资源是否存在、是否有权操作、状态是否满足等）
- 业务编排（流程串联与数据组装）
- 事务管控
- 数据访问（直接操作持久层）
- 基础设施调用（直接操作缓存、消息队列等）

## 共性规范

### 安全

**面向外部调用者的接口，须遵循以下安全规则：**

| 维度 | 规则 |
|------|------|
| 认证 | 须声明 `@TokenRequired`，拦截未认证请求 |
| 权限 | 须声明 `@Permission`，按权限码限定访问范围 |
| 会话 | 须通过 `@UserInfo` 注入会话身份，禁止信任请求参数中的身份标识 |
| 数据归属 | 租户ID、用户ID等归属标识须从会话中获取，禁止作为入参传递 |

### 入参

| 维度 | 规则 |
|------|------|
| 参数接收 | 使用 POJO / DTO 对象封装接收参数，避免使用多个松散参数 |
| 枚举值 | 使用枚举类接收 |
| GET 查询 | 多参数封装为对象，单参数可用 @RequestParam |
| 分页查询 | 继承 PageParam |
| 参数校验 | 使用 @Validated 注解 |
| 文档 | @Api（类）+ @ApiOperation（方法） |

### 出参

| 维度 | 规则 |
|------|------|
| 返回值 | 统一使用 HttpResult<T> 封装，禁止返回基础类型 |
| 分页 | 分页查询使用 Page<T> 封装，返回 HttpResult<Page<T>> |

### 接口方法命名

| 操作 | 方法名 |
|------|--------|
| 分页查询 | page |
| 新增 | add |
| 全量更新 | update |
| 删除 | delete |
| 主键查询 | detail |
| 非主键查询 | getXxx |
| 列表查询 | listXxx |
| 扩展操作 | 自定义动词，如：subscribeEvent、batchImport |

## 接口差异对照表

| 维度 | Web 接口 | 微服务接口 | 开放接口 |
|------|---------|----------|---------|
| 类名后缀 | Controller | Endpoint | Api |
| 继承基类 | BaseController | BaseController | 无 |
| 路径前缀 | /<资源复数> | /endpoint/<资源复数> | /api/<资源复数> |
| HTTP 方法 | GET/POST/PUT/DELETE | GET/POST/PUT/DELETE | 仅 GET/POST |
| 返回值封装 | HttpResult + responseOK() | HttpResult + responseOK() | 需自定义 |
| 认证 | @TokenRequired | 无 | @TokenRequired |
| 会话 | @UserInfo + 会话信息 | 无 | @UserInfo + 会话信息 |
| 权限 | 类 @Permission + 方法 @Permission("{权限码}") | 无 | 类 @Permission + 方法 @Permission |

## 代码示例

### Web

```java
    import com.hikvision.building.cloud.config.common.session.core.UserInfo;
    import com.hikvision.building.cloud.gaia.common.controller.BaseController;
    import com.hikvision.building.cloud.gaia.common.security.permission.Permission;
    import com.hikvision.building.cloud.gaia.common.structs.HttpResult;

    @Api(tags = "设备管理")
    @Validated
    @Permission
    @RestController
    @RequestMapping("/devices")
    public class DeviceController extends BaseController {

        @Autowired
        private DeviceService deviceService;

        // 分页查询
        @ApiOperation(value = "分页查询设备列表")
        @Permission("DEVICE_MANAGE")
        @GetMapping
        @TokenRequired
        public HttpResult<Page<DevicePageVO>> page(@UserInfo WebUserSession session,
                @Validated DevicePageParam param) {
            return responseOK(deviceService.page(session, param));
        }

        // 新增
        @ApiOperation(value = "添加设备")
        @Permission("DEVICE_MANAGE")
        @PostMapping
        @TokenRequired
        public HttpResult add(@UserInfo WebUserSession session,
                @Validated @RequestBody DeviceAddParam param) {
            deviceService.add(session, param);
            return responseOK();
        }

        // 根据资源唯一标识更新
        @ApiOperation(value = "编辑设备信息")
        @Permission("DEVICE_MANAGE")
        @PutMapping("/{deviceId}")
        @TokenRequired
        public HttpResult update(@UserInfo WebUserSession session,
                @PathVariable String deviceId,
                @Validated @RequestBody DeviceUpdateParam param) {
            deviceService.update(session, deviceId, param);
            return responseOK();
        }

        // 根据资源唯一标识删除
        @ApiOperation(value = "删除设备")
        @Permission("DEVICE_MANAGE")
        @DeleteMapping("/{deviceId}")
        @TokenRequired
        public HttpResult delete(@UserInfo WebUserSession session,
                @PathVariable String deviceId) {
            deviceService.delete(session, deviceId);
            return responseOK();
        }

        // 根据资源唯一标识查询
        @ApiOperation(value = "查看设备详情")
        @Permission("DEVICE_MANAGE")
        @GetMapping("/{deviceId}")
        @TokenRequired
        public HttpResult<DeviceDetailVO> detail(@UserInfo WebUserSession session,
                @PathVariable String deviceId) {
            return responseOK(deviceService.detail(session, deviceId));
        }

        // 非主键查询（单参数）：使用 @RequestParam 接收
        @ApiOperation(value = "根据设备序列号查询设备信息")
        @Permission("DEVICE_MANAGE")
        @GetMapping("/actions/getByDeviceSerial")
        @TokenRequired
        public HttpResult<DeviceVO> getByDeviceSerial(@UserInfo WebUserSession session,
                @RequestParam("deviceSerial") String deviceSerial) {
            return responseOK(deviceService.getByDeviceSerial(session, deviceSerial));
        }

        // 非主键查询（多参数）：入参封装为对象
        @ApiOperation(value = "根据xxx查询设备信息")
        @Permission("DEVICE_MANAGE")
        @GetMapping("/actions/getXxx")
        @TokenRequired
        public HttpResult<XxxVO> getXxx(@UserInfo WebUserSession session,
                @Validated XxxGetParam param) {
            return responseOK(deviceService.getXxx(session, param));
        }

        // 列表查询（非分页）：入参封装参考非主键查询
        @ApiOperation(value = "列表查询xxx")
        @Permission("DEVICE_MANAGE")
        @GetMapping("/actions/listXxx")
        @TokenRequired
        public HttpResult<List<XxxVO>> listXxx(@UserInfo WebUserSession session,
                @Validated XxxListParam param) {
            return responseOK(deviceService.listXxx(session, param));
        }

        // 扩展操作：必须为 POST /actions/xxx 形式
        @ApiOperation(value = "订阅消息事件")
        @Permission("DEVICE_SUBSCRIBE")
        @PostMapping("/actions/subscribeEvent")
        @TokenRequired
        public HttpResult subscribeEvent(@UserInfo WebUserSession session,
                @Validated @RequestBody SubscribeEventParam param) {
            deviceService.subscribeEvent(session, param);
            return responseOK();
        }
    }
```

### Endpoint

```java
    @Api(tags = "设备管理微服务接口")
    @Validated
    @RestController
    @RequestMapping("/endpoint/devices")
    public class DeviceEndpoint extends BaseController {

        @Autowired
        private DeviceService deviceService;

        // 分页查询（无会话、无权限）
        @ApiOperation("分页查询设备列表")
        @GetMapping
        public HttpResult<Page<DevicePageVO>> page(@Validated DevicePageParam param) {
            return responseOK(deviceService.page(param));
        }

        // 新增
        @ApiOperation("添加设备")
        @PostMapping
        public HttpResult add(@Validated @RequestBody DeviceAddParam param) {
            deviceService.add(param);
            return responseOK();
        }

        // 扩展操作
        @ApiOperation("订阅事件")
        @PostMapping("/actions/subscribeEvent")
        public HttpResult subscribeEvent(
                @Validated @RequestBody SubscribeEventParam param) {
            deviceService.subscribeEvent(param);
            return responseOK();
        }
    }
```

### Api

```java
    @Api(tags = "设备管理开放接口")
    @Validated
    @Permission
    @RestController
    @RequestMapping("/api/devices")
    public class DeviceApi {

        @Autowired
        private DeviceService deviceService;

        // 主键查询
        @ApiOperation("查看设备详情")
        // 无需权限码
        @Permission
        @GetMapping("/{deviceId}")
        @TokenRequired
        // 自定义 OpenHttpResult
        public OpenHttpResult<DeviceDetailVO> detail(@UserInfo OpenUserSession session, // OpenHttpResult 为自定义封装类
                @PathVariable String deviceId) {
            return OpenHttpResult(deviceService.detail(session, deviceId));
        }

        // 扩展操作
        @ApiOperation("订阅事件")
        @Permission
        @PostMapping("/actions/subscribeEvent")
        @TokenRequired
        public OpenHttpResult subscribeEvent(@UserInfo OpenUserSession session, // OpenHttpResult 为自定义封装类
                @Validated @RequestBody SubscribeEventParam param) {
            deviceService.subscribeEvent(session, param);
            return OpenHttpResult();
        }
    }
```

## 反例

**数据归属作为入参传递 —— 跨租户数据泄露**

```java
// ❌ tenantId、userId 由前端传入 —— 攻击者可修改为他人租户ID访问他人数据
@PostMapping
public HttpResult add(@RequestBody DeviceAddParam param) {
    deviceService.add(param.getTenantId(), param);
    return responseOK();
}
```

**权限码缺失 —— 越权访问**

```java
// ❌ 缺少 @Permission 或未指定权限码 —— 所有已认证用户均可访问，无权限控制
@DeleteMapping("/{deviceId}")
@TokenRequired
public HttpResult delete(@UserInfo WebUserSession session,
        @PathVariable String deviceId) {
    deviceService.delete(session, deviceId);
    return responseOK();
}
```

**接口层承载业务逻辑 —— 职责越界**

```java
// ❌ Controller 里做业务校验 + 数据组装 + 直接调 Mapper
@PostMapping
@TokenRequired
public HttpResult add(@UserInfo WebUserSession session,
        @Validated @RequestBody DeviceAddParam param) {
    Device device = deviceMapper.getById(param.getDeviceId());  // ❌ 直接调 Mapper
    if (device == null) {                                       // ❌ 业务校验
        return responseError("设备不存在");
    }
    if (!session.tenantId().equals(device.getTenantId())) {     // ❌ 数据归属校验
        return responseError("无权限");
    }
    Device newDevice = new Device();                            // ❌ 数据组装
    newDevice.setId(UuidUtil.create());
    newDevice.setTenantId(session.tenantId());
    deviceMapper.insert(newDevice);                             // ❌ 数据访问
    return responseOK();
}
```