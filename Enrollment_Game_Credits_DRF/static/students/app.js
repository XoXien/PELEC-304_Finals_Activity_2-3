/* Small enhancements; directory links and filters also work without JavaScript. */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-profile-url]').forEach(row => {
        row.addEventListener('click', event => {
            if (event.target.closest('a, button, input, select') || window.getSelection().toString()) return;
            window.location.assign(row.dataset.profileUrl);
        });
    });

    const navToggle = document.querySelector('[data-nav-toggle]');
    const scrim = document.querySelector('[data-nav-close]');
    const sidebar = document.getElementById('sidebar');
    const desktopLayout = window.matchMedia('(min-width: 961px)');
    let sidebarCollapsed = false;
    try { sidebarCollapsed = window.localStorage.getItem('enrollment-sidebar-collapsed') === '1'; } catch (_) {}

    const refreshNavigation = () => {
        const desktop = desktopLayout.matches;
        const open = document.body.classList.contains('nav-open');
        document.body.classList.toggle('sidebar-collapsed', desktop && sidebarCollapsed);
        if (navToggle) {
            const label = desktop
                ? (sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar')
                : (open ? 'Close navigation' : 'Open navigation');
            navToggle.setAttribute('aria-expanded', String(desktop ? !sidebarCollapsed : open));
            navToggle.setAttribute('aria-label', label);
            navToggle.setAttribute('title', label);
        }
        if (scrim) scrim.hidden = desktop || !open;
        if (sidebar) sidebar.inert = !desktop && !open;
    };
    const closeMobileNavigation = () => {
        document.body.classList.remove('nav-open');
        refreshNavigation();
        if (navToggle) navToggle.focus();
    };
    if (navToggle) navToggle.addEventListener('click', () => {
        if (desktopLayout.matches) {
            sidebarCollapsed = !sidebarCollapsed;
            try { window.localStorage.setItem('enrollment-sidebar-collapsed', sidebarCollapsed ? '1' : '0'); } catch (_) {}
            refreshNavigation();
        } else {
            document.body.classList.toggle('nav-open');
            refreshNavigation();
            if (document.body.classList.contains('nav-open')) sidebar?.querySelector('a')?.focus();
        }
    });
    if (scrim) scrim.addEventListener('click', closeMobileNavigation);
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && document.body.classList.contains('nav-open')) {
            closeMobileNavigation();
        }
    });
    desktopLayout.addEventListener('change', () => {
        document.body.classList.remove('nav-open');
        refreshNavigation();
    });
    refreshNavigation();

    document.querySelectorAll('[data-notice-dismiss]').forEach(button => {
        button.addEventListener('click', () => button.closest('.notice')?.remove());
    });

    const tabs = Array.from(document.querySelectorAll('[data-profile-tab]'));
    const panels = Array.from(document.querySelectorAll('[data-profile-panel]'));
    if (tabs.length) {
        document.querySelector('.profile-tabs').setAttribute('role', 'tablist');
        tabs.forEach(tab => {
            tab.setAttribute('role', 'tab');
            tab.id = `tab-${tab.dataset.profileTab}`;
            tab.setAttribute('aria-controls', tab.dataset.profileTab);
        });
        panels.forEach(panel => {
            panel.setAttribute('role', 'tabpanel');
            panel.setAttribute('aria-labelledby', `tab-${panel.id}`);
            panel.tabIndex = 0;
        });
        const selectTab = (id, updateHistory = false) => {
            const valid = tabs.some(tab => tab.dataset.profileTab === id);
            const selected = valid ? id : tabs[0].dataset.profileTab;
            tabs.forEach(tab => {
                const active = tab.dataset.profileTab === selected;
                tab.classList.toggle('is-active', active);
                tab.setAttribute('aria-selected', String(active));
                tab.tabIndex = active ? 0 : -1;
            });
            panels.forEach(panel => { panel.hidden = panel.id !== selected; });
            if (updateHistory) window.history.replaceState(null, '', `#${selected}`);
        };
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', event => {
                event.preventDefault();
                selectTab(tab.dataset.profileTab, true);
            });
            tab.addEventListener('keydown', event => {
                let next = null;
                if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
                if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
                if (event.key === 'Home') next = 0;
                if (event.key === 'End') next = tabs.length - 1;
                if (next !== null) {
                    event.preventDefault();
                    tabs[next].focus();
                    selectTab(tabs[next].dataset.profileTab, true);
                }
            });
        });
        selectTab(window.location.hash.slice(1));
        window.addEventListener('hashchange', () => selectTab(window.location.hash.slice(1)));
    }

    document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
});
