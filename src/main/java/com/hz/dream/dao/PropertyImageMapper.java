package com.hz.dream.dao;

import com.hz.dream.po.PropertyImage;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 房产图片数据访问层
 */
@Mapper
public interface PropertyImageMapper {

    /** 按主键获取 */
    PropertyImage getById(@Param("id") String id, @Param("tenantId") String tenantId);

    /** 按房产ID列表查询 */
    List<PropertyImage> listByProperty(@Param("propertyId") String propertyId,
                                       @Param("tenantId") String tenantId);

    /** 按房产ID与图片类型列表查询 */
    List<PropertyImage> listByPropertyAndType(@Param("propertyId") String propertyId,
                                              @Param("imageType") String imageType,
                                              @Param("tenantId") String tenantId);

    /** 插入（仅非空字段） */
    int insertSelective(PropertyImage propertyImage);

    /** 批量插入 */
    int batchInsert(@Param("list") List<PropertyImage> list);

    /** 按主键更新（仅非空字段） */
    int updateSelectiveById(PropertyImage propertyImage);

    /** 按房产ID删除 */
    int deleteByProperty(@Param("propertyId") String propertyId,
                         @Param("tenantId") String tenantId);

    /** 按主键删除 */
    int deleteById(@Param("id") String id, @Param("tenantId") String tenantId);
}