function checkAuth(requiredRole) {
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
