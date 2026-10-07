import os
import re

FRONTEND_DIR = 'frontend'

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

ensure_dir(os.path.join(FRONTEND_DIR, 'components', 'layout'))
ensure_dir(os.path.join(FRONTEND_DIR, 'components', 'ui'))
ensure_dir(os.path.join(FRONTEND_DIR, 'components', 'dashboard'))

# 1. Create JS files
js_dir = os.path.join(FRONTEND_DIR, 'js')
ensure_dir(js_dir)

with open(os.path.join(js_dir, 'api.js'), 'w') as f:
    f.write('''const API_BASE = '/api';

async function fetchAPI(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': Bearer  } : {}),
        ...(options.headers || {})
    };

    const res = await fetch(${API_BASE}, {
        ...options,
        headers
    });

    if (!res.ok) {
        let errStr = 'API Error';
        try {
            const errData = await res.json();
            errStr = errData.detail || errStr;
        } catch (e) {}
        if (res.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            window.location.href = window.location.pathname.includes('/management/') || window.location.pathname.includes('/student/') ? '../login.html' : 'login.html';
        }
        throw new Error(errStr);
    }
    return res.json();
}
''')

with open(os.path.join(js_dir, 'auth.js'), 'w') as f:
    f.write('''function checkAuth(requiredRole) {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    
    const isRoot = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html') || window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname.endsWith('/frontend/');
    const loginPath = isRoot ? 'login.html' : '../login.html';
    
    if (!token) {
        window.location.href = loginPath;
        return;
    }
    
    if (requiredRole && role !== requiredRole) {
        const prefix = isRoot ? '' : '../';
        if (role === 'MANAGEMENT') {
            window.location.href = prefix + 'management/dashboard.html';
        } else {
            window.location.href = prefix + 'student/dashboard.html';
        }
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    const isRoot = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html') || window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname.endsWith('/frontend/');
    window.location.href = isRoot ? 'login.html' : '../login.html';
}
''')

with open(os.path.join(js_dir, 'core.js'), 'w') as f:
    f.write('''// Synchronous head injection
const isRoot = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html') || window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '' || window.location.pathname.endsWith('/frontend/');
const prefix = isRoot ? '' : '../';

document.write(
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="css/index.css" rel="stylesheet">
    <script src="js/theme.js"></script>
    <script src="js/api.js"></script>
    <script src="js/auth.js"></script>
    <script src="js/utils.js"></script>
    <script src="js/components.js"></script>
    <script src="js/layout.js"></script>
);

document.addEventListener('DOMContentLoaded', () => {
    const title = document.body.getAttribute('data-page-title');
    if (title) document.title = title;
});
''')

with open(os.path.join(js_dir, 'layout.js'), 'w') as f:
    f.write('''async function loadLayout() {
    const layout = document.body.getAttribute('data-layout');
    if (!layout) return;

    const isRoot = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html') || window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '' || window.location.pathname.endsWith('/frontend/');
    const prefix = isRoot ? '' : '../';

    const mainContent = document.body.innerHTML;
    document.body.innerHTML = '';

    if (layout === 'management') {
        const sidebar = await fetch(prefix + 'components/layout/management-sidebar.html').then(r => r.text());
        const header = await fetch(prefix + 'components/layout/management-navbar.html').then(r => r.text());
        
        document.body.className = "bg-gray-50 dark:bg-surface-900 text-gray-900 dark:text-gray-100 flex h-screen overflow-hidden antialiased selection:bg-brand-200 selection:text-brand-900";
        document.body.innerHTML = 
            
            <div class="flex-1 flex flex-col h-screen overflow-hidden bg-gray-50 dark:bg-surface-900 relative">
                
                <div class="flex-1 overflow-auto p-4 sm:p-6 lg:p-8 custom-scrollbar" id="page-content">
                    
                </div>
            </div>
        ;
    } else if (layout === 'student') {
        const nav = await fetch(prefix + 'components/layout/student-navbar.html').then(r => r.text());
        
        document.body.className = "bg-gray-50 dark:bg-surface-900 text-gray-900 dark:text-gray-100 flex flex-col h-screen overflow-hidden antialiased selection:bg-brand-200 selection:text-brand-900";
        document.body.innerHTML = 
            
            <div class="flex-1 overflow-auto bg-gray-50 dark:bg-surface-900 custom-scrollbar p-4 sm:p-6 lg:p-8" id="page-content">
                <div class="max-w-5xl mx-auto space-y-8">
                    
                </div>
            </div>
        ;
    }

    // Process components inside
    await loadComponents(document.body);

    // Nav active states
    const currentPath = window.location.pathname.split('/').pop() || 'dashboard.html';
    document.querySelectorAll('a').forEach(a => {
        const href = a.getAttribute('href');
        if (!href) return;
        if (href === currentPath || href.startsWith(currentPath + '?')) {
            if (layout === 'management') {
                a.className = "flex items-center px-3 py-2 text-sm font-medium rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/20 dark:text-brand-400 transition";
            } else if (layout === 'student') {
                a.className = "px-3 py-2 rounded-lg text-sm font-medium bg-brand-50 text-brand-600 dark:bg-brand-900/20 dark:text-brand-400 transition";
            }
        } else {
            if (layout === 'management' && a.classList.contains('bg-brand-50')) {
                a.className = "flex items-center px-3 py-2 text-sm font-medium rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-surface-800 transition";
            } else if (layout === 'student' && a.classList.contains('bg-brand-50')) {
                a.className = "px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-surface-800 transition";
            }
        }
    });

    if (window.setupThemeToggle) setupThemeToggle();
    if (window.lucide) lucide.createIcons();
    
    // Trigger a custom event so page scripts know DOM is ready
    document.dispatchEvent(new Event('LayoutLoaded'));
}

document.addEventListener('DOMContentLoaded', loadLayout);
''')

with open(os.path.join(js_dir, 'components.js'), 'w') as f:
    f.write('''async function loadComponents(container) {
    const isRoot = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html') || window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '' || window.location.pathname.endsWith('/frontend/');
    const prefix = isRoot ? '' : '../';

    const elements = container.querySelectorAll('[data-component]');
    for (let el of elements) {
        const comp = el.getAttribute('data-component');
        try {
            const html = await fetch(${prefix}components/.html).then(r => r.text());
            el.outerHTML = html;
        } catch (e) {
            console.error('Failed to load component', comp);
        }
    }
}
''')

print('JS files created successfully')
