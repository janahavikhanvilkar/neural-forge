document.addEventListener('DOMContentLoaded', function () {
    // 1. Sidebar Toggle on Mobile
    const sidebar = document.getElementById('appSidebar');
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => sidebar.classList.toggle('show'));
    }
    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => sidebar.classList.remove('show'));
    }

    // 2. Global Search Auto-complete
    const searchInput = document.getElementById('globalSearchInput');
    const searchDropdown = document.getElementById('searchResultsDropdown');
    const searchResultsList = document.getElementById('searchResultsList');

    if (searchInput) {
        // Keyboard shortcut: Press '/' to focus search
        document.addEventListener('keydown', function(e) {
            if (e.key === '/' && document.activeElement !== searchInput && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                searchInput.focus();
            }
        });

        let debounceTimer;
        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            if (query.length < 2) {
                searchDropdown.classList.add('d-none');
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            searchResultsList.innerHTML = data.results.map(item => `
                                <a href="${item.link}" class="d-flex align-items-center justify-content-between p-2 text-decoration-none text-dark hover-bg-light rounded-2 small">
                                    <div>
                                        <span class="badge bg-secondary-subtle text-secondary me-1" style="font-size: 0.65rem;">${item.type}</span>
                                        <strong>${item.title}</strong>
                                        <div class="text-muted" style="font-size: 0.75rem;">${item.subtitle}</div>
                                    </div>
                                    <span class="badge bg-light text-dark border">${item.badge}</span>
                                </a>
                            `).join('');
                            searchDropdown.classList.remove('d-none');
                        } else {
                            searchResultsList.innerHTML = '<div class="p-2 text-muted small text-center">No matching records found.</div>';
                            searchDropdown.classList.remove('d-none');
                        }
                    })
                    .catch(() => {
                        searchDropdown.classList.add('d-none');
                    });
            }, 250);
        });

        // Hide search on click outside
        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.classList.add('d-none');
            }
        });
    }

    // 3. Live Notifications Engine
    const notifBtn = document.getElementById('notificationsBtn');
    const notifBadge = document.getElementById('notifBadge');
    const notifList = document.getElementById('notifList');
    const markAllReadBtn = document.getElementById('markAllReadBtn');

    function loadNotifications() {
        if (!notifList) return;
        fetch('/api/notifications')
            .then(res => res.json())
            .then(data => {
                if (data.unread_count > 0) {
                    notifBadge.innerText = data.unread_count;
                    notifBadge.style.display = 'inline-block';
                } else {
                    notifBadge.style.display = 'none';
                }

                if (data.notifications && data.notifications.length > 0) {
                    notifList.innerHTML = data.notifications.map(n => `
                        <a href="${n.link}" class="d-block p-3 border-bottom text-decoration-none text-dark ${!n.is_read ? 'bg-light' : ''} hover-bg-light">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <strong class="small text-dark">${n.title}</strong>
                                <span class="badge bg-secondary-subtle text-secondary" style="font-size: 0.65rem;">${n.module}</span>
                            </div>
                            <div class="text-muted small">${n.message}</div>
                            <div class="text-muted font-monospace mt-1" style="font-size: 0.65rem;">${n.created_at}</div>
                        </a>
                    `).join('');
                } else {
                    notifList.innerHTML = '<div class="p-3 text-center text-muted small">No notifications yet.</div>';
                }
            })
            .catch(() => {});
    }

    if (notifBtn) {
        loadNotifications();
        // Periodic check every 30 seconds
        setInterval(loadNotifications, 30000);
    }

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function () {
            fetch('/api/notifications/mark-read', { method: 'POST' })
                .then(() => {
                    notifBadge.style.display = 'none';
                    loadNotifications();
                });
        });
    }
});
