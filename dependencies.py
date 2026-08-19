"""
Shared FastAPI dependency injection providers.
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.database import get_db
from app.models.users import User
from app.repositories.user_repository import UserRepository, user_repository
from app.services.auth_service import AuthService, auth_service
from app.services.analytics_service import AnalyticsService, analytics_service
from app.services.report_service import ReportService, report_service
from app.services.delivery_service import DeliveryService, delivery_service
from app.services.invoice_service import InvoiceService, invoice_service
from app.services.procurement_service import (
    ProcurementService,
    procurement_service,
)
from app.services.user_service import UserService, user_service
from app.services.vendor_performance_service import (
    VendorPerformanceService,
    vendor_performance_service,
)
from app.services.vendor_service import VendorService, vendor_service


# JWT Bearer authentication scheme.
#
# This is used by Swagger/OpenAPI to send:
# Authorization: Bearer <access_token>
#
# The actual login endpoint remains unchanged and can continue
# accepting JSON username/password.
bearer_scheme = HTTPBearer()


def get_user_service() -> UserService:
    """
    Dependency provider for UserService instance.
    """
    return user_service


def get_auth_service() -> AuthService:
    """
    Dependency provider for AuthService instance.
    """
    return auth_service


def get_vendor_service() -> VendorService:
    """
    Dependency provider for VendorService instance.
    """
    return vendor_service


def get_procurement_service() -> ProcurementService:
    """
    Dependency provider for ProcurementService instance.
    """
    return procurement_service


def get_invoice_service() -> InvoiceService:
    """
    Dependency provider for InvoiceService instance.
    """
    return invoice_service


def get_delivery_service() -> DeliveryService:
    """
    Dependency provider for DeliveryService instance.
    """
    return delivery_service


def get_vendor_performance_service() -> VendorPerformanceService:
    """
    Dependency provider for VendorPerformanceService instance.
    """
    return vendor_performance_service


def get_analytics_service() -> AnalyticsService:
    """
    Dependency provider for AnalyticsService instance.
    """
    return analytics_service


def get_report_service() -> ReportService:
    """
    Dependency provider for ReportService instance.
    """
    return report_service


def get_user_repository() -> UserRepository:
    """
    Dependency provider for UserRepository instance.
    """
    return user_repository


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Resolve the authenticated active user from a Bearer access token.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        user_id = get_current_user_id(token)
    except JWTError as exc:
        raise credentials_exception from exc

    user = await repo.get_user_by_id(db, user_id)

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return user


def require_roles(
    *allowed_roles: str,
) -> Callable[..., User]:
    """
    Require the current authenticated user to have one of the allowed roles.
    """

    def normalize_role(role: str) -> str:
        return role.strip().upper().replace(" ", "_").replace("-", "_")

    normalized_roles = {
        normalize_role(role)
        for role in allowed_roles
    }

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        current_role = (
            normalize_role(current_user.role.role_name)
            if current_user.role and current_user.role.role_name
            else None
        )

        if current_role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_checker