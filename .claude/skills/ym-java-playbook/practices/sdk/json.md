# JSON SDK 工具类

## 方法

```java
import com.hikvision.building.cloud.util.common.json.JsonUtil;

JsonUtil.toJson(T pojo);                                              // 序列化为 JSON 字符串
JsonUtil.fromJson(String json, Class<T> type);                        // 反序列化为对象（输入为空返回 null）
JsonUtil.toCollection(String str, TypeReference<List<T>> ref);        // 反序列化为泛型集合
JsonUtil.toPojo(String str, TypeReference<T> ref);                    // 反序列化为泛型对象（支持嵌套泛型）
JsonUtil.toPojo(String str, Class outer, Class inner);                // 反序列化为单层嵌套泛型
JsonUtil.json2map(String str);                                        // 反序列化为 Map<String, Object>
JsonUtil.getObjectMapper();                                           // 获取底层 ObjectMapper 实例
```