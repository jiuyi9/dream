package com.hz.dream;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.hz.dream.dao")
public class HzDreamApplication {

    public static void main(String[] args) {
        SpringApplication.run(HzDreamApplication.class, args);
    }
}