# Redis SDK 工具类

## 方法

```java
import com.hikvision.building.cloud.util.common.RedisCacheUtils;

@Autowired
private RedisCacheUtils redisCacheUtils;

// 基础缓存读写
redisCacheUtils.set(String key, Object value);                             // 写入缓存（自动判断类型）
T obj = redisCacheUtils.getFailedWithRecache(String key, Class<T> clazz);  // 读取并反序列化（失败时尝试重新缓存）
T obj = redisCacheUtils.get(String key, Class<T> clazz);                   // 读取并反序列化
Object obj = redisCacheUtils.get(String key);                              // 读取原始对象
String str = redisCacheUtils.getStr(String key);                           // 读取字符串
Integer num = redisCacheUtils.getInt(String key);                          // 读取整数

// Key 管理
redisCacheUtils.del(String key);                                           // 删除单个Key
redisCacheUtils.del(Collection<String> keys);                              // 批量删除Key
redisCacheUtils.expire(String key, long timeout, TimeUnit unit);           // 设置过期时间
Long seconds = redisCacheUtils.ttl(String key);                            // 获取剩余过期时间（秒）
boolean exists = redisCacheUtils.exist(String key);                        // 判断Key是否存在
Set<String> keys = redisCacheUtils.keys(String pattern);                   // 模糊匹配Key

// 带过期时间的写入
redisCacheUtils.setEx(String key, Object value, long ms);                  // 设置并指定过期时间（毫秒）
redisCacheUtils.setEx(String key, Object value, long t, TimeUnit unit);    // 设置并指定过期时间及单位
redisCacheUtils.setWithEx(String key, Object value, long t, TimeUnit unit);// 同setEx
redisCacheUtils.setNX(String key, String val);                             // 仅Key不存在时设置
redisCacheUtils.setNX(String key, String val, long t, TimeUnit unit);      // 仅Key不存在时设置并指定过期时间
redisCacheUtils.setIfAbsent(String key, String v, Long t, TimeUnit unit);  // 仅Key不存在时设置

// 原子操作
Long v = redisCacheUtils.increment(String key);                            // 自增1
Long v = redisCacheUtils.incrementWithCache(String key);                   // 自增1（带本地缓存优化）
Long v = redisCacheUtils.incrementWithInit(String key, Long init);         // 自增1（Key不存在时使用初始值）
long v = redisCacheUtils.decrement(String key);                            // 自减1
long v = redisCacheUtils.addAndGet(String key, int count);                 // 增加指定数值（可为负数）
redisCacheUtils.delWithInit(String key);                                   // 移除本地缓存计数器并删除Key
redisCacheUtils.removeKey(String key);                                     // 移除本地缓存计数器

// List 操作
int size = redisCacheUtils.lsize(String key);                              // 获取List长度
List<T> list = redisCacheUtils.lrange(String key, long s, long e);         // 获取指定范围元素（泛型）
List<String> list = redisCacheUtils.lrangeOfStr(String key, long s, long e);// 获取指定范围元素（String）
redisCacheUtils.ltrim(String key, long s, long e);                         // 截取保留指定范围
redisCacheUtils.lRightBatchPush(String key, Collection<?> values);         // 批量右侧推入（泛型）
redisCacheUtils.lRightBatchPushOfStr(String key, Collection<String> vals); // 批量右侧推入（String）
redisCacheUtils.lLeftBatchPush(String key, Collection<?> values);          // 批量左侧推入（泛型）
redisCacheUtils.lLeftBatchPushOfStr(String key, Collection<String> vals);  // 批量左侧推入（String）
redisCacheUtils.lRightPush(String key, T obj);                             // 右侧推入单个元素
redisCacheUtils.lRightPushOfStr(String key, String obj);                   // 右侧推入单个元素（String）
redisCacheUtils.lLeftPush(String key, T obj);                              // 左侧推入单个元素
redisCacheUtils.lLeftPushOfStr(String key, String obj);                    // 左侧推入单个元素（String）
redisCacheUtils.lSet(String key, long index, T obj);                       // 设置指定索引位置的值
T obj = redisCacheUtils.lleftPop(String key);                              // 左侧弹出并移除（泛型）
String str = redisCacheUtils.lleftPopOfStr(String key);                    // 左侧弹出并移除（String）
redisCacheUtils.lremove(String key, int count, Object obj);                // 移除指定值（count>0从头，<0从尾，=0全删）
redisCacheUtils.lremoveOfStr(String key, int count, String obj);           // 移除指定值（String）

// Set 操作
redisCacheUtils.sadd(String key, T... values);                             // 添加元素
Set<T> set = redisCacheUtils.smembers(String key);                         // 获取所有成员
List<T> list = redisCacheUtils.srandomMerbers(String key, long count);     // 随机获取指定数量（可重复）
Set<T> set = redisCacheUtils.sdistinctRandomMembers(String key, long n);   // 随机获取指定数量（不重复）
T obj = redisCacheUtils.srandomMerber(String key);                         // 随机获取一个成员
boolean exists = redisCacheUtils.sisMember(String key, Object value);      // 判断值是否在Set中
Set<T> set = redisCacheUtils.sInter(String k1, String k2);                 // 获取两个Set的交集
redisCacheUtils.sremove(String key, Object... values);                     // 批量删除元素
long size = redisCacheUtils.ssize(String key);                             // 获取Set大小
T obj = redisCacheUtils.spop(String key);                                  // 随机弹出并移除一个元素

// ZSet 操作
redisCacheUtils.zadd(String key, Object value, Long score);                // 添加元素及分数
Set<ZSetOperations.TypedTuple<T>> t = redisCacheUtils.zrankWithScores(k, long s, long e);// 获取指定排名范围成员及分数
Set<T> set = redisCacheUtils.zrank(String key, long s, long e);            // 获取指定排名范围成员
Set<ZSetOperations.TypedTuple<T>> t = redisCacheUtils.zreverseRangeWithScores(k, long s, long e);// 获取倒序排名范围成员及分数
Set<T> set = redisCacheUtils.zreverseRange(String key, long s, long e);    // 获取倒序排名范围成员
redisCacheUtils.zremoveRange(String key, long s, long e);                  // 移除指定排名范围成员
redisCacheUtils.removeRangeByScore(String key, long s, long e);            // 移除指定分数范围成员
Long c = redisCacheUtils.zremoveRangeByScore(String k, double min, double max);// 移除指定分数范围成员（按double范围）
redisCacheUtils.zremove(String key, Object... value);                      // 移除指定成员
Long size = redisCacheUtils.zsize(String key);                             // 获取ZSet大小
Set<ZSetOperations.TypedTuple<T>> t = redisCacheUtils.zrangeByScoreWithScores(k, double min, double max, long offset, long count);// 获取指定分数范围成员及分数（分页）
redisCacheUtils.zincrementScore(String key, T obj, double score);          // 增加成员分数
Double score = redisCacheUtils.zscore(String key, Object obj);             // 获取成员分数

// Hash 操作
redisCacheUtils.hset(String key, String item, Object value);               // 放入单个键值对
redisCacheUtils.hmset(String key, Map<String, ?> map);                     // 批量放入键值对
Map<String, T> map = redisCacheUtils.hmget(String key);                    // 获取所有键值对
T obj = redisCacheUtils.hget(String key, String item);                     // 获取指定字段的值
List<T> list = redisCacheUtils.hMultiGet(String k, Collection<String> hs); // 批量获取指定字段的值
redisCacheUtils.hdel(String key, String... items);                         // 删除指定字段
boolean exists = redisCacheUtils.hHasKey(String key, String item);         // 判断是否存在指定字段
Boolean ok = redisCacheUtils.hSetNx(String key, String item, Object val);  // 仅字段不存在时放入
Long v = redisCacheUtils.hIncrement(String key, String item, long incr);   // 对指定字段自增
```