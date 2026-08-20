package com.hz.dream.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.format.Formatter;
import org.springframework.format.FormatterRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

/**
 * MVC 时间格式转换器
 * 处理表单 / @RequestParam / @PathVariable 中的字符串到时间类型的转换。
 *
 * 输入兼容多种常见格式（浏览器 datetime-local 控件默认输出 yyyy-MM-dd'T'HH:mm，
 * 手工输入的 yyyy-MM-dd HH:mm:ss 等），输出统一为 yyyy-MM-dd HH:mm:ss。
 *
 * 说明：Spring Boot 默认未注册 Formatter<LocalDateTime>（spring.mvc.format-date-time 未配置），
 * 表单入参走 ConversionService，因此必须显式注册 Formatter 才能按自定义格式解析。
 */
@Configuration
public class DateTimeConverterConfig implements WebMvcConfigurer {

    private static final DateTimeFormatter[] DATE_TIME_FORMATTERS = {
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"),
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss"),
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"),
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm"),
            DateTimeFormatter.ISO_LOCAL_DATE_TIME,
    };

    private static final DateTimeFormatter[] DATE_FORMATTERS = {
            DateTimeFormatter.ofPattern("yyyy-MM-dd"),
            DateTimeFormatter.ISO_LOCAL_DATE,
    };

    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addFormatterForFieldType(LocalDateTime.class, new Formatter<LocalDateTime>() {
            @Override
            public String print(LocalDateTime object, Locale locale) {
                return object == null ? "" : object.format(JacksonConfig.DATE_TIME_FORMATTER);
            }

            @Override
            public LocalDateTime parse(String text, Locale locale) {
                if (text == null || text.trim().isEmpty()) {
                    return null;
                }
                String s = text.trim();
                for (DateTimeFormatter f : DATE_TIME_FORMATTERS) {
                    try {
                        return LocalDateTime.parse(s, f);
                    } catch (Exception ignored) {
                    }
                }
                throw new IllegalArgumentException(
                        "时间格式错误，应为 " + JacksonConfig.DATE_TIME_PATTERN + "，实际值：" + text);
            }
        });

        registry.addFormatterForFieldType(LocalDate.class, new Formatter<LocalDate>() {
            @Override
            public String print(LocalDate object, Locale locale) {
                return object == null ? "" : object.format(JacksonConfig.DATE_FORMATTER);
            }

            @Override
            public LocalDate parse(String text, Locale locale) {
                if (text == null || text.trim().isEmpty()) {
                    return null;
                }
                String s = text.trim();
                for (DateTimeFormatter f : DATE_FORMATTERS) {
                    try {
                        return LocalDate.parse(s, f);
                    } catch (Exception ignored) {
                    }
                }
                throw new IllegalArgumentException(
                        "日期格式错误，应为 " + JacksonConfig.DATE_PATTERN + "，实际值：" + text);
            }
        });
    }
}