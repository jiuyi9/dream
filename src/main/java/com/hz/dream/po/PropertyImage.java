package com.hz.dream.po;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 房产图片表
 */
@Data
public class PropertyImage {

    /** 主键ID，UUID */
    private String id;

    /** 租户ID */
    private String tenantId;

    /** 所属房产ID */
    private String propertyId;

    /** 图片URL */
    private String imageUrl;

    /** 图片类型，H-房屋图 F-户型图 */
    private String imageType;

    /** 排序号，升序展示 */
    private Integer sortOrder;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;
}
