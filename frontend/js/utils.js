// Global utilities
const API_BASE = 'http://localhost:8000/api';

async function fetchAPI(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        });

        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            window.location.href = '../login.html';
            return null;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Something went wrong');
        }

        return data;
    } catch (err) {
        showToast(err.message, 'error');
        throw err;
    }
}

function showToast(message, type = 'success') {
    const existing = document.getElementById('toast-container');
    if (!existing) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const isError = type === 'error';
    const bgClass = isError ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800' : 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-100 dark:border-green-800';
    const icon = isError ? 'alert-circle' : 'check-circle';

    toast.className = `flex items-center p-4 border rounded-xl shadow-lg transition-all duration-300 transform translate-y-4 opacity-0 ${bgClass}`;
    toast.innerHTML = `
        <i data-lucide="${icon}" class="w-5 h-5 mr-3"></i>
        <span class="text-sm font-medium">${message}</span>
    `;

    document.getElementById('toast-container').appendChild(toast);
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-4', 'opacity-0');
    });

    // Remove after 3s
    setTimeout(() => {
        toast.classList.add('translate-y-4', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('hidden');
        // Small delay to allow display:block to apply before animating opacity
        setTimeout(() => {
            modal.querySelector('.modal-backdrop').classList.remove('opacity-0');
            modal.querySelector('.modal-panel').classList.remove('opacity-0', 'scale-95');
        }, 10);
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.querySelector('.modal-backdrop').classList.add('opacity-0');
        modal.querySelector('.modal-panel').classList.add('opacity-0', 'scale-95');
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }
}

function openDrawer(id) {
    const drawer = document.getElementById(id);
    if (drawer) {
        drawer.classList.remove('hidden');
        setTimeout(() => {
            drawer.querySelector('.drawer-backdrop').classList.remove('opacity-0');
            drawer.querySelector('.drawer-panel').classList.remove('translate-x-full');
        }, 10);
    }
}

function closeDrawer(id) {
    const drawer = document.getElementById(id);
    if (drawer) {
        drawer.querySelector('.drawer-backdrop').classList.add('opacity-0');
        drawer.querySelector('.drawer-panel').classList.add('translate-x-full');
        setTimeout(() => {
            drawer.classList.add('hidden');
        }, 300);
    }
}

// --- Notifications UI ---
async function initNotifications() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    // Find the navbar right section
    const navRight = document.querySelector('header .flex.items-center.space-x-4') || document.querySelector('nav .flex.items-center.space-x-4.ml-auto') || document.querySelector('.flex.items-center.space-x-4');
    if (!navRight || document.getElementById('notif-bell-container')) return;

    // Create bell container
    const container = document.createElement('div');
    container.id = 'notif-bell-container';
    container.className = 'relative flex items-center';
    
    container.innerHTML = `
        <button id="notif-bell-btn" class="relative p-2 rounded-full hover:bg-gray-100 dark:hover:bg-surface-800 transition mr-1 text-gray-500 hover:text-gray-900 dark:hover:text-white">
            <i data-lucide="bell" class="w-5 h-5"></i>
            <span id="notif-badge" class="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full hidden border-2 border-white dark:border-surface-900"></span>
        </button>
        <div id="notif-panel" class="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-white dark:bg-surface-800 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700 hidden z-50 transform origin-top-right transition-all opacity-0 scale-95 flex flex-col max-h-[80vh]">
            <div class="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center shrink-0">
                <h3 class="font-semibold text-gray-900 dark:text-white">Notifications</h3>
                <button onclick="markAllNotificationsRead()" class="text-xs font-medium text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300">Mark all read</button>
            </div>
            <div id="notif-list" class="flex-1 overflow-y-auto p-2 space-y-1">
                <!-- Items -->
            </div>
        </div>
    `;
    
    // Insert before theme toggle if it exists
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn && themeBtn.parentNode === navRight) {
        navRight.insertBefore(container, themeBtn);
    } else {
        navRight.prepend(container);
    }

    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Toggle logic
    const btn = document.getElementById('notif-bell-btn');
    const panel = document.getElementById('notif-panel');
    
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isHidden = panel.classList.contains('hidden');
        if (isHidden) {
            panel.classList.remove('hidden');
            setTimeout(() => panel.classList.remove('opacity-0', 'scale-95'), 10);
            loadNotifications();
        } else {
            panel.classList.add('opacity-0', 'scale-95');
            setTimeout(() => panel.classList.add('hidden'), 200);
        }
    });

    document.addEventListener('click', (e) => {
        if (!panel.contains(e.target) && !btn.contains(e.target) && !panel.classList.contains('hidden')) {
            panel.classList.add('opacity-0', 'scale-95');
            setTimeout(() => panel.classList.add('hidden'), 200);
        }
    });

    // Initial load for badge
    loadNotifications(true);
}

