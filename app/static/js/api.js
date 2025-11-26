// API utility functions
const API = {
    /**
     * Make authenticated API request
     */
    async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const headers = {
            ...options.headers
        };

        // Add auth token for non-GET requests
        if (options.method && options.method !== 'GET') {
            headers['Authorization'] = `Bearer ${CONFIG.AUTH_TOKEN}`;
        }

        // Add JSON content type if body is provided and not FormData
        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    /**
     * Upload file with progress tracking
     */
    async uploadFile(file, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const formData = new FormData();
            formData.append('file', file);

            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    onProgress(percentComplete, e.loaded, e.total);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(new Error('Invalid JSON response'));
                    }
                } else {
                    try {
                        const error = JSON.parse(xhr.responseText);
                        reject(new Error(error.detail || `HTTP ${xhr.status}`));
                    } catch (e) {
                        reject(new Error(`Upload failed: HTTP ${xhr.status}`));
                    }
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });

            xhr.open('POST', `${CONFIG.API_BASE_URL}/api/imports`);
            xhr.setRequestHeader('Authorization', `Bearer ${CONFIG.AUTH_TOKEN}`);
            xhr.send(formData);
        });
    },

    /**
     * Create SSE connection for real-time updates
     */
    createEventSource(endpoint) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        return new EventSource(url);
    }
};
