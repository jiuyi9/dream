package com.hz.dream.controller;

import com.hz.dream.common.HttpResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.UUID;

/**
 * 文件上传接口：图片存到本地 uploads/ 目录
 */
@Slf4j
@RestController
public class FileUploadController {

    @Value("${app.upload-dir:./uploads}")
    private String uploadDir;

    @Value("${app.upload-url-prefix:/uploads}")
    private String urlPrefix;

    /**
     * 上传图片，返回可访问 URL
     */
    @PostMapping("/api/upload/image")
    public HttpResult<String> uploadImage(@RequestParam("file") MultipartFile file) {
        log.info("→ uploadImage, fileName:{}, size:{}", file == null ? null : file.getOriginalFilename(), file == null ? 0 : file.getSize());
        if (file == null || file.isEmpty()) {
            return HttpResult.fail("file is empty");
        }
        String contentType = file.getContentType();
        if (contentType == null || !contentType.startsWith("image/")) {
            return HttpResult.fail("only image allowed");
        }
        try {
            String relativePath = buildRelativePath(file);
            Path targetDir = Paths.get(uploadDir).toAbsolutePath().normalize();
            Files.createDirectories(targetDir);
            Path target = targetDir.resolve(relativePath);
            Files.createDirectories(target.getParent());
            file.transferTo(target.toFile());

            String url = urlPrefix + "/" + relativePath;
            log.info("uploadImage, fileName:{}, size:{}, url:{}", file.getOriginalFilename(), file.getSize(), url);
            return HttpResult.success(url);
        } catch (IOException e) {
            log.error("uploadImage failed, fileName: {}", file.getOriginalFilename(), e);
            return HttpResult.fail("upload failed: " + e.getMessage());
        }
    }

    private String buildRelativePath(MultipartFile file) {
        String original = file.getOriginalFilename();
        String ext = "";
        if (original != null && original.contains(".")) {
            ext = original.substring(original.lastIndexOf('.'));
        }
        String dateDir = LocalDate.now().toString().replace('-', '/');
        String fileName = UUID.randomUUID().toString().replace("-", "") + ext;
        return dateDir + "/" + fileName;
    }
}