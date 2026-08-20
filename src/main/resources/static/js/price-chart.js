// 价格轨迹折线图（纯 SVG，无外部依赖）
// 遵循 dataviz 规范：单 y 轴、2px 折线、≥8px 数据点、recessive 网格、悬停 tooltip
window.PriceChart = (function () {

    const W = 800;
    const H = 320;
    const PAD = { top: 20, right: 40, bottom: 40, left: 70 };
    const INNER_W = W - PAD.left - PAD.right;
    const INNER_H = H - PAD.top - PAD.bottom;

    function render(container, listings, deals) {
        container.innerHTML = '';

        if ((!listings || !listings.length) && (!deals || !deals.length)) {
            container.innerHTML = '<div class="empty">暂无价格数据</div>';
            return;
        }

        const points = [];
        (listings || []).forEach(l => {
            points.push({ time: new Date(l.listingTime).getTime(), price: Number(l.listingPrice), type: 'listing' });
        });
        (deals || []).forEach(d => {
            points.push({ time: new Date(d.dealTime).getTime(), price: Number(d.dealPrice), type: 'deal' });
        });
        points.sort((a, b) => a.time - b.time);

        const tMin = points[0].time;
        const tMax = points[points.length - 1].time;
        const tPad = tMax === tMin ? 86400000 : (tMax - tMin) * 0.05;
        const xDomain = [tMin - tPad, tMax + tPad];

        const prices = points.map(p => p.price);
        let pMin = Math.min(...prices);
        let pMax = Math.max(...prices);
        const pPad = pMax === pMin ? Math.max(pMax * 0.1, 1000) : (pMax - pMin) * 0.1;
        const yDomain = [Math.max(0, pMin - pPad), pMax + pPad];

        const scaleX = t => PAD.left + (t - xDomain[0]) / (xDomain[1] - xDomain[0]) * INNER_W;
        const scaleY = p => PAD.top + (1 - (p - yDomain[0]) / (yDomain[1] - yDomain[0])) * INNER_H;

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
        svg.setAttribute('width', '100%');
        svg.style.maxWidth = '100%';
        svg.style.overflow = 'visible';

        // 网格 + Y 轴刻度
        const yTicks = 5;
        for (let i = 0; i <= yTicks; i++) {
            const v = yDomain[0] + (yDomain[1] - yDomain[0]) * i / yTicks;
            const y = scaleY(v);
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', PAD.left);
            line.setAttribute('x2', W - PAD.right);
            line.setAttribute('y1', y);
            line.setAttribute('y2', y);
            line.setAttribute('stroke', 'var(--chart-grid)');
            line.setAttribute('stroke-width', '1');
            svg.appendChild(line);

            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', PAD.left - 8);
            label.setAttribute('y', y + 4);
            label.setAttribute('text-anchor', 'end');
            label.setAttribute('fill', 'var(--chart-axis)');
            label.setAttribute('font-size', '11');
            label.textContent = formatPriceShort(v);
            svg.appendChild(label);
        }

        // X 轴时间刻度
        const xTicks = 4;
        for (let i = 0; i <= xTicks; i++) {
            const t = xDomain[0] + (xDomain[1] - xDomain[0]) * i / xTicks;
            const x = scaleX(t);
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', x);
            label.setAttribute('y', H - PAD.bottom + 18);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('fill', 'var(--chart-axis)');
            label.setAttribute('font-size', '11');
            label.textContent = formatDateShort(t);
            svg.appendChild(label);
        }

        // 挂牌价折线
        const listingPoints = points.filter(p => p.type === 'listing');
        if (listingPoints.length >= 2) {
            const path = listingPoints.map((p, i) =>
                (i === 0 ? 'M' : 'L') + scaleX(p.time) + ' ' + scaleY(p.price)
            ).join(' ');
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            line.setAttribute('d', path);
            line.setAttribute('fill', 'none');
            line.setAttribute('stroke', 'var(--chart-line)');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('stroke-linejoin', 'round');
            line.setAttribute('stroke-linecap', 'round');
            svg.appendChild(line);
        }

        // 悬停层
        const hoverLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        hoverLine.setAttribute('stroke', 'var(--ink-muted)');
        hoverLine.setAttribute('stroke-width', '1');
        hoverLine.setAttribute('stroke-dasharray', '3 3');
        hoverLine.setAttribute('opacity', '0');
        svg.appendChild(hoverLine);

        const hoverDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        hoverDot.setAttribute('r', '5');
        hoverDot.setAttribute('fill', 'var(--accent)');
        hoverDot.setAttribute('stroke', 'var(--surface-card)');
        hoverDot.setAttribute('stroke-width', '2');
        hoverDot.setAttribute('opacity', '0');
        svg.appendChild(hoverDot);

        const tooltip = document.createElement('div');
        tooltip.style.position = 'absolute';
        tooltip.style.background = 'var(--surface-card)';
        tooltip.style.border = '1px solid var(--border)';
        tooltip.style.borderRadius = 'var(--radius-md)';
        tooltip.style.padding = '8px 12px';
        tooltip.style.fontSize = '12px';
        tooltip.style.pointerEvents = 'none';
        tooltip.style.opacity = '0';
        tooltip.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        tooltip.style.zIndex = '10';
        tooltip.style.whiteSpace = 'nowrap';
        tooltip.style.transition = 'opacity 0.1s';
        container.style.position = 'relative';
        container.appendChild(tooltip);

        // 数据点
        points.forEach(p => {
            const cx = scaleX(p.time);
            const cy = scaleY(p.price);
            const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            dot.setAttribute('cx', cx);
            dot.setAttribute('cy', cy);
            dot.setAttribute('r', '5');
            dot.setAttribute('fill', p.type === 'deal' ? 'var(--status-serious)' : 'var(--chart-line)');
            dot.setAttribute('stroke', 'var(--surface-card)');
            dot.setAttribute('stroke-width', '2');
            dot.style.cursor = 'pointer';

            const hitArea = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            hitArea.setAttribute('cx', cx);
            hitArea.setAttribute('cy', cy);
            hitArea.setAttribute('r', '12');
            hitArea.setAttribute('fill', 'transparent');
            hitArea.style.cursor = 'pointer';

            const showTip = (e) => {
                const rect = container.getBoundingClientRect();
                const svgRect = svg.getBoundingClientRect();
                const scaleXFactor = svgRect.width / W;
                const scaleYFactor = svgRect.height / H;
                const px = cx * scaleXFactor;
                const py = cy * scaleYFactor;
                tooltip.innerHTML = `
                    <div style="color: var(--ink-secondary);">${p.type === 'deal' ? '成交价' : '挂牌价'}</div>
                    <div style="color: var(--ink-primary); font-weight: 600; margin-top: 2px;">${utils.formatPrice(p.price)}</div>
                    <div style="color: var(--ink-muted); margin-top: 2px;">${utils.formatDate(new Date(p.time).toISOString())}</div>
                `;
                tooltip.style.opacity = '1';
                // 先显示才能测量尺寸
                tooltip.style.left = '0px';
                tooltip.style.top = '0px';
                const tipW = tooltip.offsetWidth;
                const tipH = tooltip.offsetHeight;
                // 边缘检测：右侧不够则左侧，顶部不够则下方
                let left = px + 12;
                if (left + tipW > rect.width) {
                    left = px - tipW - 12;
                }
                if (left < 0) left = 4;
                let top = py - tipH / 2;
                if (top < 0) top = 4;
                if (top + tipH > rect.height) top = rect.height - tipH - 4;
                tooltip.style.left = left + 'px';
                tooltip.style.top = top + 'px';
                hoverLine.setAttribute('x1', px);
                hoverLine.setAttribute('x2', px);
                hoverLine.setAttribute('y1', PAD.top * scaleYFactor);
                hoverLine.setAttribute('y2', (H - PAD.bottom) * scaleYFactor);
                hoverLine.setAttribute('opacity', '0.5');
                hoverDot.setAttribute('cx', px);
                hoverDot.setAttribute('cy', py);
                hoverDot.setAttribute('opacity', '1');
            };
            const hideTip = () => {
                tooltip.style.opacity = '0';
                hoverLine.setAttribute('opacity', '0');
                hoverDot.setAttribute('opacity', '0');
            };
            hitArea.addEventListener('mouseenter', showTip);
            hitArea.addEventListener('mouseleave', hideTip);
            svg.appendChild(dot);
            svg.appendChild(hitArea);
        });

        container.appendChild(svg);
    }

    function formatPriceShort(v) {
        // v 是元，统一按万显示
        const wan = v / 10000;
        if (Math.abs(wan) >= 1) return wan.toFixed(1) + '万';
        return wan.toFixed(2);
    }

    function formatDateShort(t) {
        const d = new Date(t);
        return `${d.getMonth() + 1}/${d.getDate()}`;
    }

    return { render };
})();