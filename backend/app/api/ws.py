import json
import asyncio
from typing import Dict, List, Set, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.logging import logger

ws_router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps incident_id (or 'global') to active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {"global": set()}

    async def connect(self, websocket: WebSocket, channel: str = "global"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket client connected to channel: {channel}")

    def disconnect(self, websocket: WebSocket, channel: str = "global"):
        if channel in self.active_connections and websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)
            logger.info(f"WebSocket client disconnected from channel: {channel}")

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        targets = set()
        if channel in self.active_connections:
            targets.update(self.active_connections[channel])
        if "global" in self.active_connections:
            targets.update(self.active_connections["global"])

        dead_connections = []
        payload = json.dumps(message)
        for connection in targets:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            for ch in self.active_connections.values():
                ch.discard(dead)

manager = ConnectionManager()

@ws_router.websocket("/ws")
async def websocket_global_endpoint(websocket: WebSocket):
    await manager.connect(websocket, channel="global")
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping/heartbeat or client subscriptions
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="global")

@ws_router.websocket("/ws/{incident_id}")
async def websocket_incident_endpoint(websocket: WebSocket, incident_id: str):
    await manager.connect(websocket, channel=incident_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "channel": incident_id}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel=incident_id)
