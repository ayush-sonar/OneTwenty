const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class APIClient {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.token = localStorage.getItem('access_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        // Add JWT token if available
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const config = {
            ...options,
            headers,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth
    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                user_id: email,
                password: password,
            }),
        });

        this.token = data.access_token;
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);

        return data;
    }

    async signup(email, password) {
        return await this.request('/auth/signup', {
            method: 'POST',
            body: JSON.stringify({
                email: email,
                password: password,
            }),
        });
    }

    logout() {
        this.token = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    // Status & Settings
    async getStatus() {
        return await this.request('/status');
    }

    async updateSettings(settings) {
        return await this.request('/settings', {
            method: 'PUT',
            body: JSON.stringify(settings),
        });
    }

    // Entries
    async getEntries(countOrOptions = 10) {
        // Support both old API (count) and new API (hours, start/end)
        let query = '';
        if (typeof countOrOptions === 'number') {
            query = `?count=${countOrOptions}`;
        } else if (typeof countOrOptions === 'object') {
            const params = [];
            if (countOrOptions.hours) {
                params.push(`hours=${countOrOptions.hours}`);
            } else if (countOrOptions.count) {
                params.push(`count=${countOrOptions.count}`);
            }
            if (countOrOptions.start) {
                params.push(`start=${encodeURIComponent(countOrOptions.start)}`);
            }
            if (countOrOptions.end) {
                params.push(`end=${encodeURIComponent(countOrOptions.end)}`);
            }
            if (params.length > 0) {
                query = `?${params.join('&')}`;
            }
        }
        return await this.request(`/entries${query}`);
    }

    // Check if logged in
    isAuthenticated() {
        return !!this.token;
    }

    // API Secret Management
    async getApiSecret() {
        return await this.request('/auth/api-secret', {
            method: 'POST',
        });
    }

    async resetApiSecret() {
        return await this.request('/auth/reset-api-secret', {
            method: 'POST',
        });
    }

    async getProfile() {
        return await this.request('/auth/profile');
    }
}

export default new APIClient();
