# 消息队列模板

## 是什么

Kafka 与 RabbitMQ 的消费与发送标准模板

## 使用时机

需要异步消息消费或发送时

## Kafka 消费与发送

### 约束

- 消费须继承 `BaseConsumer`（单条）或 `OnceBaseConsumer`（批量），禁止自建消费逻辑
- 线程池须通过 `DynamicThreadPoolManager` 获取，禁止自建线程池
- groupId / topic 命名格式：`{biz}_xxx_group` / `{biz}_xxx_topic`
- containerFactory：业务集群 → `kafkaListenerContainerFactory`，设备中台 → `secondKafkaListenerContainerFactory`

### 模板

**批量接收，单条消费**

```java
import com.hikvision.building.cloud.config.common.kafka.baseconsumer.BaseConsumer;
import com.hikvision.building.cloud.config.common.dynamic.threadpool.DynamicThreadPoolManager;
import java.util.concurrent.ThreadPoolExecutor;

@Slf4j
@Component
public class XxxReceiver extends BaseConsumer<String> {

    @Autowired
    private DynamicThreadPoolManager dynamicThreadPoolManager;

    @PostConstruct
    public void init() {
        ThreadPoolExecutor threadPoolExecutor = dynamicThreadPoolManager
                .getThreadPoolExecutor({threadPoolExecutorName});
        this.setConsumeExecutor(threadPoolExecutor);
    }

    @KafkaListener(groupId = {groupId}, topics = {topic}, containerFactory = "kafkaListenerContainerFactory")
    public void receive(List<String> messages, Acknowledgment ack) {
        super.onMessage(messages, ack);
    }

    @Override
    public void onDealMessage(String message) {
        try {
            // 业务处理...
        } catch (Exception e) {
            log.error("handle message error, message: {}, exception: ", message, e);
        }
    }
}
```

**批量接收，批量消费**

```java
import com.hikvision.building.cloud.config.common.kafka.baseconsumer.OnceBaseConsumer;
import com.hikvision.building.cloud.config.common.dynamic.threadpool.DynamicThreadPoolManager;
import java.util.concurrent.ThreadPoolExecutor;

@Slf4j
@Component
public class XxxReceiver extends OnceBaseConsumer<String> {

    @Autowired
    private DynamicThreadPoolManager dynamicThreadPoolManager;

    @PostConstruct
    public void init() {
        ThreadPoolExecutor threadPoolExecutor = dynamicThreadPoolManager
                .getThreadPoolExecutor({threadPoolExecutorName});
        this.setConsumeExecutor(threadPoolExecutor);
    }

    @KafkaListener(groupId = {groupId}, topics = {topic}, containerFactory = "kafkaListenerContainerFactory")
    public void receive(List<String> msgList, Acknowledgment ack) {
        super.onMessageBatch(msgList, ack);
    }

    @Override
    protected void onDealMessage(List<String> messages) {
        try {
            // 业务处理...
        } catch (Exception e) {
            log.error("handle message error, exception: ", e);
        }
    }
}
```

**消息发送**

```java
@Autowired
@Qualifier(value = "commonKafkaTemplate")
private KafkaTemplate<String, String> commonKafkaTemplate;

commonKafkaTemplate.send(topic, JsonUtil.toJson(obj));
```

## RabbitMQ 消费与发送

### 约束

- queue 命名格式：`{biz}.xxx.queue`

### 模板

**消息接收**

```java
@Slf4j
@Component
public class XxxReceiver {

    @RabbitListener(queues = {queue})
    @RabbitHandler
    public void receiver(String message) {
        try {
            // 业务处理...
        } catch (Exception e) {
            log.error("handle message error, message: {}, exception: ", message, e);
        }
    }
}
```

**消息发送**

```java
@Autowired
private RabbitTemplate rabbitTemplate;

rabbitTemplate.convertAndSend(exchange, null, JsonUtil.toJson(obj));
```