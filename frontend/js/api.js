const API_BASE = '/api';

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
