// 统一 API 封装：处理 HttpResult，抛出业务异常
const BASE = '/api';

// ============ 移动端底部 Tab 导航注入 ============
// 窄屏（≤768px）时由 mobile.css 显示，桌面端隐藏
function injectMobileTabbar() {
    const icons = {
        listings: '<svg viewBox="0 0 24 24"><path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/></svg>',
        deals: '<svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/></svg>',
        properties: '<svg viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></svg>',
        communities: '<svg viewBox="0 0 24 24"><path d="M12 2C8 2 5 5 5 9c0 5 7 13 7 13s7-8 7-13c0-4-3-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>',
    };
    const tabs = [
        { href: '/pages/listings.html', icon: icons.listings, label: '挂牌' },
        { href: '/pages/deals.html', icon: icons.deals, label: '成交' },
        { href: '/pages/properties.html', icon: icons.properties, label: '房源' },
        { href: '/pages/communities.html', icon: icons.communities, label: '小区' },
    ];
    const current = location.pathname;
    const bar = document.createElement('nav');
    bar.className = 'mobile-tabbar';
    bar.innerHTML = tabs.map(t => {
        const active = current === t.href ? 'active' : '';
        return `<a href="${t.href}" class="${active}"><span class="tab-icon">${t.icon}</span><span>${t.label}</span></a>`;
    }).join('');
    document.body.appendChild(bar);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectMobileTabbar);
} else {
    injectMobileTabbar();
}

async function request(path, options = {}) {
    const opts = {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    };
    if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
        opts.body = JSON.stringify(opts.body);
    }
    if (opts.body instanceof FormData) {
        delete opts.headers['Content-Type'];
    }

    const resp = await fetch(BASE + path, opts);
    if (!resp.ok) {
        throw new Error(`HTTP ${resp.status} ${resp.statusText}`);
    }
    const result = await resp.json();
    if (result.code !== 200) {
        throw new Error(result.message || 'request failed');
    }
    return result.data;
}

window.api = {
    // 小区
    listCommunities: () => request('/properties/communities'),
    listCommunitiesByCity: (city) => request(`/properties/communities/by-city?city=${encodeURIComponent(city)}`),
    createCommunity: (data) => request('/properties/communities', { method: 'POST', body: data }),
    updateCommunity: (id, data) => request(`/properties/communities/${id}`, { method: 'PUT', body: data }),
    deleteCommunity: (id) => request(`/properties/communities/${id}`, { method: 'DELETE' }),

    // 房产
    getProperty: (id) => request(`/properties/${id}`),
    listProperties: (filters = {}) => {
        const qs = new URLSearchParams();
        if (filters.communityId) qs.set('communityId', filters.communityId);
        if (filters.rooms) qs.set('rooms', filters.rooms);
        if (filters.status) qs.set('status', filters.status);
        const query = qs.toString();
        return request(`/properties${query ? '?' + query : ''}`);
    },
    createProperty: (data, images) => {
        const body = { ...data, images: images || [] };
        return request('/properties', { method: 'POST', body });
    },
    updateProperty: (id, data) => request(`/properties/${id}`, { method: 'PUT', body: data }),
    deleteProperty: (id) => request(`/properties/${id}`, { method: 'DELETE' }),

    // 挂牌
    listListings: (propertyId) => request(`/properties/${propertyId}/listings`),
    createListing: (propertyId, data) => request(`/properties/${propertyId}/listings`, { method: 'POST', body: data }),
    updateListing: (propertyId, listingId, data) => request(`/properties/${propertyId}/listings/${listingId}`, { method: 'PUT', body: data }),
    deleteListing: (propertyId, listingId) => request(`/properties/${propertyId}/listings/${listingId}`, { method: 'DELETE' }),

    // 成交
    createDeal: (propertyId, dealPrice, recordPrice, dealTime, remark) => {
        const qs = new URLSearchParams();
        if (dealPrice != null) qs.set('dealPrice', dealPrice);
        if (recordPrice != null) qs.set('recordPrice', recordPrice);
        if (dealTime != null) qs.set('dealTime', dealTime);
        if (remark != null) qs.set('remark', remark);
        const query = qs.toString();
        return request(`/properties/${propertyId}/deal${query ? '?' + query : ''}`, { method: 'POST' });
    },
    updateDeal: (propertyId, dealPrice, recordPrice, dealTime, remark) => {
        const qs = new URLSearchParams();
        if (dealPrice != null) qs.set('dealPrice', dealPrice);
        if (recordPrice != null) qs.set('recordPrice', recordPrice);
        if (dealTime != null) qs.set('dealTime', dealTime);
        if (remark != null) qs.set('remark', remark);
        const query = qs.toString();
        return request(`/properties/${propertyId}/deal${query ? '?' + query : ''}`, { method: 'PUT' });
    },

    // 文件上传
    uploadImage: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return request('/upload/image', { method: 'POST', body: formData });
    },
};

// ============ 工具方法 ============

