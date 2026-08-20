# 日期处理 SDK 工具类

## 常量

```java
import com.hikvision.building.cloud.util.common.TimeUtil;

public static final String DATA_FORMAT_yyyy_MM_dd_HH_mm_ss = "yyyy-MM-dd HH:mm:ss";
public static final String DATA_FORMAT_yyyyMMddHHmmss = "yyyyMMddHHmmss";
public static final String DATA_FORMAT_y_yyyy_MM_dd_HH_mm_ss = "yyyy/MM/dd HH:mm:ss";
public static final String DEFAULT_DATA_FORMAT = "yyyy-MM-dd";
public static final String DATA_TIME_FORMAT_UTC = "yyyy-MM-dd'T'HH:mm:ss";
```


## 方法

### 获取毫秒时间戳/时间归零

```java
long zeroTime = TimeUtil.getZeroTimeByDate(Date date);                      // 当天00:00:00毫秒时间戳
long minusTime = TimeUtil.minusTime(Date date, int num);                    // 指定日期前N天00:00:00毫秒时间戳
LocalDateTime startOfDay = TimeUtil.zerolizedTime(Date date);               // 时间归零（当天00:00:00）
LocalDateTime endOfDay = TimeUtil.getEndTime(Date date);                    // 当天最后一刻（23:59:59.999）
int remainingSeconds = TimeUtil.calculateToEndTime(Date date);              // 到当天23:59:59剩余秒数
```

### 时间加减

```java
LocalDateTime newTime = TimeUtil.addTime(long time, ChronoUnit unit, int n);// 基于时间戳增减指定单位
LocalDateTime customTime = TimeUtil.reserveDateCustomTime(Date d, String t);// 保留日期替换时间部分（HH:mm:ss）
```

### 格式化

```java
String s = TimeUtil.dateToString(Date d, String format);                    // Date→字符串
String s = TimeUtil.formatLocalDateToString(LocalDate d, String format);    // LocalDate→字符串
String s = TimeUtil.formatLocalDateTimeToString(LocalDateTime d, String f); // LocalDateTime→字符串
```

### 解析

```java
LocalDateTime ldt = TimeUtil.stringToLocalDateTime(String s, String f);     // 字符串→LocalDateTime
LocalDate ld = TimeUtil.stringToLocalDate(String s, String f);              // 字符串→LocalDate
```

### 类型转换

```java
LocalDateTime ldt = TimeUtil.dateToLocalDateTime(Date d);                   // Date→LocalDateTime
LocalDate ld = TimeUtil.dateToLocalDate(Date d);                            // Date→LocalDate
Date d = TimeUtil.localDateToDate(LocalDate ld);                            // LocalDate→Date
Date d = TimeUtil.localDateTimeToDate(LocalDateTime ldt);                   // LocalDateTime→Date
long ms = TimeUtil.localDateTimeToLong(LocalDateTime dt);                   // LocalDateTime→毫秒时间戳
```

### 日期计算

```java
int days = TimeUtil.getActualMaximum(Date d);                               // 所在月份总天数
int week = TimeUtil.getWeekOfDate(Date d);                                  // 星期几（1周一，7周日）
int diffDays = TimeUtil.getAbsDateDiffDay(LocalDate a, LocalDate b);        // 相差天数（绝对值）
LocalDate firstDay = TimeUtil.newThisMonth(Date d);                         // 所在月份第一天
LocalDate lastDay = TimeUtil.lastThisMonth(Date d);                         // 所在月份最后一天
LocalDate firstDayOfYear = TimeUtil.newThisYear(Date d);                    // 所在年份第一天
List<String> dates = TimeUtil.getDatesBetweenTwoDate(String s, String e);  // 两日期之间的所有日期
```

### 获取当前时间

```java
LocalDateTime now = TimeUtil.getCurrentLocalDateTime();                     // 当前LocalDateTime（东八区）
```

### 比较与判断

```java
boolean sameDay = TimeUtil.isTheSameDay(LocalDateTime a, LocalDateTime b);  // 是否同一天
int cmp = TimeUtil.compareTwoTime(LocalDateTime a, LocalDateTime b);        // 比较（1大于/0等于/-1小于）
boolean inRange = TimeUtil.isTimeInRange(Date start, Date end);             // 当前时间是否在范围内
```

### 整点/边界

```java
LocalDateTime hourStart = TimeUtil.floorHourOfNow();                        // 当前整点时刻
LocalDateTime hourStart = TimeUtil.floorHourOfDay(LocalDateTime ldt);       // 传入时间的整点时刻
LocalDateTime minTime = TimeUtil.minOfday(LocalDate dt);                    // 指定日期最小时间（00:00:00）
LocalDateTime maxTime = TimeUtil.maxOfday(LocalDate dt);                    // 指定日期最大时间（23:59:59.999999999）
```