package com.hz.dream.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.web.context.WebServerInitializedEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.stereotype.Component;

/**
 * 启动完成后打印首页访问地址
 */
@Slf4j
@Component
public class StartupLogListener implements ApplicationListener<WebServerInitializedEvent> {

    @Override
    public void onApplicationEvent(WebServerInitializedEvent event) {
        int port = event.getWebServer().getPort();
        String contextPath = event.getApplicationContext().getEnvironment()
                .getProperty("server.servlet.context-path", "");
        String home = "http://localhost:" + port + contextPath + "/home";
        log.info("==========================================================");
        log.info("  房产交易系统已启动");
        log.info("  首页地址: {}", home);
        log.info("  接口前缀: http://localhost:{}{}/api/...", port, contextPath);
        log.info("==========================================================");
    }
}