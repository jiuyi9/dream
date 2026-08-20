# 通用 SDK 工具类

## 适用范围

涉及 String、Object、UUID 等通用处理时

## 约束

- 本 SDK 未覆盖的能力优先选用 Apache Commons、Spring 等业界成熟工具类，禁止使用来源不明的第三方库

## 方法

### String

String 处理优先使用 `org.apache.commons.lang3.StringUtils`，禁止自建替代

### Object 工具类

```java
import com.hikvision.building.cloud.util.common.ObjectUtils;

boolean isArr = ObjectUtils.isArray(Object obj);              // 判断是否为数组
boolean isArrEmpty = ObjectUtils.isEmpty(Object[] array);     // 判断数组是否为空
boolean isEmpty = ObjectUtils.isEmpty(Object obj);            // 判断对象是否为空（null/数组/字符串/集合/Map）
boolean isNotEmpty = ObjectUtils.isNotEmpty(Object obj);      // 判断对象是否非空
```

### UUID 主键生成

```java
import com.hikvision.building.cloud.util.common.UuidUtil;

String uuid = UuidUtil.create();  // 生成32位无连接符UUID，用作主键ID或TraceId
```