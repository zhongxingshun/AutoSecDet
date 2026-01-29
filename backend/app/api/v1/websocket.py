"""
WebSocket endpoint for real-time task status updates.
"""
import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import verify_access_token
from app.core.logging import get_logger
from app.services.execution_service import ExecutionService

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages WebSocket connections for task updates."""
    
    def __init__(self):
        # task_id -> set of websocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: int):
        """Accept and register a new connection."""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logger.debug(f"WebSocket connected for task {task_id}")
    
    def disconnect(self, websocket: WebSocket, task_id: int):
        """Remove a connection."""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.debug(f"WebSocket disconnected for task {task_id}")
    
    async def broadcast_to_task(self, task_id: int, message: dict):
        """Broadcast message to all connections watching a task."""
        if task_id not in self.active_connections:
            return
        
        dead_connections = set()
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.active_connections[task_id].discard(conn)


# Global connection manager
manager = ConnectionManager()


async def get_token_from_query(token: str = Query(...)) -> dict:
    """Validate token from query parameter."""
    payload = verify_access_token(token)
    if payload is None:
        return None
    return payload


@router.websocket("/ws/tasks/{task_id}")
async def task_status_websocket(
    websocket: WebSocket,
    task_id: int,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time task status updates.
    
    Connect with: ws://host/api/v1/ws/tasks/{task_id}?token={jwt_token}
    
    Messages sent:
    - {"type": "status", "data": {...}} - Task status update
    - {"type": "result", "data": {...}} - Individual result update
    - {"type": "progress", "data": {...}} - Progress update
    - {"type": "complete", "data": {...}} - Task completion
    - {"type": "error", "message": "..."} - Error message
    """
    # Validate token
    payload = verify_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await manager.connect(websocket, task_id)
    
    try:
        # Send initial status
        db = next(get_db())
        try:
            execution_service = ExecutionService(db)
            stats = execution_service.get_task_stats(task_id)
            if stats:
                await websocket.send_json({
                    "type": "status",
                    "data": stats,
                })
        finally:
            db.close()
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for any message (ping/pong or close)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        manager.disconnect(websocket, task_id)


async def notify_task_update(task_id: int, update_type: str, data: dict):
    """
    Send task update to all connected clients.
    
    Args:
        task_id: Task ID
        update_type: Type of update (status, result, progress, complete, error)
        data: Update data
    """
    await manager.broadcast_to_task(task_id, {
        "type": update_type,
        "data": data,
    })


def sync_notify_task_update(task_id: int, update_type: str, data: dict):
    """
    Synchronous wrapper for notify_task_update.
    Used from Celery tasks.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(notify_task_update(task_id, update_type, data))
