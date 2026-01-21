/**
 * Authorization module
 */

class Auth {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.tokenType = localStorage.getItem('token_type') || 'bearer';
        this.user = null;
    }

    isAuthenticated() {
        return !!this.token;
    }

    getAuthHeader() {
        if (!this.token) return {};
        return {
            'Authorization': `${this.tokenType} ${this.token}`
        };
    }

    async checkAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login.html';
            return false;
        }

        try {
            const apiUrl = window.location.hostname === 'localhost' ? 'http://localhost:8000' : `http://${window.location.hostname}:8000`;
            const response = await fetch(`${apiUrl}/api/auth/me`, {
                headers: this.getAuthHeader()
            });

            if (response.ok) {
                this.user = await response.json();
                return true;
            } else {
                // Token expired or invalid
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('Auth check error:', error);
            return false;
        }
    }

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        window.location.href = '/login.html';
    }

    async fetchWithAuth(url, options = {}) {
        const headers = {
            ...options.headers,
            ...this.getAuthHeader()
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Unauthorized - redirect to login
            this.logout();
            throw new Error('Unauthorized');
        }

        return response;
    }
}

// Global auth instance
const auth = new Auth();

// Check auth on page load
document.addEventListener('DOMContentLoaded', async () => {
    await auth.checkAuth();
});
