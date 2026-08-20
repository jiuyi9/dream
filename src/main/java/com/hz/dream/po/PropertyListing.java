package com.hz.dream.po;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 房产挂牌记录表（调价历史）
 */
@Data
public class PropertyListing {

    /** 主键ID，UUID */
    private String id;

    /** 租户ID */
    private String tenantId;

    /** 所属房产ID */
    private String propertyId;

    /** 挂牌价格，单位元 */
    private BigDecimal listingPrice;

    /** 挂牌时间 */
    private LocalDateTime listingTime;

    /** 备注 */
    private String remark;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;
}
