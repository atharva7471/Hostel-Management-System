// Synchronous head injection
const isRoot = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html') || window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '' || window.location.pathname.endsWith('/frontend/');
const prefix = isRoot ? '' : '../';

document.write(`
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: { 50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd', 400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8', 800: '#1e40af', 900: '#1e3a8a' },
                        surface: { 50: '#f9fafb', 100: '#f3f4f6', 200: '#e5e7eb', 300: '#d1d5db', 400: '#9ca3af', 500: '#6b7280', 600: '#4b5563', 700: '#374151', 800: '#1f2937', 900: '#111827' }
                    },
                    fontFamily: { sans: ['Inter', 'sans-serif'] }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        body { font-family: 'Inter', sans-serif; }
    </style>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="${prefix}css/index.css" rel="stylesheet">
    <script src="${prefix}js/theme.js"></script>
    <script src="${prefix}js/auth.js"></script>
    <script src="${prefix}js/api.js"></script>
    <script src="${prefix}js/utils.js"></script>
    <script src="${prefix}js/components.js"></script>
    <script src="${prefix}js/layout.js"></script>
`);

document.addEventListener('DOMContentLoaded', () => {
    const title = document.body.getAttribute('data-page-title');
    if (title) document.title = title;
});
