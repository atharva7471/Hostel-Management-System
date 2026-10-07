// Synchronous head injection
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
