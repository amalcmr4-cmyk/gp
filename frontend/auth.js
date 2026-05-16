// Centralized auth helper for DataWizard (plain browser JS)
(function () {
    'use strict';

    function decodeJwtPayload(token) {
        if (!token || typeof token !== 'string') return null;
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        try {
            const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
            const padded = payload.padEnd(payload.length + (4 - (payload.length % 4)) % 4, '=');
            return JSON.parse(atob(padded));
        } catch (err) { return null; }
    }

    function getUserFromStorage() {
        const stored = localStorage.getItem('user') || localStorage.getItem('dw_user') || localStorage.getItem('currentUser');
        if (!stored) return null;
        try { const parsed = JSON.parse(stored); return parsed && typeof parsed === 'object' ? parsed : null; } catch (e) { return null; }
    }

    function getUserFromToken(token) {
        const payload = decodeJwtPayload(token);
        if (!payload) return null;
        return {
            name: payload.name || payload.full_name || payload.given_name || payload.preferred_username || payload.username || '',
            email: payload.email || payload.sub || payload.username || ''
        };
    }

    function getCurrentUser() {
        const stored = getUserFromStorage();
        if (stored && (stored.name || stored.email)) return stored;

        const token = localStorage.getItem('access_token');
        if (!token) return null;

        const userFromToken = getUserFromToken(token);
        if (userFromToken && (userFromToken.name || userFromToken.email)) return userFromToken;

        return null;
    }

    function login({ access_token, id_token, refresh_token, user, redirect } = {}) {
        if (access_token) localStorage.setItem('access_token', access_token);
        if (id_token) localStorage.setItem('id_token', id_token);
        if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
        if (user) {
            try { localStorage.setItem('user', typeof user === 'string' ? user : JSON.stringify(user)); } catch (e) {}
        }
        // notify listeners
        window.dispatchEvent(new CustomEvent('auth-changed', { detail: { loggedIn: true } }));
        if (redirect) window.location.href = redirect;
    }

    function logout({ clearAllSession = false, redirect } = {}) {
        const keys = ['access_token','id_token','refresh_token','user','dw_user','currentUser'];
        keys.forEach(k => localStorage.removeItem(k));
        if (clearAllSession) {
            try { sessionStorage.clear(); } catch (e) {}
        }
        window.dispatchEvent(new CustomEvent('auth-changed', { detail: { loggedIn: false } }));
        if (redirect) window.location.href = redirect;
    }

    // Expose helper
    window.auth = {
        login: login,
        logout: logout,
        getCurrentUser: getCurrentUser
    };

})();
