# 工程约束

## 技术栈

| 类别 | 版本 / 选型 |
|------|-------------|
| JDK | 11 |
| Spring Boot | 2.3.9.RELEASE |
| Spring Cloud | Hoxton.SR12 |
| 数据库访问层 | Druid + MyBatis + XML |
| 缓存 | Redis |
| 消息队列 | Kafka（RabbitMQ 仅在用户明确要求时可用） |

> 上述技术栈为唯一允许选项，禁止引入列表外的任何框架或组件（如 MyBatis-Plus、JPA、MongoDB）

## 文件修改边界

- 仅允许修改 `src/main/java/**` 与 `src/test/**` 下的文件
- 禁止修改 `pom.xml`、`yml`、`properties`、脚本、配置、文档等工程基础设施文件
- 因上述限制，发现依赖/配置缺失时不得自行处理，由人工后续补充

## 模板与工具类复用

- infra 模板与 sdk 工具类为强制基线，**必须直接复用，禁止绕过基线、重复造轮子或私自封装**