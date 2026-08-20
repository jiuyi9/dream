# 业务逻辑层规范

## 定位

Service 是业务流程的编排者——决定做什么、按什么顺序做、异常怎么中断，执行细节下沉。

**做**

- 业务校验与冲突防护
- 业务流程编排
- 事务管控

**不做**

- 入参校验（参数格式、合法性、完整性）
- 通用工具封装
- 通用常量与枚举定义

## 三阶段执行模型

业务方法遵循三阶段执行模型：**准入（Guard）→ 执行（Execution）→ 后置处理（Post-Action）**。

```
准入（Guard）
  ├─ 业务校验
  │   ├─ 横向归属
  │   ├─ 存在性
  │   ├─ 纵向权限
  │   └─ 业务前提
  │       ├─ 状态
  │       ├─ 唯一性
  │       ├─ 关联有效性
  │       ├─ 数量约束
  │       └─ ...
  └─ 冲突防护
      ├─ 幂等判定
      └─ 并发准入

执行（Execution）
  ├─ 核心业务逻辑
  └─ 数据持久化

后置处理（Post-Action）
  ├─ 变更同步
  │   ├─ 事件投递
  │   └─ 缓存更新
  └─ 运维观测
      ├─ 审计日志
      └─ 指标上报
```

> 后置处理是条件性阶段——无外部副作用时不存在。简单 CRUD 只有准入和执行

## 准入

准入是执行的前提——只做判定，不做变更。判定不通过时，通过 CheckUtils 主动中断流程。

### 做哪些判定

准入包含两类判定：业务校验判定"该不该做"，冲突防护判定"能不能独占进入"。

#### 业务校验

业务校验逐层递进：横向归属 → 存在性 → 纵向权限 → 业务前提。

| 维度 | 判定内容 | 失败含义 |
|------|---------|---------|
| 横向归属 | 目标资源是否属于当前操作者的归属域 | 不在当前归属域内，任何后续判定无从谈起 |
| 存在性 | 目标资源是否存在 | 资源不存在，权限与前提无从谈起 |
| 纵向权限 | 当前操作者是否具备目标资源的操作权限 | 无权操作，后续检查无实际意义 |
| 业务前提 | 目标资源当前状态是否满足操作要求 | 前提不满足，操作不可执行 |

业务前提因业务场景而异，常见子类型：

| 子类型 | 检查角度 | 示例 |
|--------|---------|------|
| 状态 | 资源本身能不能被操作 | 考勤组已锁定不可修改 |
| 唯一性 | 操作结果会不会冲突 | 分组名称不能重复 |
| 关联有效性 | 关联资源是否满足条件 | 关联设备必须在线 |
| 数量约束 | 操作范围是否在允许界限内 | 名额不能超限、最多创建 N 个分组 |

#### 冲突防护

| 维度 | 判定内容 | 适用场景 |
|------|---------|---------|
| 幂等判定 | 操作是否已执行过 | 消息消费、并发重试、支付重复请求 |
| 并发准入 | 当前操作者能否独占进入 | 并发修改会导致不可接受结果 |

### 怎么判定

#### 业务校验

**查询策略**

**从入参提取所有资源标识后**，按数据获取成本由低到高，逐步推进：不回库 → 同源合并 → 异源按需 → 复用已有。

1. **不回库优先**：会话属性、缓存命中即可完成判定，无需查询数据库
2. **同源合并**：必须回库时，单次查询获取核心实体，集中完成同一实体相关的判定
3. **异源按需**：主实体无法覆盖的约束（唯一性、跨表关联），按需发起独立查询，只取最小字段集
4. **复用已有**：已加载的数据不再重复查询

**查询约束**

- 所有持久化查询必须携带归属标识（如 tenantId）
- 涉及集合标识时，统一批量查询，禁止在循环中逐条调用数据库

**标识判定规则**

- 单个标识：查询结果为空即判定失败
- 集合标识：先对标识集合去重，再比对查询结果数量与去重后标识数量。数量不一致则判定失败

#### 冲突防护

**幂等判定**

- 执行时机：在获取业务数据之后、核心业务逻辑执行之前
- 判定方式：从数据库或缓存中查询比对，常见判定依据：状态字段已变更（如 `order.getStatus() == SYNCED`）、操作记录已存在（如重复支付请求的流水号）
- 判定结果：命中则跳过后续判定，直接返回

**并发准入**

