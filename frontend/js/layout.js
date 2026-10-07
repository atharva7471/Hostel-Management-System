async function loadLayout() {
    const layout = document.body.getAttribute('data-layout');
    if (!layout) return;

    const isRoot = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html') || window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '' || window.location.pathname.endsWith('/frontend/');
    const prefix = isRoot ? '' : '../';

    let mainContent = '';
    if (layout !== 'auth') {
        mainContent = document.body.innerHTML;
        document.body.innerHTML = '';
    }

    if (layout === 'management') {
        const sidebar = await fetch(prefix + 'components/layout/management-sidebar.html').then(r => r.text());
        const header = await fetch(prefix + 'components/layout/management-navbar.html').then(r => r.text());
        
        document.body.className = "bg-gray-50 dark:bg-surface-900 text-gray-900 dark:text-gray-100 flex h-screen overflow-hidden antialiased selection:bg-brand-200 selection:text-brand-900";
        document.body.innerHTML = `
            ${sidebar}
            <div class="flex-1 flex flex-col h-screen overflow-hidden bg-gray-50 dark:bg-surface-900 relative">
                ${header}
                <div class="flex-1 overflow-auto p-4 sm:p-6 lg:p-8 custom-scrollbar" id="page-content">
                    ${mainContent}
                </div>
            </div>
        `;
    } else if (layout === 'student') {
        const nav = await fetch(prefix + 'components/layout/student-navbar.html').then(r => r.text());
        
        document.body.className = "bg-gray-50 dark:bg-surface-900 text-gray-900 dark:text-gray-100 flex flex-col h-screen overflow-hidden antialiased selection:bg-brand-200 selection:text-brand-900";
        document.body.innerHTML = `
            ${nav}
            <div class="flex-1 overflow-auto bg-gray-50 dark:bg-surface-900 custom-scrollbar p-4 sm:p-6 lg:p-8" id="page-content">
                <div class="max-w-5xl mx-auto space-y-8">
                    ${mainContent}
                </div>
            </div>
        `;
    } else if (layout === 'auth') {
        document.body.className = "bg-gray-50 dark:bg-surface-900 text-gray-900 dark:text-gray-100 min-h-screen flex flex-col items-center justify-center px-4 antialiased selection:bg-brand-200 selection:text-brand-900 relative";
        // Do not touch innerHTML for auth to preserve inline scripts
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
