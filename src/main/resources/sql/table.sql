-- ============================================================
-- 社区表
-- ============================================================
CREATE TABLE IF NOT EXISTS communities (
    id              CHAR(32)      NOT NULL COMMENT '主键ID，UUID',
    tenant_id       CHAR(32)      NOT NULL COMMENT '租户ID',
    community_name  VARCHAR(20)   NOT NULL COMMENT '小区名称',
    city            VARCHAR(100)  COMMENT '所在城市',
    district        VARCHAR(100)  COMMENT '所在区域',
    address         VARCHAR(500)  COMMENT '详细地址',
    developer       VARCHAR(200)  COMMENT '开发商',
    create_time     DATETIME      NOT NULL DEFAULT NOW() COMMENT '创建时间',
    update_time     DATETIME      NOT NULL DEFAULT NOW() ON UPDATE NOW() COMMENT '更新时间',
    CONSTRAINT pk_communities PRIMARY KEY (id),
    UNIQUE KEY uk_communities_tenant_name (tenant_id, community_name)
) COMMENT='社区表';


-- ============================================================
-- 房产表（业务主体：挂牌/成交信息合并于此）
-- ============================================================
CREATE TABLE IF NOT EXISTS properties (
    id                CHAR(32)      NOT NULL COMMENT '主键ID，UUID',
    tenant_id         CHAR(32)      NOT NULL COMMENT '租户ID',
    community_id      CHAR(32)      NOT NULL COMMENT '所属小区ID',
    building          VARCHAR(50)   NOT NULL COMMENT '栋号',
    room_no           VARCHAR(20)   COMMENT '门牌号',
    floor             INT           NOT NULL COMMENT '所在楼层',
    total_floor       INT           NOT NULL COMMENT '总楼层',
    area              DECIMAL(10,2) COMMENT '建筑面积，单位平方米',
    layout            VARCHAR(20)   COMMENT '户型，如3室1厅1卫',
    status            VARCHAR(10)   NOT NULL DEFAULT 'VACANT' COMMENT '状态，VACANT-空置 LIST-挂牌 SOLD-成交',
    listing_price     DECIMAL(14,2) COMMENT '当前挂牌价，单位元；成交后保留为成交时挂牌价快照',
    first_listing_time DATETIME     COMMENT '首次挂牌时间；调价时不变',
    deal_price        DECIMAL(14,2) COMMENT '成交价格，单位元',
    record_price      DECIMAL(14,2) COMMENT '备案价，单位元',
    deal_time         DATETIME      COMMENT '成交时间',
    remark            VARCHAR(2000) COMMENT '备注',
    create_time       DATETIME      NOT NULL DEFAULT NOW() COMMENT '创建时间',
    update_time       DATETIME      NOT NULL DEFAULT NOW() ON UPDATE NOW() COMMENT '更新时间',
    CONSTRAINT pk_properties PRIMARY KEY (id),
    KEY idx_properties_tenant_community (tenant_id, community_id),
    KEY idx_properties_tenant_status (tenant_id, status)
) COMMENT='房产表';


-- ============================================================
-- 房产图片表（1:N，含房屋图与户型图）
-- ============================================================
CREATE TABLE IF NOT EXISTS property_images (
    id              CHAR(32)      NOT NULL COMMENT '主键ID，UUID',
    tenant_id       CHAR(32)      NOT NULL COMMENT '租户ID',
    property_id     CHAR(32)      NOT NULL COMMENT '所属房产ID',
    image_url       VARCHAR(500)  NOT NULL COMMENT '图片URL',
    image_type      CHAR(1)       NOT NULL DEFAULT 'H' COMMENT '图片类型，H-房屋图 F-户型图',
    sort_order      INT           NOT NULL DEFAULT 0 COMMENT '排序号，升序展示',
    create_time     DATETIME      NOT NULL DEFAULT NOW() COMMENT '创建时间',
    update_time     DATETIME      NOT NULL DEFAULT NOW() ON UPDATE NOW() COMMENT '更新时间',
    CONSTRAINT pk_property_images PRIMARY KEY (id),
    KEY idx_property_images_tenant_property (tenant_id, property_id)
) COMMENT='房产图片表';


-- ============================================================
-- 房产挂牌记录表（1:N，调价历史；当前挂牌由 properties.status 判断）
-- ============================================================
CREATE TABLE IF NOT EXISTS property_listings (
    id              CHAR(32)      NOT NULL COMMENT '主键ID，UUID',
    tenant_id       CHAR(32)      NOT NULL COMMENT '租户ID',
    property_id     CHAR(32)      NOT NULL COMMENT '所属房产ID',
    listing_price   DECIMAL(14,2) NOT NULL COMMENT '挂牌价格，单位元',
    listing_time    DATETIME      NOT NULL COMMENT '挂牌时间',
    remark          VARCHAR(2000) COMMENT '备注',
    create_time     DATETIME      NOT NULL DEFAULT NOW() COMMENT '创建时间',
    update_time     DATETIME      NOT NULL DEFAULT NOW() ON UPDATE NOW() COMMENT '更新时间',
    CONSTRAINT pk_property_listings PRIMARY KEY (id),
    KEY idx_tenant_property (tenant_id, property_id),
    KEY idx_tenant_property_time (tenant_id, property_id, listing_time)
) COMMENT='房产挂牌记录表';