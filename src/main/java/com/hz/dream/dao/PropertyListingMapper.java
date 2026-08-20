package com.hz.dream.dao;

import com.hz.dream.po.PropertyListing;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 房产挂牌记录数据访问层（调价历史）
 */
@Mapper
public interface PropertyListingMapper {

    /** 按主键获取 */
    PropertyListing getById(@Param("id") String id, @Param("tenantId") String tenantId);

    /** 按房产ID查询历史挂牌记录（按时间倒序） */
    List<PropertyListing> listByProperty(@Param("propertyId") String propertyId,
                                         @Param("tenantId") String tenantId);

    /** 插入（仅非空字段） */
    int insertSelective(PropertyListing propertyListing);

    /** 按主键更新（仅非空字段） */
    int updateSelectiveById(PropertyListing propertyListing);

    /** 按主键删除 */
    int deleteById(@Param("id") String id, @Param("tenantId") String tenantId);
}
