---
name: ym-devops
description: |
  DevOps 工具集，包含 Jenkins 镜像构建和镜像发布。
  触发场景：
  - 镜像构建: 用户提到"构建"、"打包"、"触发 Jenkins"、"build"、"deploy" 等命令时使用
  - 镜像发布: 用户提到"发布平台"、"发布服务"、"发布组件"、"查看组件"、"resolve"、"准备发布" 等命令时使用
---

# DevOps 工具集

## 概述

本 skill 包含两套独立工具：

1. **Jenkins 镜像构建** - 通过 resolve / build / result 三步触发 Jenkins 构建并获取结果
2. **镜像发布** - 将 Jenkins 产出的镜像通过云眸发布平台的接口发布到对应环境

## 目录结构

```
ym-devops/
├── SKILL.md
└── scripts/
    ├── jenkins/                      # Jenkins 镜像构建
    │   ├── jenkins.json              # Jenkins 系统配置
    │   └── jenkins_build.py          # Jenkins 构建脚本
    └── publish/                      # 镜像发布
        ├── publish.json              # 发布平台配置
        ├── login.py                  # 发布平台登录
        └── publish.py                # 发布操作
```

---

## Jenkins 镜像构建

### 概述

触发 Jenkins 构建任务，产出镜像标签。

### 工作流程

#### 步骤一：解析构建参数

执行 `resolve` 命令解析构建参数：

```bash
python ${CLAUDE_SKILL_DIR}/scripts/jenkins/jenkins_build.py resolve \
  [<slug>] \
  [--branch <branch>] \
  [--components <components>] \
  [--jdk <version>]
```

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `slug` | 否 | Jenkins 任务短标识，支持短标识或完整 job 名，大小写不敏感匹配 | `siot`（对应 `iBuilding-87A0-UNIT-CLOUD-siot`） |
| `--branch` / `-b` | 否 | 分支名 | `master` |
| `--components` / `-c` | 否 | 要构建的组件，多个用逗号分割 | `siot-a,siot-b` |
| `--jdk` | 否 | JDK 版本 | `11.0.15.1` |

返回 JSON：

```json
{
  "job": "iBuilding-87A0-UNIT-CLOUD-siot",
  "branch": "develop",
  "componentSections": ["siot-a", "siot-b", "siot-c"],
  "selectedComponents": ["siot-a"],
  "jdkVersion": "11.0.15.1"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `job` | string | 完整 Jenkins job 名 |
| `branch` | string | 分支名 |
| `componentSections` | string[] | 可构建组件列表 |
| `selectedComponents` | string[] | 选中的待构建组件 |
| `jdkVersion` | string | JDK 版本 |

校验规则：

- 各字段均不得为空，任一缺失则提示用户补充
- `selectedComponents` 为空但 `componentSections` 有值时，列出可用组件引导用户选择

校验通过后展示以下信息，用户确认后进入步骤二：

```markdown
即将触发构建：
- 构建工程: <job>
- 分支: <branch>
- 构建组件: <selectedComponents>
- JDK 版本: <jdkVersion>
```

#### 步骤二：提交构建任务

将步骤一确认的参数传入 `build` 命令，提交构建任务并获取构建信息：

```bash
python ${CLAUDE_SKILL_DIR}/scripts/jenkins/jenkins_build.py build \
  --job <job> \
  --components <components> \
  --branch <branch> \
  --jdk <version>
```

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--job` | 是 | 完整 Jenkins job 名 | `iBuilding-87A0-UNIT-CLOUD-siot` |
| `--components` | 是 | 要构建的组件，多个用逗号分割 | `siot-a,siot-b` |
| `--branch` | 是 | 分支名称 | `master` |
| `--jdk` | 是 | JDK 版本 | `11.0.15.1` |

返回 JSON：

```json
{
  "job": "iBuilding-87A0-UNIT-CLOUD-siot",
  "buildNumber": 1234,
  "consoleUrl": "https://ebg-ci.hikvision.com.cn/job/iBuilding-87A0-UNIT-CLOUD-siot/1234/console"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `job` | string | 完整 job 名 |
| `buildNumber` | int | 构建编号 |
| `consoleUrl` | string | Jenkins 控制台 |

触发成功后展示以下信息，随后进入步骤三：

```markdown
构建任务已提交：
- 构建编号: <buildNumber>
- Jenkins 控制台: <consoleUrl>
```

#### 步骤三：等待构建结果

执行 `result` 命令，等待构建结束并返回最终结果：

```bash
python ${CLAUDE_SKILL_DIR}/scripts/jenkins/jenkins_build.py result \
  --job <job> \
  --build-number <buildNumber>
```

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--job` | 是 | 完整 Jenkins job 名 | `iBuilding-87A0-UNIT-CLOUD-siot` |
| `--build-number` / `-n` | 是 | 构建编号 | `1234` |

返回 JSON：

