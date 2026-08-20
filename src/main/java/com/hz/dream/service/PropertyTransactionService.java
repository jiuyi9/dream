package com.hz.dream.service;

import com.hz.dream.dao.CommunityMapper;
import com.hz.dream.dao.PropertyImageMapper;
import com.hz.dream.dao.PropertyListingMapper;
import com.hz.dream.dao.PropertyMapper;
import com.hz.dream.po.Community;
import com.hz.dream.po.Property;
import com.hz.dream.po.PropertyImage;
import com.hz.dream.po.PropertyListing;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 房产交易服务：以 property 表为主体的挂牌/成交流程
 *
 * 状态流转：VACANT（空置）→ LIST（挂牌）→ SOLD（成交，终态）
 * - 空置时不存在任何挂牌或成交信息
 * - 挂牌记录（property_listings）仅作为调价历史；当前挂牌由 properties.status=LIST 判断
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PropertyTransactionService {

    private static final String STATUS_VACANT = "VACANT";
    private static final String STATUS_LIST   = "LIST";
    private static final String STATUS_SOLD   = "SOLD";

    private final CommunityMapper       communityMapper;
    private final PropertyMapper        propertyMapper;
    private final PropertyImageMapper   propertyImageMapper;
    private final PropertyListingMapper propertyListingMapper;

    /**
     * 租户ID：由配置注入，本服务统一使用此租户隔离数据
     */
    @Value("${app.tenant-id:default}")
    private String tenantId;

    // ============ 房产 ============

    /**
     * 查询房产详情（含图片）
     */
    public Property getPropertyDetail(String propertyId) {
        log.info("→ getPropertyDetail, propertyId:{}", propertyId);
        Property property = propertyMapper.getById(propertyId, tenantId);
        if (property == null) {
            return null;
        }
        List<PropertyImage> images = propertyImageMapper.listByProperty(propertyId, tenantId);
        property.setImages(images);
        log.info("getPropertyDetail, propertyId:{}, imageCount:{}", propertyId, images.size());
        return property;
    }

    /**
     * 复合条件查询房产列表：communityId/rooms/status 均可空
     *
     * @param communityId 小区ID，可空
     * @param rooms       几室（如 "3"），可空；按 layout LIKE 'N室%' 前缀匹配
     * @param status      状态，可空；LIST-挂牌中，SOLD-已成交，空=挂牌+成交
     */
    public List<Property> listProperties(String communityId, String rooms, String status) {
        log.info("→ listProperties, communityId:{}, rooms:{}, status:{}", communityId, rooms, status);
        return propertyMapper.listByConditions(communityId, rooms, status, tenantId);
    }

    /**
     * 新增房产（含图片批量入库）：初始 status=VACANT，无挂牌/成交信息
     */
    @Transactional
    public Property createProperty(Property property, List<PropertyImage> images) {
        log.info("→ createProperty, communityId:{}, building:{}", property.getCommunityId(), property.getBuilding());
        Community community = communityMapper.getById(property.getCommunityId(), tenantId);
        if (community == null) {
            throw new IllegalArgumentException("community not exists, communityId: " + property.getCommunityId());
        }
        if (property.getFloor() != null && property.getTotalFloor() != null
                && property.getFloor() > property.getTotalFloor()) {
            throw new IllegalArgumentException("floor cannot be greater than totalFloor");
        }
        property.setTenantId(tenantId);
        property.setStatus(STATUS_VACANT);
        propertyMapper.insertSelective(property);
        log.info("createProperty, propertyId:{}", property.getId());

        if (images != null && !images.isEmpty()) {
            images.forEach(img -> {
                if (img.getId() == null || img.getId().isEmpty()) {
                    img.setId(java.util.UUID.randomUUID().toString().replace("-", ""));
                }
                img.setTenantId(tenantId);
                img.setPropertyId(property.getId());
            });
            propertyImageMapper.batchInsert(images);
        }
        return property;
    }

    /**
     * 更新房产基本信息及图片
     */
    @Transactional
    public Property updateProperty(Property property) {
        log.info("→ updateProperty, propertyId:{}", property.getId());
        Property existing = propertyMapper.getById(property.getId(), tenantId);
        if (existing == null) {
            throw new IllegalArgumentException("property not exists, id: " + property.getId());
        }
        if (property.getFloor() != null && property.getTotalFloor() != null
                && property.getFloor() > property.getTotalFloor()) {
            throw new IllegalArgumentException("floor cannot be greater than totalFloor");
        }
        property.setTenantId(tenantId);
        propertyMapper.updateSelectiveById(property);

        // 图片同步：先删旧图，再批量插入新图
        List<PropertyImage> images = property.getImages();
        if (images != null) {
            propertyImageMapper.deleteByProperty(property.getId(), tenantId);
            if (!images.isEmpty()) {
                images.forEach(img -> {
                    if (img.getId() == null || img.getId().isEmpty()) {
                        img.setId(java.util.UUID.randomUUID().toString().replace("-", ""));
                    }
                    img.setTenantId(tenantId);
                    img.setPropertyId(property.getId());
                });
                propertyImageMapper.batchInsert(images);
            }
            log.info("updatePropertyImages, propertyId:{}, imageCount:{}", property.getId(), images.size());
        }
        log.info("updateProperty, propertyId:{}", property.getId());
        return property;
    }

    /**
     * 删除房产（连同图片一并清理）
     */
    @Transactional
    public void deleteProperty(String propertyId) {
        log.info("→ deleteProperty, propertyId:{}", propertyId);
        propertyImageMapper.deleteByProperty(propertyId, tenantId);
        // 挂牌历史记录按业务需要保留为历史数据，这里仅删除房产本身与图片
        propertyMapper.deleteById(propertyId, tenantId);
        log.info("deleteProperty, propertyId:{}", propertyId);
    }

    // ============ 挂牌 ============

    /**
     * 新增挂牌记录：写入 property_listings，并同步 property 主体
     * - VACANT→LIST：首次挂牌，主体 status=LIST、listing_price=本条价、first_listing_time=本条时间
     * - LIST：调价，主体 listing_price=最新一条价、first_listing_time=最早一条时间
     * - SOLD：终态，拒绝
     *
     * 主体 listing_price / first_listing_time 始终与挂牌记录列表保持一致：
     * listing_price = 最新一条记录的价，first_listing_time = 最早一条记录的时间。
     */
    @Transactional
    public PropertyListing createListing(PropertyListing listing) {
        log.info("→ createListing, propertyId:{}, listingPrice:{}", listing.getPropertyId(), listing.getListingPrice());
        Property property = propertyMapper.getById(listing.getPropertyId(), tenantId);
        if (property == null) {
            throw new IllegalArgumentException("property not exists, id: " + listing.getPropertyId());
        }
        if (STATUS_SOLD.equals(property.getStatus())) {
            throw new IllegalStateException("property already sold, cannot list again");
        }

        listing.setTenantId(tenantId);
        if (listing.getId() == null || listing.getId().isEmpty()) {
            listing.setId(java.util.UUID.randomUUID().toString().replace("-", ""));
        }
        if (listing.getListingTime() == null) {
            listing.setListingTime(LocalDateTime.now());
        }
        propertyListingMapper.insertSelective(listing);

        // 同步主体：VACANT→LIST；listing_price/first_listing_time 按记录列表重算
        String newStatus = STATUS_VACANT.equals(property.getStatus()) ? STATUS_LIST : property.getStatus();
        resyncPropertyFromListings(property.getId(), newStatus);

        log.info("createListing, listingId:{}, propertyId:{}, price:{}, fromStatus:{}",
                listing.getId(), listing.getPropertyId(), listing.getListingPrice(), property.getStatus());
        return listing;
    }

    /**
     * 编辑挂牌历史记录：改 property_listings，并同步主体 listing_price / first_listing_time
     */
    @Transactional
    public PropertyListing updateListing(String listingId, PropertyListing listing) {
        log.info("→ updateListing, listingId:{}", listingId);
        PropertyListing existing = propertyListingMapper.getById(listingId, tenantId);
        if (existing == null) {
            throw new IllegalArgumentException("listing not exists, id: " + listingId);
        }
        Property property = propertyMapper.getById(existing.getPropertyId(), tenantId);
        if (property != null && STATUS_SOLD.equals(property.getStatus())) {
            throw new IllegalStateException("property already sold, cannot edit listing");
        }
        listing.setId(listingId);
        listing.setTenantId(tenantId);
        listing.setPropertyId(null); // 不允许改所属房产
        propertyListingMapper.updateSelectiveById(listing);

        if (property != null) {
            resyncPropertyFromListings(property.getId(), property.getStatus());
        }
        log.info("updateListing, listingId:{}", listingId);
        return propertyListingMapper.getById(listingId, tenantId);
    }

    /**
     * 删除挂牌历史记录：删 property_listings，并同步主体
     * - 记录全删完 → 主体回 VACANT、listing_price=null、first_listing_time=null
     * - 仍有记录 → listing_price/first_listing_time 按剩余记录重算
     */
    @Transactional
    public void deleteListing(String listingId) {
        log.info("→ deleteListing, listingId:{}", listingId);
        PropertyListing existing = propertyListingMapper.getById(listingId, tenantId);
        if (existing == null) {
            throw new IllegalArgumentException("listing not exists, id: " + listingId);
        }
        Property property = propertyMapper.getById(existing.getPropertyId(), tenantId);
        if (property != null && STATUS_SOLD.equals(property.getStatus())) {
            throw new IllegalStateException("property already sold, cannot delete listing");
        }
        propertyListingMapper.deleteById(listingId, tenantId);

        if (property != null) {
            // 记录可能已全删，此时回 VACANT
            List<PropertyListing> remaining = propertyListingMapper.listByProperty(property.getId(), tenantId);
            String newStatus = remaining.isEmpty() ? STATUS_VACANT : property.getStatus();
            resyncPropertyFromListings(property.getId(), newStatus);
        }
        log.info("deleteListing, listingId:{}", listingId);
    }

    /**
     * 查询房产历史挂牌记录
     */
    public List<PropertyListing> listListingsByProperty(String propertyId) {
        log.info("→ listListingsByProperty, propertyId:{}", propertyId);
        return propertyListingMapper.listByProperty(propertyId, tenantId);
    }

    /**
     * 按挂牌记录列表重算并同步主体挂牌字段：
     * - listing_price = 最新一条（listing_time 最大）记录的价
     * - first_listing_time = 最早一条（listing_time 最小）记录的时间
     * - 记录为空时 listing_price / first_listing_time 置 NULL
     * - status 由调用方决定（VACANT→LIST、记录全删→VACANT、其余保持）
     */
    private void resyncPropertyFromListings(String propertyId, String status) {
        List<PropertyListing> all = propertyListingMapper.listByProperty(propertyId, tenantId);
        BigDecimal latestPrice = null;
        LocalDateTime earliestTime = null;
        if (!all.isEmpty()) {
            // listByProperty 返回按 listing_time DESC，故第一条是最新
            latestPrice = all.get(0).getListingPrice();
            // 最早时间：取最后一条（DESC 的末尾）
            earliestTime = all.get(all.size() - 1).getListingTime();
        }
        propertyMapper.updateListingFields(propertyId, tenantId, status, latestPrice, earliestTime);
    }

    // ============ 成交 ============

    /**
     * 成交：校验 status=LIST，更新 property（status=SOLD、deal_price、deal_time、remark）；
     * listing_price 保留作为成交时挂牌价快照。成交即终态，但成交信息后续可改。
     */
    @Transactional
    public Property createDeal(String propertyId, BigDecimal dealPrice, BigDecimal recordPrice, LocalDateTime dealTime, String remark) {
        log.info("→ createDeal, propertyId:{}, dealPrice:{}, recordPrice:{}, dealTime:{}", propertyId, dealPrice, recordPrice, dealTime);
        Property property = propertyMapper.getById(propertyId, tenantId);
        if (property == null) {
            throw new IllegalArgumentException("property not exists, id: " + propertyId);
        }
        if (!STATUS_LIST.equals(property.getStatus())) {
            throw new IllegalStateException("property is not in LIST status, cannot deal, current: " + property.getStatus());
        }
        Property update = new Property();
        update.setId(property.getId());
        update.setTenantId(tenantId);
        update.setStatus(STATUS_SOLD);
        update.setDealPrice(dealPrice);
        update.setRecordPrice(recordPrice);
        update.setDealTime(dealTime == null ? LocalDateTime.now() : dealTime);
        if (remark != null) {
            update.setRemark(remark);
        }
        propertyMapper.updateSelectiveById(update);

        log.info("createDeal, propertyId:{}, dealPrice:{}, recordPrice:{}, listingPrice:{}",
                propertyId, dealPrice, recordPrice, property.getListingPrice());

        // 返回最新状态
        Property latest = propertyMapper.getById(propertyId, tenantId);
        latest.setImages(propertyImageMapper.listByProperty(propertyId, tenantId));
        return latest;
    }

    /**
     * 修改成交信息：仅 SOLD 状态可改；deal_price / record_price / deal_time / remark 任一非空则更新
     */
    @Transactional
    public Property updateDeal(String propertyId, BigDecimal dealPrice, BigDecimal recordPrice, LocalDateTime dealTime, String remark) {
        log.info("→ updateDeal, propertyId:{}, dealPrice:{}, recordPrice:{}, dealTime:{}", propertyId, dealPrice, recordPrice, dealTime);
        Property property = propertyMapper.getById(propertyId, tenantId);
        if (property == null) {
            throw new IllegalArgumentException("property not exists, id: " + propertyId);
        }
        if (!STATUS_SOLD.equals(property.getStatus())) {
            throw new IllegalStateException("property is not in SOLD status, cannot update deal, current: " + property.getStatus());
        }
        Property update = new Property();
        update.setId(property.getId());
        update.setTenantId(tenantId);
        if (dealPrice != null) {
            update.setDealPrice(dealPrice);
        }
        if (recordPrice != null) {
            update.setRecordPrice(recordPrice);
        }
        if (dealTime != null) {
            update.setDealTime(dealTime);
        }
        if (remark != null) {
            update.setRemark(remark);
        }
        propertyMapper.updateSelectiveById(update);

        log.info("updateDeal, propertyId:{}, dealPrice:{}, recordPrice:{}, dealTime:{}", propertyId, dealPrice, recordPrice, dealTime);

        Property latest = propertyMapper.getById(propertyId, tenantId);
        latest.setImages(propertyImageMapper.listByProperty(propertyId, tenantId));
        return latest;
    }

    // ============ 小区 ============

    /**
     * 查询小区列表
     */
    public List<Community> listCommunities() {
        log.info("→ listCommunities");
        return communityMapper.listByTenant(tenantId);
    }

    /**
     * 按城市查询小区
     */
    public List<Community> listCommunitiesByCity(String city) {
        log.info("→ listCommunitiesByCity, city:{}", city);
        return communityMapper.listByCity(city, tenantId);
    }

    /**
     * 新增小区
     */
    @Transactional
    public Community createCommunity(Community community) {
        log.info("→ createCommunity, communityName:{}", community.getCommunityName());
        Community existing = communityMapper.getByName(community.getCommunityName(), tenantId);
        if (existing != null) {
            throw new IllegalStateException("community name already exists: " + community.getCommunityName());
        }
        community.setTenantId(tenantId);
        communityMapper.insertSelective(community);
        log.info("createCommunity, communityId:{}", community.getId());
        return community;
    }

    /**
     * 更新小区
     */
    @Transactional
    public Community updateCommunity(Community community) {
        log.info("→ updateCommunity, communityId:{}", community.getId());
        Community existing = communityMapper.getById(community.getId(), tenantId);
        if (existing == null) {
            throw new IllegalArgumentException("community not exists, id: " + community.getId());
        }
        // 名称变更时校验唯一性
        if (community.getCommunityName() != null && !community.getCommunityName().equals(existing.getCommunityName())) {
            Community sameName = communityMapper.getByName(community.getCommunityName(), tenantId);
            if (sameName != null && !sameName.getId().equals(community.getId())) {
                throw new IllegalStateException("community name already exists: " + community.getCommunityName());
            }
        }
        community.setTenantId(tenantId);
        communityMapper.updateSelectiveById(community);
        log.info("updateCommunity, communityId:{}", community.getId());
        return community;
    }

    /**
     * 删除小区
     */
    @Transactional
    public void deleteCommunity(String communityId) {
        log.info("→ deleteCommunity, communityId:{}", communityId);
        Community existing = communityMapper.getById(communityId, tenantId);
        if (existing == null) {
            throw new IllegalArgumentException("community not exists, id: " + communityId);
        }
        communityMapper.deleteById(communityId, tenantId);
        log.info("deleteCommunity, communityId:{}", communityId);
    }
}
