# 缓存管理规范

## 是什么

统一管理 Redis 缓存与本地缓存，屏蔽底层操作细节

## 使用时机

需要使用 Redis 缓存或本地缓存时

## 约束

- 缓存须由统一 Cache 类集中封装管理，Key 及增删改查方法内聚其中，严禁业务代码直接操作或分散维护
- Redis 操作必须使用 `RedisCacheUtils`，禁止直接使用 `StringRedisTemplate` / `RedisTemplate`
- 本地缓存优先推荐 Caffeine

## 示例

```java
@Component
public class XxxCache {

    // 本地缓存（Caffeine）
    private Cache localCache;

    // Redis 缓存工具
    @Autowired
    private RedisCacheUtils redisCacheUtils;

    // Key 前缀常量
    private static final String KEY_PREFIX = "xxx:xxx";

    // 获取缓存 Key（统一在类内部管理）
    private String getKey(String bizId) {
        return KEY_PREFIX + bizId;
    }

    // 按需封装业务所需的缓存方法（如：get、set、delete 等）
}
```

