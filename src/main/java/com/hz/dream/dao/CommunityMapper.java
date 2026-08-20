package com.hz.dream.dao;

import com.hz.dream.po.Community;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 社区数据访问层
 */
@Mapper
public interface CommunityMapper {

    /** 按主键获取 */
    Community getById(@Param("id") String id, @Param("tenantId") String tenantId);

    /** 按小区名称获取（同租户下唯一） */
    Community getByName(@Param("name") String name, @Param("tenantId") String tenantId);

    /** 列表查询 */
    List<Community> listByTenant(@Param("tenantId") String tenantId);

    /** 按城市列表查询 */
    List<Community> listByCity(@Param("city") String city, @Param("tenantId") String tenantId);

    /** 插入（仅非空字段） */
    int insertSelective(Community community);

    /** 按主键更新（仅非空字段） */
    int updateSelectiveById(Community community);

    /** 按主键删除 */
    int deleteById(@Param("id") String id, @Param("tenantId") String tenantId);
}