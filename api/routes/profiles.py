"""Connection profile API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from api.auth import get_current_user, require_permission
from utils.rbac import Permission
from utils.logging_config import get_logger
from utils.credential_manager import get_credential_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


@router.get("/")
async def list_profiles(
    current_user: dict = Depends(require_permission(Permission.VIEW_CONFIG.value))
):
    """List all connection profiles."""
    try:
        cred_manager = get_credential_manager()
        profiles = cred_manager.list_profiles()
        return {"status": "success", "profiles": profiles}
    except Exception as e:
        logger.error(f"Failed to list profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{profile_name}")
async def get_profile(
    profile_name: str,
    current_user: dict = Depends(require_permission(Permission.VIEW_CONFIG.value))
):
    """Get a connection profile."""
    try:
        cred_manager = get_credential_manager()
        profile = cred_manager.load_connection_profile(profile_name)
        # Don't return password in response
        profile.pop('password', None)
        return {"status": "success", "profile": profile}
    except Exception as e:
        logger.error(f"Failed to get profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found: {profile_name}"
        )


@router.post("/")
async def create_profile(
    profile_data: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.MANAGE_PROFILES.value))
):
    """Create a new connection profile."""
    try:
        cred_manager = get_credential_manager()
        cred_manager.save_connection_profile(
            profile_name=profile_data['name'],
            db_type=profile_data['db_type'],
            host=profile_data['host'],
            port=profile_data.get('port'),
            service=profile_data['service'],
            username=profile_data['username'],
            password=profile_data['password']
        )
        return {"status": "success", "message": f"Profile '{profile_data['name']}' created"}
    except Exception as e:
        logger.error(f"Failed to create profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{profile_name}")
async def delete_profile(
    profile_name: str,
    current_user: dict = Depends(require_permission(Permission.MANAGE_PROFILES.value))
):
    """Delete a connection profile."""
    try:
        cred_manager = get_credential_manager()
        cred_manager.delete_connection_profile(profile_name)
        return {"status": "success", "message": f"Profile '{profile_name}' deleted"}
    except Exception as e:
        logger.error(f"Failed to delete profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

