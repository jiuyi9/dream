package com.hz.dream.common;

import lombok.Data;

/**
 * 统一响应封装
 */
@Data
public class HttpResult<T> {

    /** 业务码：200 成功，其他为失败 */
    private int code;

    /** 提示信息 */
    private String message;

    /** 业务数据 */
    private T data;

    private HttpResult(int code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    public static <T> HttpResult<T> success() {
        return new HttpResult<>(200, "success", null);
    }

    public static <T> HttpResult<T> success(T data) {
        return new HttpResult<>(200, "success", data);
    }

    public static <T> HttpResult<T> fail(int code, String message) {
        return new HttpResult<>(code, message, null);
    }

    public static <T> HttpResult<T> fail(String message) {
        return new HttpResult<>(500, message, null);
    }
}