- 加锁判断：

| 是否加锁 | 条件 | 示例 |
|---------|------|------|
| 需要加锁 | 并发修改会导致不可接受的结果 | 唯一性校验后插入、状态流转、库存/名额扣减、关联资源变更 |
| 不需要加锁 | 并发修改的结果可接受 | 同一实体不同字段独立修改 |

- 加锁方式：通过 Redis Lock（RedisLockHelper、RedissonLock） 进行加锁
- 锁释放：必须在 finally 中释放，确保异常路径不遗留锁

### 怎么处理判定结果

| 场景 | 处理方式 |
|------|---------|
| 分页/列表无数据 | 返回空集合 |
| 其他判定不通过 | 使用 CheckUtils 抛出对应的业务异常 |

## 执行

在事务内完成业务计算与持久化写入。

### 做什么

- 核心业务逻辑：基于准入阶段加载的实体，构建变更后的状态
- 数据持久化：将变更后的实体写入数据库

### 怎么做

- 计算逻辑封装在实体方法中（如 merge、from），Service 只调用构建结果
- 核心业务逻辑与数据持久化在同一事务内紧密完成
- 禁止在事务内触发不可控副作用（远程调用、MQ 发送等）——耗时操作前置到事务前，副作用后置到后置处理

## 后置处理

将已提交的业务事实送达外部系统，确保最终一致性。

### 做什么

#### 变更同步

将业务变更同步到外部系统。

- 事件投递：将业务事实作为领域事件送达下游系统（MQ、回调等）
- 缓存更新：将变更后的数据同步到缓存，确保后续查询的一致性

#### 运维观测

为运维和合规提供可观测性。

- 审计日志：记录关键业务操作的执行轨迹，满足合规追溯需求
- 指标上报：将业务执行的关键度量上报至监控系统，支撑运营决策和告警

### 怎么做

后置处理处于事务保护之外。

#### 触发时机

后置处理在业务变更生效后触发。

- 有事务时：在事务提交后触发
- 无事务时：在执行完成后直接触发

#### 执行方式

异步执行，不阻塞主流程返回。

#### 容错

后置处理失败不影响主流程，但需要确保最终一致。处理原则逐层递进：

- **隔离**：异常不得向上抛出至主流程，确保主业务结果不受影响
- **可重放**：失败后必须能重新触发，确保最终可达一致
- **幂等**：同一事件重复触发不得产生新的副作用，确保重放安全

按失败对业务的影响程度分级处理：

| 影响程度 | 适用场景 | 处理方式 |
|---------|---------|---------|
| 可容忍 | 缓存更新、审计日志、指标上报 | 静默失败 + 监控告警 |
| 不可容忍 | 关键事件投递、下游状态同步 | 补偿重试 + 幂等保障 |

> 补偿重试和幂等保障不在 Service 方法内编码。消费者幂等在消费端实现，本地消息表在基础设施层保障。

## 事务管控

使用 @Transactional 注解控制事务。

### 使用原则

- 纯查询操作：禁止开启事务
- 变更操作：开启事务，但要避免长事务
- 长耗时操作（大步骤编排、复杂的异步消费）：禁止开启事务，使用幂等保障

### 事务边界

| 时机 | 操作 | 目的 |
|------|------|------|
| 事务前（准入） | 数据查询、业务计算、远程调用获取数据 | 预加载决策依据，避免事务内等待 |
| 事务内（执行） | 数据写入 | 保障原子性，失败整体回滚 |
| 事务后（后置处理） | 事件投递、缓存维护、审计日志、指标上报 | 隔离副作用，确保事务原子性不受影响 |

> 使用 @Transactional 注解时，读操作常被包含在事务边界内，难以完全实现事务前预加载。需要缩短事务持锁时间时，可通过方法拆分或编程式事务实现

## 代码组织

- **编排者原则**：入口方法只做编排，执行细节下沉
- **类内组织**：查询在前、变更在后、私有在最后
- **依赖边界**：公共逻辑抽取独立组件，跨 Service 的流程由上层编排者协调

## 代码示例

