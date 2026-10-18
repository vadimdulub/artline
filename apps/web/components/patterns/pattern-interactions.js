import { spScene } from './pattern-geometry';
import { lockBodyScroll } from '@/lib/modal-scroll';
export function mountPatternGuide(root, copy) {
    const controller = new AbortController();
    const listen = (node, event, handler) => node.addEventListener(event, handler, { signal: controller.signal });
    const escape = value => String(value).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const $ = s => root.querySelector(s);
    const $$ = s => [...root.querySelectorAll(s)];
    const cleanup = [];
    const rad = Math.PI / 180;
    const palettes = [
        { ground: '#163c68', fill: '#62bcb6', line: '#efdfb7', accent: '#d3a555' },
        { ground: '#422d24', fill: '#9b7350', line: '#f1e4c9', accent: '#d3b997' },
        { ground: '#efe8db', fill: '#b06b49', line: '#422c22', accent: '#d8b18d' }
    ];
    const families = Object.fromEntries(copy.construction.families.map(f => [f.id, f]));
    function pt(r, a) { return [r * Math.cos(a * rad), r * Math.sin(a * rad)]; }
    function points(n, r, offset = -90) { return Array.from({ length: n }, (_, i) => pt(r, offset + i * 360 / n)); }
    function fmt(ps) { return ps.map(p => p.map(v => Number(v.toFixed(3))).join(',')).join(' '); }
    function ratio(n) { return n === 5 ? (3 - Math.sqrt(5)) / 2 : n === 6 ? 1 / Math.sqrt(3) : Math.cos(Math.PI / 4) / Math.cos(Math.PI / n); }
    function star(n, r) { return fmt(Array.from({ length: n * 2 }, (_, i) => pt(i % 2 ? r * ratio(n) : r, -90 + i * 180 / n))); }
    function poly(n, r, attrs = '') { return `<polygon points="${star(n, r)}" ${attrs}/>`; }
    function scaffolding(n, r, { circle = true, spokes = true, angle = true } = {}) {
        const p = points(n, r), groups = n === 12 ? 3 : 2;
        let out = circle ? `<circle r="${r}" fill="none" stroke="#e9d9b5" stroke-opacity=".65" stroke-dasharray="4 6"/>` : '';
        if (spokes)
            out += p.map(v => `<line x2="${v[0]}" y2="${v[1]}" stroke="#e9d9b5" stroke-opacity=".28"/>`).join('');
        if (n === 5)
            out += `<polygon points="${fmt([0, 2, 4, 1, 3].map(i => p[i]))}" fill="none" stroke="#efdfb7" stroke-width="2"/>`;
        else
            for (let j = 0; j < groups; j++)
                out += `<polygon points="${fmt(p.filter((_, i) => i % groups === j))}" fill="none" stroke="${j === 1 ? '#62bcb6' : '#efdfb7'}" stroke-width="2"/>`;
        out += p.map(v => `<circle cx="${v[0]}" cy="${v[1]}" r="3.5" fill="#efdfb7"/>`).join('');
        if (angle) {
            const a = 360 / n, q = r * .34, e = pt(q, -90 + a), t = pt(q * 1.6, -90 + a / 2);
            out += `<path d="M0 0 L0 ${-q} A${q} ${q} 0 0 1 ${e[0]} ${e[1]} Z" fill="#efdfb7" fill-opacity=".18" stroke="#efdfb7" stroke-width="1"/><text x="${t[0]}" y="${t[1]}" fill="#f2efe8" font-size="18" text-anchor="middle" dominant-baseline="middle">${a}°</text>`;
        }
        return out;
    }
    function svg(content, view = '-280 -190 560 380', label = copy.ui.pattern) {
        return `<svg viewBox="${view}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${escape(label)}"><title>${escape(label)}</title>${content}</svg>`;
    }
    function repeats(n, { r = 37, spacing = 103, width = 560, height = 380, ground = '#163c68', fill = '#62bcb6', line = '#efdfb7' } = {}) {
        let out = `<rect x="${-width / 2}" y="${-height / 2}" width="${width}" height="${height}" fill="${ground}"/>`;
        const stagger = n === 6 || n === 12, dy = spacing * (stagger ? Math.sqrt(3) / 2 : 1);
        for (let row = -Math.ceil(height / dy / 2) - 1; row <= Math.ceil(height / dy / 2) + 1; row++)
            for (let col = -Math.ceil(width / spacing / 2) - 1; col <= Math.ceil(width / spacing / 2) + 1; col++)
                out += `<g transform="translate(${col * spacing + (stagger && Math.abs(row) % 2 ? spacing / 2 : 0)} ${row * dy})">${poly(n, r, `fill="${fill}" stroke="${line}" stroke-width="1.5"`)}</g>`;
        return out;
    }
    function setPressed(selector, attr, value) { $$(selector).forEach(b => b.setAttribute('aria-pressed', String(b.getAttribute(attr) === String(value)))); }
    let family = 'eight', stage = 0;
    function renderConstruction() {
        const f = families[family];
        let drawing = '';
        if (stage === 0)
            drawing = scaffolding(f.n, 139);
        else if (stage === 1)
            drawing = `<circle r="139" fill="none" stroke="#efdfb7" stroke-opacity=".3" stroke-dasharray="4 6"/>` + poly(f.n, 139, 'fill="#62bcb6" stroke="#efdfb7" stroke-width="2.4"');
        else if (f.n === 5) {
            for (let i = 0; i < 4; i++)
                drawing += `<g transform="rotate(${i * 36})">${poly(5, 158 * Math.pow(ratio(5), i), `fill="${i % 2 ? '#163c68' : '#62bcb6'}" stroke="#efdfb7" stroke-width="1.8"`)}</g>`;
        }
        else
            drawing = repeats(f.n);
        $('#construction-view').innerHTML = svg(drawing, undefined, `${f.title}: ${[copy.ui.construction, copy.ui.motif, copy.ui.arrangement][stage]}`);
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) $('#construction-view svg').animate([{opacity:.4},{opacity:1}],{duration:220});
        $('#construction-title').textContent = f.titles[stage];
        $('#construction-text').textContent = f.text[stage];
        $('#construction-fact').textContent = f.facts[stage];
        $('#construction-foot').textContent = f.foot;
        setPressed('[data-family]', 'data-family', family);
        setPressed('[data-stage]', 'data-stage', stage);
    }
    $$('[data-family]').forEach(b => { b.querySelector('svg').innerHTML = poly(families[b.dataset.family].n, 13, 'fill="none" stroke="currentColor" stroke-width="1.2"'); listen(b, 'click', () => { family = b.dataset.family; renderConstruction(); }); });
    $$('[data-stage]').forEach(b => listen(b, 'click', () => { stage = Number(b.dataset.stage); renderConstruction(); }));
    renderConstruction();
    let turn = 0;
    function renderSymmetry() {
        const base = poly(8, 79, 'fill="none" stroke="#9c958a" stroke-width="1.5" stroke-dasharray="4 4"');
        $('#symmetry-star').innerHTML = svg(base + `<g transform="rotate(${turn})">${poly(8, 79, 'fill="#62bcb6" fill-opacity=".6" stroke="#163c68" stroke-width="2"')}</g>`, '-130 -130 260 260', copy.ui.star);
        let ghost = '', field = '';
        for (let y = -1; y <= 1; y++)
            for (let x = -1; x <= 1; x++) {
                ghost += `<g transform="translate(${x * 64} ${y * 64})">${poly(8, 17, 'fill="none" stroke="#a9a193" stroke-width="1" stroke-dasharray="3 3"')}</g>`;
                field += `<g transform="translate(${x * 64} ${y * 64})">${poly(8, 17, 'fill="#62bcb6" stroke="#163c68" stroke-width="1.3"')}</g>`;
            }
        $('#symmetry-grid').innerHTML = svg(ghost + `<g transform="rotate(${turn})">${field}</g>`, '-130 -130 260 260', copy.ui.grid);
        const match = turn % 90 === 0;
        $('#turn-value').value = `${turn}°`;
        $('#grid-status').textContent = match ? copy.ui.matches : copy.ui.notMatch;
        $('#grid-status').dataset.match = match;
        $('#symmetry-note').textContent = turn === 0 ? copy.symmetry.initial : match ? copy.symmetry.matched : copy.symmetry.turned;
    }
    listen($('#turn-button'), 'click', () => { turn = (turn + 45) % 360; renderSymmetry(); });
    listen($('#turn-reset'), 'click', () => { turn = 0; renderSymmetry(); });
    renderSymmetry();
    $$('.ig-art').forEach(art => {
        const drawing = art.querySelector('svg'), description = art.querySelector('.ig-art-description'), tag = art.querySelector('.ig-detail-tag');
        art.querySelectorAll('[data-art-view]').forEach(button => listen(button, 'click', () => {
            art.querySelectorAll('[data-art-view]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
            drawing.setAttribute('viewBox', button.dataset.box);
            drawing.setAttribute('aria-label', button.dataset.description);
            description.textContent = button.dataset.description;
            tag.textContent = (button.dataset.artView === 'whole' ? copy.ui.whole : copy.ui.detail) + ' · ' + copy.ui.enlarge;
            if (button.dataset.artView !== 'whole') {
                const image = drawing.querySelector('image');
                image.setAttribute('href', image.dataset.detailImage);
            }
        }));
    });
    let colourMode = 'reverse';
    function renderColour() {
        const p = palettes[0];
        $('#colour-reference').innerHTML = svg(repeats(8, { width: 420, height: 290, spacing: 94, r: 35, ...p }), '-210 -145 420 290', copy.ui.original);
        const cfg = colourMode === 'reverse' ? { ground: p.fill, fill: p.ground, line: p.line } : colourMode === 'lines' ? { ground: p.ground, fill: 'none', line: p.line } : { ground: p.ground, fill: p.fill, line: p.line };
        $('#colour-changed').innerHTML = svg(repeats(8, { width: 420, height: 290, spacing: 94, r: 35, ...cfg }), '-210 -145 420 290', copy.colour.question);
        $('#colour-label').textContent = { reverse: copy.ui.swap, lines: copy.ui.outlines, same: copy.ui.original }[colourMode];
        $('#colour-note').textContent = { reverse: copy.colour.states[0], lines: copy.colour.states[1], same: copy.colour.states[2] }[colourMode];
        setPressed('[data-colour-mode]', 'data-colour-mode', colourMode);
    }
    $$('[data-colour-mode]').forEach(b => listen(b, 'click', () => { colourMode = b.dataset.colourMode; renderColour(); }));
    renderColour();
    {
        const studioPalettes = [
            { ground: '#142f49', line: '#ead9b2', colours: ['#193c64', '#4b929c', '#b47b4e', '#e8d6b1'] },
            { ground: '#ede7d7', line: '#263e34', colours: ['#245d4e', '#7c9a76', '#d0ab58', '#eee6cf'] },
            { ground: '#eadccc', line: '#f1dbb7', colours: ['#a65338', '#cc8c65', '#513a33', '#ead3ae'] },
            { ground: '#eae7df', line: '#183247', colours: ['#d8ddd9', '#708c98', '#c2a478', '#eeeae0'] },
            { ground: '#372a24', line: '#ead4ac', colours: ['#62432f', '#a37b53', '#d5b68a', '#3e3028'] },
            { ground: '#f3f0e6', line: '#365a79', colours: ['#f6f2e8', '#d6e0e2', '#b3c6d0', '#e7e7de'] }
        ];
        studioPalettes.forEach((p, i) => { p.name = copy.ui.palettes[i]; });
        const studioPatterns = copy.studio.patterns;
        const studioState = { pattern: 'starcross', palette: 0, style: 'mosaic', scale: 100, weight: 1.2, angle: 0 };
        const studioPaint = new Map(), studioHistory = [];
        let studioFaces = [], studioWidth = 0, studioHeight = 0, studioSize = 0, studioFocused = '';
        const studioCurrent = () => studioPatterns.find(p => p.id === studioState.pattern);
        const studioPalette = () => studioPalettes[studioState.palette];
        function studioPoints(ps) { return ps.map(p => p.map(n => Number(n.toFixed(3))).join(',')).join(' '); }
        function studioColour(face, thumbnail = false) {
            const p = studioPalette();
            if (!thumbnail && studioPaint.has(face.key))
                return p.colours[studioPaint.get(face.key)];
            return studioState.style === 'outline' ? p.ground : p.colours[face.tone];
        }
        function studioSvg(faces, w, h, interactive = false) {
            const p = studioPalette(), weight = interactive ? studioState.weight : .7;
            const available = faces.filter(f => f.cx > 5 && f.cx < w - 5 && f.cy > 5 && f.cy < h - 5);
            let focus = available.find(f => f.key === studioFocused) || available.reduce((best, f) => !best || Math.hypot(f.cx - w / 2, f.cy - h / 2) < Math.hypot(best.cx - w / 2, best.cy - h / 2) ? f : best, null);
            if (interactive)
                studioFocused = focus?.key || '';
            let drawing = `<rect width="${w}" height="${h}" fill="${p.ground}"/>`;
            for (const f of faces) {
                const pts = studioPoints(f.points), visible = f.cx > 5 && f.cx < w - 5 && f.cy > 5 && f.cy < h - 5;
                const attrs = interactive ? `data-face="${f.key}" data-tone="${f.tone}" role="button" tabindex="${f.key === studioFocused ? 0 : -1}" aria-label="${escape(copy.ui.pattern)} ${f.tone + 1}: ${escape(copy.ui.changed)}" ${visible ? 'data-visible="true"' : ''}` : '';
                drawing += `<polygon ${attrs} points="${pts}" fill="${studioColour(f, !interactive)}" stroke="${p.line}" stroke-width="${weight * (studioState.style === 'double' ? 3 : 1)}" stroke-linejoin="round"/>`;
            }
            if (studioState.style === 'double')
                for (const f of faces)
                    drawing += `<polygon points="${studioPoints(f.points)}" fill="none" stroke="${p.ground}" stroke-width="${weight}" stroke-linejoin="round" pointer-events="none"/>`;
            const access = interactive ? `id="maker-svg" role="group" aria-label="${escape(studioCurrent().name)}. ${escape(copy.studio.hint)}"` : 'aria-hidden="true"';
            return `<svg ${access} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}">${interactive ? `<title>${escape(studioCurrent().name)}</title><desc>${escape(copy.studio.keyboard)}</desc>` : ''}${drawing}</svg>`;
        }
        function studioRenderGallery() {
            for (const p of studioPatterns) {
                const button = $(`[data-studio-pattern="${p.id}"]`);
                button.querySelector('.sp-thumbnail').innerHTML = studioSvg(spScene(p, 224, 128, 100, 0, true), 224, 128);
                button.setAttribute('aria-pressed', String(p.id === studioState.pattern));
            }
        }
        function studioRenderView() {
            const holder = $('#maker-view'), width = Math.round(holder.clientWidth);
            if (width < 1)
                return;
            studioWidth = width;
            studioHeight = window.innerWidth <= 780 ? 420 : 560;
            studioFaces = spScene(studioCurrent(), width, studioHeight, studioState.scale, studioState.angle);
            holder.innerHTML = studioSvg(studioFaces, width, studioHeight, true);
            $('#studio-current-name').textContent = studioCurrent().name;
            $('#studio-pattern-note').textContent = studioCurrent().note;
            $('#maker-scale-value').value = `${studioState.scale}%`;
            $('#maker-weight-value').value = studioState.weight.toLocaleString(root.lang, { maximumFractionDigits: 1 });
            $('#maker-angle-value').value = `${studioState.angle}°`;
            $('#maker-undo').disabled = studioHistory.length === 0;
            $('#maker-reset').disabled = studioPaint.size === 0;
            $('#studio-palette-name').textContent = studioPalette().name;
            $$('[data-studio-palette]').forEach(b => b.setAttribute('aria-pressed', String(Number(b.dataset.studioPalette) === studioState.palette)));
        }
        function studioPaintFace(target) {
            const id = target.dataset.face, prev = studioPaint.has(id) ? studioPaint.get(id) : null, base = Number(target.dataset.tone);
            const current = prev ?? base, next = studioState.style === 'outline' ? (prev ?? -1) + 1 : (current + 1) % studioPalette().colours.length;
            studioHistory.push({ id, prev });
            if (studioState.style === 'outline' ? next === studioPalette().colours.length : next === base)
                studioPaint.delete(id);
            else
                studioPaint.set(id, next);
            target.setAttribute('fill', studioPaint.has(id) ? studioPalette().colours[next] : (studioState.style === 'outline' ? studioPalette().ground : studioPalette().colours[base]));
            if (studioFocused !== id) {
                const old = $('#maker-view [tabindex="0"]');
                if (old)
                    old.setAttribute('tabindex', '-1');
                target.setAttribute('tabindex', '0');
                studioFocused = id;
            }
            $('#maker-undo').disabled = false;
            $('#maker-reset').disabled = studioPaint.size === 0;
            $('#maker-live').textContent = copy.ui.changed;
        }
        $$('[data-studio-pattern]').forEach(b => listen(b, 'click', () => {
            studioState.pattern = b.dataset.studioPattern;
            studioPaint.clear();
            studioHistory.length = 0;
            studioFocused = '';
            $$('[data-studio-pattern]').forEach(button => button.setAttribute('aria-pressed', String(button === b)));
            studioRenderView();
            $('#maker-live').textContent = `${copy.ui.selected}: ${studioCurrent().name}`;
        }));
        $$('[data-studio-palette]').forEach(b => listen(b, 'click', () => {
            studioState.palette = Number(b.dataset.studioPalette);
            studioRenderGallery();
            studioRenderView();
        }));
        listen($('#maker-style'), 'change', e => { studioState.style = e.target.value; studioRenderGallery(); studioRenderView(); });
        for (const [id, key] of [['maker-scale', 'scale'], ['maker-weight', 'weight'], ['maker-angle', 'angle']]) {
            listen($('#' + id), 'input', e => { studioState[key] = Number(e.target.value); studioRenderView(); });
        }
        listen($('#maker-view'), 'click', e => { const target = e.target.closest('[data-face]'); if (target)
            studioPaintFace(target); });
        listen($('#maker-view'), 'keydown', e => {
            const target = e.target.closest('[data-face]');
            if (!target)
                return;
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                studioPaintFace(target);
                return;
            }
            const vectors = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowDown: [0, 1], ArrowUp: [0, -1] };
            if (!vectors[e.key])
                return;
            e.preventDefault();
            const current = studioFaces.find(f => f.key === target.dataset.face);
            if (!current)
                return;
            const [vx, vy] = vectors[e.key];
            let best = null, bestScore = Infinity;
            for (const f of studioFaces) {
                if (f.cx < 5 || f.cx > studioWidth - 5 || f.cy < 5 || f.cy > studioHeight - 5)
                    continue;
                const dx = f.cx - current.cx, dy = f.cy - current.cy, forward = dx * vx + dy * vy, side = Math.abs(dx * vy - dy * vx);
                if (forward < 1)
                    continue;
                const score = forward + side * 2;
                if (score < bestScore) {
                    best = f;
                    bestScore = score;
                }
            }
            if (best) {
                target.setAttribute('tabindex', '-1');
                const next = $(`[data-face="${best.key}"]`);
                next.setAttribute('tabindex', '0');
                next.focus({ preventScroll: true });
                studioFocused = best.key;
            }
        });
        listen($('#maker-undo'), 'click', () => {
            const change = studioHistory.pop();
            if (!change)
                return;
            if (change.prev === null)
                studioPaint.delete(change.id);
            else
                studioPaint.set(change.id, change.prev);
            studioRenderView();
            $('#maker-live').textContent = copy.ui.undone;
        });
        listen($('#maker-reset'), 'click', () => {
            studioPaint.clear();
            studioHistory.length = 0;
            studioRenderView();
            $('#maker-live').textContent = copy.ui.resetDone;
        });
        function studioExportString() {
            const node = $('#maker-svg').cloneNode(true);
            node.setAttribute('width', '2000');
            node.setAttribute('height', String(Math.round(2000 * studioHeight / studioWidth)));
            node.querySelector('desc').textContent = copy.studio.exportNote;
            for (const el of [node, ...node.querySelectorAll('*')])
                for (const a of [...el.attributes])
                    if (a.name.startsWith('data-') || ['tabindex', 'role', 'aria-label', 'id'].includes(a.name))
                        el.removeAttribute(a.name);
            return new XMLSerializer().serializeToString(node);
        }
        function studioDownload(blob, extension, pattern = studioState.pattern) {
            const url = URL.createObjectURL(blob), a = document.createElement('a');
            a.href = url;
            a.download = `artlines-${pattern}.${extension}`;
            a.click();
            setTimeout(() => URL.revokeObjectURL(url), 1500);
        }
        listen($('#maker-download'), 'click', () => {
            studioDownload(new Blob([studioExportString()], { type: 'image/svg+xml;charset=utf-8' }), 'svg');
            $('#maker-live').textContent = copy.ui.exportReady;
        });
        listen($('#maker-download-png'), 'click', async () => {
            const button = $('#maker-download-png');
            button.disabled = true;
            button.setAttribute('aria-busy', 'true');
            const exportPattern = studioState.pattern, exportHeight = Math.round(2000 * studioHeight / studioWidth);
            const url = URL.createObjectURL(new Blob([studioExportString()], { type: 'image/svg+xml;charset=utf-8' }));
            try {
                const image = new Image();
                await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = reject; image.src = url; });
                const canvas = document.createElement('canvas');
                canvas.width = 2000;
                canvas.height = exportHeight;
                canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
                const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
                if (!blob)
                    throw new Error('PNG export failed');
                studioDownload(blob, 'png', exportPattern);
                $('#maker-live').textContent = copy.ui.exportReady;
            }
            catch {
                $('#maker-live').textContent = copy.ui.exportError;
            }
            finally {
                URL.revokeObjectURL(url);
                button.disabled = false;
                button.removeAttribute('aria-busy');
            }
        });
        const resizeObserver = new ResizeObserver(entries => { const width = Math.round(entries[0].contentRect.width); if (width !== studioSize) {
            studioSize = width;
            studioRenderView();
        } });
        resizeObserver.observe($('#maker-view'));
        cleanup.push(() => resizeObserver.disconnect());
        studioRenderGallery();
        studioRenderView();
    }
    const lazyImages = [...root.querySelectorAll('[data-lazy-image]')];
    const loadImage = image => { if (!image.getAttribute('href'))
        image.setAttribute('href', image.dataset.lazyImage); };
    const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) {
        loadImage(entry.target);
        observer.unobserve(entry.target);
    } }), { rootMargin: '300px' });
    lazyImages.forEach(image => observer.observe(image));
    const dialog = $('#image-dialog');
    let opener = null, unlock = null;
    listen(root, 'click', event => {
        const anchor = event.target.closest('[data-enlarge-image]');
        if (!anchor || !root.contains(anchor))
            return;
        event.preventDefault();
        opener = anchor;
        const image = anchor.querySelector('img');
        dialog.querySelector('img').src = anchor.dataset.full;
        dialog.querySelector('img').alt = image?.alt || anchor.dataset.title;
        const credit = anchor.closest('figure')?.querySelector('figcaption');
        dialog.querySelector('p').textContent = credit?.textContent || '';
        unlock = lockBodyScroll();
        dialog.showModal();
    });
    listen(dialog.querySelector('button'), 'click', () => dialog.close());
    listen(dialog, 'close', () => { unlock?.(); unlock = null; dialog.querySelector('img').removeAttribute('src'); opener?.focus({ preventScroll: true }); });
    return () => { controller.abort(); observer.disconnect(); cleanup.forEach(fn => fn()); if (dialog.open)
        dialog.close(); unlock?.(); };
}