```json
{
  "job": "iBuilding-87A0-UNIT-CLOUD-siot",
  "buildNumber": 1234,
  "result": "SUCCESS",
  "imageTag": "20260724-1234-siot-master",
  "successComponents": "siot-a,siot-b",
  "failedComponents": "",
  "consoleUrl": "https://ebg-ci.hikvision.com.cn/job/iBuilding-87A0-UNIT-CLOUD-siot/1234/console"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `job` | string | 完整 job 名 |
| `buildNumber` | int | 构建编号 |
| `result` | string | Jenkins 构建结果，`SUCCESS` 表示成功 |
| `imageTag` | string | 镜像标签 |
| `successComponents` | string | 构建成功的组件，逗号分隔 |
| `failedComponents` | string | 构建失败的组件，逗号分隔 |
| `consoleUrl` | string | Jenkins 控制台 |

构建结束后根据结果展示：

```markdown
构建完成：
- 构建结果: <result>
- 构建编号: <buildNumber>
- 镜像标签: <imageTag>
- 成功组件: <successComponents>
- 失败组件: <failedComponents>
- Jenkins 控制台: <consoleUrl> （展示原始URL）
```

构建结束后，根据组件状态分情况处理：

- 全部成功（`successComponents` 非空且 `failedComponents` 为空）→ 若用户已有明确发布意愿则直接发布，否则询问是否发布
- 存在失败（`failedComponents` 非空）→ 让用户选择：发布已成功的组件，还是排查失败组件后重新构建

> 发布时仅允许选择 `successComponents` 中的组件

---

## 镜像发布

### 概述

将 Jenkins 产出的镜像通过云眸发布平台的接口发布到对应环境。

### 工作流程

#### 步骤一：解析发布参数

执行 `resolve` 命令解析发布参数：

```bash
python ${CLAUDE_SKILL_DIR}/scripts/publish/publish.py resolve --components <components> --image-tag <imageTag> [--env <env>]
```

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--components` / `-c` | 是 | 组件名称，多个用逗号分隔 | `siot-a,siot-b` |
| `--image-tag` / `-t` | 是 | 镜像标签 | `20260724-1234-siot-master` |
| `--env` / `-e` | 否 | 发布环境，默认 `ys7-pb` | `ys7-pb` |

返回 JSON：

```json
{
  "imageTag": "20260724-1234-siot-master",
  "env": "ys7-pb",
  "envId": 123,
  "envRuntimeUrl": "http://xxx.xxx.com.cn/k8s?env=ys7-pb",
  "components": [
    {
      "name": "siot-a",
      "componentId": "abc456",
      "imageName": "siot-a",
      "version": "v1.0.0",
      "versionId": "def789"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `imageTag` | string | 镜像标签 |
| `env` | string | 环境名 |
| `envId` | int | 环境 ID |
| `envRuntimeUrl` | string | 环境运行情况查看地址 |
| `components[].name` | string | 组件名 |
| `components[].componentId` | string | 组件 ID |
| `components[].imageName` | string | 镜像名 |
| `components[].version` | string | 发布版本 |
| `components[].versionId` | string | 版本 ID |

展示以下信息，用户确认后进入发布，如需调整版本则进入步骤二：

```markdown
即将发布：
- 镜像标签: <imageTag>
- 环境: <env>
- 组件列表:
  | 组件 | 版本 |
  |------|------|
  | <name> | <version> |
  | ... | ... |
```

#### 步骤二：调整版本（按需）

用户需要调整版本时，执行 `versions` 查看单个组件的版本列表：

```bash
python ${CLAUDE_SKILL_DIR}/scripts/publish/publish.py versions <component>
```

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `component` | 是 | 组件名称 | `siot-a` |

返回 JSON：

```json
{
  "component": "siot-a",
  "versions": [
    {"name": "v2.0.0", "versionId": "ghi012"},
    {"name": "v1.0.0", "versionId": "def789"}
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `component` | string | 组件名 |
| `versions[].name` | string | 版本名 |
| `versions[].versionId` | string | 版本 ID |

展示版本列表供用户选择：

```markdown
<component> 可用版本：
| 版本 |
|------|
| v2.0.0 |
| v1.0.0 |
```

用户选择版本后，将对应组件的 `version` 和 `versionId` 更新为选定值，重新展示确认信息。

#### 步骤三：执行发布

确认后，开启多个子进程（最多5个），逐个调用 `publish` 命令发布每个组件：

```bash
python ${CLAUDE_SKILL_DIR}/scripts/publish/publish.py publish \
  --component-id <componentId> \
  --version-id <versionId> \
  --image-name <imageName> \
  --image-tag <imageTag> \
  [--env <env>]
```

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--component-id` | 是 | 组件 ID | `abc456` |
| `--version-id` | 是 | 版本 ID | `def789` |
| `--image-name` | 是 | 镜像名 | `siot-a` |
| `--image-tag` / `-t` | 是 | 镜像标签 | `20260724-1234-siot-master` |
| `--env` / `-e` | 否 | 发布环境，默认 `ys7-pb` | `ys7-pb` |

成功返回 `{"success": true}`，失败返回 `{"success": false}` 并退出码 1。

等所有子进程发布完成后汇总展示：

```markdown
发布完成：
- 成功组件: <component1>,<component2>
- 失败组件: <component1>,<component2>

详情请查看: <envRuntimeUrl>（展示原始url链接）
```