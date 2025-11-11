"""
Authentication endpoints (placeholder for MVP).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()
security = HTTPBearer()


@router.post("/login")
async def login():
    """Login endpoint (to be implemented)."""
    # TODO: Implement login logic
    return {"message": "Login endpoint - to be implemented"}


@router.post("/register")
async def register():
    """Registration endpoint (to be implemented)."""
    # TODO: Implement registration logic
    return {"message": "Register endpoint - to be implemented"}


@router.get("/me")
async def get_current_user():
    """Get current user (to be implemented)."""
    # TODO: Implement user retrieval
    return {"message": "Get current user - to be implemented"}