```java
@Slf4j
@Service
public class AttendanceGroupService {

    @Autowired
    private AttendanceGroupMapper attendanceGroupMapper;
    @Autowired
    private UserGroupRelMapper userGroupRelMapper;
    @Autowired
    private DeviceMapper deviceMapper;
    @Autowired
    private DeviceGroupRelMapper deviceGroupRelMapper;
    @Autowired
    private UserDeviceRelMapper userDeviceRelMapper;
    @Autowired
    private PersonMapper personMapper;
    @Autowired
    private PersonGroupRelMapper personGroupRelMapper;
    @Autowired
    private UserPersonRelMapper userPersonRelMapper;
    @Autowired
    private RedisLockHelper redisLockHelper;
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    // === 查询操作：纯查询不加 @Transactional ===

    public AttendanceGroupDetailVO detail(String tenantId, String groupId) {
        AttendanceGroup group = attendanceGroupMapper.getByIdAndTenant(tenantId, groupId);                 // 归属+存在性合并判定
        CheckUtils.notEmpty(group, AttendanceGroupExceptionEnum.GROUP_NOT_EXISTS);                        // 存在性
        return AttendanceGroupDetailVO.from(group);
    }

    // === 变更操作：加 @Transactional ===

    @Transactional
    public void updateAttendanceGroup(String tenantId, String userId, AttendanceGroupUpdateParam param) {
        // === 准入：并发准入 ===
        String lockKey = AttendanceGroupConstants.GROUP_UPDATE_LOCK + param.getGroupId();
        String clientId = UuidUtil.create();
        boolean locked = redisLockHelper.tryLock(lockKey, clientId, AttendanceGroupConstants.GROUP_UPDATE_LOCK_TIME);
        CheckUtils.isTrue(locked, AttendanceGroupExceptionEnum.GROUP_UPDATE_CONFLICT);
        try {
            // === 准入：业务校验 ===
            AttendanceGroup group = attendanceGroupMapper.getByIdAndTenant(tenantId, param.getGroupId());  // 归属+存在性合并判定
            CheckUtils.notEmpty(group, AttendanceGroupExceptionEnum.GROUP_NOT_EXISTS);                    // 存在性
            boolean hasGroupPermission = userGroupRelMapper.existsByGroupIdAndUserId(tenantId, userId, param.getGroupId());
            CheckUtils.isTrue(hasGroupPermission, AttendanceGroupExceptionEnum.NO_PERMISSION);             // 纵向权限
            CheckUtils.isTrue(!group.isLocked(), AttendanceGroupExceptionEnum.GROUP_LOCKED);              // 业务前提·状态

            AttendanceGroup existingGroup = attendanceGroupMapper.getByGroupNameAndTenant(tenantId, param.getGroupName());
            boolean nameAvailable = existingGroup == null || Objects.equals(existingGroup.getId(), param.getGroupId());
            CheckUtils.isTrue(nameAvailable, AttendanceGroupExceptionEnum.GROUP_NAME_DUPLICATE);           // 业务前提·唯一性

            List<Device> devices = validateAndGetDevices(tenantId, userId, param.getDeviceIds());         // 业务前提·关联有效性
            List<Person> persons = validateAndGetPersons(tenantId, userId, param.getPersonIds());         // 业务前提·关联有效性

            // === 执行 ===
            updateGroup(group, param, tenantId);
            log.info("update attendance group, groupId:{}, tenantId:{}", group.getId(), tenantId);

            // === 后置处理 ===
            TransactionSynchronizationUtils.registerAfterCommit(() -> {
                kafkaTemplate.send(AttendanceGroupConstants.GROUP_UPDATE_TOPIC, JsonUtil.toJson(group));   // 事件投递
            });
        } finally {
            redisLockHelper.releaseLock(lockKey, clientId);
        }
    }

    // === 私有方法 ===

    private void updateGroup(AttendanceGroup group, AttendanceGroupUpdateParam param, String tenantId) {
        group.setName(param.getGroupName());
        attendanceGroupMapper.updateById(group);
        deviceGroupRelMapper.deleteByGroupId(tenantId, group.getId());
        deviceGroupRelMapper.batchInsert(tenantId, group.getId(), param.getDeviceIds());
        personGroupRelMapper.deleteByGroupId(tenantId, group.getId());
        personGroupRelMapper.batchInsert(tenantId, group.getId(), param.getPersonIds());
    }

    private List<Device> validateAndGetDevices(String tenantId, String userId, List<String> deviceIds) {
        List<String> distinctIds = deviceIds.stream().distinct().collect(Collectors.toList());            // 标识去重
        List<Device> devices = deviceMapper.listByIdsAndTenant(tenantId, distinctIds);
        CheckUtils.isTrue(distinctIds.size() == devices.size(), DeviceExceptionEnum.DEVICE_NOT_EXISTS);   // 存在性·集合判定
        int permittedCount = userDeviceRelMapper.countByUserIdAndDeviceIds(tenantId, userId, distinctIds);
        CheckUtils.isTrue(distinctIds.size() == permittedCount, DeviceExceptionEnum.NO_PERMISSION);       // 纵向权限·集合判定
        boolean hasOffline = devices.stream().anyMatch(d -> !d.isOnline());
        CheckUtils.isTrue(!hasOffline, DeviceExceptionEnum.DEVICE_OFFLINE);                               // 业务前提·关联有效性
        return devices;
    }

    private List<Person> validateAndGetPersons(String tenantId, String userId, List<String> personIds) {
        List<String> distinctIds = personIds.stream().distinct().collect(Collectors.toList());            // 标识去重
        List<Person> persons = personMapper.listByIdsAndTenant(tenantId, distinctIds);
        CheckUtils.isTrue(distinctIds.size() == persons.size(), PersonExceptionEnum.PERSON_NOT_EXISTS);   // 存在性·集合判定
        int permittedCount = userPersonRelMapper.countByUserIdAndPersonIds(tenantId, userId, distinctIds);
        CheckUtils.isTrue(distinctIds.size() == permittedCount, PersonExceptionEnum.NO_PERMISSION);       // 纵向权限·集合判定
        return persons;
    }
}
```

