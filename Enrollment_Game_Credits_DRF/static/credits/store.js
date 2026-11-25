/* The product grid consumes the DRF API on the same origin. */
document.addEventListener('DOMContentLoaded', () => {
    const catalog = document.querySelector('[data-catalog]');
    if (!catalog) return;
    const grid = catalog.querySelector('[data-product-grid]');
    const count = catalog.querySelector('[data-catalog-count]');
    const status = catalog.querySelector('[data-catalog-status]');
    const failure = catalog.querySelector('[data-catalog-error]');
    const empty = catalog.querySelector('[data-empty]');
    const form = catalog.querySelector('[data-catalog-search]');
    const search = form.querySelector('[name="search"]');
    const order = form.querySelector('[data-ordering]');
    const available = form.querySelector('[data-available]');
    const pagination = catalog.querySelector('[data-pagination]');
    const previous = catalog.querySelector('[data-previous]');
    const next = catalog.querySelector('[data-next]');
    const pageLabel = catalog.querySelector('[data-page-label]');
    const chips = Array.from(catalog.querySelectorAll('[data-game]'));
    const number = new Intl.NumberFormat('en-PH');
    const money = new Intl.NumberFormat('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const state = { game: '', search: '', ordering: 'id', available: false, page: 1 };
    let controller;
    let requestNumber = 0;

    function element(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }
    function icon(name) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.classList.add('icon');
        svg.setAttribute('aria-hidden', 'true');
        const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttribute('href', `${catalog.dataset.iconsUrl}#${name}`);
        svg.append(use);
        return svg;
    }
    function localLink(value) {
        const url = new URL(value, window.location.origin);
        if (url.origin !== window.location.origin) throw new Error('Unexpected product URL');
        return url.href;
    }
    function card(product) {
        const theme = ['coral', 'gold', 'mint', 'violet'].includes(product.theme) ? product.theme : 'mint';
        const link = localLink(product.product_url);
        const article = element('article', 'product-card');
        const visual = element('a', `product-visual theme-${theme}`);
        visual.href = link;
        visual.setAttribute('aria-label', `View ${product.name}`);
        const symbol = element('span', 'visual-symbol');
        symbol.append(icon('gem'));
        visual.append(element('span', 'visual-orbit'), element('span', 'game-initials', product.short_name), symbol);
        if (product.featured) visual.append(element('span', 'featured-label', 'FEATURED'));
        const info = element('div', 'product-info');
        const title = element('a', 'product-name', `${number.format(product.credit_amount)} ${product.credit_unit}`);
        title.href = link;
        const stock = element('span', `availability${product.available ? '' : ' unavailable'}`);
        stock.append(element('i'), document.createTextNode(product.available ? 'Available' : 'Unavailable'));
        const bottom = element('div', 'product-bottom');
        const price = element('span', 'price');
        price.append(element('small', '', 'PHP'), document.createTextNode(` ₱${money.format(Number(product.price))}`));
        const open = element('a', 'product-open');
        open.href = link;
        open.setAttribute('aria-label', `View ${product.name}`);
        open.append(icon('arrow'));
        bottom.append(price, open);
        info.append(element('p', 'product-game', product.game_name), title, stock, bottom);
        article.append(visual, info);
        return article;
    }
    function updateControls() {
        search.value = state.search;
        order.value = state.ordering;
        available.checked = state.available;
        chips.forEach(chip => {
            const selected = chip.dataset.game === state.game;
            chip.classList.toggle('selected', selected);
            chip.setAttribute('aria-pressed', String(selected));
        });
    }
    function query() {
        const params = new URLSearchParams();
        if (state.game) params.set('game', state.game);
        if (state.search) params.set('search', state.search);
        if (state.ordering !== 'id') params.set('ordering', state.ordering);
        if (state.available) params.set('available', 'true');
        if (state.page > 1) params.set('page', String(state.page));
        return params;
    }
    function readLocation() {
        const params = new URLSearchParams(window.location.search);
        state.game = chips.some(chip => chip.dataset.game === params.get('game')) ? (params.get('game') || '') : '';
        state.search = (params.get('search') || '').slice(0, 120);
        state.ordering = Array.from(order.options).some(option => option.value === params.get('ordering')) ? params.get('ordering') : 'id';
        state.available = params.get('available') === 'true';
        const page = Number(params.get('page'));
        state.page = Number.isSafeInteger(page) && page > 0 ? page : 1;
        updateControls();
    }
    async function load(updateHistory = true) {
        if (controller) controller.abort();
        controller = new AbortController();
        const current = ++requestNumber;
        const params = query();
        if (updateHistory) {
            const location = new URL(window.location.href);
            location.search = params.toString();
            window.history.replaceState(null, '', location);
        }
        const url = new URL(catalog.dataset.productsUrl, window.location.origin);
        url.search = params.toString();
        url.searchParams.set('format', 'json');
        url.searchParams.set('page_size', '24');
        status.hidden = false;
        status.textContent = 'Loading credit packages…';
        failure.hidden = true;
        grid.setAttribute('aria-busy', 'true');
        try {
            const response = await fetch(url, { headers: { Accept: 'application/json' }, signal: controller.signal });
            if (!response.ok) throw new Error('Could not load products');
            const data = await response.json();
            if (current !== requestNumber) return;
            if (!Array.isArray(data.results)) throw new Error('Unexpected API response');
            const cards = data.results.map(card);
            grid.replaceChildren(...cards);
            grid.hidden = data.count === 0;
            empty.hidden = data.count !== 0;
            count.textContent = `${data.count} ${data.count === 1 ? 'package' : 'packages'}`;
            previous.disabled = !data.previous;
            next.disabled = !data.next;
            pagination.hidden = !data.previous && !data.next;
            pageLabel.textContent = `Page ${state.page} of ${Math.max(1, Math.ceil(data.count / 24))}`;
        } catch (error) {
            if (error.name === 'AbortError' || current !== requestNumber) return;
            grid.hidden = true;
            empty.hidden = true;
            pagination.hidden = true;
            failure.hidden = false;
            count.textContent = 'Unable to load';
        } finally {
            if (current === requestNumber) {
                status.hidden = true;
                grid.setAttribute('aria-busy', 'false');
            }
        }
    }
    chips.forEach(chip => chip.addEventListener('click', () => {
        state.game = chip.dataset.game;
        state.page = 1;
        updateControls();
        load();
    }));
    form.addEventListener('submit', event => {
        event.preventDefault();
        state.search = search.value.trim().slice(0, 120);
        state.page = 1;
        load();
    });
    search.addEventListener('search', () => {
        if (!search.value) { state.search = ''; state.page = 1; load(); }
    });
    order.addEventListener('change', () => { state.ordering = order.value; state.page = 1; load(); });
    available.addEventListener('change', () => { state.available = available.checked; state.page = 1; load(); });
    previous.addEventListener('click', () => { if (state.page > 1) { state.page -= 1; load(); } });
    next.addEventListener('click', () => { state.page += 1; load(); });
    catalog.querySelector('[data-retry]').addEventListener('click', () => load());
    catalog.querySelector('[data-reset]').addEventListener('click', () => {
        Object.assign(state, { game: '', search: '', ordering: 'id', available: false, page: 1 });
        updateControls();
        load();
    });
    window.addEventListener('popstate', () => { readLocation(); load(false); });
    readLocation();
    load(false);
});
