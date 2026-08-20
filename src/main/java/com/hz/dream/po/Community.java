package com.hz.dream.po;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 社区表
 */
@Data
public class Community {

    /** 主键ID，UUID */
    private String id;

    /** 租户ID */
    private String tenantId;

    /** 小区名称 */
    private String communityName;

    /** 所在城市 */
    private String city;

    /** 所在区域 */
    private String district;

    /** 详细地址 */
    private String address;

    /** 开发商 */
    private String developer;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;
}