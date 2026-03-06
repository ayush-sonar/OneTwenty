"""
WebSocket endpoint for real-time glucose data updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.websocket.manager import manager
from jose import jwt, JWTError
from app.core.config import settings
from app.repositories.user import UserRepository
import asyncio

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time updates.
    
    Authentication: JWT token via query parameter
    Usage: ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN
    """
    tenant_id = None
    
    try:
        # Authenticate using JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Get tenant for user
        repo = UserRepository()
        tenant_id = repo.get_tenant_for_user(user_id)
        
        if not tenant_id:
            await websocket.close(code=1008, reason="No tenant found")
            return
        
        tenant_id = str(tenant_id)
        
    except JWTError as e:
        print(f"[WebSocket] JWT error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    except Exception as e:
        print(f"[WebSocket] Auth error: {e}")
        await websocket.close(code=1011, reason="Internal error")
        return
    
    # Connect the WebSocket
    await manager.connect(websocket, tenant_id)
    
    try:
        # Keep connection alive and handle ping/pong
        while True:
            try:
                # Wait for messages from client (ping, etc.)
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                
                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive (Heroku 55s timeout)
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
                    
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected normally")
    except Exception as e:
        print(f"[WebSocket] Connection error: {e}")
    finally:
        await manager.disconnect(websocket, tenant_id)
