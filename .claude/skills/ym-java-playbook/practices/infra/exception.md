# 异常处理规范

## 是什么

业务异常码定义与异常抛出的标准模板

## 使用时机

需要定义业务异常码或抛出业务异常时

## 异常码定义

### 约束

- 异常码由 8 位数字组成且全局不得重复，结构：业务线（2位）+ 模块（2位）+ 资源（2位）+ 错误（2位）
- 异常码必须实现 `ExceptionInfo` 接口
- 异常码须区分语义，如：权限不足用 `NO_PERMISSION`，存在性失败用 `NOT_EXISTS`

### 模板

```java
@Getter
@AllArgsConstructor
public enum DeviceExceptionEnum implements ExceptionInfo {
    DEVICE_NOT_EXISTS(88100101, "设备不存在"),;
}
```

## 异常抛出

### 约束

- 业务异常抛出必须使用 `CheckUtils` 工具类
- 禁止裸抛 `RuntimeException` 或自定义异常类

### 模板

```java
import com.hikvision.building.cloud.util.common.CheckUtils;

// 非空校验：obj 为空时抛出业务异常
CheckUtils.notEmpty(Object obj, ExceptionInfo errorCode);
// 为空校验：obj 非空时抛出业务异常
CheckUtils.isEmpty(Object obj, ExceptionInfo errorCode);
// 条件校验：flag 为 false 时抛出业务异常
CheckUtils.isTrue(boolean flag, ExceptionInfo errorCode);

// 示例：Service 中查询设备，若不存在则抛出业务异常
Device device = deviceMapper.getByIdAndTenant(tenantId, deviceId);
CheckUtils.notEmpty(device, DeviceExceptionEnum.DEVICE_NOT_EXISTS);
```

## 正反例

**裸抛 RuntimeException —— 异常码不可追踪**

```java
// ❌ 裸抛 RuntimeException：无异常码、无语义、无法追踪
if (device == null) {
    throw new RuntimeException("设备不存在");
}

// ✅ 使用 CheckUtils + ExceptionInfo：异常码可追踪、语义清晰
CheckUtils.notEmpty(device, DeviceExceptionEnum.DEVICE_NOT_EXISTS);
```

**自定义异常类 —— 绕过统一异常体系**

```java
// ❌ 自定义异常类：绕过 ExceptionInfo 体系，异常码不可管理
public class DeviceNotFoundException extends RuntimeException {
    public DeviceNotFoundException(String message) {
        super(message);
    }
}

// ✅ 使用 ExceptionInfo 枚举：异常码集中管理、全局唯一
public enum DeviceExceptionEnum implements ExceptionInfo {
    DEVICE_NOT_EXISTS(88100101, "设备不存在");
}
```

**异常码语义混淆 —— 无法区分错误原因**

```java
// ❌ 所有场景共用同一个异常码：无法区分是"不存在"还是"无权限"
CheckUtils.notEmpty(device, DeviceExceptionEnum.DEVICE_ERROR);
CheckUtils.isTrue(hasPermission, DeviceExceptionEnum.DEVICE_ERROR);

// ✅ 异常码须区分语义
CheckUtils.notEmpty(device, DeviceExceptionEnum.DEVICE_NOT_EXISTS);
CheckUtils.isTrue(hasPermission, DeviceExceptionEnum.DEVICE_NO_PERMISSION);
```