---
name: ym-java-playbook
description: 云眸 Java 后端编码规范与实现指南，凡涉及 Java 编码必须遵守
allowed-tools: Read, Glob, Grep
---

# 云眸 Java 编码规范

## 使用时机

- 编写任意 Java 后端代码
- 重构现有代码
- 不确定某个场景的代码写法

## 目录总览

```
ym-java-playbook/
├── rules/                    — 约束：无条件遵守的红线，编码前必读
└── practices/                — 实践：分层编码实践，含专属约束与示例
```

### rules（规则约束）

```
rules/
├── project-constraints.md   — 工程级强制基线（技术栈、修改边界、复用纪律）
└── code-constraints.md      — 通用代码风格规范
```

### practices（分层实践）

```
practices/
├── core/                     — 业务核心层
│   ├── interface.md          — 写接口（Web / Endpoint / Api）
│   ├── service.md            — 写业务逻辑
│   └── repository.md         — 操作数据库
├── infra/                    — 基础设施层
│   ├── cache.md              — 缓存管理规范
│   ├── mq.md                 — 消息队列模板
│   ├── xxljob.md             — 定时任务模板
│   └── exception.md          — 业务异常模板
└── sdk/                      — 工具类层
    ├── common.md             — 通用 SDK
    ├── json.md               — JSON 序列化/反序列化
    ├── datetime.md           — 日期时间处理
    ├── redis.md              — Redis 操作
    └── lock.md               — 分布式锁
```

> 实践需根据项目实际架构灵活适配，如 MVC、DDD 等，核心规范不变，分层语义因项目而异

