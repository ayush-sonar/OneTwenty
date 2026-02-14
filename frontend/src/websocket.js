/**
 * WebSocket client for real-time glucose data updates
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // Start with 2 seconds
        this.listeners = new Map();
        this.isConnecting = false;
    }

    /**
     * Connect to WebSocket server
     * @param {string} token - JWT authentication token
     */
    connect(token) {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            console.log('[WebSocket] Already connected or connecting');
            return;
        }

        this.isConnecting = true;

        // Determine WebSocket URL based on environment
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const apiUrl = import.meta.env.VITE_API_URL || 'https://nightscout-saas-59b9ddfa8c5b.herokuapp.com';
        const wsUrl = apiUrl.replace(/^https?:/, protocol);
        const url = `${wsUrl}/api/v1/ws?token=${token}`;

        console.log('[WebSocket] Connecting to:', wsUrl);

        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log('[WebSocket] Connected successfully');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 2000;
                this.emit('connected');

                // Start ping interval to keep connection alive
                this.startPingInterval();
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log('[WebSocket] Received:', message.type);

                    if (message.type === 'new_entry') {
                        this.emit('new_entry', message.data);
                    } else if (message.type === 'ping') {
                        // Respond to server ping
                        this.send({ type: 'pong' });
                    } else if (message.type === 'pong') {
                        // Server responded to our ping
                        console.log('[WebSocket] Pong received');
                    }
                } catch (error) {
                    console.error('[WebSocket] Error parsing message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('[WebSocket] Error:', error);
                this.isConnecting = false;
                this.emit('error', error);
            };

            this.ws.onclose = (event) => {
                console.log('[WebSocket] Disconnected:', event.code, event.reason);
                this.isConnecting = false;
                this.stopPingInterval();
                this.emit('disconnected');

                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
                    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

                    setTimeout(() => {
                        this.connect(token);
                    }, delay);
                } else {
                    console.error('[WebSocket] Max reconnection attempts reached');
                    this.emit('max_reconnect_reached');
                }
            };
        } catch (error) {
            console.error('[WebSocket] Connection error:', error);
            this.isConnecting = false;
            this.emit('error', error);
        }
    }

    /**
     * Send a message to the server
     */
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('[WebSocket] Cannot send message, not connected');
        }
    }

    /**
     * Start ping interval to keep connection alive (Heroku requirement)
     */
    startPingInterval() {
        this.stopPingInterval(); // Clear any existing interval
        this.pingInterval = setInterval(() => {
            this.send({ type: 'ping' });
        }, 25000); // Ping every 25 seconds (Heroku timeout is 55s)
    }

    /**
     * Stop ping interval
     */
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Disconnect from WebSocket
     */
    disconnect() {
        this.stopPingInterval();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    }

    /**
     * Register an event listener
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * Remove an event listener
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * Emit an event to all registered listeners
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[WebSocket] Error in ${event} listener:`, error);
                }
            });
        }
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Export singleton instance
export default new WebSocketClient();
