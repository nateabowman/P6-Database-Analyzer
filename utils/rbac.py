"""Role-based access control (RBAC) for P6 Database Analyzer."""

from typing import List, Dict, Set, Optional
from enum import Enum
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Permission(Enum):
    """System permissions."""
    # Analysis permissions
    RUN_ANALYSIS = "analysis:run"
    VIEW_ANALYSIS = "analysis:view"
    EXPORT_REPORTS = "reports:export"
    
    # Configuration permissions
    MANAGE_CONNECTIONS = "config:connections"
    MANAGE_PROFILES = "config:profiles"
    VIEW_CONFIG = "config:view"
    
    # User management permissions
    MANAGE_USERS = "users:manage"
    VIEW_USERS = "users:view"
    
    # System permissions
    VIEW_LOGS = "system:logs"
    MANAGE_SETTINGS = "system:settings"
    ADMIN = "system:admin"


class Role:
    """Role definition with permissions."""
    
    def __init__(self, name: str, permissions: List[Permission], description: str = ""):
        self.name = name
        self.permissions = set(permissions)
        self.description = description
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a permission."""
        return permission in self.permissions
    
    def add_permission(self, permission: Permission):
        """Add a permission to the role."""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Permission):
        """Remove a permission from the role."""
        self.permissions.discard(permission)


class RBACManager:
    """Manages roles and permissions."""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self._initialize_default_roles()
    
    def _initialize_default_roles(self):
        """Initialize default system roles."""
        # Admin role - all permissions
        admin_role = Role(
            "admin",
            list(Permission),
            "Administrator with full access"
        )
        self.roles["admin"] = admin_role
        
        # Analyst role - analysis and reporting
        analyst_role = Role(
            "analyst",
            [
                Permission.RUN_ANALYSIS,
                Permission.VIEW_ANALYSIS,
                Permission.EXPORT_REPORTS,
                Permission.VIEW_CONFIG,
                Permission.VIEW_LOGS
            ],
            "Database analyst with analysis and reporting capabilities"
        )
        self.roles["analyst"] = analyst_role
        
        # Viewer role - read-only access
        viewer_role = Role(
            "viewer",
            [
                Permission.VIEW_ANALYSIS,
                Permission.VIEW_CONFIG,
                Permission.VIEW_USERS
            ],
            "Read-only access to analysis results"
        )
        self.roles["viewer"] = viewer_role
        
        # Operator role - limited management
        operator_role = Role(
            "operator",
            [
                Permission.RUN_ANALYSIS,
                Permission.VIEW_ANALYSIS,
                Permission.EXPORT_REPORTS,
                Permission.MANAGE_CONNECTIONS,
                Permission.VIEW_LOGS
            ],
            "Operator with analysis and connection management"
        )
        self.roles["operator"] = operator_role
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """Get a role by name."""
        return self.roles.get(role_name)
    
    def create_role(self, name: str, permissions: List[Permission], description: str = "") -> Role:
        """
        Create a new custom role.
        
        Args:
            name: Role name
            permissions: List of permissions
            description: Role description
        
        Returns:
            Created role
        """
        if name in self.roles:
            raise ValueError(f"Role '{name}' already exists")
        
        role = Role(name, permissions, description)
        self.roles[name] = role
        logger.info(f"Created role: {name}")
        return role
    
    def check_permission(self, user_roles: List[str], permission: Permission) -> bool:
        """
        Check if user has a permission based on their roles.
        
        Args:
            user_roles: List of user role names
            permission: Permission to check
        
        Returns:
            True if user has permission
        """
        for role_name in user_roles:
            role = self.get_role(role_name)
            if role and role.has_permission(permission):
                return True
        return False
    
    def get_user_permissions(self, user_roles: List[str]) -> Set[Permission]:
        """
        Get all permissions for a user based on their roles.
        
        Args:
            user_roles: List of user role names
        
        Returns:
            Set of permissions
        """
        permissions = set()
        for role_name in user_roles:
            role = self.get_role(role_name)
            if role:
                permissions.update(role.permissions)
        return permissions


# Global RBAC manager instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get the global RBAC manager instance."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager

