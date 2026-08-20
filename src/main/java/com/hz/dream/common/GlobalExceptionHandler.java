package com.hz.dream.common;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

/**
 * 全局异常处理：把业务异常统一转成 HttpResult
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    @ResponseStatus(HttpStatus.OK)
    public HttpResult<Void> handleIllegalArgument(IllegalArgumentException e) {
        log.warn("illegal argument: {}", e.getMessage());
        return HttpResult.fail(400, e.getMessage());
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    @ResponseStatus(HttpStatus.OK)
    public HttpResult<Void> handleTypeMismatch(MethodArgumentTypeMismatchException e) {
        log.warn("param type mismatch: {}", e.getMessage());
        String msg = "参数 " + e.getName() + " 格式错误";
        if (e.getCause() instanceof IllegalArgumentException && e.getCause().getMessage() != null) {
            msg = e.getCause().getMessage();
        }
        return HttpResult.fail(400, msg);
    }

    @ExceptionHandler(IllegalStateException.class)
    @ResponseStatus(HttpStatus.OK)
    public HttpResult<Void> handleIllegalState(IllegalStateException e) {
        log.warn("illegal state: {}", e.getMessage());
        return HttpResult.fail(409, e.getMessage());
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.OK)
    public HttpResult<Void> handleException(Exception e) {
        log.error("unexpected error", e);
        return HttpResult.fail(500, "server error");
    }
}