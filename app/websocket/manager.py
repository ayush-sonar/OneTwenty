"""
WebSocket connection manager for real-time updates.
Manages connections per tenant and broadcasts new entries.
"""
from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        # tenant_id -> list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Accept and register a new WebSocket connection for a tenant."""
        await websocket.accept()
        
        async with self._lock:
            if tenant_id not in self.active_connections:
                self.active_connections[tenant_id] = []
            self.active_connections[tenant_id].append(websocket)
        
        print(f"[WebSocket] Client connected for tenant {tenant_id}. Total connections: {len(self.active_connections[tenant_id])}")

    async def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if tenant_id in self.active_connections:
                if websocket in self.active_connections[tenant_id]:
                    self.active_connections[tenant_id].remove(websocket)
                
                # Clean up empty tenant lists
                if not self.active_connections[tenant_id]:
                    del self.active_connections[tenant_id]
        
        print(f"[WebSocket] Client disconnected for tenant {tenant_id}")

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        """Broadcast a message to all connections for a specific tenant."""
        if tenant_id not in self.active_connections:
            return  # No connections for this tenant
        
        # Create list copy to avoid modification during iteration
        connections = self.active_connections[tenant_id].copy()
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if conn in self.active_connections.get(tenant_id, []):
                        self.active_connections[tenant_id].remove(conn)
        
        print(f"[WebSocket] Broadcasted to {len(connections) - len(disconnected)} clients for tenant {tenant_id}")

    def get_connection_count(self, tenant_id: str = None) -> int:
        """Get the number of active connections for a tenant or total."""
        if tenant_id:
            return len(self.active_connections.get(tenant_id, []))
        return sum(len(conns) for conns in self.active_connections.values())


# Global instance
manager = ConnectionManager()
