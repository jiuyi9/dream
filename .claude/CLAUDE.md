# CLAUDE.md

## 语言

- 请始终使用中文回复

## Shared

| 共享资源 | 用途 |
|----------|------|
| `shared/ym-api-spec.md` | 云眸 API 规范 |

## Skills

| skill | 用途 | 适用场景 |
|------|------|----------|
| `ym-java-playbook` | 云眸 Java 后端编码规范与实现指南，含约束、实践与示例 | 编写任意 Java 后端代码、重构现有代码、不确定某个场景的代码写法时 |
| `ym-api-design` | 按云眸 API 规范生成 Web 接口及开放接口设计文档 | 设计阶段生成接口文档，或从代码提取接口信息生成标准化文档时 |
| `ym-code-review` | 质量与安全双维度代码审查，输出结构化审查报告 | 审查指定内容或未提交的代码变更时 |
| `ym-mysql` | MySQL 8.0+ 全栈指南，含 SQL 编写/审查/调优、表结构设计、索引优化、慢查询/死锁诊断、MyBatis 集成、数据建模 | 涉及 SQL 编写/审查/调优、表设计、索引优化、故障诊断、MyBatis 开发、数据建模时 |
| `ym-devops` | DevOps 工具集，包含 Jenkins 镜像构建与镜像发布两套独立工具 | 需要构建/打包/触发 Jenkins 构建，或发布服务/组件到环境时 |

> **以上 Skills 优先匹配**

## MCP

| MCP | 用途 | 适用场景 |
|-----|------|----------|
| `get_ym_api` | 查询云眸 API 管理平台中定义的接口协议信息 | 需要获取某个接口的完整定义（请求/响应结构、参数约定等）时 |
| `idea-mcp` | 与 IDEA 交互：文件导航与读写、文本/正则/符号搜索、代码诊断重构、构建运行、调试等 | 涉及项目代码的查找、分析、修改、构建、调试等功能时，优先使用此 MCP，而非直接操作文件系统 |
| `chrome-devtools` | 浏览器调试与控制：截图、性能分析、网络请求查看、页面交互等 | 需要调试前端页面、分析性能、抓取网络请求、模拟用户操作时 |

## Plugins

### Superpowers

Superpowers 为默认工作方式，各场景匹配即启用对应技能。若未安装，请执行：

```bash
/plugin install superpowers@claude-plugins-official
/reload-plugins
```

## 典型场景

> 以下为推荐映射，非强制约束。各 Skill 与 MCP 按场景自动匹配，Superpowers 贯穿全流程

### 项目需求开发

| 环节 | Skill | MCP |
|------|-------|-----|
| 需求分析 | — | — |
| 方案设计 | ym-api-design、ym-mysql | get_ym_api |
| 编码实现 | ym-java-playbook、ym-mysql | get_ym_api、idea-mcp |
| 代码审查 | ym-code-review | idea-mcp |
| 构建部署 | ym-devops | — |
| 功能测试 | — | chrome-devtools |