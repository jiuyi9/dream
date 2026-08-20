# 定时任务模板

## 是什么

分布式定时任务（xxl-job）的标准模板

## 使用时机

需要实现分布式定时任务时

## 约束


## 模板

```java

import org.springframework.context.ApplicationListener;
import com.xxl.job.core.handler.annotation.JobHandler;
import com.xxl.job.core.biz.model.ReturnT;
import com.xxl.job.core.handler.IJobHandler;

import com.hikvision.building.cloud.gaia.common.event.ServiceReadyEvent;
import com.hikvision.building.cloud.sdk.job.client.JobClient;
import com.hikvision.building.cloud.sdk.job.client.dto.JobInfoDto;
import com.hikvision.building.cloud.sdk.job.config.XxlJobProperties;

@Slf4j
@Component
@JobHandler(value = "xxxJob")
public class XxxJob extends IJobHandler implements ApplicationListener<ServiceReadyEvent> {

    @Autowired
    private JobClient jobClient;

    @Autowired
    private XxlJobProperties xxlJobProperties;

    // IJobHandler 的 execute 执行方法实现
    @Override
    public ReturnT<String> execute(String s) {

        try {
            // 执行代码逻辑
        } catch (Exception e) {
            log.error("xxxJob execute failed", e);
        }
        return SUCCESS;
    }

    // xxlJob 定义
    @Override
    public void onApplicationEvent(ServiceReadyEvent event) {
        if (xxlJobProperties.isEnabled()) {
            JobInfoDto attendTaskJob = JobInfoDto.builder().jobDesc({任务描述}).jobCron({cron表达式})
                    .author(xxlJobProperties.getAppName()).jobGroupName(xxlJobProperties.getAppName())
                    .executorHandler({xxxJob}) // 和 @JobHandler 的value 对应
                    .clientId({jobId}).build();
            ReturnT<String> result = jobClient.add(attendTaskJob);
            log.info("init xxx job result: {}", result);
        }
    }
}
```