```java
// === 长耗时操作：不加 @Transactional，使用幂等保障 ===

@Slf4j
@Service
public class OrderService {

    @Autowired
    private OrderMapper orderMapper;
    @Autowired
    private RedisLockHelper redisLockHelper;
    @Autowired
    private OrderCache orderCache;

    public void syncOrder(OrderSyncEvent event) {
        // === 准入：并发准入 ===
        String lockKey = OrderConstants.ORDER_SYNC_LOCK + event.getOrderId();
        String clientId = UuidUtil.create();
        boolean locked = redisLockHelper.tryLock(lockKey, clientId, OrderConstants.ORDER_SYNC_LOCK_TIME);
        CheckUtils.isTrue(locked, OrderExceptionEnum.ORDER_SYNC_CONFLICT);
        try {
            // === 准入：业务校验 ===
            Order order = orderMapper.getByIdAndTenant(event.getTenantId(), event.getOrderId());
            CheckUtils.notEmpty(order, OrderExceptionEnum.ORDER_NOT_EXISTS);                              // 存在性
            if (order.getStatus() == OrderStatus.SYNCED) {
                return; // 幂等判定：已同步则跳过
            }

            // === 执行 ===
            syncOrderDetail(order, event);
            log.info("sync order, orderId:{}, tenantId:{}", order.getId(), event.getTenantId());

            // === 后置处理 ===
            orderCache.refresh(event.getTenantId(), order.getId());                                        // 缓存更新
        } finally {
            redisLockHelper.releaseLock(lockKey, clientId);
        }
    }

    // === 私有方法 ===

    private void syncOrderDetail(Order order, OrderSyncEvent event) {
        order.setStatus(OrderStatus.SYNCED);
        orderMapper.updateById(order);
        // ... 其他同步逻辑
    }
}

// === Receiver：消息消费 ===

@Slf4j
@Component
public class OrderSyncReceiver extends BaseConsumer<String> {

    @Autowired
    private DynamicThreadPoolManager dynamicThreadPoolManager;
    @Autowired
    private OrderService orderService;

    @PostConstruct
    public void init() {
        ThreadPoolExecutor threadPoolExecutor = dynamicThreadPoolManager
                .getThreadPoolExecutor(OrderConstants.ORDER_SYNC_THREAD_POOL);
        this.setConsumeExecutor(threadPoolExecutor);
    }

    @KafkaListener(groupId = "order_sync_group", topics = "order_sync_topic",
            containerFactory = "kafkaListenerContainerFactory")
    public void receive(List<String> messages, Acknowledgment ack) {
        super.onMessage(messages, ack);
    }

    @Override
    public void onDealMessage(String message) {
        try {
            OrderSyncEvent event = JsonUtil.fromJson(message, OrderSyncEvent.class);
            orderService.syncOrder(event);
        } catch (Exception e) {
            log.error("handle message error, message: {}, exception: ", message, e);
        }
    }
}
```