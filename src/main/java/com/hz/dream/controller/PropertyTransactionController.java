package com.hz.dream.controller;

import com.hz.dream.common.HttpResult;
import com.hz.dream.po.Community;
import com.hz.dream.po.Property;
import com.hz.dream.po.PropertyListing;
import com.hz.dream.service.PropertyTransactionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 房产交易接口
 */
@RestController
@RequestMapping("/api/properties")
@RequiredArgsConstructor
public class PropertyTransactionController {

    private final PropertyTransactionService propertyTransactionService;

    // ============ 房产 ============

    @GetMapping("/{propertyId}")
    public HttpResult<Property> detail(@PathVariable String propertyId) {
        return HttpResult.success(propertyTransactionService.getPropertyDetail(propertyId));
    }

    @GetMapping
    public HttpResult<List<Property>> list(@RequestParam(required = false) String communityId,
                                           @RequestParam(required = false) String rooms,
                                           @RequestParam(required = false) String status) {
        return HttpResult.success(propertyTransactionService.listProperties(communityId, rooms, status));
    }

    @PostMapping
    public HttpResult<Property> create(@RequestBody Property property) {
        return HttpResult.success(propertyTransactionService.createProperty(property, property.getImages()));
    }

    @PutMapping("/{propertyId}")
    public HttpResult<Property> update(@PathVariable String propertyId,
                                       @RequestBody Property property) {
        property.setId(propertyId);
        return HttpResult.success(propertyTransactionService.updateProperty(property));
    }

    @DeleteMapping("/{propertyId}")
    public HttpResult<Void> delete(@PathVariable String propertyId) {
        propertyTransactionService.deleteProperty(propertyId);
        return HttpResult.success();
    }

    // ============ 挂牌 ============

    @GetMapping("/{propertyId}/listings")
    public HttpResult<List<PropertyListing>> listListings(@PathVariable String propertyId) {
        return HttpResult.success(propertyTransactionService.listListingsByProperty(propertyId));
    }

    @PostMapping("/{propertyId}/listings")
    public HttpResult<PropertyListing> createListing(@PathVariable String propertyId,
                                                     @RequestBody PropertyListing listing) {
        listing.setPropertyId(propertyId);
        return HttpResult.success(propertyTransactionService.createListing(listing));
    }

    @PutMapping("/{propertyId}/listings/{listingId}")
    public HttpResult<PropertyListing> updateListing(@PathVariable String propertyId,
                                                     @PathVariable String listingId,
                                                     @RequestBody PropertyListing listing) {
        listing.setPropertyId(propertyId);
        return HttpResult.success(propertyTransactionService.updateListing(listingId, listing));
    }

    @DeleteMapping("/{propertyId}/listings/{listingId}")
    public HttpResult<Void> deleteListing(@PathVariable String propertyId,
                                          @PathVariable String listingId) {
        propertyTransactionService.deleteListing(listingId);
        return HttpResult.success();
    }

    // ============ 成交 ============

    @PostMapping("/{propertyId}/deal")
    public HttpResult<Property> createDeal(@PathVariable String propertyId,
                                          @RequestParam(required = false) BigDecimal dealPrice,
                                          @RequestParam(required = false) BigDecimal recordPrice,
                                          @RequestParam(required = false) LocalDateTime dealTime,
                                          @RequestParam(required = false) String remark) {
        return HttpResult.success(propertyTransactionService.createDeal(propertyId, dealPrice, recordPrice, dealTime, remark));
    }

    @PutMapping("/{propertyId}/deal")
    public HttpResult<Property> updateDeal(@PathVariable String propertyId,
                                          @RequestParam(required = false) BigDecimal dealPrice,
                                          @RequestParam(required = false) BigDecimal recordPrice,
                                          @RequestParam(required = false) LocalDateTime dealTime,
                                          @RequestParam(required = false) String remark) {
        return HttpResult.success(propertyTransactionService.updateDeal(propertyId, dealPrice, recordPrice, dealTime, remark));
    }

    // ============ 小区 ============

    @GetMapping("/communities")
    public HttpResult<List<Community>> listCommunities() {
        return HttpResult.success(propertyTransactionService.listCommunities());
    }

    @GetMapping("/communities/by-city")
    public HttpResult<List<Community>> listCommunitiesByCity(@RequestParam String city) {
        return HttpResult.success(propertyTransactionService.listCommunitiesByCity(city));
    }

    @PostMapping("/communities")
    public HttpResult<Community> createCommunity(@RequestBody Community community) {
        return HttpResult.success(propertyTransactionService.createCommunity(community));
    }

    @PutMapping("/communities/{communityId}")
    public HttpResult<Community> updateCommunity(@PathVariable String communityId,
                                                 @RequestBody Community community) {
        community.setId(communityId);
        return HttpResult.success(propertyTransactionService.updateCommunity(community));
    }

    @DeleteMapping("/communities/{communityId}")
    public HttpResult<Void> deleteCommunity(@PathVariable String communityId) {
        propertyTransactionService.deleteCommunity(communityId);
        return HttpResult.success();
    }
}
