"""
API v1 router aggregating all endpoints.
"""
from fastapi import APIRouter

from app.api.v1 import health, auth, users, cases, categories, tasks, websocket, reports

api_router = APIRouter()

# Health check
api_router.include_router(health.router)

# Authentication
api_router.include_router(auth.router)

# User management
api_router.include_router(users.router)

# Case management
api_router.include_router(cases.router)

# Category management
api_router.include_router(categories.router)

# Task management
api_router.include_router(tasks.router)

# WebSocket
api_router.include_router(websocket.router)

# Reports
api_router.include_router(reports.router)