async function loadNotifications(onlyBadge = false) {
    try {
        const data = await fetchAPI('/notifications/');
        const unreadCount = data.filter(n => !n.is_read).length;
        
        const badge = document.getElementById('notif-badge');
        if (badge) {
            if (unreadCount > 0) badge.classList.remove('hidden');
            else badge.classList.add('hidden');
        }

        if (onlyBadge) return;

        const list = document.getElementById('notif-list');
        if (data.length === 0) {
            list.innerHTML = '<div class="p-8 text-center"><div class="w-12 h-12 bg-gray-50 dark:bg-surface-900 rounded-full flex items-center justify-center mx-auto mb-3 text-gray-400"><i data-lucide="bell-off" class="w-6 h-6"></i></div><p class="text-sm text-gray-500 font-medium">No notifications</p></div>';
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        const icons = {
            'PAYMENT': 'credit-card',
            'COMPLAINT': 'message-square-warning',
            'MAINTENANCE': 'wrench',
            'ALLOCATION': 'bed',
            'ANNOUNCEMENT': 'megaphone',
            'GENERAL': 'bell'
        };

        list.innerHTML = data.map(n => `
            <div class="p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-surface-700/50 transition cursor-pointer flex gap-3 ${n.is_read ? 'opacity-75' : 'bg-brand-50/50 dark:bg-brand-900/10'}" onclick="markNotificationRead('${n._id}', this, event)">
                <div class="w-8 h-8 rounded-full ${n.type === 'ANNOUNCEMENT' ? 'bg-orange-100 text-orange-600 dark:bg-orange-900/30' : 'bg-brand-100 text-brand-600 dark:bg-brand-900/30'} flex items-center justify-center shrink-0">
                    <i data-lucide="${icons[n.type] || icons.GENERAL}" class="w-4 h-4"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-gray-900 dark:text-white truncate ${!n.is_read ? '' : 'font-medium'}">${n.title}</p>
                    <p class="text-[13px] text-gray-600 dark:text-gray-400 mt-0.5 line-clamp-2">${n.message}</p>
                    <p class="text-[11px] text-gray-400 mt-1 font-medium">${new Date(n.created_at).toLocaleString()}</p>
                </div>
                ${!n.is_read ? '<div class="w-2 h-2 rounded-full bg-brand-500 mt-2 shrink-0"></div>' : ''}
            </div>
        `).join('');
        if (typeof lucide !== 'undefined') lucide.createIcons();
    } catch (e) {}
}

window.markNotificationRead = async function(id, element, e) {
    if (e) e.stopPropagation();
    try {
        await fetchAPI(`/notifications/${id}/read`, { method: 'PATCH' });
        element.classList.remove('bg-brand-50/50', 'dark:bg-brand-900/10');
        element.classList.add('opacity-75');
        const title = element.querySelector('.font-semibold');
        if(title) { title.classList.remove('font-semibold'); title.classList.add('font-medium'); }
        const dot = element.querySelector('.bg-brand-500');
        if(dot) dot.remove();
        loadNotifications(true); // update badge
    } catch (e) {}
}

window.markAllNotificationsRead = async function() {
    try {
        await fetchAPI('/notifications/read-all', { method: 'PATCH' });
        loadNotifications();
    } catch (e) {}
}

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initNotifications, 200);
});
