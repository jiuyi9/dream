# 编码规范约束

## 代码风格

- 单个方法不超过 60 行。方法体只保留流程编排/校验/调度，核心逻辑拆到私有方法中
- 对象转换抽离独立方法，或在目标类中提供 `of()`、`from()` 等静态工厂方法
- 优先使用卫语句拆解复杂逻辑
- 优先使用当前 JDK 版本支持的现代语法（如 Stream、Lambda、方法引用），避免无谓地使用旧式写法

## 代码注释

- 所有类、接口和方法必须通过注释说明其用途，语义清晰且简洁
- 复杂方法必须通过注释说明整体步骤，并在关键步骤处补充说明

## 日志打印

- 统一使用 Slf4j，禁止 `System.out.println`
- 日志内容必须使用英文
- INFO 记录关键流程，WARN 记录可恢复异常/异常数据，ERROR 记录业务受影响异常，DEBUG/TRACE 仅用于排查
- 严禁输出密码、密钥、证件及银行卡等敏感信息，禁止直接打印含此类数据的整体对象
- 禁止在循环或高频场景中大量打印日志，禁止无意义或重复日志

## 常量管理

- Topic、Queue、Cache Key、配置项 Key 等基础设施标识符必须定义为常量，禁止硬编码
- 常量按业务/功能域分散维护，禁止单一"大而全"的常量类
- 状态、类型、结果等固定集合优先使用枚举

## 日期时间

- 禁止使用 `java.sql.Date`、`java.sql.Time`、`java.sql.Timestamp`
- 优先使用 `LocalDateTime`、`LocalDate`

## Lombok

- 所有 POJO 必须优先使用 Lombok
- 仅允许：`@Data`、`@Getter`、`@Setter`、`@NoArgsConstructor`、`@AllArgsConstructor`、`@EqualsAndHashCode`、`@ToString`、`@Slf4j`