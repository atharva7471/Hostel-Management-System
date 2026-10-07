async function loadComponents(container) {
    const isRoot = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html') || window.location.pathname.endsWith('index.html') || window.location.pathname.split('/').pop() === '' || window.location.pathname.endsWith('/frontend/');
    const prefix = isRoot ? '' : '../';

    const elements = container.querySelectorAll('[data-component]');
    for (let el of elements) {
        const comp = el.getAttribute('data-component');
        try {
            let html = await fetch(${prefix}components/.html).then(r => r.text());
            
            // Basic prop replacement
            const attrs = el.attributes;
            for (let i = 0; i < attrs.length; i++) {
                if (attrs[i].name.startsWith('data-prop-')) {
                    const propName = attrs[i].name.replace('data-prop-', '');
                    const regex = new RegExp('{{' + propName + '}}', 'g');
                    html = html.replace(regex, attrs[i].value);
                }
            }
            
            // Children replacement
            html = html.replace(/{{children}}/g, el.innerHTML);
            
            el.outerHTML = html;
        } catch (e) {
            console.error('Failed to load component', comp);
        }
    }
}
