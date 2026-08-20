package com.hz.dream.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * 页面入口：/home 重定向到挂牌页
 */
@Controller
public class HomeController {

    @GetMapping("/home")
    public String home() {
        return "redirect:/pages/listings.html";
    }
}