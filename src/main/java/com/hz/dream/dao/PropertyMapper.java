package com.hz.dream.dao;

import com.hz.dream.po.Property;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 房产数据访问层
 */
@Mapper
public interface PropertyMapper {

    /** 按主键获取 */
    Property getById(@Param("id") String id, @Param("tenantId") String tenantId);

    /** 复合条件列表查询：communityId/rooms/status 均可空，rooms 按 layout LIKE 'N室%' 前缀匹配，status 取 LIST/SOLD */
    List<Property> listByConditions(@Param("communityId") String communityId,
                                     @Param("rooms") String rooms,
                                     @Param("status") String status,
                                     @Param("tenantId") String tenantId);

    /** 插入（仅非空字段） */
    int insertSelective(Property property);

    /** 按主键更新（仅非空字段） */
    int updateSelectiveById(Property property);

    /**
     * 按主键更新挂牌相关字段（显式 SET，允许置空）。
     * 用于挂牌记录增删改后同步主体：status / listing_price / first_listing_time。
     */
    int updateListingFields(@Param("id") String id,
                            @Param("tenantId") String tenantId,
                            @Param("status") String status,
                            @Param("listingPrice") java.math.BigDecimal listingPrice,
                            @Param("firstListingTime") java.time.LocalDateTime firstListingTime);

    /** 按主键删除 */
    int deleteById(@Param("id") String id, @Param("tenantId") String tenantId);
}