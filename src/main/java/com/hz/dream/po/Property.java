package com.hz.dream.po;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 房产表（业务主体：挂牌/成交信息合并于此）
 */
@Data
public class Property {

    /** 主键ID，UUID */
    private String id;

    /** 租户ID */
    private String tenantId;

    /** 所属小区ID */
    private String communityId;

    /** 栋号 */
    private String building;

    /** 门牌号 */
    private String roomNo;

    /** 所在楼层 */
    private Integer floor;

    /** 总楼层 */
    private Integer totalFloor;

    /** 建筑面积，单位平方米 */
    private BigDecimal area;

    /** 户型，如3室1厅1卫 */
    private String layout;

    /** 状态，VACANT-空置 LIST-挂牌 SOLD-成交 */
    private String status;

    /** 当前挂牌价，单位元；成交后保留为成交时挂牌价快照 */
    private BigDecimal listingPrice;

    /** 首次挂牌时间；调价时不变 */
    private LocalDateTime firstListingTime;

    /** 成交价格，单位元 */
    private BigDecimal dealPrice;

    /** 备案价，单位元 */
    private BigDecimal recordPrice;

    /** 成交时间 */
    private LocalDateTime dealTime;

    /** 备注 */
    private String remark;

    /** 创建时间 */
    private LocalDateTime createTime;

    /** 更新时间 */
    private LocalDateTime updateTime;

    /** 房产图片（非持久化，详情查询时填充） */
    private transient List<PropertyImage> images;

    /** 户型图URL（非持久化，列表查询时填充第一张户型图） */
    private transient String floorPlanUrl;
}