// 最多 N 位小数（默认 2），去掉末尾 0：50.00→50，3.50→3.5，3.14→3.14
function trimTrailingZero(n, maxDigits = 2) {
    return Number(n.toFixed(maxDigits)).toLocaleString('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: maxDigits,
    });
}

window.utils = {
    toast(message, type = 'success') {
        const el = document.createElement('div');
        el.className = `toast toast-${type}`;
        el.textContent = message;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2500);
    },

    uuid() {
        // RFC4122 v4
        return 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'.replace(/x/g, () =>
            Math.floor(Math.random() * 16).toString(16)
        );
    },

    formatDate(s) {
        if (!s) return '-';
        return s.replace('T', ' ').substring(0, 16);
    },

    /**
     * 砍价幅度标签：挂牌价 vs 实际价（成交价或备案价）
     * 紧凑格式：-50 (10%) / +50 (0.5%) / 平（单位万，由列名说明）
     * 百分比：≥1% 仅整数，<1% 保留两位小数
     * 涨用红（tag-up），跌用绿（tag-down）
     */
    cutTag(listingPrice, price) {
        if (listingPrice == null || price == null || Number(listingPrice) <= 0) return '-';
        const diff = Number(listingPrice) - Number(price);
        const pct = Math.abs(diff / Number(listingPrice) * 100);
        const pctLabel = pct >= 10 ? Math.round(pct) + '%'
            : pct >= 1 ? trimTrailingZero(pct, 1) + '%'
            : trimTrailingZero(pct, 2) + '%';
        const amt = trimTrailingZero(Math.abs(diff) / 10000) + '万';
        if (Number(diff) > 0) return `<span class="tag tag-down">-${amt} (${pctLabel})</span>`;
        if (Number(diff) < 0) return `<span class="tag tag-up">+${amt} (${pctLabel})</span>`;
        return `<span class="tag">平 ${amt}</span>`;
    },

    /**
     * datetime-local 值（yyyy-MM-dd'T'HH:mm[:ss]）→ 后端统一格式 yyyy-MM-dd HH:mm:ss
     * 缺秒补 :00。空值返回 null。
     */
    toBackendDateTime(v) {
        if (!v) return null;
        const s = v.trim();
        if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(s)) return s;
        const m = s.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}(?::\d{2})?)$/);
        if (m) {
            const time = m[2].length === 5 ? m[2] + ':00' : m[2];
            return `${m[1]} ${time}`;
        }
        return s;
    },

    formatPrice(n) {
        if (n == null) return '-';
        const wan = Number(n) / 10000;
        return '¥' + trimTrailingZero(wan) + ' 万';
    },

    /** 紧凑价格：纯数字（单位万），用于表格列，如 50 / 3.5 */
    formatPriceShort(n) {
        if (n == null) return '-';
        const wan = Number(n) / 10000;
        return trimTrailingZero(wan);
    },

    /** 元 → 万（用于输入框回显，保留原始精度） */
    yuanToWan(n) {
        if (n == null || n === '') return '';
        return (Number(n) / 10000).toString();
    },

    /** 万 → 元（用于提交表单，输入框值是万） */
    wanToYuan(v) {
        if (v === null || v === undefined || v === '') return null;
        const wan = Number(v);
        if (Number.isNaN(wan)) return null;
        return Math.round(wan * 10000);
    },

    /** 单价：总价(元) / 面积(㎡)，按 万/㎡ 显示 */
    formatUnitPrice(price, area) {
        if (price == null || area == null || Number(area) <= 0) return '-';
        const wan = Number(price) / 10000 / Number(area);
        return trimTrailingZero(wan) + ' 万/㎡';
    },

    /** 紧凑单价：纯数字（单位万/㎡），用于表格列 */
    formatUnitPriceShort(price, area) {
        if (price == null || area == null || Number(area) <= 0) return '-';
        const wan = Number(price) / 10000 / Number(area);
        return trimTrailingZero(wan);
    },

    /** 拼接图片访问 URL */
    imageUrl(url) {
        if (!url) return '';
        if (/^https?:\/\//.test(url)) return url;
        return url;
    },

    /** 自定义确认弹窗，返回 Promise<boolean> */
    confirm(message) {
        return new Promise((resolve) => {
            const mask = document.createElement('div');
            mask.className = 'modal-mask confirm-modal';
            mask.innerHTML = `
                <div class="modal">
                    <div class="modal-header">
                        <h3>请确认</h3>
                        <button class="modal-close">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="confirm-icon">!</div>
                        <div class="confirm-text"></div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn" data-action="cancel">取消</button>
                        <button class="btn btn-primary" data-action="ok">确定</button>
                    </div>
                </div>
            `;
            mask.querySelector('.confirm-text').textContent = message;
            document.body.appendChild(mask);

            const close = (result) => {
                mask.remove();
                resolve(result);
            };
            mask.querySelector('[data-action="ok"]').addEventListener('click', () => close(true));
            mask.querySelector('[data-action="cancel"]').addEventListener('click', () => close(false));
            mask.querySelector('.modal-close').addEventListener('click', () => close(false));
            mask.addEventListener('click', (e) => { if (e.target === mask) close(false); });
        });
    },
};