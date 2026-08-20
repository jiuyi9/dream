# 分布式锁 SDK 工具类

## 方法

### RedisLockHelper（优先使用）

```java
import com.hikvision.building.cloud.util.common.RedisLockHelper;

@Autowired
private RedisLockHelper redisLockHelper;

redisLockHelper.tryLock(String lockKey, String clientId, long milliseconds);   // 获取锁（SET NX + PX，clientId 推荐使用 UuidUtil.create() 生成）
redisLockHelper.releaseLock(String lockKey, String clientId);                  // 释放锁（Lua 脚本校验 clientId 后删除，防止误释他人锁）
```

### RedissonLockUtil（长耗时独占场景）

```java
import com.hikvision.building.cloud.util.common.RedissonLockUtil;

@Autowired
private RedissonLockUtil redissonLockUtil;

redissonLockUtil.lock(String lockKey, long leaseTime);                          // 阻塞加锁（指定持有时间）
redissonLockUtil.lock(String lockKey);                                          // 阻塞加锁（默认30秒，watchdog 自动续期）
boolean locked = redissonLockUtil.tryLock(String lockKey, long waitTime);       // 尝试加锁（指定等待时间，watchdog 自动续期）
boolean locked = redissonLockUtil.tryLockNoWait(String lockKey, long leaseTime);// 尝试加锁（无 watchdog，指定持有时间，不等待）
boolean locked = redissonLockUtil.tryLock(String lockKey, long leaseTime, long waitTime); // 尝试加锁（指定持有时间和等待时间）
redissonLockUtil.unlock(String lockKey);                                        // 解锁
boolean locked = redissonLockUtil.isLock(String lockKey);                       // 判断锁是否已被持有
boolean held = redissonLockUtil.isHeldByCurrentThread(String lockKey);          // 判断当前线程是否持有该锁
```